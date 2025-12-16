# Parental Control System - Database Setup

## Prerequisites

1. **MySQL Server** installed and running
2. **Python 3.9+**
3. Virtual environment activated

## Database Setup Steps

### 1. Create the Database

**Option A: Using MySQL Command Line**

```bash
mysql -u root -p < setup_database.sql
```

**Option B: Using MySQL Workbench**
- Open MySQL Workbench
- Open the `setup_database.sql` file
- Execute the script

**Option C: Manual Setup**

```sql
CREATE DATABASE parental_control;
USE parental_control;

CREATE TABLE content_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(500),
    detected_text LONGTEXT,
    ip_address VARCHAR(50),
    browser_info VARCHAR(255),
    platform VARCHAR(100),
    screen_resolution VARCHAR(50),
    timezone VARCHAR(50),
    language VARCHAR(50),
    timestamp DATETIME,
    device_info_json LONGTEXT,
    scores_json LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_ip (ip_address)
);
```

### 2. Configure Database Credentials

Edit `backend_model/api_model.py` and update the `DB_CONFIG`:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",  # Change to your password
    "database": "parental_control"
}
```

### 3. Install Python Dependency

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
source venv/bin/activate
python3 backend_model/api_model.py
```

The API will:
- Create tables automatically if they don't exist
- Listen on `http://127.0.0.1:8000`

## Database Structure

### Table: `content_alerts`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Primary key, auto-increment |
| `url` | VARCHAR(500) | Detected website URL |
| `detected_text` | LONGTEXT | Inappropriate content text (first 1000 chars) |
| `ip_address` | VARCHAR(50) | Child's public IP address |
| `browser_info` | VARCHAR(255) | Browser user agent |
| `platform` | VARCHAR(100) | Operating system |
| `screen_resolution` | VARCHAR(50) | Screen resolution (e.g., "1920x1080") |
| `timezone` | VARCHAR(50) | Device timezone |
| `language` | VARCHAR(50) | Browser language |
| `timestamp` | DATETIME | When alert occurred |
| `device_info_json` | LONGTEXT | Complete device info as JSON |
| `scores_json` | LONGTEXT | Toxicity scores as JSON |
| `created_at` | TIMESTAMP | Database insertion time |

## Querying Alerts

View all recent alerts:
```sql
SELECT url, ip_address, platform, timestamp 
FROM content_alerts 
ORDER BY timestamp DESC 
LIMIT 10;
```

View alerts by IP:
```sql
SELECT * FROM content_alerts 
WHERE ip_address = '203.0.113.25' 
ORDER BY timestamp DESC;
```

View alerts by date:
```sql
SELECT * FROM content_alerts 
WHERE DATE(timestamp) = '2025-12-16' 
ORDER BY timestamp DESC;
```

View most visited problematic sites:
```sql
SELECT url, COUNT(*) as alert_count 
FROM content_alerts 
GROUP BY url 
ORDER BY alert_count DESC;
```

## Troubleshooting

**Connection Error: "Access denied for user 'root'@'localhost'"**
- Check MySQL is running: `mysql -u root -p`
- Update password in `DB_CONFIG`

**Table doesn't exist**
- The app creates tables automatically on startup
- Or manually run `setup_database.sql`

**Database doesn't exist**
- Run setup script first
- Check database name matches `DB_CONFIG`

## Features

✅ Automatic table creation  
✅ Device information tracking (IP, OS, browser, screen, timezone)  
✅ Content text storage (first 1000 characters)  
✅ Toxicity scores saved as JSON  
✅ Timestamp indexing for fast queries  
✅ IP address indexing for easy lookups  
✅ Email sent after database save  
