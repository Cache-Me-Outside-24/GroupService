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

# pydantic model to represent a group member
class Member(BaseModel):
    id: str
    email: str
    name: str
    currency_preference: str
    profile_pic: str
    links: List[Link]

# response model
class GetGroupMembersResponse(BaseModel):
    members: List[Member]
    links: List[Link]  # HATEOAS links


@router.get(
    "/groups/{group_id}/members",
    response_model=GetGroupMembersResponse,
    status_code=200,
    summary="Get information on the members of a group by its GroupID",
    description="Retrieve detailed information about a group's members by its GroupID.",
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
        user_info = get_user_info_from_id(member[1])
        user_links = [
            {"rel": "user", "href": f"/api/users/{user_info[0]}"}
        ]
        
        members.append(Member(
            id=user_info[0],
            email=user_info[1],
            name=user_info[2],
            currency_preference=user_info[3],
            profile_pic=user_info[4],
            links=user_links
        ))
    
    # HATEOAS links
    links = [
        {"rel": "self", "href": f"/api/groups/{group_id}/members"},
        {"rel": "group", "href": f"/api/groups/{group_id}"},
        {"rel": "expenses", "href": f"/api/groups/{group_id}/expenses"},
    ]

    return GetGroupMembersResponse(
        members=members,
        links=links,
    )

def get_user_info_from_id(id):
    """
        TODO: Replace with call to user microservice.
    """
    sql = SQLMachine()

    result = sql.select("user_service_db", "users", {"id": id})
    if not result:
        raise Exception("No user with this id found.")

    return result[0]