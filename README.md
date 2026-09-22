# 🏙️ CivicFix — Smart City Complaint Management System

A full-stack web app where citizens report city issues and admins manage/resolve them.

---

## 📁 Folder Structure

```
civicfix/
├── app.py                  ← Flask backend (all API routes)
├── requirements.txt        ← Python dependencies
├── schema.sql              ← MySQL database schema
├── uploads/                ← Uploaded complaint images (auto-created)
└── frontend/
    ├── style.css           ← Shared design system
    ├── index.html          ← Landing page
    ├── login.html          ← Login page
    ├── register.html       ← Registration page
    ├── complaint_form.html ← Submit complaint
    ├── user_dashboard.html ← Citizen dashboard
    └── admin_dashboard.html← Admin dashboard
```

---

## ⚙️ Step 1: Install MySQL

### Windows
1. Download MySQL Installer: https://dev.mysql.com/downloads/installer/
2. Run installer → choose "MySQL Server" + "MySQL Workbench"
3. Set a root password during setup (remember it!)
4. Start MySQL from Windows Services or MySQL Workbench

### macOS
```bash
brew install mysql
brew services start mysql
mysql_secure_installation   # set root password
```

### Ubuntu/Linux
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo mysql_secure_installation
```

---

## 🗄️ Step 2: Set Up the Database

### Option A: Command Line
```bash
# Login to MySQL
mysql -u root -p

# Paste and run the schema
source /path/to/civicfix/schema.sql;

# Or manually:
CREATE DATABASE civicfix;
USE civicfix;
# Then paste the CREATE TABLE statements from schema.sql
```

### Option B: MySQL Workbench
1. Open MySQL Workbench
2. Connect to localhost with root
3. File → Open SQL Script → select `schema.sql`
4. Click the ⚡ (Execute) button

### Verify Setup
```sql
USE civicfix;
SHOW TABLES;
-- Should show: users, complaints

SELECT * FROM users;
-- Should show the default admin account
```

---

## 🐍 Step 3: Set Up Python Environment

```bash
# Navigate to project folder
cd civicfix

# Create virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔌 Step 4: Configure MySQL in Flask

Open `app.py` and find the DB_CONFIG section:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',   # ← CHANGE THIS
    'database': 'civicfix',
    'port': 3306
}
```

Replace `'your_password'` with your actual MySQL root password.

### Test the Connection
```bash
python -c "
import mysql.connector
conn = mysql.connector.connect(
    host='localhost', user='root',
    password='your_password', database='civicfix'
)
print('✅ Connected!', conn.get_server_info())
conn.close()
"
```

---

## 🚀 Step 5: Run the App

```bash
# Make sure you're in the civicfix/ folder with venv activated
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Open your browser: **http://localhost:5000**

---

## 👤 Demo Accounts

| Role  | Email                  | Password  |
|-------|------------------------|-----------|
| Admin | admin@civicfix.com     | admin123  |

To create a citizen account, click "Register" on the homepage.

---

## 🔗 API Endpoints

| Method | Route             | Description                  | Auth Required |
|--------|-------------------|------------------------------|---------------|
| POST   | /register         | Register new user            | No            |
| POST   | /login            | Login & start session        | No            |
| POST   | /logout           | Clear session                | Yes           |
| GET    | /me               | Get current user info        | Yes           |
| POST   | /add-complaint    | Submit new complaint         | User          |
| GET    | /get-complaints   | Get complaints (own/all)     | Yes           |
| POST   | /update-status    | Update complaint status      | Admin only    |
| GET    | /stats            | Get complaint statistics     | Yes           |

---

## 🗄️ Database Schema

```sql
-- Users table
CREATE TABLE users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,       -- bcrypt hashed
    role       ENUM('user','admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Complaints table
CREATE TABLE complaints (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    title       VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category    ENUM('Pothole','Garbage','Water Leakage',
                     'Street Light','Sewage','Road Damage',
                     'Noise Pollution','Other') NOT NULL,
    location    VARCHAR(300) NOT NULL,
    image       VARCHAR(255) DEFAULT NULL,
    status      ENUM('Submitted','In Progress','Resolved') DEFAULT 'Submitted',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 🛠️ Troubleshooting

**"Access denied for user 'root'"**
→ Wrong password in DB_CONFIG. Double-check your MySQL root password.

**"No module named 'flask'"**
→ Run `pip install -r requirements.txt` with venv activated.

**"Can't connect to MySQL server"**
→ MySQL service isn't running. Start it:
- Windows: Services → MySQL → Start
- macOS: `brew services start mysql`
- Linux: `sudo systemctl start mysql`

**Images not uploading**
→ Make sure the `uploads/` folder exists in the civicfix directory.

**Port 5000 already in use**
→ Change `app.run(port=5000)` to `app.run(port=5001)` in app.py.

---

## 🔐 Security Notes (for production)

1. Change `app.secret_key` to a long random string
2. Use environment variables for DB credentials (not hardcoded)
3. Add HTTPS / SSL certificate
4. Use a production WSGI server like Gunicorn
5. Limit file upload types and scan for malware
6. Add rate limiting on login/register endpoints
