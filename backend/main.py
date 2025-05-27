__version__ = "1.0"
__author__ = "Wiered"

import os

from dotenv import load_dotenv
from fastapi import FastAPI

from src.api import api_router

load_dotenv()

import uvicorn

app = FastAPI()
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT"))
    except:
        port = 8080
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
