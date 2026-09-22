# ── Base image: Python 3.11 slim version ──
FROM python:3.11-slim

# ── Set working directory inside container ──
WORKDIR /app

# ── Copy requirements first (for caching) ──
COPY requirements.txt .

# ── Install Python dependencies ──
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy entire project into container ──
COPY . .

# ── Create uploads folder ──
RUN mkdir -p uploads

# ── Expose Flask port ──
EXPOSE 5000

# ── Start Flask app ──
CMD ["python", "app.py"]