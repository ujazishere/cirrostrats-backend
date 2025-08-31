from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import routes.route as route
from services.search import (
    get_search_timeline_service,
    get_all_searches_service,
    get_user_searches_service
)
from routes import search_routes


app = FastAPI()

app.include_router(route.router)

origins = [
    "http://localhost:5173"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)


@app.get("/")
def root():
    return {"message": "Hello World"}

app.include_router(search_routes.router)
