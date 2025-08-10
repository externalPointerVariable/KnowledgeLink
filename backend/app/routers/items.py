import datetime
from typing import List, Dict
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.dependencies import get_db_client, get_authenticated_user
from app.services.ai import scrape_content, generate_summary, generate_embedding
from app.model.link import Link, LinkIn, SearchResult


router = APIRouter(prefix="/api", tags=["links"])

@router.post("/links", response_model=Dict[str, str])
async def create_link(
    link_in: LinkIn,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_authenticated_user),
    db: AsyncIOMotorDatabase = Depends(get_db_client)
):
    """
    Receives a URL and triggers a background task to process it.
    """
    links_collection = db["links"]

    existing_link = await links_collection.find_one({"userId": user_id, "url": link_in.url})
    if existing_link:
        raise HTTPException(
            status_code=409,
            detail="Link already exists for this user."
        )

    async def process_and_save_link(
        db: AsyncIOMotorDatabase,
        user_id: str,
        url: str
    ):
        """
        Background task to scrape, summarize, embed, and save a link.
        """
        try:
            print(f"Starting background processing for URL: {url}")
            title, content = await scrape_content(url)
            summary = await generate_summary(content)
            embedding = await generate_embedding(content)

            if embedding:
                link_data = Link(
                    id=str(ObjectId()),
                    userId=user_id,
                    url=url,
                    title=title,
                    summary=summary,
                    content_embedding=embedding,
                    createdAt=datetime.datetime.utcnow()
                )
                await db["links"].insert_one(link_data.model_dump(by_alias=True, exclude={'id'}))
                print(f"Successfully processed and saved link: {url}")
            else:
                print(f"Failed to generate embedding for {url}. Not saving.")

        except Exception as e:
            print(f"An error occurred in background task for {url}: {e}")

    background_tasks.add_task(
        process_and_save_link,
        db=db,
        user_id=user_id,
        url=link_in.url
    )
    return {"message": "Link submission received. Processing in the background."}

@router.get("/links", response_model=List[Link])
async def get_links(
    user_id: str = Depends(get_authenticated_user),
    db: AsyncIOMotorDatabase = Depends(get_db_client)
):
    """
    Fetches all links for the currently authenticated user.
    """
    links_collection = db["links"]
    links = await links_collection.find({"userId": user_id}).sort("createdAt", -1).to_list(100)
    return links

@router.get("/search", response_model=List[SearchResult])
async def search_links(
    q: str,
    user_id: str = Depends(get_authenticated_user),
    db: AsyncIOMotorDatabase = Depends(get_db_client)
):
    """
    Performs a vector search on the user's links based on a natural language query.
    """
    links_collection = db["links"]
    
    query_embedding = await generate_embedding(q, is_query=True)
    if not query_embedding:
        raise HTTPException(status_code=500, detail="Could not generate embedding for the query.")

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "content_embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": 10
            }
        },
        {
            "$match": {"userId": user_id}
        },
        {
            "$project": {
                "_id": 0,
                "url": 1,
                "title": 1,
                "summary": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]
    
    results = await links_collection.aggregate(pipeline).to_list(10)
    return results
