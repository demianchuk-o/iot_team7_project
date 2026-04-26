from fastapi import FastAPI
from main_router import router as processed_agent_router, parking_router, traffic_light_router

app = FastAPI()

app.include_router(
    processed_agent_router,
    prefix="/processed_agent_data",
    tags=["Processed Agent Data"]
)

app.include_router(parking_router)
app.include_router(traffic_light_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
