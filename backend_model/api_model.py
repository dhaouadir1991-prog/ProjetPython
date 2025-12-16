from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
import uvicorn

import smtplib
from email.mime.text import MIMEText
from email.message import EmailMessage

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

app = FastAPI()

# ✅ CORS (autorise Reddit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.reddit.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Pipeline corrigé (TRÈS IMPORTANT)
classifier = pipeline(
    "text-classification",
    model="unitary/unbiased-toxic-roberta",
    tokenizer="unitary/unbiased-toxic-roberta",
    top_k=None,
    truncation=True,
    max_length=512
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

    scores = classifier(text)[0]

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
        EMAIL = "dhaouadi.r1991@gmail.com"
        APP_PASSWORD = "vcfrqhspbcjyeouj"

        msg = EmailMessage()
        msg["Subject"] = "⚠️ Alerte de contrôle parental - Contenu inapproprié détecté"
        msg["From"] = EMAIL
        msg["To"] = EMAIL
        
        # Format device information
        from datetime import datetime
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)