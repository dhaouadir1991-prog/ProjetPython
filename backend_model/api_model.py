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
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            max-width: 600px;
            margin: 0 auto;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .header {{
            color: #d9534f;
            font-size: 24px;
            margin-bottom: 20px;
        }}
        .content {{
            color: #333;
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        .url {{
            background-color: #f9f9f9;
            padding: 10px;
            border-left: 4px solid #d9534f;
            margin: 15px 0;
            word-break: break-all;
        }}
        .footer {{
            color: #999;
            font-size: 12px;
            border-top: 1px solid #ddd;
            padding-top: 15px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">⚠️ Alerte de contrôle parental</div>
        <div class="content">
            <p>Bonjour,</p>
            <p>Un contenu potentiellement inapproprié a été détecté lors de l'utilisation du navigateur de votre enfant.</p>
            <p><strong>Site détecté:</strong></p>
            <div class="url">{url}</div>
            <p>Nous vous recommandons de vérifier l'activité et de discuter avec votre enfant des contenus appropriés.</p>
        </div>
        <div class="footer">
            <p>Ce message a été généré automatiquement par le système de contrôle parental.</p>
        </div>
    </div>
</body>
</html>
"""

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
    text = payload["text"]
    url=payload["url"]
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
        msg["Subject"] = "⚠️ Alerte de contrôle parental"
        msg["From"] = EMAIL
        msg["To"] = EMAIL
        
        # Use email template
        html_content = EMAIL_TEMPLATE.format(url=url)
        msg.set_content("Contenu inapproprié détecté sur: " + url)
        msg.add_alternative(html_content, subtype="html")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.send_message(msg)

    return {
        "non_adequate": non_adequate,
        "scores": scores
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)