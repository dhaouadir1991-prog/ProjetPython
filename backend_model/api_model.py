from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
import uvicorn

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

    return {
        "non_adequate": non_adequate,
        "scores": scores
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)