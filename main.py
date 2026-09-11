import os
import json
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import requests

from services.cultural_engine import cultural_engine

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = FastAPI(title="DharoharSetu", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ── Storyteller import (lazy to avoid circular) ──────────────────────────────
from services.storyteller import ai_storyteller

# ── Pydantic models for submissions ──────────────────────────────────────────
VALID_CATEGORIES = ["Temple", "Fort", "Palace", "Mosque", "Church", "Monument",
                    "Stupa", "Archaeological Site", "Nature Site", "Heritage Village", "Other"]
VALID_MONTHS = ["January","February","March","April","May","June",
                "July","August","September","October","November","December"]

class SiteSubmission(BaseModel):
    name: str
    hindi_name: str
    district: str
    state: str
    lat: float
    lng: float
    category: str
    description: str
    folklore_secret: Optional[str] = ""
    best_time_to_visit: Optional[str] = "October to March"
    image_url: Optional[str] = ""

class FestivalSubmission(BaseModel):
    name: str
    hindi_name: str
    state: str
    district: str
    season_month: str
    traditional_timing: Optional[str] = ""
    cultural_significance: str
    must_experience: Optional[str] = ""
    summary: Optional[str] = ""


# ── Helpers ───────────────────────────────────────────────────────────────────
def _validate_site(s: SiteSubmission):
    errors = []
    if len(s.name.strip()) < 3:
        errors.append("Site name must be at least 3 characters.")
    if len(s.state.strip()) < 2:
        errors.append("State name is required.")
    if not (-90 <= s.lat <= 90):
        errors.append("Latitude must be between -90 and 90.")
    if not (-180 <= s.lng <= 180):
        errors.append("Longitude must be between -180 and 180.")
    if not (6.0 <= s.lat <= 37.5 and 68.0 <= s.lng <= 97.5):
        errors.append("Coordinates must be within India.")
    if len(s.description.strip()) < 10:
        errors.append("Description must be at least 10 characters.")
    return errors

def _validate_festival(f: FestivalSubmission):
    errors = []
    if len(f.name.strip()) < 3:
        errors.append("Festival name must be at least 3 characters.")
    if len(f.state.strip()) < 2:
        errors.append("State is required.")
    if len(f.cultural_significance.strip()) < 10:
        errors.append("Cultural significance must be at least 10 characters.")
    return errors

def _save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_json(path: Path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


# ── Routes ────────────────────────────────────────────────────────────────────
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
        "version": "4.0.0",
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
    return {"count": len(sites), "mode": mode, "state": state, "sites": sites}

@app.get("/api/states")
async def get_all_states():
    states = sorted(list(set(s["state"] for s in cultural_engine.sites)))
    return {"states": states}

@app.get("/api/festivals")
async def get_festivals(state: str = Query("Jammu and Kashmir")):
    fests = cultural_engine.get_festivals(state)
    return {"state": state, "count": len(fests), "festivals": fests}

@app.get("/api/storyteller")
async def get_site_story(site_id: str = Query(...), lang: str = Query("hi")):
    return ai_storyteller.generate_site_story(site_id, lang=lang)

@app.get("/api/route")
async def get_route(
    from_lat: float = Query(...), from_lng: float = Query(...),
    to_lat: float = Query(...),   to_lng: float = Query(...)
):
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
        coords = route["geometry"]["coordinates"]
        distance_km = round(route["distance"] / 1000, 1)
        duration_min = round(route["duration"] / 60, 1)
        return {"status": "ok", "distance_km": distance_km, "duration_minutes": duration_min, "coordinates": coords}
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="OSRM routing service timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── NEW: User Site Submission ─────────────────────────────────────────────────
@app.post("/api/submit/site")
async def submit_site(submission: SiteSubmission):
    """Accept a user-submitted heritage site. Validates and auto-approves if valid."""
    errors = _validate_site(submission)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    new_id = "user_" + uuid.uuid4().hex[:8]
    site_obj = {
        "id": new_id,
        "name": submission.name.strip(),
        "hindi_name": submission.hindi_name.strip() or submission.name.strip(),
        "district": submission.district.strip(),
        "state": submission.state.strip(),
        "lat": submission.lat,
        "lng": submission.lng,
        "category": submission.category,
        "period": "Contemporary",
        "cultural_zone": submission.state.strip(),
        "description": submission.description.strip(),
        "folklore_secret": submission.folklore_secret.strip() if submission.folklore_secret else "",
        "best_time_to_visit": submission.best_time_to_visit or "October to March",
        "image_url": submission.image_url or "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=800&q=80",
        "user_submitted": True
    }

    # Save to user_sites.json (persistent)
    user_sites_path = DATA_DIR / "user_sites.json"
    existing = _load_json(user_sites_path, [])
    existing.append(site_obj)
    _save_json(user_sites_path, existing)

    # Reload in memory so it shows immediately without restart
    cultural_engine.reload_user_data()

    return {
        "status": "approved",
        "message": "Aapka heritage site safaltapoorvak jod diya gaya hai! / Your heritage site has been added successfully!",
        "site_id": new_id,
        "site": site_obj
    }


# ── NEW: User Festival Submission ─────────────────────────────────────────────
@app.post("/api/submit/festival")
async def submit_festival(submission: FestivalSubmission):
    """Accept a user-submitted local festival. Validates and auto-approves if valid."""
    errors = _validate_festival(submission)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    new_id = "ufest_" + uuid.uuid4().hex[:8]
    fest_obj = {
        "id": new_id,
        "name": submission.name.strip(),
        "hindi_name": submission.hindi_name.strip() or submission.name.strip(),
        "state": submission.state.strip(),
        "district": submission.district.strip(),
        "season_month": submission.season_month.strip(),
        "traditional_timing": submission.traditional_timing or "",
        "cultural_significance": submission.cultural_significance.strip(),
        "must_experience": submission.must_experience or "",
        "summary": submission.summary or submission.cultural_significance.strip(),
        "user_submitted": True
    }

    # Save to user_festivals.json (persistent)
    user_fests_path = DATA_DIR / "user_festivals.json"
    existing = _load_json(user_fests_path, [])
    existing.append(fest_obj)
    _save_json(user_fests_path, existing)

    # Reload in memory
    cultural_engine.reload_user_data()

    return {
        "status": "approved",
        "message": "Aapka lok-utsav safaltapoorvak jod diya gaya hai! / Your festival has been added successfully!",
        "festival_id": new_id,
        "festival": fest_obj
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
