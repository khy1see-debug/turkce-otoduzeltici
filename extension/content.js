// Türkçe Otomatik Düzeltici - Content Script
// Sayfadaki metin kutularında veya seçili metinlerde yerinde düzeltme yapar.

function showToast(message, isSuccess = true) {
  let toast = document.getElementById("turkce-duzelt-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "turkce-duzelt-toast";
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      padding: 12px 20px;
      border-radius: 8px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 13px;
      font-weight: 600;
      box-shadow: 0 10px 25px rgba(0,0,0,0.3);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      display: flex;
      align-items: center;
      gap: 8px;
    `;
    document.body.appendChild(toast);
  }

  toast.style.backgroundColor = isSuccess ? "#0f172a" : "#7f1d1d";
  toast.style.color = isSuccess ? "#38bdf8" : "#fca5a5";
  toast.style.border = isSuccess ? "1px solid #1e293b" : "1px solid #991b1b";
  toast.innerHTML = isSuccess ? `✨ ${message}` : `⚠️ ${message}`;
  toast.style.opacity = "1";
  toast.style.transform = "translateY(0)";

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
  }, 2500);
}

async function correctSelectedOrActiveText() {
  const activeEl = document.activeElement;
  let targetText = "";
  let isInput = false;

  if (activeEl && (activeEl.tagName === "TEXTAREA" || (activeEl.tagName === "INPUT" && activeEl.type === "text"))) {
    isInput = true;
    const start = activeEl.selectionStart;
    const end = activeEl.selectionEnd;
    targetText = start !== end ? activeEl.value.substring(start, end) : activeEl.value;
  } else {
    targetText = window.getSelection().toString();
  }

  if (!targetText.trim()) {
    showToast("Düzeltilecek metin seçilmedi.", false);
    return;
  }

  try {
    const res = await fetch("http://127.0.0.1:8765/api/correct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: targetText, mode: "fix" })
    });

    if (!res.ok) throw new Error("API hatası");
    const data = await res.json();
    const corrected = data.corrected;

    if (isInput && activeEl) {
      const start = activeEl.selectionStart;
      const end = activeEl.selectionEnd;
      if (start !== end) {
        activeEl.setRangeText(corrected, start, end, "end");
      } else {
        activeEl.value = corrected;
      }
      activeEl.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
      document.execCommand("insertText", false, corrected);
    }

    showToast("Türkçe İmla Başarıyla Düzeltildi!", true);
  } catch (err) {
    showToast("Yerel Stüdyo kapalı! (turkce-otoduzeltici'yi başlatın)", false);
  }
}

// Background script mesajını dinle
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "CORRECT_SELECTION") {
    correctSelectedOrActiveText();
  }
});

// Sayfa içi kısayol: Alt+Shift+Q
document.addEventListener("keydown", (e) => {
  if (e.altKey && e.shiftKey && (e.key === "Q" || e.key === "q")) {
    e.preventDefault();
    correctSelectedOrActiveText();
  }
});
