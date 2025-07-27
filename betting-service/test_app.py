from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Betting Service Test")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "betting-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=18002)