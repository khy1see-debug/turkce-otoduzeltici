"""
0-Token Çevrimdışı Türkçe Otomatik Düzeltici - Web Stüdyosu ve REST API.
LanguageTool / DeepL standartlarında modern, etkileşimli tek sayfalık web arayüzü
ve harici uygulamalar için REST API uç noktaları sunar. Sıfır harici bağımlılık (Python standart kütüphanesi).
"""

import json
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from src.grammar import analyze_sentence
from src.deasciifier import deasciify_text, asciify_text
from src.turkish_case import turkish_lower, turkish_upper, turkish_capitalize

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Türkçe Otomatik Düzeltici — Web Stüdyosu (0-Token)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0f1d;
            --bg-secondary: #111827;
            --bg-card: #1f2937;
            --border-color: #374151;
            --accent-blue: #3b82f6;
            --accent-gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            --text-primary: #f9fafb;
            --text-secondary: #9ca3af;
            --success: #10b981;
            --danger: #ef4444;
            --radius: 12px;
        }

        [data-theme="light"] {
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-card: #f1f5f9;
            --border-color: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            transition: background-color 0.2s, border-color 0.2s;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background-color: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .badge-tr {
            background: var(--accent-gradient);
            color: white;
            font-weight: 800;
            font-size: 14px;
            padding: 6px 12px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        h1 {
            font-size: 18px;
            font-weight: 700;
            letter-spacing: -0.3px;
        }

        .tag-offline {
            background-color: rgba(16, 185, 129, 0.15);
            color: var(--success);
            font-size: 11px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 20px;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .theme-toggle-btn {
            background-color: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 8px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
        }

        main {
            flex: 1;
            max-width: 1300px;
            width: 100%;
            margin: 0 auto;
            padding: 24px 32px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .control-bar {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            padding: 12px 20px;
            border-radius: var(--radius);
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }

        .mode-selectors {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .mode-btn {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
        }

        .mode-btn.active {
            background: var(--accent-gradient);
            color: white;
            border-color: transparent;
        }

        .sample-select {
            background-color: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 13px;
            cursor: pointer;
            outline: none;
        }

        .live-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
        }

        .editor-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            min-height: 380px;
        }

        @media (max-width: 860px) {
            .editor-container {
                grid-template-columns: 1fr;
            }
        }

        .editor-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .editor-header {
            padding: 12px 18px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            font-weight: 600;
            background-color: rgba(255, 255, 255, 0.02);
        }

        .editor-textarea {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            padding: 18px;
            color: var(--text-primary);
            font-size: 15px;
            line-height: 1.6;
            resize: none;
            min-height: 280px;
        }

        .editor-output {
            flex: 1;
            padding: 18px;
            font-size: 15px;
            line-height: 1.6;
            overflow-y: auto;
            min-height: 280px;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .editor-footer {
            padding: 10px 18px;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--text-secondary);
            background-color: rgba(255, 255, 255, 0.02);
        }

        .btn-group {
            display: flex;
            gap: 8px;
        }

        .action-icon-btn {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
        }

        .action-icon-btn:hover {
            border-color: var(--accent-blue);
        }

        .main-action-btn {
            background: var(--accent-gradient);
            color: white;
            border: none;
            padding: 12px 32px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
        }

        .main-action-btn:hover {
            opacity: 0.95;
            transform: translateY(-1px);
        }

        /* TDK Kurallar ve Değişiklik Listesi */
        .changes-section {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 20px;
        }

        .changes-title {
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .changes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 12px;
        }

        .change-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .change-words {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }

        .word-orig {
            color: var(--danger);
            text-decoration: line-through;
            font-family: 'JetBrains Mono', monospace;
            background: rgba(239, 68, 68, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
        }

        .word-corr {
            color: var(--success);
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            background: rgba(16, 185, 129, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
        }

        .change-rule {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .empty-state {
            color: var(--text-secondary);
            font-size: 13px;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }
    </style>
</head>
<body data-theme="dark">
    <header>
        <div class="logo-group">
            <span class="badge-tr">TR</span>
            <h1>Türkçe Otomatik Düzeltici</h1>
            <span class="tag-offline">⚡ 0-Token Çevrimdışı</span>
        </div>
        <div class="header-actions">
            <button class="theme-toggle-btn" onclick="toggleTheme()">🌓 Tema Değiştir</button>
        </div>
    </header>

    <main>
        <div class="control-bar">
            <div class="mode-selectors">
                <button class="mode-btn active" onclick="setMode('full', this)">🤖 Otomatik Akıllı İmla</button>
                <button class="mode-btn" onclick="setMode('ai', this)">✨ NVIDIA AI (Llama 3.3 70B)</button>
                <button class="mode-btn" onclick="setMode('deasciify', this)">🔤 De-asciifier</button>
                <button class="mode-btn" onclick="setMode('asciify', this)">🌐 Asciifier</button>
                <button class="mode-btn" onclick="setMode('sentence_case', this)">🔠 Cümle Düzeni</button>
                <button class="mode-btn" onclick="setMode('uppercase', this)">TÜMÜ BÜYÜK</button>
                <button class="mode-btn" onclick="setMode('lowercase', this)">tümü küçük</button>
            </div>

            <div style="display:flex; align-items:center; gap: 12px;">
                <select class="sample-select" onchange="loadSample(this.value)">
                    <option value="">💡 Örnek Metin Seç...</option>
                    <option value="sendemigeliyorusn yarinaksam bulusalimmi">Bitişik ve Soru Eki</option>
                    <option value="ogrencileringozlerindensevincokunuyorducunkuokullaracildi">Uzun De-asciifier</option>
                    <option value="slm knk nbr bugun dcydemisin oyun alakmi">Chat Argosu & Kısaltmalar</option>
                    <option value="çoooook tesekkurler lütfeeeen geliyoruuuum">Harf Uzatmaları</option>
                    <option value="herkez birşey biliyo ama yanlız kaldım orjinal labaratuvar">TDK Yaygın Hataları</option>
                </select>

                <label class="live-toggle">
                    <input type="checkbox" id="liveToggle" onchange="toggleLiveMode()">
                    ⚡ Canlı Düzeltme
                </label>
            </div>
        </div>

        <div class="editor-container">
            <!-- Sol: Giriş -->
            <div class="editor-card">
                <div class="editor-header">
                    <span>Giriş Metni</span>
                    <div class="btn-group">
                        <button class="action-icon-btn" onclick="clearInput()">🗑️ Temizle</button>
                        <button class="action-icon-btn" onclick="pasteClipboard()">📋 Yapıştır</button>
                    </div>
                </div>
                <textarea id="inputText" class="editor-textarea" placeholder="Düzeltilecek veya çevrilecek Türkçe metni buraya yazın veya yapıştırın... (Örn: sendemigeliyorusn bugun hava cok guzel)" oninput="onInputChanged()"></textarea>
                <div class="editor-footer">
                    <span id="inputStats">0 karakter | 0 kelime</span>
                    <button class="main-action-btn" onclick="processText()">✨ Şimdi Düzelt</button>
                </div>
            </div>

            <!-- Sağ: Çıkış -->
            <div class="editor-card">
                <div class="editor-header">
                    <span>Düzeltilmiş Sonuç</span>
                    <div class="btn-group">
                        <button class="action-icon-btn" onclick="copyOutput(this)">📋 Kopyala</button>
                        <button class="action-icon-btn" onclick="downloadOutput()">💾 İndir (.txt)</button>
                    </div>
                </div>
                <div id="outputText" class="editor-output">Düzeltilmiş veya çevrilmiş sonuç burada görünecektir.</div>
                <div class="editor-footer">
                    <span id="outputStats">0 karakter | 0 kelime</span>
                    <span id="timeBadge" style="color: var(--success); font-weight:600;">⚡ 0 ms</span>
                </div>
            </div>
        </div>

        <!-- TDK Kural Açıklamaları -->
        <div class="changes-section">
            <div class="changes-title">
                <span>📚 TDK Kuralları ve Uygulanan Düzeltmeler</span>
                <span id="changesCountBadge" style="font-size:12px; background:var(--bg-card); padding:2px 8px; border-radius:12px;">0 kural</span>
            </div>
            <div id="changesGrid" class="changes-grid">
                <div class="empty-state">Henüz bir metin düzeltilmedi veya düzeltilecek hata bulunamadı.</div>
            </div>
        </div>
    </main>

    <script>
        let currentMode = 'full';
        let debounceTimer = null;

        function setMode(mode, element) {
            currentMode = mode;
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            element.classList.add('active');
            processText();
        }

        function toggleTheme() {
            const body = document.body;
            const newTheme = body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            body.setAttribute('data-theme', newTheme);
        }

        function clearInput() {
            document.getElementById('inputText').value = '';
            document.getElementById('outputText').innerText = 'Düzeltilmiş veya çevrilmiş sonuç burada görünecektir.';
            updateStats();
            renderChanges([]);
        }

        async function pasteClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('inputText').value = text;
                onInputChanged();
                processText();
            } catch (err) {
                alert('Pano izni verilmedi veya desteklenmiyor.');
            }
        }

        function copyOutput(btn) {
            const out = document.getElementById('outputText').innerText;
            if (out) {
                navigator.clipboard.writeText(out);
                const originalText = btn.innerText;
                btn.innerText = '✅ Kopyalandı!';
                setTimeout(() => btn.innerText = originalText, 1500);
            }
        }

        function downloadOutput() {
            const out = document.getElementById('outputText').innerText;
            if (!out) return;
            const blob = new Blob([out], { type: 'text/plain;charset=utf-8' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'duzeltilmis_metin.txt';
            a.click();
        }

        function loadSample(text) {
            if (!text) return;
            document.getElementById('inputText').value = text;
            onInputChanged();
            processText();
        }

        function toggleLiveMode() {
            if (document.getElementById('liveToggle').checked) {
                processText();
            }
        }

        function onInputChanged() {
            updateStats();
            if (document.getElementById('liveToggle').checked) {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(processText, 250);
            }
        }

        function updateStats() {
            const text = document.getElementById('inputText').value;
            const chars = text.length;
            const words = text.trim() ? text.trim().split(/\\s+/).length : 0;
            document.getElementById('inputStats').innerText = `${chars} karakter | ${words} kelime`;
        }

        async function processText() {
            const text = document.getElementById('inputText').value;
            if (!text.trim()) {
                document.getElementById('outputText').innerText = '';
                document.getElementById('outputStats').innerText = '0 karakter | 0 kelime';
                document.getElementById('timeBadge').innerText = '⚡ 0 ms';
                renderChanges([]);
                return;
            }

            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text, mode: currentMode })
                });
                const data = await response.json();
                if (data.ok) {
                    document.getElementById('outputText').innerText = data.result;
                    const chars = data.result.length;
                    const words = data.result.trim() ? data.result.trim().split(/\s+/).length : 0;
                    document.getElementById('outputStats').innerText = `${chars} karakter | ${words} kelime`;
                    document.getElementById('timeBadge').innerText = `⚡ ${data.stats ? data.stats.time_ms : 0} ms`;
                    renderChanges(data.changes || []);
                }
            } catch (err) {
                console.error(err);
            }
        }

        function renderChanges(changes) {
            const grid = document.getElementById('changesGrid');
            const badge = document.getElementById('changesCountBadge');
            badge.innerText = `${changes.length} kural`;

            if (!changes || changes.length === 0) {
                grid.innerHTML = '<div class="empty-state">Henüz bir metin düzeltilmedi veya düzeltilecek hata bulunamadı.</div>';
                return;
            }

            grid.innerHTML = changes.map(c => `
                <div class="change-card">
                    <div class="change-words">
                        <span class="word-orig">${escapeHtml(c.original)}</span>
                        <span>➜</span>
                        <span class="word-corr">${escapeHtml(c.corrected)}</span>
                    </div>
                    <div class="change-rule">${escapeHtml(c.rule)}</div>
                </div>
            `).join('');
        }

        function escapeHtml(str) {
            return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
    </script>
</body>
</html>
"""


class CorrectionApiHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "offline": True, "token_cost": 0}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode("utf-8"))
        except Exception:
            self._send_json({"ok": False, "error": "Geçersiz JSON"}, 400)
            return

        text = payload.get("text", "")
        mode = payload.get("mode", "full")

        if parsed.path == "/api/process" or parsed.path == "/api/correct":
            t0 = time.time()
            changes = []
            if mode == "ai":
                from src.ai_engine import fix_with_ai
                api_key = payload.get("api_key")
                ai_res = fix_with_ai(text, api_key=api_key)
                if ai_res:
                    result = ai_res
                else:
                    is_all_caps = text.isupper() and len([c for c in text if c.isalpha()]) > 2
                    analysis = analyze_sentence(text)
                    result = analysis["corrected"]
                    if is_all_caps:
                        result = turkish_upper(result)
                    changes = analysis["changes"]
            elif mode == "deasciify":
                result = deasciify_text(text)
            elif mode == "asciify":
                result = asciify_text(text)
            elif mode == "uppercase":
                result = turkish_upper(text)
            elif mode == "lowercase":
                result = turkish_lower(text)
            elif mode == "sentence_case":
                sentences = text.split(".")
                result = ". ".join(turkish_capitalize(s.strip()) for s in sentences if s.strip())
                if text.endswith("."):
                    result += "."
            else:
                is_all_caps = text.isupper() and len([c for c in text if c.isalpha()]) > 2
                analysis = analyze_sentence(text)
                result = analysis["corrected"]
                if is_all_caps:
                    result = turkish_upper(result)
                changes = analysis["changes"]

            elapsed_ms = round((time.time() - t0) * 1000, 2)
            self._send_json({
                "ok": True,
                "result": result,
                "corrected": result,
                "changes": changes,
                "stats": {
                    "char_count": len(result),
                    "word_count": len(result.split()),
                    "changes_count": len(changes),
                    "time_ms": elapsed_ms
                }
            })
        else:
            self._send_json({"ok": False, "error": "Bilinmeyen uç nokta"}, 404)

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        # Sessiz HTTP sunucusu
        pass


def run_web_studio(port: int = 8765, open_browser: bool = True):
    """Web Stüdyosunu başlatır ve varsayılan tarayıcıda açar."""
    server_address = ("127.0.0.1", port)
    try:
        httpd = HTTPServer(server_address, CorrectionApiHandler)
    except OSError:
        # Port meşgulse alternatif porta geç
        server_address = ("127.0.0.1", port + 1)
        httpd = HTTPServer(server_address, CorrectionApiHandler)
        port = port + 1

    url = f"http://127.0.0.1:{port}"
    print("=" * 65)
    print("🇹🇷 Türkçe Otomatik Düzeltici Web Stüdyosu Başlatıldı!")
    print(f"🌐 Adres: {url}")
    print("⚡ 0-Token & Tamamen Çevrimdışı (Offline)")
    print("Durdurmak için Ctrl+C tuşlayabilirsiniz.")
    print("=" * 65)

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        print("\nWeb stüdyosu kapatıldı.")
        httpd.server_close()


if __name__ == "__main__":
    run_web_studio()
