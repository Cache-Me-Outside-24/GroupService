from fastapi import APIRouter
from services.sql_comands import SQLMachine
from pydantic import BaseModel

router = APIRouter()

@router.get("/groups/{group_id}", status_code=201)
def get_group_from_id(group_id: str): #TODO: error handling and 400 code if it doesnt worka
    print(group_id)
    sql = SQLMachine()

    result = sql.select("group_service_db", "group", {"group_id": group_id})
    return result
