-- Create database for Parental Control System
CREATE DATABASE IF NOT EXISTS parental_control;

-- Use the database
USE parental_control;

-- Create content_alerts table
CREATE TABLE IF NOT EXISTS content_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(500),
    detected_text LONGTEXT,
    ip_address VARCHAR(50),
    browser_info VARCHAR(255),
    platform VARCHAR(100),
    screen_resolution VARCHAR(50),
    timezone VARCHAR(50),
    language VARCHAR(50),
    detected_at DATETIME,
    device_info_json LONGTEXT,
    scores_json LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_detected_at (detected_at),
    INDEX idx_ip (ip_address)
) ENGINE=InnoDB;

-- Show tables
SHOW TABLES;

-- Display table structure
DESCRIBE content_alerts;
