// Türkçe Otomatik Düzeltici - Manifest V3 Background Service Worker
const API_URL = "http://127.0.0.1:8765/api/correct";

// Sağ tık bağlam menüsü oluştur
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "turkce-duzelt-secim",
    title: "🇹🇷 Türkçe İmla Düzelt",
    contexts: ["selection", "editable"]
  });
});

// Bağlam menüsü tıklandığında
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "turkce-duzelt-secim" && tab?.id) {
    chrome.tabs.sendMessage(tab.id, { action: "CORRECT_SELECTION" });
  }
});

// Content script veya popup'tan gelen API isteklerini yönlendir
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "CORRECT_TEXT") {
    fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: request.text, mode: "fix" })
    })
      .then(res => res.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(err => sendResponse({ success: false, error: err.message }));

    return true; // Asenkron yanıt için bekle
  }
});
