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
    group_id: str
    name: str
    members: List[str]
    labels: List[str]
    links: List[Link]  # HATEOAS links


# response model for a paginated list of groups
class PaginatedGroupsResponse(BaseModel):
    data: List[GetGroupResponse]
    links: List[Link]  # Pagination links


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

    result = sql.select("group_service_db", "group", {"group_id": group_id})

    # if no result is found, raise a 404 error
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")

    result["members"] = result["members"].split(",") if "members" in result else []
    result["labels"] = result["labels"].split(",") if "labels" in result else []

    # HATEOAS links
    links = [
        {"rel": "self", "href": f"/api/groups/{group_id}"},
        {"rel": "members", "href": f"/api/groups/{group_id}/members"},
        {"rel": "expenses", "href": f"/api/groups/{group_id}/expenses"},
    ]

    return GetGroupResponse(
        group_id=result["group_id"],
        name=result["name"],
        members=result["members"],
        labels=result["labels"],
        links=links,
    )
