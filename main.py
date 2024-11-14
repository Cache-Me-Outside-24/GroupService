import logging
import time
import uvicorn

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from resources import create_group, get_group_from_id, get_all_groups, delete_group, get_group_members

app = FastAPI()

app.include_router(create_group.router)
app.include_router(get_group_from_id.router)
app.include_router(get_all_groups.router)
app.include_router(delete_group.router)
app.include_router(get_group_members.router)

# set up middleware logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# middleware to log requests before and after
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")

    # log before the request is processed
    start_time = time.time()

    # call the next process in the pipeline
    response = await call_next(request)

    # log after the request is processed
    process_time = time.time() - start_time
    logger.info(f"Response status: {response.status_code} | Time: {process_time:.4f}s")

    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Replace "*" with your UI's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def get_root():
    # GroupService info
    microservice_info = {
        "name": "GroupService",
        "description": "Manages group creation and detail retrieval",
    }
    return microservice_info

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)