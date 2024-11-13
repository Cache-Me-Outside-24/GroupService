from fastapi import APIRouter, HTTPException, Response
from services.sql_comands import SQLMachine
from pydantic import BaseModel
from typing import List

router = APIRouter()

### HATEOAS ###

# pydantic model for HATEOAS links
class Link(BaseModel):
    rel: str
    href: str

# response model
class GetGroupResponse(BaseModel):
    group_id: int
    name: str
    group_photo: str
    members: List[str]
    labels: List[str]
    links: List[Link]  # HATEOAS links


@router.get(
    "/groups/{group_id}",
    response_model=GetGroupResponse,
    status_code=200,
    summary="Get a group by its GroupID",
    description="Retrieve detailed information about a group by its unique ID.",
    responses={
        202: {
            "description": "Request accepted but still processing. Check back later for results."
        },
        404: {"description": "Group not found. The specified group ID does not exist."},
    },
)
def get_group_from_id(
    group_id: str,
):
    sql = SQLMachine()

    result = sql.select("group_service_db", "groups", {"group_id": group_id})

    # if no result is found, raise a 404 error
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")
    
    result = result[0]

    members_result = sql.select("group_service_db", "group_members", {"group_id": group_id})
    members = []

    for member in members_result:
        members.append(get_user_name_from_id(member[1]))

    # TODO: get members + labels from other tables
    # result["members"] = result["members"].split(",") if "members" in result else []
    # result["labels"] = result["labels"].split(",") if "labels" in result else []

    # HATEOAS links
    links = [
        {"rel": "self", "href": f"/api/groups/{group_id}"},
        {"rel": "members", "href": f"/api/groups/{group_id}/members"},
        {"rel": "expenses", "href": f"/api/groups/{group_id}/expenses"},
    ]

    return GetGroupResponse(
        group_id=result[0],
        name=result[1],
        group_photo=result[2],
        members=members,
        labels=[],
        links=links,
    )

def get_user_name_from_id(id):
    """
        TODO: Replace with call to user microservice.
    """
    sql = SQLMachine()

    result = sql.select("user_service_db", "users", {"id": id})
    if not result:
        raise Exception("No user with this id found.")

    return result[0][2]