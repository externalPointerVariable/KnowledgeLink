import os
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config.config import settings
from app.dependencies import client, db
from app.routers.items import router
from app.routers.auth import auth_router

# Define the lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    if not settings.DATABASE_URL:
        raise RuntimeError("MongoDB connection string is not configured.")
    
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    try:
        await client.admin.command("ping")
        db = client[settings.DB_NAME]
        print("Connected to MongoDB successfully.")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise RuntimeError("Could not connect to the database.")

    yield
    
    print("Shutting down MongoDB client.")
    client.close()

# Initialize the FastAPI app
app = FastAPI(title="KnowledgeLink API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the routers
app.include_router(auth_router)
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to the KnowledgeLink API. Navigate to /docs for the API documentation."}

