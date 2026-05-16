"""
CivicFix - Smart City Complaint Management System
Flask Backend Application
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import mysql.connector
import bcrypt
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='frontend', static_url_path='')
app.secret_key = 'civicfix_secret_key_change_in_production'
CORS(app, supports_credentials=True)

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# ─────────────────────────────────────────────
# MySQL Database Connection
# ─────────────────────────────────────────────
import os

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'rathikavi'),
    'database': os.environ.get('DB_NAME', 'civicfix'),
    'port': int(os.environ.get('DB_PORT', 3306))
}
def get_db():
    """Create and return a MySQL database connection."""
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─────────────────────────────────────────────
# Serve Frontend Pages
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('frontend', filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────

@app.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role     = data.get('role', 'user')   # 'user' or 'admin'

    if not all([name, email, password]):
        return jsonify({'error': 'All fields are required'}), 400

    # Hash the password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 409

        cursor.execute(
            'INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)',
            (name, email, hashed, role)
        )
        conn.commit()
        return jsonify({'message': 'Registration successful'}), 201
    finally:
        cursor.close()
        conn.close()


@app.route('/login', methods=['POST'])
def login():
    """Authenticate a user and start a session."""
    data = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Invalid email or password'}), 401

        # Store user info in session
        session['user_id']   = user['id']
        session['user_name'] = user['name']
        session['user_role'] = user['role']

        return jsonify({
            'message': 'Login successful',
            'user': {
                'id':   user['id'],
                'name': user['name'],
                'role': user['role']
            }
        }), 200
    finally:
        cursor.close()
        conn.close()


@app.route('/logout', methods=['POST'])
def logout():
    """Clear the user session."""
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/me', methods=['GET'])
def me():
    """Return the currently logged-in user info."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({
        'id':   session['user_id'],
        'name': session['user_name'],
        'role': session['user_role']
    }), 200

# ─────────────────────────────────────────────
# COMPLAINT ROUTES
# ─────────────────────────────────────────────

@app.route('/add-complaint', methods=['POST'])
def add_complaint():
    """Submit a new complaint (multipart/form-data)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login to submit a complaint'}), 401

    title       = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category    = request.form.get('category', '').strip()
    location    = request.form.get('location', '').strip()

    if not all([title, description, category, location]):
        return jsonify({'error': 'All fields are required'}), 400

    # Handle optional image upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            image_filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            '''INSERT INTO complaints
               (user_id, title, description, category, location, image, status)
               VALUES (%s, %s, %s, %s, %s, %s, 'Submitted')''',
            (session['user_id'], title, description, category, location, image_filename)
        )
        conn.commit()
        return jsonify({'message': 'Complaint submitted successfully', 'id': cursor.lastrowid}), 201
    finally:
        cursor.close()
        conn.close()


@app.route('/get-complaints', methods=['GET'])
def get_complaints():
    """
    Fetch complaints.
    - Admin: all complaints
    - User:  their own complaints only
    Query params: status (filter), page, per_page
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    status   = request.args.get('status', '')
    page     = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset   = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Build query
        base_query = '''
            SELECT c.*, u.name AS user_name, u.email AS user_email
            FROM complaints c
            JOIN users u ON c.user_id = u.id
        '''
        conditions = []
        params = []

        if session['user_role'] != 'admin':
            conditions.append('c.user_id = %s')
            params.append(session['user_id'])

        if status:
            conditions.append('c.status = %s')
            params.append(status)

        if conditions:
            base_query += ' WHERE ' + ' AND '.join(conditions)

        base_query += ' ORDER BY c.created_at DESC LIMIT %s OFFSET %s'
        params += [per_page, offset]

        cursor.execute(base_query, params)
        complaints = cursor.fetchall()

        # Convert datetime to string
        for c in complaints:
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        # Count totals
        count_query = 'SELECT COUNT(*) AS total FROM complaints c'
        count_params = []
        if session['user_role'] != 'admin':
            count_query += ' WHERE c.user_id = %s'
            count_params.append(session['user_id'])
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']

        return jsonify({'complaints': complaints, 'total': total, 'page': page}), 200
    finally:
        cursor.close()
        conn.close()


@app.route('/update-status', methods=['POST'])
def update_status():
    """Admin-only: update the status of a complaint."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    if session.get('user_role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data         = request.get_json()
    complaint_id = data.get('complaint_id')
    new_status   = data.get('status')

    valid_statuses = ['Submitted', 'In Progress', 'Resolved']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE complaints SET status = %s WHERE id = %s',
            (new_status, complaint_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Complaint not found'}), 404
        return jsonify({'message': 'Status updated successfully'}), 200
    finally:
        cursor.close()
        conn.close()


@app.route('/stats', methods=['GET'])
def stats():
    """Return aggregate stats (used by dashboards)."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if session['user_role'] == 'admin':
            cursor.execute('''
                SELECT
                    COUNT(*) AS total,
                    SUM(status = 'Submitted')   AS submitted,
                    SUM(status = 'In Progress') AS in_progress,
                    SUM(status = 'Resolved')    AS resolved
                FROM complaints
            ''')
        else:
            cursor.execute('''
                SELECT
                    COUNT(*) AS total,
                    SUM(status = 'Submitted')   AS submitted,
                    SUM(status = 'In Progress') AS in_progress,
                    SUM(status = 'Resolved')    AS resolved
                FROM complaints WHERE user_id = %s
            ''', (session['user_id'],))
        return jsonify(cursor.fetchone()), 200
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
