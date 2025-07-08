__all__ = ["app"]
__version__ = "0.1"
__author__ = "Wiered"

import os
import logging

from fastapi import FastAPI, Request

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(name)s %(message)s",
    level=logging.INFO,
)

app = FastAPI()

@app.get("/")
async def root(request: Request):
    return {"message": "Hello World"}

