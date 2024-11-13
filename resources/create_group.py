from fastapi import APIRouter, HTTPException, Response
from services.sql_comands import SQLMachine
from pydantic import BaseModel
from typing import List

router = APIRouter()


# Define a Pydantic model for the request body
class CreateGroupRequest(BaseModel):
    name: str  # name of the group
    group_photo: str # link to a picture for the group
    members: List[str]  # list of group members (emails)

### HATEOAS ###


# Link model to represent HATEOAS links
class Link(BaseModel):
    rel: str
    href: str


# Model for a single group with HATEOAS links
class CreateGroupResponse(BaseModel):
    group_id: int
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
    try:
        sql = SQLMachine()

        # TODO: process progress of request completion after accepted
        if group.name == "deferred":  # temp condition to simulate async handling
            raise HTTPException(
                status_code=202,
                detail="Group creation accepted, processing asynchronously",
            )

        group_data = group.model_dump()

        # insert group into db
        id = sql.insert("group_service_db", "groups", {"group_name": group_data["name"], "group_photo": group_data["group_photo"]})

        # insert members into db
        for member in group_data["members"]:
            uid = get_uid_from_email(member)
            sql.insert("group_service_db", "group_members", {"user_id": uid, "group_id": id})


        # HATEOAS links
        links = [
            {"rel": "self", "href": f"/api/groups/{id}"},
            {"rel": "members", "href": f"/api/groups/{id}/members"},
            {"rel": "expenses", "href": f"/api/groups/{id}/expenses"},
        ]

        response.headers["Link"] = f'</groups/{id}>; rel="created-resource"'
        return CreateGroupResponse(group_id=id, name=group.name, links=links)

    except Exception as e:
        print(repr(e))
        raise HTTPException(
            status_code=400, detail="An error occurred while creating the group"
        )

def get_uid_from_email(email: str):
    """
        Temporary fix to get group creation to work properly.
        TODO: REPLACE WITH CALL TO USER MICROSERVICE
    """
    sql = SQLMachine()

    result = sql.select("user_service_db", "users", {"email": email})
    if not result:
        raise Exception("No user with this email found.")

    return result[0][0]