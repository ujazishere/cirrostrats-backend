from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
from routes.route import register_routes
from utils.logging_config import setup_logging
from utils.logging_middleware import RequestContextLogMiddleware

# Initialize structured logging early
setup_logging(service="cirrostrats-backend-api")

app = FastAPI()

origins = [
    "http://localhost:5173",
    "https://your-ngrok-url.ngrok-free.app",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Access logging and request-id propagation
app.add_middleware(RequestContextLogMiddleware)

register_routes(app)

@app.get("/")
def root():
    return {"message": "Hello World"}
