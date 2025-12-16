from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from transformers import pipeline
import uvicorn

import smtplib
from email.mime.text import MIMEText
from email.message import EmailMessage
import mysql.connector
from datetime import datetime
import json

# Email template
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            max-width: 700px;
            margin: 0 auto;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }}
        .header {{
            background: linear-gradient(135deg, #d9534f 0%, #c9302c 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 25px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 5px;
        }}
        .header p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .content {{
            color: #333;
            line-height: 1.8;
            margin-bottom: 25px;
        }}
        .section {{
            margin-bottom: 20px;
        }}
        .section-title {{
            font-weight: bold;
            color: #d9534f;
            font-size: 16px;
            margin-bottom: 10px;
            border-bottom: 2px solid #d9534f;
            padding-bottom: 8px;
        }}
        .info-box {{
            background-color: #f5f5f5;
            padding: 15px;
            border-left: 4px solid #d9534f;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .info-label {{
            font-weight: 600;
            color: #555;
            width: 40%;
        }}
        .info-value {{
            color: #333;
            word-break: break-all;
            width: 60%;
            text-align: right;
        }}
        .alert-box {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }}
        .action-box {{
            background-color: #e8f4f8;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }}
        .footer {{
            color: #999;
            font-size: 12px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
            margin-top: 25px;
            text-align: center;
        }}
        .timestamp {{
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Alerte de Contrôle Parental</h1>
            <p>Contenu inapproprié détecté</p>
        </div>
        
        <div class="content">
            <p>Bonjour,</p>
            <p>Notre système de contrôle parental a détecté du contenu potentiellement inapproprié lors de l'utilisation du navigateur de votre enfant.</p>
            
            <div class="section">
                <div class="section-title">📍 Information du Site</div>
                <div class="info-box">
                    <div class="info-row">
                        <span class="info-label">URL détectée:</span>
                        <span class="info-value">{url}</span>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">💻 Information de l'Appareil</div>
                <div class="info-box">
                    {device_info_html}
                </div>
            </div>
            
            <div class="alert-box">
                <strong>⚠️ Conseil:</strong> Nous vous recommandons vivement de vérifier l'activité en ligne de votre enfant et de discuter des contenus appropriés. Vous pouvez aussi ajuster les paramètres de restriction du navigateur.
            </div>
            
            <div class="action-box">
                <strong>💡 Prochaines étapes:</strong>
                <ul style="margin-top: 10px; margin-left: 20px;">
                    <li>Parlez avec votre enfant du contenu détecté</li>
                    <li>Renforcez les contrôles parentaux si nécessaire</li>
                    <li>Envisagez de limiter certains sites web</li>
                    <li>Encouragez une navigation sécurisée</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Ce message a été généré automatiquement par le système de contrôle parental.</p>
            <p class="timestamp">Heure de détection: {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""

def format_device_info(device_info: dict) -> str:
    """Format device information as HTML table rows"""
    html_rows = ""
    
    if not device_info:
        return "<div class='info-row'><span class='info-label'>Aucune info</span><span class='info-value'>-</span></div>"
    
    mappings = {
        "publicIP": "Adresse IP Publique",
        "userAgent": "Navigateur",
        "platform": "Système d'Exploitation",
        "language": "Langue",
        "screenWidth": "Résolution Écran",
        "timezone": "Fuseau Horaire",
        "onLine": "Connecté",
        "timestamp": "Heure de Détection"
    }
    
    for key, label in mappings.items():
        value = device_info.get(key, "-")
        
        # Format specific values
        if key == "screenWidth":
            width = device_info.get("screenWidth", 0)
            height = device_info.get("screenHeight", 0)
            value = f"{width}x{height}" if width and height else "-"
        elif key == "onLine":
            value = "✅ Oui" if value else "❌ Non"
        elif key == "userAgent":
            value = str(value)[:50] + "..." if len(str(value)) > 50 else value
        
        html_rows += f"""
        <div class="info-row">
            <span class="info-label">{label}:</span>
            <span class="info-value">{value}</span>
        </div>
        """
    
    return html_rows


# MySQL Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Change this to your MySQL password
    "database": "parental_control"
}


def create_database_connection():
    """Create a connection to MySQL database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        return None


def create_tables():
    """Create tables if they don't exist"""
    try:
        connection = create_database_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        
        # Create alerts table
        create_alerts_table = """
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
        ) ENGINE=InnoDB
        """
        
        cursor.execute(create_alerts_table)
        connection.commit()
        print("✅ Database tables created/verified successfully!")
        cursor.close()
        connection.close()
        return True
    except mysql.connector.Error as err:
        print(f"❌ Error creating tables: {err}")
        return False


def save_alert_to_database(text, url, device_info, scores):
    """Save alert data to MySQL database"""
    try:
        connection = create_database_connection()
        if not connection:
            print("⚠️ Could not connect to database")
            return False
        
        cursor = connection.cursor()
        
        # Extract device info
        ip = device_info.get("publicIP", "Unknown")
        browser = device_info.get("userAgent", "Unknown")
        platform = device_info.get("platform", "Unknown")
        screen = f"{device_info.get('screenWidth', 'N/A')}x{device_info.get('screenHeight', 'N/A')}"
        timezone = device_info.get("timezone", "Unknown")
        language = device_info.get("language", "Unknown")
        
        # Parse and format timestamp for MySQL DATETIME
        timestamp_str = device_info.get("timestamp", datetime.now().isoformat())
        try:
            # Parse ISO format timestamp (e.g., '2025-12-16T18:46:52.531Z')
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]  # Remove 'Z'
            
            # Try to parse with milliseconds
            if '.' in timestamp_str:
                timestamp_obj = datetime.fromisoformat(timestamp_str.split('.')[0])
            else:
                timestamp_obj = datetime.fromisoformat(timestamp_str)
            
            # Format for MySQL DATETIME: YYYY-MM-DD HH:MM:SS
            mysql_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"⚠️ Error parsing timestamp: {e}, using current time")
            mysql_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert complex objects to JSON
        device_info_json = json.dumps(device_info)
        scores_json = json.dumps(scores)
        
        # Insert alert into database
        insert_query = """
        INSERT INTO content_alerts 
        (url, detected_text, ip_address, browser_info, platform, screen_resolution, 
         timezone, language, detected_at, device_info_json, scores_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            url,
            text[:1000],  # Save first 1000 chars of text
            ip,
            browser[:254],
            platform,
            screen,
            timezone,
            language,
            mysql_timestamp,
            device_info_json,
            scores_json
        )
        
        cursor.execute(insert_query, values)
        connection.commit()
        alert_id = cursor.lastrowid
        
        print(f"✅ Alert saved to database with ID: {alert_id}")
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Error saving to database: {err}")
        return False
    except Exception as err:
        print(f"❌ Unexpected error: {err}")
        return False


# Global classifier (lazy loaded)
classifier = None

# Lazy load classifier
def get_classifier():
    global classifier
    if classifier is None:
        print("📥 Loading toxic content classifier model...")
        classifier = pipeline(
            "text-classification",
            model="unitary/unbiased-toxic-roberta",
            tokenizer="unitary/unbiased-toxic-roberta",
            top_k=None,
            truncation=True,
            max_length=512
        )
        print("✅ Classifier model loaded successfully!")
    return classifier

# Modern lifespan context manager (replaces deprecated on_event)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting API server...")
    create_tables()
    print("✅ Database tables ready!")
    yield
    # Shutdown
    print("🛑 Shutting down API server...")

app = FastAPI(lifespan=lifespan)

# ✅ CORS (autorise Reddit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.reddit.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/moderate")
async def moderate(payload: dict):
    text = payload.get("text", "")
    url = payload.get("url", "")
    device_info = payload.get("deviceInfo", {})
    
    print(f"=== Content Moderation Request ===")
    print(f"URL: {url}")
    print(f"Device Info: {device_info}")
    print(payload)

    # Get classifier (lazy load on first use)
    clf = get_classifier()
    scores = clf(text)[0]

    non_adequate = any(
        s["score"] > 0.7 and s["label"] in [
            "toxicity",
            "insult",
            "threat",
            "identity_attack"
        ]
        for s in scores
    )



    if non_adequate:
        # 1. Save to database first
        print("💾 Saving alert to database...")
        save_alert_to_database(text, url, device_info, scores)
        
        # 2. Then send email
        EMAIL = "dhaouadi.r1991@gmail.com"
        APP_PASSWORD = "vcfrqhspbcjyeouj"

        msg = EmailMessage()
        msg["Subject"] = "⚠️ Alerte de contrôle parental - Contenu inapproprié détecté"
        msg["From"] = EMAIL
        msg["To"] = EMAIL
        
        # Format device information
        device_info_html = format_device_info(device_info)
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
        
        # Use email template with device info
        html_content = EMAIL_TEMPLATE.format(
            url=url,
            device_info_html=device_info_html,
            timestamp=timestamp
        )
        
        # Plain text fallback
        text_content = f"""
Alerte de Contrôle Parental
==========================

Contenu inapproprié détecté lors de l'utilisation du navigateur de votre enfant.

URL détectée: {url}

Information de l'Appareil:
- IP Publique: {device_info.get('publicIP', 'Non disponible')}
- Navigateur: {device_info.get('platform', 'Non disponible')}
- Système: {device_info.get('language', 'Non disponible')}
- Résolution: {device_info.get('screenWidth', 'N/A')}x{device_info.get('screenHeight', 'N/A')}
- Fuseau Horaire: {device_info.get('timezone', 'Non disponible')}

Heure de Détection: {timestamp}

Nous vous recommandons de vérifier l'activité en ligne et de discuter avec votre enfant.
"""
        
        msg.set_content(text_content)
        msg.add_alternative(html_content, subtype="html")

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL, APP_PASSWORD)
                server.send_message(msg)
            print("✅ Email sent successfully!")
        except Exception as e:
            print(f"❌ Error sending email: {e}")

    return {
        "non_adequate": non_adequate,
        "scores": scores
    }


# ============= HEALTH CHECK ENDPOINT =============

@app.get("/health")
async def health_check():
    """Quick health check endpoint - responds immediately"""
    return {
        "status": "ok",
        "message": "API is running",
        "model_loaded": classifier is not None
    }


# ============= HOME PAGE =============

@app.get("/", response_class=HTMLResponse)
async def home():
    """Main dashboard home page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Parental Control System - Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                min-height: 100vh;
                padding: 15px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header-card {
                background: white;
                border-radius: 10px;
                padding: 30px 20px;
                text-align: center;
                margin-bottom: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                border-top: 5px solid #e74c3c;
            }
            .header-card h1 {
                font-size: clamp(28px, 6vw, 42px);
                color: #1a1a1a;
                margin-bottom: 10px;
            }
            .header-card p {
                font-size: clamp(14px, 2vw, 18px);
                color: #555;
                margin-bottom: 20px;
            }
            .cards-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: white;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
                transition: transform 0.3s, box-shadow 0.3s;
                text-decoration: none;
                color: inherit;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                border-left: 4px solid #e74c3c;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 30px rgba(231, 76, 60, 0.3);
            }
            .card-icon {
                font-size: 40px;
                margin-bottom: 15px;
            }
            .card h2 {
                font-size: clamp(18px, 3vw, 24px);
                color: #1a1a1a;
                margin-bottom: 10px;
            }
            .card p {
                color: #666;
                font-size: clamp(12px, 1.5vw, 14px);
                margin-bottom: 20px;
                flex-grow: 1;
                line-height: 1.5;
            }
            .card-button {
                background: #e74c3c;
                color: white;
                padding: 12px 24px;
                border-radius: 5px;
                text-decoration: none;
                text-align: center;
                font-weight: bold;
                transition: background 0.3s;
                border: none;
                cursor: pointer;
            }
            .card-button:hover {
                background: #c0392b;
            }
            .footer-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
                color: #555;
                border-top: 3px solid #e74c3c;
            }
            .quick-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 12px;
                margin-bottom: 30px;
            }
            .stat-box {
                background: rgba(255, 255, 255, 0.95);
                padding: 18px 12px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .stat-box .label {
                color: #666;
                font-size: clamp(11px, 1.2vw, 14px);
                margin-bottom: 8px;
            }
            .stat-box .value {
                font-size: clamp(24px, 4vw, 32px);
                font-weight: bold;
                color: #e74c3c;
            }
            @media (max-width: 768px) {
                body {
                    padding: 10px;
                }
                .header-card {
                    padding: 20px 15px;
                    margin-bottom: 20px;
                }
                .cards-grid {
                    gap: 15px;
                }
                .card {
                    padding: 20px;
                }
                .quick-stats {
                    gap: 10px;
                }
            }
            @media (max-width: 480px) {
                .cards-grid {
                    grid-template-columns: 1fr;
                }
                .quick-stats {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-card">
                <h1>🛡️ Parental Control System</h1>
                <p>Content Moderation & Safety Management Dashboard</p>
            </div>
            
            <div class="quick-stats" id="stats-container">
                <div class="stat-box">
                    <div class="label">Total Alerts</div>
                    <div class="value" id="total-alerts">Loading...</div>
                </div>
                <div class="stat-box">
                    <div class="label">Monitored IPs</div>
                    <div class="value" id="monitored-ips">Loading...</div>
                </div>
                <div class="stat-box">
                    <div class="label">Problematic URLs</div>
                    <div class="value" id="problem-urls">Loading...</div>
                </div>
                <div class="stat-box">
                    <div class="label">System Status</div>
                    <div class="value" id="system-status">Loading...</div>
                </div>
            </div>
            
            <div class="cards-grid">
                <a href="/alerts" class="card">
                    <div>
                        <div class="card-icon">📋</div>
                        <h2>All Alerts</h2>
                        <p>View and manage all detected inappropriate content alerts. Browse through all records with pagination and filtering options.</p>
                    </div>
                    <button class="card-button">View Alerts</button>
                </a>
                
                <a href="/alerts/stats" class="card">
                    <div>
                        <div class="card-icon">📊</div>
                        <h2>Statistics</h2>
                        <p>Analyze patterns and trends. See top problematic IPs, URLs, platforms, and activity over time.</p>
                    </div>
                    <button class="card-button">View Statistics</button>
                </a>
                
                <div class="card" style="background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%); border-left: 4px solid #e74c3c;">
                    <div>
                        <div class="card-icon">⚙️</div>
                        <h2>System Info</h2>
                        <p>Model Status: <strong id="model-status">Loading...</strong></p>
                        <p>API Endpoint: <strong>http://127.0.0.1:8000/moderate</strong></p>
                    </div>
                    <button class="card-button" onclick="checkHealth()">Check Health</button>
                </div>
            </div>
            
            <div class="footer-card">
                <p>🔒 This system automatically monitors web content for parental control purposes.</p>
                <p style="margin-top: 10px; font-size: 12px;">Last updated: <span id="update-time">Just now</span></p>
            </div>
        </div>
        
        <script>
            // Load statistics on page load
            window.addEventListener('load', function() {
                loadStatistics();
                checkHealth();
                updateTime();
                setInterval(updateTime, 1000);
            });
            
            function loadStatistics() {
                fetch('/alerts/stats')
                    .then(r => r.text())
                    .then(() => {
                        // For now, just show a basic count
                        fetch('/alerts?limit=1')
                            .then(r => r.text())
                            .catch(() => {});
                    })
                    .catch(() => {});
            }
            
            function checkHealth() {
                fetch('/health')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('system-status').textContent = 
                            data.status === 'ok' ? '✅ OK' : '❌ Error';
                        document.getElementById('model-status').textContent = 
                            data.model_loaded ? 'Ready' : 'Loading...';
                    })
                    .catch(() => {
                        document.getElementById('system-status').textContent = '❌ Offline';
                    });
            }
            
            function updateTime() {
                const now = new Date();
                const time = now.toLocaleTimeString();
                document.getElementById('update-time').textContent = time;
            }
        </script>
    </body>
    </html>
    """
    return html_content

# ============= ENDPOINTS TO LIST DATA FROM DATABASE =============

@app.get("/alerts", response_class=HTMLResponse)
async def get_alerts(limit: int = 50, offset: int = 0):
    """Get all alerts from database with pagination - HTML Dashboard"""
    try:
        connection = create_database_connection()
        if not connection:
            return "<h1>Database connection failed</h1>"
        
        cursor = connection.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM content_alerts")
        total = cursor.fetchone()["total"]
        
        # Get paginated data
        query = "SELECT * FROM content_alerts ORDER BY detected_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, (limit, offset))
        alerts = cursor.fetchall()
        
        # Parse JSON fields
        for alert in alerts:
            try:
                alert['device_info_json'] = json.loads(alert['device_info_json']) if alert['device_info_json'] else {}
                alert['scores_json'] = json.loads(alert['scores_json']) if alert['scores_json'] else {}
            except:
                pass
        
        cursor.close()
        connection.close()
        
        # Build alerts table rows
        alerts_rows = ""
        for alert in alerts:
            timestamp = alert.get('detected_at', 'N/A')
            url = alert.get('url', 'N/A')[:60]
            ip = alert.get('ip_address', 'N/A')
            platform = alert.get('platform', 'N/A')
            alerts_rows += f"""
            <tr>
                <td>{alert.get('id', 'N/A')}</td>
                <td><a href="/alerts/{alert.get('id', '')}" class="link">{url}</a></td>
                <td>{ip}</td>
                <td>{platform}</td>
                <td>{timestamp}</td>
                <td><button onclick="deleteAlert({alert.get('id', '')})">Delete</button></td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Parental Control Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    min-height: 100vh;
                    padding: 10px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                    padding: clamp(20px, 5vw, 30px);
                    text-align: center;
                }}
                .header h1 {{
                    font-size: clamp(24px, 5vw, 32px);
                    margin-bottom: 10px;
                }}
                .nav {{
                    display: flex;
                    gap: 10px;
                    padding: clamp(12px, 2vw, 20px);
                    background: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                    flex-wrap: wrap;
                    overflow-x: auto;
                }}
                .nav a {{
                    padding: 8px 16px;
                    background: #e74c3c;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background 0.3s;
                    white-space: nowrap;
                    font-size: clamp(12px, 1.5vw, 14px);
                }}
                .nav a:hover {{
                    background: #c0392b;
                }}
                .content {{
                    padding: clamp(15px, 3vw, 30px);
                }}
                .section-title {{
                    font-size: clamp(18px, 4vw, 24px);
                    color: #1a1a1a;
                    margin-bottom: 20px;
                    border-bottom: 3px solid #e74c3c;
                    padding-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: clamp(12px, 1.5vw, 14px);
                }}
                th {{
                    background: #1a1a1a;
                    color: white;
                    padding: 12px 8px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 12px 8px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                tr:hover {{
                    background: #f5f5f5;
                }}
                .link {{
                    color: #e74c3c;
                    text-decoration: none;
                    cursor: pointer;
                }}
                .link:hover {{
                    text-decoration: underline;
                }}
                button {{
                    background: #e74c3c;
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: background 0.3s;
                    font-size: clamp(11px, 1.2vw, 13px);
                }}
                button:hover {{
                    background: #c0392b;
                }}
                .pagination {{
                    display: flex;
                    gap: 10px;
                    margin: 20px 0;
                    justify-content: center;
                    flex-wrap: wrap;
                }}
                .pagination a, .pagination span {{
                    padding: 10px 15px;
                    background: #e74c3c;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-size: clamp(11px, 1.2vw, 13px);
                }}
                .pagination a:hover {{
                    background: #c0392b;
                }}
                .pagination .active {{
                    background: #1a1a1a;
                    font-weight: bold;
                }}
                .stats-box {{
                    background: #fff5f5;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #e74c3c;
                }}
                .stats-box h3 {{
                    color: #e74c3c;
                    margin-bottom: 10px;
                }}
                @media (max-width: 768px) {{
                    body {{
                        padding: 5px;
                    }}
                    .container {{
                        border-radius: 5px;
                    }}
                    .header {{
                        padding: 15px;
                    }}
                    .content {{
                        padding: 12px;
                    }}
                    table {{
                        font-size: 11px;
                    }}
                    th, td {{
                        padding: 8px 4px;
                    }}
                    button {{
                        padding: 6px 8px;
                    }}
                }}
                @media (max-width: 480px) {{
                    table {{
                        font-size: 10px;
                    }}
                    th, td {{
                        padding: 6px 3px;
                    }}
                    .nav {{
                        gap: 5px;
                    }}
                    .nav a {{
                        padding: 6px 10px;
                    }}
                }}
            </style>
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Parental Control Dashboard</h1>
                    <p>Content Moderation & Alerts Management</p>
                </div>
                
                <div class="nav">
                    <a href="/alerts">📋 All Alerts</a>
                    <a href="/alerts/stats">📊 Statistics</a>
                    <a href="/">🏠 Home</a>
                </div>
                
                <div class="content">
                    <div class="section-title">📋 All Detected Alerts</div>
                    
                    <div class="stats-box">
                        <h3>Total Alerts: {total}</h3>
                        <p>Showing {len(alerts)} alerts (Page: {offset // limit + 1})</p>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>URL</th>
                                <th>IP Address</th>
                                <th>Platform</th>
                                <th>Detected At</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {alerts_rows if alerts_rows else '<tr><td colspan="6" style="text-align: center; color: #999;">No alerts found</td></tr>'}
                        </tbody>
                    </table>
                    
                    <div class="pagination">
                        {f'<a href="/alerts?offset=0">First</a>' if offset > 0 else '<span>First</span>'}
                        {f'<a href="/alerts?offset={max(0, offset - limit)}">Previous</a>' if offset > 0 else '<span>Previous</span>'}
                        <span class="active">{offset // limit + 1}</span>
                        {f'<a href="/alerts?offset={offset + limit}">Next</a>' if len(alerts) == limit else '<span>Next</span>'}
                    </div>
                </div>
            </div>
            
            <script>
                function deleteAlert(alertId) {{
                    if (confirm('Are you sure you want to delete this alert?')) {{
                        fetch(`/alerts/${{alertId}}`, {{ method: 'DELETE' }})
                            .then(r => r.json())
                            .then(d => {{
                                if (d.status === 'success') {{
                                    alert('Alert deleted successfully');
                                    location.reload();
                                }} else {{
                                    alert('Error: ' + d.error);
                                }}
                            }});
                    }}
                }}
            </script>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"


@app.get("/alerts/ip/{ip_address}", response_class=HTMLResponse)
async def get_alerts_by_ip(ip_address: str, limit: int = 50):
    """Get alerts filtered by IP address - HTML Dashboard"""
    try:
        connection = create_database_connection()
        if not connection:
            return "<h1>Database connection failed</h1>"
        
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM content_alerts WHERE ip_address = %s ORDER BY detected_at DESC LIMIT %s"
        cursor.execute(query, (ip_address, limit))
        alerts = cursor.fetchall()
        
        # Parse JSON fields
        for alert in alerts:
            try:
                alert['device_info_json'] = json.loads(alert['device_info_json']) if alert['device_info_json'] else {}
                alert['scores_json'] = json.loads(alert['scores_json']) if alert['scores_json'] else {}
            except:
                pass
        
        cursor.close()
        connection.close()
        
        alerts_rows = ""
        for alert in alerts:
            timestamp = alert.get('detected_at', 'N/A')
            url = alert.get('url', 'N/A')[:60]
            alerts_rows += f"""
            <tr>
                <td>{alert.get('id', 'N/A')}</td>
                <td><a href="/alerts/{alert.get('id', '')}" class="link">{url}</a></td>
                <td>{timestamp}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alerts by IP - Parental Control Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    min-height: 100vh;
                    padding: 10px;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                    padding: clamp(20px, 5vw, 30px);
                    text-align: center;
                }}
                .header h1 {{
                    font-size: clamp(22px, 5vw, 32px);
                    margin-bottom: 10px;
                }}
                .nav {{
                    display: flex;
                    gap: 10px;
                    padding: clamp(12px, 2vw, 20px);
                    background: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                    flex-wrap: wrap;
                    overflow-x: auto;
                }}
                .nav a {{
                    padding: 8px 16px;
                    background: #e74c3c;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background 0.3s;
                    white-space: nowrap;
                    font-size: clamp(12px, 1.5vw, 14px);
                }}
                .nav a:hover {{
                    background: #c0392b;
                }}
                .content {{
                    padding: clamp(15px, 3vw, 30px);
                }}
                .section-title {{
                    font-size: clamp(18px, 4vw, 24px);
                    color: #1a1a1a;
                    margin-bottom: 20px;
                    border-bottom: 3px solid #e74c3c;
                    padding-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: clamp(12px, 1.5vw, 14px);
                }}
                th {{
                    background: #1a1a1a;
                    color: white;
                    padding: 12px 8px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 12px 8px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                tr:hover {{
                    background: #f5f5f5;
                }}
                .link {{
                    color: #e74c3c;
                    text-decoration: none;
                    cursor: pointer;
                }}
                .link:hover {{
                    text-decoration: underline;
                }}
                .info-box {{
                    background: #fff5f5;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #e74c3c;
                }}
                @media (max-width: 768px) {{
                    body {{
                        padding: 5px;
                    }}
                    .content {{
                        padding: 12px;
                    }}
                    table {{
                        font-size: 11px;
                    }}
                    th, td {{
                        padding: 8px 4px;
                    }}
                }}
                @media (max-width: 480px) {{
                    table {{
                        font-size: 10px;
                    }}
                    th, td {{
                        padding: 6px 3px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Alerts by IP Address</h1>
                    <p>{ip_address}</p>
                </div>
                
                <div class="nav">
                    <a href="/alerts">📋 All Alerts</a>
                    <a href="/alerts/stats">📊 Statistics</a>
                    <a href="/">🏠 Home</a>
                </div>
                
                <div class="content">
                    <div class="section-title">Found {len(alerts)} alerts from this IP</div>
                    
                    <div class="info-box">
                        <strong>IP Address:</strong> {ip_address}
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>URL</th>
                                <th>Detected At</th>
                            </tr>
                        </thead>
                        <tbody>
                            {alerts_rows if alerts_rows else '<tr><td colspan="3" style="text-align: center; color: #999;">No alerts found</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"


@app.get("/alerts/date/{date}", response_class=HTMLResponse)
async def get_alerts_by_date(date: str, limit: int = 50):
    """Get alerts filtered by date (format: YYYY-MM-DD) - HTML Dashboard"""
    try:
        connection = create_database_connection()
        if not connection:
            return "<h1>Database connection failed</h1>"
        
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM content_alerts WHERE DATE(detected_at) = %s ORDER BY detected_at DESC LIMIT %s"
        cursor.execute(query, (date, limit))
        alerts = cursor.fetchall()
        
        # Parse JSON fields
        for alert in alerts:
            try:
                alert['device_info_json'] = json.loads(alert['device_info_json']) if alert['device_info_json'] else {}
                alert['scores_json'] = json.loads(alert['scores_json']) if alert['scores_json'] else {}
            except:
                pass
        
        cursor.close()
        connection.close()
        
        alerts_rows = ""
        for alert in alerts:
            timestamp = alert.get('detected_at', 'N/A')
            url = alert.get('url', 'N/A')[:60]
            alerts_rows += f"""
            <tr>
                <td>{alert.get('id', 'N/A')}</td>
                <td><a href="/alerts/{alert.get('id', '')}" class="link">{url}</a></td>
                <td>{alert.get('ip_address', 'N/A')}</td>
                <td>{timestamp}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alerts by Date - Parental Control Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    min-height: 100vh;
                    padding: 10px;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                    padding: clamp(20px, 5vw, 30px);
                    text-align: center;
                }}
                .header h1 {{
                    font-size: clamp(22px, 5vw, 32px);
                    margin-bottom: 10px;
                }}
                .nav {{
                    display: flex;
                    gap: 10px;
                    padding: clamp(12px, 2vw, 20px);
                    background: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                    flex-wrap: wrap;
                    overflow-x: auto;
                }}
                .nav a {{
                    padding: 8px 16px;
                    background: #e74c3c;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background 0.3s;
                    white-space: nowrap;
                    font-size: clamp(12px, 1.5vw, 14px);
                }}
                .nav a:hover {{
                    background: #c0392b;
                }}
                .content {{
                    padding: clamp(15px, 3vw, 30px);
                }}
                .section-title {{
                    font-size: clamp(18px, 4vw, 24px);
                    color: #1a1a1a;
                    margin-bottom: 20px;
                    border-bottom: 3px solid #e74c3c;
                    padding-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: clamp(12px, 1.5vw, 14px);
                }}
                th {{
                    background: #1a1a1a;
                    color: white;
                    padding: 12px 8px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 12px 8px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                tr:hover {{
                    background: #f5f5f5;
                }}
                .link {{
                    color: #e74c3c;
                    text-decoration: none;
                    cursor: pointer;
                }}
                .link:hover {{
                    text-decoration: underline;
                }}
                .info-box {{
                    background: #fff5f5;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #e74c3c;
                }}
                @media (max-width: 768px) {{
                    body {{
                        padding: 5px;
                    }}
                    .content {{
                        padding: 12px;
                    }}
                    table {{
                        font-size: 11px;
                    }}
                    th, td {{
                        padding: 8px 4px;
                    }}
                }}
                @media (max-width: 480px) {{
                    table {{
                        font-size: 10px;
                    }}
                    th, td {{
                        padding: 6px 3px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 Alerts by Date</h1>
                    <p>{date}</p>
                </div>
                
                <div class="nav">
                    <a href="/alerts">📋 All Alerts</a>
                    <a href="/alerts/stats">📊 Statistics</a>
                    <a href="/">🏠 Home</a>
                </div>
                
                <div class="content">
                    <div class="section-title">Found {len(alerts)} alerts on this date</div>
                    
                    <div class="info-box">
                        <strong>Date:</strong> {date}
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>URL</th>
                                <th>IP Address</th>
                                <th>Detected At</th>
                            </tr>
                        </thead>
                        <tbody>
                            {alerts_rows if alerts_rows else '<tr><td colspan="4" style="text-align: center; color: #999;">No alerts found</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"


@app.get("/alerts/url", response_class=HTMLResponse)
async def get_alerts_by_url(url: str, limit: int = 50):
    """Get alerts filtered by URL - HTML Dashboard"""
    try:
        connection = create_database_connection()
        if not connection:
            return "<h1>Database connection failed</h1>"
        
        cursor = connection.cursor(dictionary=True)
        
        # Use LIKE for partial URL matching
        query = "SELECT * FROM content_alerts WHERE url LIKE %s ORDER BY detected_at DESC LIMIT %s"
        cursor.execute(query, (f"%{url}%", limit))
        alerts = cursor.fetchall()
        
        # Parse JSON fields
        for alert in alerts:
            try:
                alert['device_info_json'] = json.loads(alert['device_info_json']) if alert['device_info_json'] else {}
                alert['scores_json'] = json.loads(alert['scores_json']) if alert['scores_json'] else {}
            except:
                pass
        
        cursor.close()
        connection.close()
        
        alerts_rows = ""
        for alert in alerts:
            timestamp = alert.get('detected_at', 'N/A')
            ip = alert.get('ip_address', 'N/A')
            alerts_rows += f"""
            <tr>
                <td>{alert.get('id', 'N/A')}</td>
                <td><a href="/alerts/{alert.get('id', '')}" class="link">{url}</a></td>
                <td>{ip}</td>
                <td>{timestamp}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alerts by URL - Parental Control Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    min-height: 100vh;
                    padding: 10px;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                    padding: clamp(20px, 5vw, 30px);
                    text-align: center;
                }}
                .header h1 {{
                    font-size: clamp(22px, 5vw, 32px);
                    margin-bottom: 10px;
                }}
                .nav {{
                    display: flex;
                    gap: 10px;
                    padding: clamp(12px, 2vw, 20px);
                    background: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                    flex-wrap: wrap;
                    overflow-x: auto;
                }}
                .nav a {{
                    padding: 8px 16px;
                    background: #e74c3c;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background 0.3s;
                    white-space: nowrap;
                    font-size: clamp(12px, 1.5vw, 14px);
                }}
                .nav a:hover {{
                    background: #c0392b;
                }}
                .content {{
                    padding: clamp(15px, 3vw, 30px);
                }}
                .section-title {{
                    font-size: clamp(18px, 4vw, 24px);
                    color: #1a1a1a;
                    margin-bottom: 20px;
                    border-bottom: 3px solid #e74c3c;
                    padding-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: clamp(12px, 1.5vw, 14px);
                }}
                th {{
                    background: #1a1a1a;
                    color: white;
                    padding: 12px 8px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 12px 8px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                tr:hover {{
                    background: #f5f5f5;
                }}
                .link {{
                    color: #e74c3c;
                    text-decoration: none;
                    cursor: pointer;
                }}
                .link:hover {{
                    text-decoration: underline;
                }}
                .info-box {{
                    background: #fff5f5;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #e74c3c;
                }}
                @media (max-width: 768px) {{
                    body {{
                        padding: 5px;
                    }}
                    .content {{
                        padding: 12px;
                    }}
                    table {{
                        font-size: 11px;
                    }}
                    th, td {{
                        padding: 8px 4px;
                    }}
                }}
                @media (max-width: 480px) {{
                    table {{
                        font-size: 10px;
                    }}
                    th, td {{
                        padding: 6px 3px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔗 Alerts by URL</h1>
                    <p>Search: {url}</p>
                </div>
                
                <div class="nav">
                    <a href="/alerts">📋 All Alerts</a>
                    <a href="/alerts/stats">📊 Statistics</a>
                    <a href="/">🏠 Home</a>
                </div>
                
                <div class="content">
                    <div class="section-title">Found {len(alerts)} alerts matching this URL</div>
                    
                    <div class="info-box">
                        <strong>Search URL:</strong> {url}
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>URL</th>
                                <th>IP Address</th>
                                <th>Detected At</th>
                            </tr>
                        </thead>
                        <tbody>
                            {alerts_rows if alerts_rows else '<tr><td colspan="4" style="text-align: center; color: #999;">No alerts found</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"


@app.get("/alerts/stats", response_class=HTMLResponse)
async def get_alerts_statistics():
    """Get statistics about alerts - HTML Dashboard"""
    try:
        connection = create_database_connection()
        if not connection:
            return "<h1>Database connection failed</h1>"
        
        cursor = connection.cursor(dictionary=True)
        
        # Total alerts
        cursor.execute("SELECT COUNT(*) as total FROM content_alerts")
        total = cursor.fetchone()["total"]
        
        # Alerts by IP (top 10)
        cursor.execute("""
            SELECT ip_address, COUNT(*) as count 
            FROM content_alerts 
            GROUP BY ip_address 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_ips = cursor.fetchall()
        
        # Most visited problematic sites (top 10)
        cursor.execute("""
            SELECT url, COUNT(*) as count 
            FROM content_alerts 
            GROUP BY url 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_urls = cursor.fetchall()
        
        # Alerts by platform
        cursor.execute("""
            SELECT platform, COUNT(*) as count 
            FROM content_alerts 
            GROUP BY platform
        """)
        by_platform = cursor.fetchall()
        
        # Alerts by date (last 7 days)
        cursor.execute("""
            SELECT DATE(detected_at) as date, COUNT(*) as count 
            FROM content_alerts 
            WHERE detected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(detected_at) 
            ORDER BY date DESC
        """)
        last_7_days = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        # Build HTML tables
        ips_rows = ""
        for item in top_ips:
            ips_rows += f"<tr><td>{item.get('ip_address', 'N/A')}</td><td>{item.get('count', 0)}</td></tr>"
        
        urls_rows = ""
        for item in top_urls:
            url = str(item.get('url', 'N/A'))[:80]
            urls_rows += f"<tr><td><a href='/alerts/url?url={item.get('url', '')}' class='link'>{url}</a></td><td>{item.get('count', 0)}</td></tr>"
        
        platform_rows = ""
        for item in by_platform:
            platform_rows += f"<tr><td>{item.get('platform', 'N/A')}</td><td>{item.get('count', 0)}</td></tr>"
        
        dates_rows = ""
        for item in last_7_days:
            dates_rows += f"<tr><td>{item.get('date', 'N/A')}</td><td>{item.get('count', 0)}</td></tr>"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Statistics - Parental Control Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #d9534f 0%, #c9302c 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #d9534f 0%, #c9302c 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 32px;
                    margin-bottom: 10px;
                }}
                .nav {{
                    display: flex;
                    gap: 10px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                    flex-wrap: wrap;
                }}
                .nav a {{
                    padding: 10px 20px;
                    background: #d9534f;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background 0.3s;
                }}
                .nav a:hover {{
                    background: #c9302c;
                }}
                .content {{
                    padding: 30px;
                }}
                .section-title {{
                    font-size: 24px;
                    color: #333;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #d9534f;
                    padding-bottom: 10px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #d9534f 0%, #c9302c 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .stat-card h3 {{
                    font-size: 14px;
                    margin-bottom: 10px;
                    opacity: 0.9;
                }}
                .stat-card .number {{
                    font-size: 36px;
                    font-weight: bold;
                }}
                .stats-section {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                    gap: 30px;
                    margin-bottom: 40px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                }}
                th {{
                    background: #d9534f;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                tr:hover {{
                    background: #f5f5f5;
                }}
                .table-container {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .link {{
                    color: #d9534f;
                    text-decoration: none;
                    cursor: pointer;
                }}
                .link:hover {{
                    text-decoration: underline;
                    color: #c9302c;
                }}
                @media (max-width: 768px) {{
                    .stats-section {{
                        grid-template-columns: 1fr;
                    }}
                    .header h1 {{
                        font-size: 24px;
                    }}
                }}
                @media (max-width: 480px) {{
                    .nav {{
                        flex-direction: column;
                    }}
                    .nav a {{
                        width: 100%;
                        text-align: center;
                    }}
                    .stats-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Statistics Dashboard</h1>
                    <p>Content Moderation Analytics & Insights</p>
                </div>
                
                <div class="nav">
                    <a href="/alerts">📋 All Alerts</a>
                    <a href="/alerts/stats">📊 Statistics</a>
                    <a href="/">🏠 Home</a>
                </div>
                
                <div class="content">
                    <div class="section-title">📈 Overall Statistics</div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Total Alerts</h3>
                            <div class="number">{total}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Unique IPs</h3>
                            <div class="number">{len(top_ips)}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Problematic URLs</h3>
                            <div class="number">{len(top_urls)}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Platforms Detected</h3>
                            <div class="number">{len(by_platform)}</div>
                        </div>
                    </div>
                    
                    <div class="stats-section">
                        <div class="table-container">
                            <h3 style="margin-bottom: 15px; color: #333;">🔍 Top 10 IPs</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>IP Address</th>
                                        <th>Alert Count</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {ips_rows if ips_rows else '<tr><td colspan="2" style="text-align: center; color: #999;">No data available</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="table-container">
                            <h3 style="margin-bottom: 15px; color: #333;">⚠️ Top 10 Problematic URLs</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>URL</th>
                                        <th>Alert Count</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {urls_rows if urls_rows else '<tr><td colspan="2" style="text-align: center; color: #999;">No data available</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div class="stats-section">
                        <div class="table-container">
                            <h3 style="margin-bottom: 15px; color: #333;">💻 Alerts by Platform</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Platform</th>
                                        <th>Alert Count</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {platform_rows if platform_rows else '<tr><td colspan="2" style="text-align: center; color: #999;">No data available</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="table-container">
                            <h3 style="margin-bottom: 15px; color: #333;">📅 Last 7 Days Activity</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Alert Count</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {dates_rows if dates_rows else '<tr><td colspan="2" style="text-align: center; color: #999;">No data available</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"


@app.get("/alerts/{alert_id}", response_class=HTMLResponse)
async def get_alert_detail(alert_id: int):
    """Get detailed information about a specific alert - HTML View"""
    try:
        connection = create_database_connection()
        if not connection:
            return "<h1>Database connection failed</h1>"
        
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM content_alerts WHERE id = %s"
        cursor.execute(query, (alert_id,))
        alert = cursor.fetchone()
        
        if not alert:
            cursor.close()
            connection.close()
            return "<h1>Alert not found</h1>"
        
        # Parse JSON fields
        try:
            device_info = json.loads(alert['device_info_json']) if alert['device_info_json'] else {}
            scores = json.loads(alert['scores_json']) if alert['scores_json'] else {}
        except:
            device_info = {}
            scores = {}
        
        cursor.close()
        connection.close()
        
        # Build device info HTML
        device_html = ""
        if device_info:
            for key, value in device_info.items():
                device_html += f"<tr><td><strong>{key}:</strong></td><td>{value}</td></tr>"
        
        # Build scores HTML
        scores_html = ""
        if scores:
            for score in scores:
                label = score.get('label', 'Unknown')
                score_val = score.get('score', 0)
                bar_width = int(score_val * 100)
                color = "#d9534f" if score_val > 0.7 else "#f0ad4e"
                scores_html += f"""
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span><strong>{label}</strong></span>
                        <span>{score_val:.1%}</span>
                    </div>
                    <div style="background: #e0e0e0; border-radius: 4px; height: 20px; overflow: hidden;">
                        <div style="background: {color}; width: {bar_width}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
                """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alert Details - Parental Control Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #d9534f 0%, #c9302c 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    font-size: 32px;
                    margin-bottom: 10px;
                }}
                .nav {{
                    display: flex;
                    gap: 10px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                    flex-wrap: wrap;
                }}
                .nav a {{
                    padding: 10px 20px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    transition: background 0.3s;
                }}
                .nav a:hover {{
                    background: #764ba2;
                }}
                .content {{
                    padding: 30px;
                }}
                .section {{
                    margin-bottom: 30px;
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                }}
                .section-title {{
                    font-size: 20px;
                    color: #333;
                    margin-bottom: 15px;
                    font-weight: bold;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                td:first-child {{
                    width: 30%;
                    font-weight: bold;
                    color: #667eea;
                }}
                button {{
                    background: #d9534f;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: background 0.3s;
                }}
                button:hover {{
                    background: #c9302c;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Alert Details</h1>
                    <p>ID: #{alert.get('id', 'N/A')}</p>
                </div>
                
                <div class="nav">
                    <a href="/alerts">📋 All Alerts</a>
                    <a href="/alerts/stats">📊 Statistics</a>
                    <a href="/">🏠 Home</a>
                </div>
                
                <div class="content">
                    <div class="section">
                        <div class="section-title">🌐 Website Information</div>
                        <table>
                            <tr><td>URL:</td><td>{alert.get('url', 'N/A')}</td></tr>
                            <tr><td>Detected At:</td><td>{alert.get('detected_at', 'N/A')}</td></tr>
                            <tr><td>Detected Text:</td><td style="word-break: break-all;">{alert.get('detected_text', 'N/A')[:200]}...</td></tr>
                        </table>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">💻 Device Information</div>
                        <table>
                            <tr><td>IP Address:</td><td>{alert.get('ip_address', 'N/A')}</td></tr>
                            <tr><td>Browser:</td><td>{alert.get('browser_info', 'N/A')}</td></tr>
                            <tr><td>Platform:</td><td>{alert.get('platform', 'N/A')}</td></tr>
                            <tr><td>Screen Resolution:</td><td>{alert.get('screen_resolution', 'N/A')}</td></tr>
                            <tr><td>Timezone:</td><td>{alert.get('timezone', 'N/A')}</td></tr>
                            <tr><td>Language:</td><td>{alert.get('language', 'N/A')}</td></tr>
                        </table>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">📊 Toxicity Scores</div>
                        {scores_html if scores_html else '<p style="color: #999;">No scores available</p>'}
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <button onclick="deleteAlert({alert.get('id', '')})">🗑️ Delete Alert</button>
                        <button onclick="history.back()" style="background: #667eea; margin-left: 10px;">← Go Back</button>
                    </div>
                </div>
            </div>
            
            <script>
                function deleteAlert(alertId) {{
                    if (confirm('Are you sure you want to delete this alert?')) {{
                        fetch(`/alerts/${{alertId}}`, {{ method: 'DELETE' }})
                            .then(r => r.json())
                            .then(d => {{
                                if (d.status === 'success') {{
                                    alert('Alert deleted successfully');
                                    window.location.href = '/alerts';
                                }} else {{
                                    alert('Error: ' + d.error);
                                }}
                            }});
                    }}
                }}
            </script>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"


@app.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int):
    """Delete an alert from database"""
    try:
        connection = create_database_connection()
        if not connection:
            return {"error": "Database connection failed", "status": "error"}
        
        cursor = connection.cursor()
        
        query = "DELETE FROM content_alerts WHERE id = %s"
        cursor.execute(query, (alert_id,))
        connection.commit()
        
        rows_affected = cursor.rowcount
        cursor.close()
        connection.close()
        
        if rows_affected == 0:
            return {"error": "Alert not found", "status": "not_found"}
        
        return {"status": "success", "message": f"Alert {alert_id} deleted successfully"}
    except Exception as e:
        return {"error": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)