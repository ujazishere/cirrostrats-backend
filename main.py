from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
from routes.route import register_routes

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

register_routes(app)

@app.get("/")
def root():
    return {"message": "Hello World"}
