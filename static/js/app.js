// ========================================================
// DharoharSetu - Clean, Simple & Fast Client Application
// ========================================================

const appState = {
  lat: 32.5625,
  lng: 75.1200,
  stateName: "Jammu and Kashmir",
  mode: "nearby", // "nearby" or "state"
  lang: "hi",     // "hi" or "en"
  map: null,
  userMarker: null,
  markersLayer: null,
  sites: [],
  festivals: [],
  activeSite: null,
  isPlayingAudio: false
};

const STATE_BOUNDS = {
  "Jammu and Kashmir": { bounds: [[32.2, 74.0], [34.5, 76.5]], center: [32.9, 75.1], zoom: 9 },
  "Bihar": { bounds: [[24.3, 83.3], [27.5, 88.3]], center: [25.6, 85.5], zoom: 8 }
};

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  setupStateDropdown();
  detectLocation();
});

function initMap() {
  appState.map = L.map("map", { zoomControl: false }).setView([appState.lat, appState.lng], 10);
  L.control.zoom({ position: "bottomright" }).addTo(appState.map);

  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; CARTO | DharoharSetu',
    maxZoom: 19
  }).addTo(appState.map);

  appState.markersLayer = L.layerGroup().addTo(appState.map);
}

function setupStateDropdown() {
  const select = document.getElementById("state-select");
  if (select) {
    select.addEventListener("change", (e) => {
      appState.stateName = e.target.value;
      const info = STATE_BOUNDS[appState.stateName];
      if (info) {
        appState.lat = info.center[0];
        appState.lng = info.center[1];
      }
      setMode("state");
    });
  }
}

// Auto Detect Location (GPS with IP Fallback)
async function detectLocation() {
  const btn = document.getElementById("btn-gps");
  if (btn) btn.innerHTML = "⏳ Detecting...";

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        appState.lat = pos.coords.latitude;
        appState.lng = pos.coords.longitude;
        if (btn) btn.innerHTML = "📍 GPS Active";
        finishLocationDetect();
      },
      () => fallbackIPLocation(btn),
      { timeout: 3000 }
    );
  } else {
    fallbackIPLocation(btn);
  }
}

async function fallbackIPLocation(btn) {
  try {
    const res = await fetch("/api/location/auto-ip");
    const data = await res.json();
    if (data.latitude && data.longitude) {
      appState.lat = data.latitude;
      appState.lng = data.longitude;
      appState.stateName = data.state;
      syncStateDropdown(data.state);
    }
  } catch (e) {
    console.warn("IP detect fallback used default coords");
  }
  if (btn) btn.innerHTML = "📍 Located";
  finishLocationDetect();
}

function syncStateDropdown(stateName) {
  const select = document.getElementById("state-select");
  if (select) {
    for (let opt of select.options) {
      if (stateName.toLowerCase().includes(opt.value.toLowerCase()) || opt.value.toLowerCase().includes(stateName.toLowerCase())) {
        select.value = opt.value;
        appState.stateName = opt.value;
        break;
      }
    }
  }
}

async function finishLocationDetect() {
  updateUserMarker();
  await loadData();
}

