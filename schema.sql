-- ============================================================
-- CivicFix - Smart City Complaint Management System
-- MySQL Database Schema
-- ============================================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS civicfix;
USE civicfix;

-- ============================================================
-- Table: users
-- Stores registered citizens and admin accounts
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100)  NOT NULL,
    email      VARCHAR(150)  NOT NULL UNIQUE,
    password   VARCHAR(255)  NOT NULL,          -- bcrypt hashed
    role       ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table: complaints
-- Stores all city complaints submitted by users
-- ============================================================
CREATE TABLE IF NOT EXISTS complaints (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    title       VARCHAR(200) NOT NULL,
    description TEXT         NOT NULL,
    category    ENUM(
        'Pothole',
        'Garbage',
        'Water Leakage',
        'Street Light',
        'Sewage',
        'Road Damage',
        'Noise Pollution',
        'Other'
    ) NOT NULL,
    location    VARCHAR(300) NOT NULL,
    image       VARCHAR(255) DEFAULT NULL,       -- stored filename
    status      ENUM('Submitted', 'In Progress', 'Resolved') DEFAULT 'Submitted',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_status   (status),
    INDEX idx_user_id  (user_id),
    INDEX idx_category (category)
);

-- ============================================================
-- Seed Data: Default admin account
-- Password: admin123  (bcrypt hash below)
-- Change this password immediately in production!
-- ============================================================
INSERT INTO users (name, email, password, role) VALUES (
    'Admin',
    'admin@civicfix.com',
    '$2b$12$KiXbOeKMhJJPDoHMCMzOGOdFX4H6VHSo8z.lQF1c.Fm3Uo.IaKP4q',
    'admin'
) ON DUPLICATE KEY UPDATE name = name;

-- ============================================================
-- Sample complaint (optional, for testing)
-- ============================================================
-- INSERT INTO complaints (user_id, title, description, category, location, status)
-- VALUES (1, 'Large pothole on MG Road', 'Deep pothole causing accidents near bus stop.',
--         'Pothole', 'MG Road, near Bus Stop 12', 'Submitted');
