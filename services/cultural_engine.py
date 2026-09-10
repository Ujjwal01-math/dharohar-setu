import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

class CulturalEngine:
    def __init__(self):
        self.sites_file = DATA_DIR / "heritage_sites.json"
        self.festivals_file = DATA_DIR / "hidden_festivals.json"
        self._load_data()

    def _load_data(self):
        with open(self.sites_file, "r", encoding="utf-8") as f:
            self.sites: List[Dict[str, Any]] = json.load(f)
        with open(self.festivals_file, "r", encoding="utf-8") as f:
            self.festivals: List[Dict[str, Any]] = json.load(f)

    def detect_location_from_ip(self) -> Dict[str, Any]:
        """Detects user location seamlessly via IP."""
        try:
            import requests
            r = requests.get("https://ipwho.is/", timeout=4)
            if r.status_code == 200:
                data = r.json()
                if data.get("success", True):
                    lat = float(data.get("latitude", 32.5625))
                    lng = float(data.get("longitude", 75.1200))
                    state = data.get("region", "Jammu and Kashmir")
                    city = data.get("city", "Samba")
                    return self.analyze_location(lat, lng, fallback_state=state, fallback_city=city)
        except Exception:
            pass
        return self.analyze_location(32.5625, 75.1200, fallback_state="Jammu and Kashmir", fallback_city="Samba")

    def analyze_location(self, lat: float, lng: float, fallback_state: Optional[str] = None, fallback_city: Optional[str] = None) -> Dict[str, Any]:
        state = fallback_state
        district = fallback_city

        try:
            import requests
            headers = {"User-Agent": "DharoharSetu-SIH/1.0"}
            r = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json", headers=headers, timeout=3.5)
            if r.status_code == 200:
                addr = r.json().get("address", {})
                state = addr.get("state") or addr.get("state_district") or state
                district = addr.get("county") or addr.get("city") or addr.get("town") or district
        except Exception:
            pass

        if not state:
            state = "Jammu and Kashmir"
            district = "Samba"

        return {
            "latitude": lat,
            "longitude": lng,
            "state": state,
            "district": district or "Central"
        }

    def get_sites(self, lat: float, lng: float, mode: str = "nearby", state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Site fetching:
        - mode == 'state': returns ALL sites in the state (no distance filter at all)
        - mode == 'nearby': returns sites within 150km of user location
        """
        results = []
        target_state = (state or "Jammu and Kashmir").strip()

        for site in self.sites:
            dist = haversine_km(lat, lng, site["lat"], site["lng"])
            site_data = dict(site)
            site_data["distance_km"] = dist

            if mode == "state":
                # Pure state filter — no distance cutoff whatsoever
                if (target_state.lower() in site["state"].lower() or
                        site["state"].lower() in target_state.lower()):
                    results.append(site_data)
            else:
                # Nearby: within 150km
                if dist <= 150:
                    results.append(site_data)

        results.sort(key=lambda x: x["distance_km"])
        return results

    def get_festivals(self, state: str) -> List[Dict[str, Any]]:
        """Returns ALL regional festivals for the state."""
        target = state.lower()
        matched = [f for f in self.festivals if f["state"].lower() in target or target in f["state"].lower()]
        return matched if matched else self.festivals[:5]

cultural_engine = CulturalEngine()
