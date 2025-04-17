from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
from httpx import QueryParams
from pathlib import Path

app = FastAPI()

# Static frontend + icons
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all (you can restrict later)
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    return FileResponse(Path("frontend/index.html"))

@app.get("/api/image-proxy")
async def image_proxy(url: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        return StreamingResponse(
            content=res.aiter_bytes(),
            status_code=res.status_code,
            media_type=res.headers.get("content-type", "image/jpeg")
        )

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
        print("🔥 SEARCH ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/manga/{manga_id}")
async def manga_detail(manga_id: str):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"https://api.mangadex.org/manga/{manga_id}?includes[]=cover_art"
            )
            res.raise_for_status()

            data = res.json().get("data", {})
            attr = data.get("attributes", {})
            cover_id = next(
                (r["attributes"].get("fileName")
                 for r in data.get("relationships", [])
                 if r.get("type") == "cover_art"),
                None
            )

            cover_url = (
                f"https://uploads.mangadex.org/covers/{manga_id}/{cover_id}"
                if cover_id else None
            )

            return {
                "id": manga_id,
                "title": attr.get("title", {}).get("en", "No Title"),
                "description": attr.get("description", {}).get("en", "No Description"),
                "cover_url": cover_url
            }

    except Exception as e:
        print("🔥 MANGA DETAIL ERROR:", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch manga details: {str(e)}")

@app.get("/api/chapters/{manga_id}")
async def chapters(manga_id: str):
    async with httpx.AsyncClient() as client:
        all_chapters = []
        offset = 0
        limit = 100  # MangaDex's safe max per page

        while True:
            try:
                url = (
                    f"https://api.mangadex.org/chapter?"
                    f"manga={manga_id}&translatedLanguage[]=en"
                    f"&limit={limit}&offset={offset}&order[chapter]=asc"
                )
                res = await client.get(url)
                res.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400 and offset == 0:
                    # Try without ordering
                    url = (
                        f"https://api.mangadex.org/chapter?"
                        f"manga={manga_id}&translatedLanguage[]=en"
                        f"&limit={limit}&offset={offset}"
                    )
                    res = await client.get(url)
                    res.raise_for_status()
                else:
                    raise

            data = res.json()
            chunk = data.get("data", [])
            all_chapters.extend(chunk)

            total = data.get("total", 0)
            offset += limit

            if offset >= total:
                break

        print(f"✅ Total chapters fetched: {len(all_chapters)}")

        return [
            {
                "id": ch.get("id"),
                "chapter": ch.get("attributes", {}).get("chapter"),
                "title": ch.get("attributes", {}).get("title")
            }
            for ch in all_chapters
        ]

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
        print("🔥 PAGE FETCH ERROR:", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to load pages: {str(e)}")