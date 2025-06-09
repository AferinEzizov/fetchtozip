from fastapi import FastAPI 
from app.api.routes import router


app = FastAPI(title="Fetch to Zip Microservice")
app.include_router(router)
