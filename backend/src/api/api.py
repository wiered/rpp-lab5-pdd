__all__ = ["app"]
__version__ = "0.1"
__author__ = "Wiered"

import os

from fastapi import FastAPI, Form, Request, status

from src.database import DataBase, db

app = FastAPI()

@app.get("/")
async def root(request: Request):
    return {"message": "Hello World"}

