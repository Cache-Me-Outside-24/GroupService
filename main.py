from typing import Union
from fastapi import FastAPI, Depends, HTTPException
from starlette.config import Config
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse

app=FastAPI()

@app.get("/")
def get_root():
    return {"do it work"}
