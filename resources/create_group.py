from fastapi import APIRouter, HTTPException, Response, UploadFile, Form
from services.sql_comands import SQLMachine
from pydantic import BaseModel
from typing import List
from google.cloud import storage

router = APIRouter()


# Define a Pydantic model for the request body
class CreateGroupRequest(BaseModel):
    name: str  # name of the group
    group_photo: str = None  # link to a picture for the group
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


# GCP Bucket Configuration
BUCKET_NAME = "cache-me-outside"


def upload_to_gcp(file: UploadFile, destination_blob_name: str) -> str:
    """
    Uploads a file to GCP bucket and returns the public URI.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        # Upload the file
        blob.upload_from_file(file.file)

        # Make the file publicly accessible
        blob.make_public()

        return blob.public_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")


@router.post("/upload-photo")
async def upload_photo(file: UploadFile):
    """
    Endpoint to upload a photo to GCP bucket and return its URI.
    """
    try:
        # Generate a unique file name for the photo
        destination_blob_name = f"temp/{file.filename}"
        public_url = upload_to_gcp(file, destination_blob_name)
        return {"uri": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
async def create_new_group(
    request: CreateGroupRequest,
    response: Response = None,
):
    try:
        name = request.name
        member_emails = request.members
        group_photo = request.group_photo
        sql = SQLMachine()

        # Insert group into the database
        group_id = sql.insert(
            "group_service_db",
            "groups",
            {
                "group_name": name,
                "group_photo": group_photo,  # Save the URI in the database
            },
        )

        # Insert members into the database
        for email in member_emails:
            uid = get_uid_from_email(email)
            sql.insert(
                "group_service_db",
                "group_members",
                {"user_id": uid, "group_id": group_id},
            )

        # Rename the photo in GCP bucket to include the group_id
        if group_photo:
            storage_client = storage.Client()
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(f"temp/{group_photo.split('/')[-1]}")  # Temp file name
            new_blob_name = f"groups/{group_id}_photo.png"
            bucket.rename_blob(blob, new_blob_name)

            # Update the database with the new URI
            updated_photo_uri = (
                f"https://storage.googleapis.com/{BUCKET_NAME}/{new_blob_name}"
            )
            sql.update(
                "group_service_db",
                "groups",
                {"group_photo": updated_photo_uri},
                {"group_id": group_id},
            )

        # HATEOAS links
        links = [
            {"rel": "self", "href": f"groups/{group_id}"},
            {"rel": "members", "href": f"groups/{group_id}/members"},
            {"rel": "expenses", "href": f"groups/{group_id}/expenses"},
        ]

        response.headers["Link"] = f'</groups/{group_id}>; rel="created-resource"'
        return CreateGroupResponse(group_id=group_id, name=name, links=links)

    except Exception as e:
        print(repr(e))
        raise HTTPException(
            status_code=400, detail="An error occurred while creating the group"
        )


@router.get("/groups/{group_id}/photo")
def get_group_photo(group_id: int):
    try:
        # Access your SQL database to fetch the photo path
        sql = SQLMachine()
        result = sql.select("group_service_db", "groups", {"group_id": group_id})
        if not result or not result[0]["group_photo"]:
            raise HTTPException(status_code=404, detail="Group photo not found")

        photo_uri = result[0]["group_photo"]

        # Extract the object name from the URI
        object_name = photo_uri.split(f"{BUCKET_NAME}/")[-1]

        # Access the bucket and fetch the object
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(object_name)

        # Serve the file
        return Response(content=blob.download_as_bytes(), media_type="image/png")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve group photo: {str(e)}"
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
