from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
from pathlib import Path

app = FastAPI()

# Serve static files like icons, manifest, images
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve index.html at root
@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    return FileResponse(Path("frontend/index.html"))

# Health check
@app.get("/api/health")
def health():
    return {"status": "ok"}

# Search manga by title
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

# Get manga description and cover
@app.get("/api/manga/{manga_id}")
async def manga_detail(manga_id: str):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://api.mangadex.org/manga/{manga_id}?includes[]=cover_art")
            res.raise_for_status()
            data = res.json().get("data", {})
            attr = data.get("attributes", {})
            cover_id = next((r["attributes"]["fileName"] for r in data.get("relationships", []) if r["type"] == "cover_art"), None)

            return {
                "id": manga_id,
                "title": attr.get("title", {}).get("en", "No Title"),
                "description": attr.get("description", {}).get("en", "No Description"),
                "cover_url": f"https://uploads.mangadex.org/covers/{manga_id}/{cover_id}" if cover_id else None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch manga details: {str(e)}")

# Get all English chapters for a manga
@app.get("/api/chapters/{manga_id}")
async def chapters(manga_id: str):
    try:
        url = (
            f"https://api.mangadex.org/chapter?"
            f"manga={manga_id}&translatedLanguage[]=en"
            f"&order[chapter]=asc&limit=500"
        )
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            res.raise_for_status()
            return [
                {
                    "id": c["id"],
                    "chapter": c["attributes"].get("chapter"),
                    "title": c["attributes"].get("title")
                }
                for c in res.json().get("data", [])
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chapters/{manga_id}")
async def chapters(manga_id: str):
    try:
        url = (
            f"https://api.mangadex.org/chapter?"
            f"manga={manga_id}&translatedLanguage[]=en"
            f"&order[chapter]=asc&limit=500"
        )
        async with httpx.AsyncClient() as client:
            res = await client.get(url)
            res.raise_for_status()
            chapters_raw = res.json().get("data", [])

            chapter_list = []
            for c in chapters_raw:
                try:
                    attr = c.get("attributes", {})
                    chapter_list.append({
                        "id": c.get("id"),
                        "chapter": attr.get("chapter") or None,
                        "title": attr.get("title") or None
                    })
                except Exception as inner:
                    print(f"Skipped malformed chapter entry: {c} → {inner}")
                    continue

            print(f"✅ Loaded {len(chapter_list)} chapters for manga {manga_id}")
            return chapter_list

    except Exception as e:
        print("🔥 CHAPTER API ERROR:", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch chapters: {str(e)}")