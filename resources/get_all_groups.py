from fastapi import APIRouter, HTTPException, Response, Query
from services.sql_comands import SQLMachine
from pydantic import BaseModel
from typing import List

router = APIRouter()

### HATEOAS ###


# pydantic model for HATEOAS links
class Link(BaseModel):
    rel: str
    href: str


# response model for single group in list
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
    "/groups",
    response_model=PaginatedGroupsResponse,
    status_code=200,
    summary="Get all groups",
    description="Retrieve a paginated list of all groups",
    responses={
        202: {
            "description": "Request accepted but still processing. Check back later for results."
        },
        400: {"description": "Bad Request - Could not fetch the groups"},
    },
)
def get_all_groups(limit: int = Query(10), offset: int = Query(0)):
    try:
        sql = SQLMachine()

        # fetch a paginated list of groups
        result = sql.select_paginated(
            "group_service_db", "group", limit=limit, offset=offset
        )
        paginated_results = result["results"]
        total_count = result["total_count"]

        # create HATEOAS links for each group
        groups = []
        for result in paginated_results:
            result["members"] = (
                result["members"].split(",") if "members" in result else []
            )
            result["labels"] = result["labels"].split(",") if "labels" in result else []

            group_links = [
                {"rel": "self", "href": f"/api/groups/{result['group_id']}"},
                {"rel": "members", "href": f"/api/groups/{result['group_id']}/members"},
                {
                    "rel": "expenses",
                    "href": f"/api/groups/{result['group_id']}/expenses",
                },
            ]

            groups.append(
                GetGroupResponse(
                    group_id=result["group_id"],
                    name=result["name"],
                    members=result["members"],
                    labels=result["labels"],
                    links=group_links,
                )
            )

        # pagination links
        pagination_links = [
            {"rel": "current", "href": f"/api/groups?limit={limit}&offset={offset}"},
        ]
        if offset > 0:
            pagination_links.append(
                {
                    "rel": "prev",
                    "href": f"/api/groups?limit={limit}&offset={max(0, offset - limit)}",
                }
            )
        if offset + limit < total_count:
            pagination_links.append(
                {
                    "rel": "next",
                    "href": f"/api/groups?limit={limit}&offset={offset + limit}",
                }
            )

        return PaginatedGroupsResponse(data=groups, links=pagination_links)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="An error occurred while creating the group"
        )
