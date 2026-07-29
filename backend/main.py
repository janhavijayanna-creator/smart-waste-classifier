from fastapi import FastAPI
from backend.routes.prediction import router as prediction_router

app = FastAPI(
    title="Smart Waste Classification API",
    version="1.0.0"
)

app.include_router(prediction_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to Smart Waste Classification API"
    }