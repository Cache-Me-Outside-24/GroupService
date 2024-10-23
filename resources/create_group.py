from fastapi import APIRouter
from services.sql_comands import SQLMachine
from pydantic import BaseModel

router = APIRouter()

@router.post("/groups", status_code=201)
def create_new_group(group: dict[str, str]): #TODO: error handling and 400 code if it doesnt work
    print(group)
    sql = SQLMachine()

    id = sql.insert("group_service_db", "group", group)
    return {"group-id": id}