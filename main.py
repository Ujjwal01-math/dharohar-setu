import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests

from services.cultural_engine import cultural_engine
from services.storyteller import ai_storyteller

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="DharoharSetu", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = BASE_DIR / "templates" / "index.html"
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "app": "DharoharSetu (धरोहर सेतु)",
        "version": "3.0.0",
        "total_monuments": len(cultural_engine.sites),
        "total_festivals": len(cultural_engine.festivals)
    }

@app.get("/api/location/auto-ip")
async def auto_ip_location():
    return cultural_engine.detect_location_from_ip()

@app.get("/api/location/analyze")
async def analyze_location(lat: float = Query(32.5625), lng: float = Query(75.1200)):
    return cultural_engine.analyze_location(lat, lng)

@app.get("/api/sites")
async def get_sites(
    lat: float = Query(32.5625),
    lng: float = Query(75.1200),
    mode: str = Query("nearby"),
    state: Optional[str] = "Jammu and Kashmir"
):
    sites = cultural_engine.get_sites(lat=lat, lng=lng, mode=mode, state=state)
    return {
        "count": len(sites),
        "mode": mode,
        "state": state,
        "sites": sites
    }

@app.get("/api/states")
async def get_all_states():
    """Return all unique states that have heritage sites."""
    states = sorted(list(set(s["state"] for s in cultural_engine.sites)))
    return {"states": states}

@app.get("/api/festivals")
async def get_festivals(state: str = Query("Jammu and Kashmir")):
    fests = cultural_engine.get_festivals(state)
    return {
        "state": state,
        "count": len(fests),
        "festivals": fests
    }

@app.get("/api/storyteller")
async def get_site_story(site_id: str = Query(...), lang: str = Query("hi")):
    return ai_storyteller.generate_site_story(site_id, lang=lang)

@app.get("/api/route")
async def get_route(
    from_lat: float = Query(...),
    from_lng: float = Query(...),
    to_lat: float = Query(...),
    to_lng: float = Query(...)
):
    """
    Get driving route between two coordinates using OSRM.
    Returns GeoJSON polyline, distance (km) and duration (minutes).
    """
    try:
        osrm_url = (
            f"https://router.project-osrm.org/route/v1/driving/"
            f"{from_lng},{from_lat};{to_lng},{to_lat}"
            f"?overview=full&geometries=geojson&steps=false"
        )
        resp = requests.get(osrm_url, timeout=10)
        data = resp.json()

        if data.get("code") != "Ok":
            raise HTTPException(status_code=404, detail="Route not found")

        route = data["routes"][0]
        coords = route["geometry"]["coordinates"]  # [[lng, lat], ...]
        distance_km = round(route["distance"] / 1000, 1)
        duration_min = round(route["duration"] / 60, 1)

        return {
            "status": "ok",
            "distance_km": distance_km,
            "duration_minutes": duration_min,
            "coordinates": coords  # [lng, lat] pairs — frontend must reverse to [lat, lng] for Leaflet
        }
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="OSRM routing service timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
