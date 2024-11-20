from fastapi import APIRouter, HTTPException, Response, Query
from services.sql_comands import SQLMachine

router = APIRouter()

@router.delete(
    "/groups/{group_id}",
    status_code=204,
    summary="Get a group by its GroupID",
    description="Retrieve detailed information about a group by its unique ID.",
    responses={
        404: {"description": "Group not found. The specified group ID does not exist."},
        500: {"description": "Something strange happened."}
    },
)
def delete_group(
    group_id: str
):
    sql = SQLMachine()

    result = sql.delete("group_service_db", "group_members", {"group_id": group_id})
    result = sql.delete("group_service_db", "groups", {"group_id": group_id})

    if result == 0:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if result > 1:
        raise HTTPException(status_code=500, detail=f"Too many ({result}) rows deleted.")
    
    return Response(status_code=204)