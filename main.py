from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle

import routes.route as route
from routes import search_routes

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

app.include_router(route.router)
app.include_router(search_routes.router)

@app.get("/")
def root():
    return {"message": "Hello World"}
