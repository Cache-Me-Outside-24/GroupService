from typing import Union
from fastapi import FastAPI, Depends, HTTPException
from dotenv import load_dotenv
from resources import create_group, get_group_from_id, get_all_groups

app = FastAPI()

app.include_router(create_group.router)
app.include_router(get_group_from_id.router)
app.include_router(get_all_groups.router)


@app.get("/")
def get_root():
    return {"do it work"}
