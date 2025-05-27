__all__ = ["app"]
__version__ = "0.1"
__author__ = "Wiered"

import os

from fastapi import FastAPI, Form, Request, status

from src.database import DataBase

app = FastAPI()
db = DataBase(
    os.environ.get("DB_NAME"),
    os.environ.get("DB_USER"),
    os.environ.get("DB_HOST"),
    os.environ.get("DB_PASSWORD"),
    os.environ.get("DB_PORT"),
    )

@app.get("/")
async def root(request: Request):
    return {"message": "Hello World"}

