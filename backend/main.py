from fastapi import FastAPI, Path, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import httpx

app = FastAPI()

# Serve static files (images, CSS, etc.)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# CORS for frontend -> backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve index.html at root path
@app.get("/")
def serve_index():
    return FileResponse(Path("frontend/index.html"))

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/search")
async def search(title: str):
    try:
        url = f"https://api.mangadex.org/manga?title={title}&limit=10"
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            res.raise_for_status()
            return [
                {
                    "id": m["id"],
                    "title": m["attributes"]["title"].get("en", "No English title")
                }
                for m in res.json().get("data", [])
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chapters/{manga_id}")
async def chapters(manga_id: str):
    try:
        url = f"https://api.mangadex.org/chapter?manga={manga_id}&translatedLanguage[]=en&order[chapter]=asc"
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            res.raise_for_status()
            return [
                {
                    "id": c["id"],
                    "chapter": c["attributes"].get("chapter", "N/A")
                }
                for c in res.json().get("data", [])
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pages/{chapter_id}")
async def pages(chapter_id: str):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://api.mangadex.org/at-home/server/{chapter_id}")
            res.raise_for_status()

            json_data = res.json()
            base_url = json_data["baseUrl"]
            chapter = json_data["chapter"]

            hash_value = chapter["hash"]
            page_filenames = chapter["data"]

            return [f"{base_url}/data/{hash_value}/{filename}" for filename in page_filenames]

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to load pages: {str(e)}")