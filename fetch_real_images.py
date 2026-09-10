import requests
import json

def get_wiki_image(title):
    try:
        headers = {"User-Agent": "DharoharSetuBot/1.0 (contact: test@example.com)"}
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=pageimages&format=json&pithumbsize=900"
        r = requests.get(url, headers=headers, timeout=6)
        pages = r.json().get("query", {}).get("pages", {})
        for pid, pdata in pages.items():
            if "thumbnail" in pdata:
                return pdata["thumbnail"]["source"]
    except Exception as e:
        print(f"Error fetching {title}: {e}")
    return None

mapping = {
  "site-jk-01": "Samba_district",
  "site-jk-02": "Purmandal",
  "site-jk-03": "Purmandal",
  "site-jk-04": "Kathua_district",
  "site-jk-05": "Mansar_Lake",
  "site-jk-06": "Bahu_Fort",
  "site-jk-07": "Mubarak_Mandi_Palace",
  "site-jk-08": "Peer_Kho_Cave_Temple",
  "site-jk-09": "Akhnoor",
  "site-jk-10": "Krimchi_temples",
  "site-jk-11": "Billawar",
  "site-jk-12": "Vaishno_Devi",
  "site-jk-13": "Martand_Sun_Temple",
  "site-jk-14": "Hari_Parbat",
  "site-bih-01": "Nalanda_mahavihara",
  "site-bih-02": "Mahabodhi_Temple",
  "site-bih-03": "Barabar_Caves",
  "site-bih-04": "Cyclopean_Wall_of_Rajgir",
  "site-bih-05": "Tomb_of_Sher_Shah_Suri",
  "site-bih-06": "Mundeshwari_Temple",
  "site-bih-07": "Madhubani_art",
  "site-bih-08": "Kesaria_stupa",
  "site-bih-09": "Rohtasgarh_Fort",
  "site-raj-01": "Amer_Fort",
  "site-raj-02": "Mehrangarh",
  "site-raj-03": "Kumbhalgarh",
  "site-up-01": "Kashi_Vishwanath_Temple",
  "site-up-02": "Dhamek_Stupa",
  "site-mp-01": "Khajuraho_Group_of_Monuments",
  "site-mp-02": "Bhimbetka_rock_shelters"
}

with open("data/heritage_sites.json", "r", encoding="utf-8") as f:
    sites = json.load(f)

updated_count = 0
for s in sites:
    wiki_title = mapping.get(s["id"])
    if wiki_title:
        real_img = get_wiki_image(wiki_title)
        if real_img:
            s["image_url"] = real_img
            updated_count += 1
            print(f"Updated {s['name']} with real photo!")

with open("data/heritage_sites.json", "w", encoding="utf-8") as f:
    json.dump(sites, f, indent=2, ensure_ascii=False)

print(f"Successfully updated {updated_count} sites with authentic Wikipedia photographs!")
