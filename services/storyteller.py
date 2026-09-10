import os
from typing import Dict, Any, Optional
from services.cultural_engine import cultural_engine

# ── Gemini API (optional – falls back to template if key not set) ──────────
_gemini_model = None

def _get_gemini():
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        return _gemini_model
    except Exception:
        return None

def _call_gemini(prompt: str) -> Optional[str]:
    model = _get_gemini()
    if not model:
        return None
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception:
        return None


class AIStoryteller:
    """
    AI-powered heritage and cultural folklore narrative engine.
    Uses Gemini API if GOOGLE_API_KEY is set, otherwise falls back to rich
    template-based storytelling in Hindi and English.
    """

    def generate_site_story(self, site_id: str, lang: str = "hi") -> Dict[str, Any]:
        site = next((s for s in cultural_engine.sites if s["id"] == site_id), None)
        if not site:
            return {"error": "Heritage site not found"}

        # Try Gemini first
        gemini_result = self._try_gemini_story(site, lang)
        if gemini_result:
            return gemini_result

        # Fallback: template-based
        name = site.get("name", "")
        hindi_name = site.get("hindi_name", name)
        period = site.get("period", "Ancient Era")
        secret = site.get("folklore_secret", "")
        desc = site.get("description", "")
        zone = site.get("cultural_zone", "")
        best_time = site.get("best_time_to_visit", "October to March")

        if lang == "hi":
            title = f"रहस्य और गौरव: {hindi_name}"
            intro = (f"नमस्कार! आप इस समय {zone} के सबसे गौरवशाली धरोहर, '{hindi_name}' के सानिध्य में हैं। "
                     f"यह स्थल {period} से भारतीय सभ्यता और संस्कृति का साक्षी रहा है।")
            lore = f"यहाँ की एक अनोखी लोक-कथा और रहस्य यह है कि: {secret}"
            deep_dive = (f"{desc} जब आप यहाँ की दीवारों, मेहराबों और प्राचीन पत्थरों को ध्यान से देखते हैं, "
                         f"तो आपको ऐसा प्रतीत होगा मानो सदियों का इतिहास आपसे सीधे संवाद कर रहा हो।")
            practical = (f"भ्रमण का सबसे उत्तम समय: {best_time} है। "
                         f"यहाँ की मिट्टी और वास्तुकला की पवित्रता का सदैव सम्मान करें।")
        else:
            title = f"Secrets & Legend: {name}"
            intro = (f"Greetings, explorer! You are in the presence of '{name}', one of the monumental jewels "
                     f"of the {zone}. Dating back to {period}, this sacred ground preserves millennia of civilizational wisdom.")
            lore = f"A hidden legend preserved in local folklore whispers that: {secret}"
            deep_dive = (f"{desc} Notice the precise geometry, acoustics, and craftsmanship that modern architects "
                         f"still study with reverence.")
            practical = f"Recommended visiting window: {best_time}. Remember to tread respectfully."

        speech_text = f"{intro} {lore} {deep_dive}"
        return {
            "site_id": site_id,
            "name": name,
            "hindi_name": hindi_name,
            "language": lang,
            "title": title,
            "ai_powered": False,
            "story_chapters": [
                {"heading": "ऐतिहासिक संदर्भ" if lang == "hi" else "Historical Context", "content": intro},
                {"heading": "अनकही लोक-कथा व रहस्य" if lang == "hi" else "Folklore & Mysteries", "content": lore},
                {"heading": "वास्तुकला का चमत्कार" if lang == "hi" else "Architectural Marvel", "content": deep_dive},
                {"heading": "यात्री परामर्श" if lang == "hi" else "Traveler Advisory", "content": practical}
            ],
            "speech_narration": speech_text
        }

    def _try_gemini_story(self, site: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
        """Generate a rich story using Gemini API. Returns None if unavailable."""
        name       = site.get("name", "")
        hindi_name = site.get("hindi_name", name)
        period     = site.get("period", "")
        secret     = site.get("folklore_secret", "")
        desc       = site.get("description", "")
        state      = site.get("state", "India")
        best_time  = site.get("best_time_to_visit", "October to March")

        if lang == "hi":
            prompt = (
                f"तुम एक प्रसिद्ध भारतीय लोककथा वाचक हो। नीचे दिए गए विरासत स्थल के बारे में "
                f"हिंदी में एक मनमोहक, जीवंत कहानी लिखो जो किसी पर्यटक को सुनाई जाए।\n\n"
                f"स्थल: {hindi_name} ({name})\nराज्य: {state}\nकाल: {period}\n"
                f"विवरण: {desc}\nलोककथा / रहस्य: {secret}\nसर्वोत्तम यात्रा समय: {best_time}\n\n"
                f"कहानी को 4 भागों में बाँटो (हर भाग को --- से अलग करो):\n"
                f"1. ऐतिहासिक संदर्भ (2-3 वाक्य)\n"
                f"2. लोक-कथा व रहस्य (2-3 वाक्य)\n"
                f"3. वास्तुकला का चमत्कार (2-3 वाक्य)\n"
                f"4. यात्री परामर्श (1-2 वाक्य)\n"
                f"केवल कहानी लिखो, शीर्षक नहीं।"
            )
            headings = ["ऐतिहासिक संदर्भ", "अनकही लोक-कथा व रहस्य", "वास्तुकला का चमत्कार", "यात्री परामर्श"]
            title = f"रहस्य और गौरव: {hindi_name}"
        else:
            prompt = (
                f"You are a renowned Indian oral historian and storyteller. Write an evocative, "
                f"immersive story in English about the following heritage site for a curious traveler.\n\n"
                f"Site: {name}\nState: {state}\nPeriod: {period}\n"
                f"Description: {desc}\nFolklore/Mystery: {secret}\nBest time to visit: {best_time}\n\n"
                f"Divide the story into 4 parts separated by ---:\n"
                f"1. Historical Context (2-3 sentences)\n"
                f"2. Folklore & Mysteries (2-3 sentences)\n"
                f"3. Architectural Marvel (2-3 sentences)\n"
                f"4. Traveler Advisory (1-2 sentences)\n"
                f"Write only the story, no headings."
            )
            headings = ["Historical Context", "Folklore & Mysteries", "Architectural Marvel", "Traveler Advisory"]
            title = f"Secrets & Legend: {name}"

        raw = _call_gemini(prompt)
        if not raw:
            return None

        parts = [p.strip() for p in raw.split("---")]
        while len(parts) < 4:
            parts.append("")

        return {
            "site_id": site["id"],
            "name": name,
            "hindi_name": hindi_name,
            "language": lang,
            "title": title,
            "ai_powered": True,
            "story_chapters": [{"heading": headings[i], "content": parts[i]} for i in range(4)],
            "speech_narration": " ".join(parts[:3]),
        }

    def generate_festival_story(self, festival_id: str, lang: str = "hi") -> Dict[str, Any]:
        fest = next((f for f in cultural_engine.festivals if f["id"] == festival_id), None)
        if not fest:
            return {"error": "Festival not found"}

        name        = fest.get("name", "")
        hindi_name  = fest.get("hindi_name", name)
        significance = fest.get("cultural_significance", "")
        must_exp    = fest.get("must_experience", "")
        summary     = fest.get("summary", "")

        if lang == "hi":
            title = f"लोक-संस्कृति की अनमोल गूंज: {hindi_name}"
            intro = (f"धरोहर सेतु उत्सव रडार: आपके क्षेत्र में शीघ्र ही '{hindi_name}' का आयोजन होने जा रहा है! "
                     f"यह कोई साधारण मेला नहीं, बल्कि हमारी माटी की जीवित लोक-परम्परा है।")
            lore = f"इस पावन उत्सव का सांस्कृतिक महत्व: {significance}"
            experience = f"यदि आप यहाँ हैं, तो यह अनुभव बिल्कुल न चूकें: {must_exp}"
            speech_text = f"{intro} {summary} {lore} {experience}"
        else:
            title = f"Living Folk Heritage: {name}"
            intro = (f"DharoharSetu Utsav Radar: The micro-regional celebration of '{name}' is approaching "
                     f"in your vicinity! This is an authentic living tradition passed through generations.")
            lore = f"Cultural & Folk Significance: {significance}"
            experience = f"What you must experience firsthand: {must_exp}"
            speech_text = f"{intro} {summary} {lore} {experience}"

        return {
            "festival_id": festival_id,
            "name": name,
            "hindi_name": hindi_name,
            "language": lang,
            "title": title,
            "summary": summary,
            "cultural_significance": significance,
            "must_experience": must_exp,
            "speech_narration": speech_text,
        }


ai_storyteller = AIStoryteller()
