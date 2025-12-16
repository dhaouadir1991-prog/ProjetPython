from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.reddit.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

classifier = pipeline(
    "text-classification",
    model="unitary/unbiased-toxic-roberta",
    top_k=None
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