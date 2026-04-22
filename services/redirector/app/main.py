from fastapi import FastAPI

app = FastAPI(title="Redirector Service")

@app.get("/health")
async def health_check():
    return {"status": "ok"}