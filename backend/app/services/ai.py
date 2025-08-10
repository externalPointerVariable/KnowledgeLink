import asyncio
from typing import List
import google.generativeai as genai
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from app.config.config import settings

# Configure Gemini API with the key from settings
genai.configure(api_key=settings.GEMINI_API_KEY)
model_summary = genai.GenerativeModel('gemini-2.0-flash-preview-05-20')


async def scrape_content(url: str):
    """
    Asynchronously scrapes the title and main text content from a given URL.
    Uses aiohttp for non-blocking requests and BeautifulSoup for parsing.
    """
    async with ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                title = soup.title.string if soup.title and soup.title.string else 'No Title'
                paragraphs = soup.find_all('p')
                content = " ".join([p.get_text() for p in paragraphs])
                
                return title, content
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return "No Title", "Could not scrape content."


async def generate_summary(text: str):
    """
    Uses the Gemini API to generate a concise summary of the text.
    Uses asyncio.to_thread for blocking API calls to avoid blocking the event loop.
    """
    try:
        prompt = f"Summarize the following text concisely:\n\n{text}"
        response = await asyncio.to_thread(model_summary.generate_content, prompt)
        return response.text
    except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary could not be generated."

async def generate_embedding(text: str, is_query: bool = False) -> List[float]:
    """
    Generates a vector embedding for the given text using the Gemini API.
    `is_query` flag is used to select the correct task type for vector search.
    """
    try:
        task_type = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
        response = await asyncio.to_thread(
            genai.embed_content,
            model="embedding-001",
            content=text,
            task_type=task_type
        )
        return response['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

