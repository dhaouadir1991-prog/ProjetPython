from fastapi import FastAPI
from transformers import pipeline
import uvicorn

app = FastAPI()

classifier = pipeline(
    "text-classification",
    model="unitary/unbiased-toxic-roberta",
    top_k=None
)

@app.post("/moderate")
def moderate(payload: dict):
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