from fastapi import FastAPI
from main_router import router as sensor_router

app = FastAPI(title="RoadVision Store API")

app.include_router(
    sensor_router,
    prefix="/sensors",
    tags=["Sensors"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
