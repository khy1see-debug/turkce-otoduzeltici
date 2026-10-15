// Türkçe Otomatik Düzeltici - Popup Script
const API_BASE = "http://127.0.0.1:8765";

const statusBadge = document.getElementById("statusBadge");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const inputText = document.getElementById("inputText");
const modeSelect = document.getElementById("modeSelect");
const correctBtn = document.getElementById("correctBtn");
const outputText = document.getElementById("outputText");
const copyBtn = document.getElementById("copyBtn");

// 1. Motorun çalışıp çalışmadığını kontrol et
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { method: "GET" });
    if (res.ok) {
      statusBadge.className = "status-badge status-online";
      statusDot.className = "dot dot-online";
      statusText.innerText = "Yerel Motor Aktif";
      return true;
    }
  } catch (e) {
    // offline
  }
  statusBadge.className = "status-badge status-offline";
  statusDot.className = "dot dot-offline";
  statusText.innerText = "Motor Kapalı (Başlatın)";
  return false;
}

// 2. Metni Düzelt
async function correct() {
  const text = inputText.value.trim();
  if (!text) return;

  const mode = modeSelect.value;
  outputText.style.color = "#94a3b8";
  outputText.innerText = "Düzeltiliyor...";
  copyBtn.style.display = "none";

  try {
    const res = await fetch(`${API_BASE}/api/correct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, mode })
    });

    if (!res.ok) throw new Error("Sunucu yanıt vermedi");
    const data = await res.json();
    outputText.style.color = "#38bdf8";
    outputText.innerText = data.corrected;
    copyBtn.style.display = "block";
  } catch (err) {
    outputText.style.color = "#f87171";
    outputText.innerText = "Hata: Yerel Stüdyo kapalı! Masaüstü uygulamasını veya 'python -m src.cli --web' komutunu başlatın.";
  }
}

// 3. Panoya Kopyala
copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(outputText.innerText);
  copyBtn.innerText = "Kopyalandı!";
  setTimeout(() => { copyBtn.innerText = "Kopyala"; }, 1500);
});

// Event Listener'lar
correctBtn.addEventListener("click", correct);

inputText.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") {
    correct();
  }
});

// Başlangıçta sağlık kontrolü yap
checkHealth();
