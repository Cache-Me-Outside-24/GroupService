from fastapi import APIRouter, HTTPException, Response
from services.sql_comands import SQLMachine
from pydantic import BaseModel
from typing import List

router = APIRouter()


# Define a Pydantic model for the request body
class CreateGroupRequest(BaseModel):
    name: str  # name of the group
    members: List[str]  # list of group members (just emails for now)


### HATEOAS ###


# Link model to represent HATEOAS links
class Link(BaseModel):
    rel: str
    href: str


# Model for a single group with HATEOAS links
class CreateGroupResponse(BaseModel):
    group_id: str
    name: str
    links: List[Link]  # Related links


# Model for a paginated list of groups
class PaginatedGroupsResponse(BaseModel):
    data: List[CreateGroupResponse]
    links: List[Link]  # Links for pagination


# For OpenAPI documentation
@router.post(
    "/groups",
    status_code=201,
    summary="Create a new group",
    description="Creates a new group with a name and a list of members. Returns 201 Created with a link header if successful.",
    responses={
        201: {
            "description": "Group created successfully with Link header",
            "headers": {
                "Link": {
                    "description": "URL of the created resource",
                    "schema": {"type": "string"},
                    "example": '</groups/1>; rel="created-resource"',
                }
            },
        },
        202: {
            "description": "Request accepted and processing asynchronously. Use the provided URL to check status.",
        },
        400: {"description": "Bad Request - Could not create the group"},
    },
)
def create_new_group(group: CreateGroupRequest, response: Response):
    print(group)
    try:
        sql = SQLMachine()

        # TODO: process progress of request completion after accepted
        if group.name == "deferred":  # temp condition to simulate async handling
            raise HTTPException(
                status_code=202,
                detail="Group creation accepted, processing asynchronously",
            )

        # convert list of members to a comma-separated string for inserting into db
        members_str = ",".join(group.members)

        group_data = group.dict()
        group_data["members"] = members_str

        # insert group into db
        id = sql.insert("group_service_db", "group", group_data)

        # HATEOAS links
        links = [
            {"rel": "self", "href": f"/api/groups/{id}"},
            {"rel": "members", "href": f"/api/groups/{id}/members"},
            {"rel": "expenses", "href": f"/api/groups/{id}/expenses"},
        ]

        response.headers["Link"] = f'</groups/{id}>; rel="created-resource"'
        return CreateGroupResponse(group_id=id, name=group.name, links=links)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail="An error occurred while creating the group"
        )