function updateUserMarker() {
  if (appState.userMarker) {
    appState.map.removeLayer(appState.userMarker);
  }
  const icon = L.divIcon({
    className: "custom-user-marker",
    html: `<div class="custom-pin pin-user"><span>📍</span></div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36]
  });
  appState.userMarker = L.marker([appState.lat, appState.lng], { icon })
    .addTo(appState.map)
    .bindPopup("<b>Aapka Sthaan</b>");
}

// Mode Switching (Nearby 100km vs Entire State)
function setMode(mode) {
  appState.mode = mode;
  document.getElementById("btn-mode-nearby").classList.toggle("active-mode", mode === "nearby");
  document.getElementById("btn-mode-state").classList.toggle("active-mode", mode === "state");

  if (mode === "state") {
    const info = STATE_BOUNDS[appState.stateName];
    if (info) {
      appState.map.fitBounds(info.bounds, { padding: [30, 30], duration: 1.2 });
    }
  } else {
    appState.map.flyTo([appState.lat, appState.lng], 10, { duration: 1.2 });
  }

  loadData();
}

// Load Sites and Festivals
async function loadData() {
  try {
    // 1. Fetch Sites
    const res = await fetch(`/api/sites?lat=${appState.lat}&lng=${appState.lng}&mode=${appState.mode}&state=${encodeURIComponent(appState.stateName)}`);
    const data = await res.json();
    appState.sites = data.sites;
    renderSitesOnMap(appState.sites);

    // 2. Fetch Festivals
    const festRes = await fetch(`/api/festivals?state=${encodeURIComponent(appState.stateName)}`);
    const festData = await festRes.json();
    appState.festivals = festData.festivals;
    document.getElementById("badge-fest-count").textContent = appState.festivals.length;

  } catch (err) {
    console.error("Error loading data:", err);
  }
}

// Render Sites on Map
function renderSitesOnMap(sites) {
  appState.markersLayer.clearLayers();

  sites.forEach(site => {
    const icon = L.divIcon({
      className: "custom-monument-marker",
      html: `<div class="custom-pin pin-monument"><span>🏛️</span></div>`,
      iconSize: [36, 36],
      iconAnchor: [18, 36]
    });

    const marker = L.marker([site.lat, site.lng], { icon })
      .bindTooltip(`<b>${site.name}</b><br><small>${site.district} (${site.distance_km} km)</small>`, { direction: "top" });

    marker.on("click", () => {
      showPlaceCard(site);
    });

    appState.markersLayer.addLayer(marker);
  });
}

// Show Bottom Place Card
function showPlaceCard(site) {
  appState.activeSite = site;
  stopVoiceNarration();

  const card = document.getElementById("place-card");
  document.getElementById("card-img").src = site.image_url;
  document.getElementById("card-name").textContent = site.name;
  document.getElementById("card-hindi").textContent = site.hindi_name;
  document.getElementById("card-category").textContent = `${site.district} • ${site.category}`;
  document.getElementById("card-distance").textContent = `${site.distance_km} km`;
  document.getElementById("card-desc").textContent = `${site.description} Rahasya: ${site.folklore_secret}`;
  document.getElementById("card-directions").href = `https://www.google.com/maps/dir/?api=1&destination=${site.lat},${site.lng}`;

  card.classList.remove("hidden");
}

function closePlaceCard() {
  document.getElementById("place-card").classList.add("hidden");
  stopVoiceNarration();
}

// AI Voice Narration (Web Speech API)
function playVoiceNarration() {
  if (appState.isPlayingAudio) {
    stopVoiceNarration();
    return;
  }
  if (!appState.activeSite) return;

  const site = appState.activeSite;
  const speechText = appState.lang === "hi"
    ? `नमस्कार! आप ${site.hindi_name} के बारे में सुन रहे हैं। ${site.description} यहाँ की एक प्राचीन लोक-कथा है कि ${site.folklore_secret}`
    : `Greetings! You are exploring ${site.name}. ${site.description} Local folklore whispers that ${site.folklore_secret}`;

  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.lang = appState.lang === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;

    utterance.onstart = () => {
      appState.isPlayingAudio = true;
      document.getElementById("voice-icon").textContent = "⏸️";
      document.getElementById("voice-text").textContent = "Audio Pause Karein";
    };
    utterance.onend = () => stopVoiceNarration();
    utterance.onerror = () => stopVoiceNarration();

    window.speechSynthesis.speak(utterance);
  }
}

function stopVoiceNarration() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  appState.isPlayingAudio = false;
  const icon = document.getElementById("voice-icon");
  const text = document.getElementById("voice-text");
  if (icon) icon.textContent = "▶️";
  if (text) text.textContent = "AI Lok-Katha Suniye (Audio)";
}

// Festivals Modal
function openFestivalsModal() {
  const modal = document.getElementById("festivals-modal");
  const list = document.getElementById("festivals-list");
  document.getElementById("fest-modal-title").textContent = `${appState.stateName} Ke Sabhi Pramukh Lok-Utsav`;

  list.innerHTML = appState.festivals.map(f => `
    <div class="p-4 bg-amber-50/80 rounded-xl border border-amber-300 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 rounded bg-amber-200 text-amber-900 text-[10px] font-bold uppercase tracking-wider">
            📍 ${f.district} (${f.season_month})
          </span>
          <span class="text-xs font-bold text-amber-800">
            🗓️ ${f.traditional_timing}
          </span>
        </div>
        <h4 class="text-base font-bold text-stone-900 mt-1 font-royal">
          ${f.name} <span class="font-hindi text-sm font-normal text-amber-900">(${f.hindi_name})</span>
        </h4>
        <p class="text-xs text-stone-700 mt-1 leading-relaxed">
          ${f.cultural_significance}
        </p>
        <p class="text-[11px] text-amber-900 font-semibold mt-1">
          ✦ <b>Kya Dekhein / Khayein:</b> ${f.must_experience}
        </p>
      </div>
      <a href="https://www.google.com/maps/dir/?api=1&destination=${f.lat},${f.lng}" target="_blank" class="px-3 py-1.5 bg-amber-700 hover:bg-amber-800 text-white text-xs font-semibold rounded-lg shrink-0">
        Directions ➔
      </a>
    </div>
  `).join("");

  modal.classList.remove("hidden");
}

function closeFestivalsModal() {
  document.getElementById("festivals-modal").classList.add("hidden");
}

function toggleLanguage() {
  appState.lang = appState.lang === "hi" ? "en" : "hi";
  document.getElementById("btn-lang").textContent = appState.lang === "hi" ? "हिन्दी / ENG" : "ENG / हिन्दी";
}
