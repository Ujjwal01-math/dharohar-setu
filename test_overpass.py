import requests

overpass_url = "https://overpass-api.de/api/interpreter"
query = """
[out:json][timeout:15];
(
  node["historic"](around:60000, 32.56, 75.12);
  way["historic"](around:60000, 32.56, 75.12);
  node["tourism"="museum"](around:60000, 32.56, 75.12);
);
out center 40;
"""

try:
    r = requests.post(overpass_url, data={"data": query}, timeout=15)
    data = r.json()
    elements = data.get("elements", [])
    print(f"Overpass found {len(elements)} real heritage sites!")
    for el in elements[:10]:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        if name:
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            print(f"- {name} ({tags.get('historic', 'heritage')}) @ {lat}, {lon}")
except Exception as e:
    print("Error:", e)
