-- Create and select database
CREATE DATABASE IF NOT EXISTS face_login_db;
USE face_login_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(100),
    role VARCHAR(50) DEFAULT 'employee',
    face_encoding LONGTEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Login logs table (track access attempts)
CREATE TABLE IF NOT EXISTS login_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    employee_id VARCHAR(50),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('success', 'failed') NOT NULL,
    confidence_score FLOAT,
    ip_address VARCHAR(45),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes for faster lookups
CREATE INDEX idx_employee_id ON users(employee_id);
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_login_time ON login_logs(login_time);
CREATE INDEX idx_login_status ON login_logs(status);

-- Sample insert
INSERT INTO users (employee_id, full_name, email, department, role, face_encoding)
VALUES 
    ('EMP001', 'vel', 'vel@company.com', 'IT', 'admin', '[0.123, 0.456, ...]'),
    
-- Verify tables
SHOW TABLES;
SELECT * FROM users;