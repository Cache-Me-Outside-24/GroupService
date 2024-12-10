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
    links: List[Link]  # HATEOAS links


class GroupRequest(BaseModel):
    user_id: str
    limit: int = 10  # Default value
    offset: int = 0  # Default value


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
def get_all_groups(request: GroupRequest):
    try:
        sql = SQLMachine()
        user_id = request.user_id
        limit = request.limit
        offset = request.offset

        # Step 1: Fetch all group_ids associated with the user_id
        user_groups = sql.select(
            "group_service_db", "group_members", {"user_id": user_id}
        )
        group_ids = [group["group_id"] for group in user_groups]

        # Step 2: Fetch group details for each group_id
        groups = []
        for group_id in group_ids:
            # Fetch group details
            group_details = sql.select(
                "group_service_db", "groups", {"group_id": group_id}
            )
            if not group_details:
                continue
            group_details = group_details[0]

            # Step 3: Fetch all user_ids associated with this group_id
            group_members = sql.select(
                "group_service_db", "group_members", {"group_id": group_id}
            )
            member_user_ids = [member["user_id"] for member in group_members]

            # Step 4: Fetch email addresses for each user_id
            member_emails = []
            for member_user_id in member_user_ids:
                user_details = sql.select(
                    "user_service_db", "users", {"id": member_user_id}
                )
                if user_details:
                    member_emails.append(user_details[0]["email"])

            # Create HATEOAS links
            group_links = [
                {"rel": "self", "href": f"groups/{group_id}"},
                {"rel": "members", "href": f"groups/{group_id}/members"},
                {"rel": "expenses", "href": f"groups/{group_id}/expenses"},
            ]

            groups.append(
                GetGroupResponse(
                    group_id=group_details["group_id"],
                    name=group_details["group_name"],
                    members=member_emails,
                    links=group_links,
                )
            )

        # Step 5: Add pagination links
        pagination_links = [
            {"rel": "current", "href": f"groups?limit={limit}&offset={offset}"},
        ]
        if offset > 0:
            pagination_links.append(
                {
                    "rel": "prev",
                    "href": f"groups?limit={limit}&offset={max(0, offset - limit)}",
                }
            )
        if offset + limit < len(groups):
            pagination_links.append(
                {
                    "rel": "next",
                    "href": f"groups?limit={limit}&offset={offset + limit}",
                }
            )

        # Apply pagination
        paginated_groups = groups[offset : offset + limit]

        return PaginatedGroupsResponse(data=paginated_groups, links=pagination_links)

    except Exception as e:
        print(f"Error fetching groups: {repr(e)}")
        raise HTTPException(
            status_code=400, detail="An error occurred while fetching groups"
        )
