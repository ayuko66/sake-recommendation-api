from fastapi import FastAPI

app = FastAPI(title="Sake Reco MVP")

@app.get("/health")
def health():
    return {"status": "ok"}