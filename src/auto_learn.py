"""
Hata Analizi, Devrik Cümle İncelemesi ve Otomatik Öğrenme Modülü.
Kullanıcı düzeltme veritabanını (self_learning.db) ve uygulama loglarını (app.log)
analiz ederek sık tekrarlanan kelimeleri kişisel sözlüğe ekler, hataları raporlar.
"""

import os
import sys
import re
import sqlite3
import logging
from pathlib import Path
from collections import Counter
from typing import Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.turkish_case import turkish_lower
from src.dictionary import is_valid_word, add_personal_word, list_personal_words

logger = logging.getLogger("auto_learn")

def get_appdata_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        p = Path(appdata) / "turkce-otoduzeltici"
    else:
        p = Path.home() / ".config" / "turkce-otoduzeltici"
    p.mkdir(parents=True, exist_ok=True)
    return p

def analyze_logs(log_path: Path) -> Dict[str, Any]:
    """app.log dosyasını analiz eder ve hata türlerini gruplar."""
    res = {
        "exists": log_path.exists(),
        "total_lines": 0,
        "errors": Counter(),
        "recent_errors": []
    }
    if not log_path.exists():
        return res

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]
        res["total_lines"] = len(lines)
        
        for line in lines:
            if "KRİTİK HATA" in line or "Traceback" in line or "SyntaxError" in line:
                res["errors"]["Syntax/Kritik"] += 1
                res["recent_errors"].append(line)
            elif "API Çağrı Hatası" in line or "timed out" in line or "503" in line:
                if "Gemini" in line:
                    res["errors"]["Gemini API Timeout/Error"] += 1
                elif "NVIDIA" in line:
                    res["errors"]["NVIDIA API Timeout/Error"] += 1
                else:
                    res["errors"]["Genel API Hatası"] += 1
            elif "HATA" in line.upper() or "ERROR" in line.upper():
                res["errors"]["Diğer Hatalar"] += 1
                
        # Son 5 kritik hatayı tut
        res["recent_errors"] = res["recent_errors"][-5:]
    except Exception as e:
        res["read_error"] = str(e)

    return res

def analyze_corrections(db_path: Path) -> Dict[str, Any]:
    """self_learning.db içerisindeki correction_events ve word_learning tablolarını analiz eder."""
    res = {
        "exists": db_path.exists(),
        "total_corrections": 0,
        "learned_words_promoted": [],
        "frequent_user_words": [],
        "sample_devrik_or_conversational": []
    }
    if not db_path.exists():
        return res

    try:
        conn = sqlite3.connect(str(db_path), timeout=10.0)
        cursor = conn.cursor()

        # Toplam düzeltme sayısı
        cursor.execute("SELECT COUNT(*) FROM correction_events")
        res["total_corrections"] = cursor.fetchone()[0]

        # Son düzeltmeler ve devrik/günlük konuşma örnekleri
        cursor.execute("SELECT original_text, corrected_text FROM correction_events ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        
        token_counter = Counter()
        devrik_samples = []

        for orig, corr in rows:
            orig = orig.strip()
            corr = corr.strip()
            # Devrik ya da samimi/günlük konuşma tespiti (soru veya devrik yüklem)
            words = orig.split()
            if len(words) >= 3:
                # Cümlenin yapısını incele
                devrik_samples.append((orig, corr))

            # Düzeltilmiş metinde korunan özel kelimeleri topla (kesme işaretli ekleri ayıklayarak)
            clean_tokens = re.findall(r"[a-zA-ZçÇğĞıİöÖşŞüÜ]+(?:['’][a-zA-ZçÇğĞıİöÖşŞüÜ]+)?", corr)
            for t in clean_tokens:
                stem = re.split(r"['’]", t)[0]
                low = turkish_lower(stem)
                if len(low) >= 3 and not is_valid_word(low):
                    token_counter[low] += 1

        # En sık kullanılan ve henüz ana sözlükte olmayan özel kelimeler
        from src.slang import ALL_EXPANSIONS
        candidates = []
        for word, count in token_counter.most_common(20):
            if word in ALL_EXPANSIONS or word in {"den", "dan", "ten", "tan", "nin", "nın", "şuan"}:
                continue
            candidates.append({"word": word, "frequency": count})
            # 3 ve üzeri kez kabul edilmiş özel kelimeyse kişisel sözlüğe dahil et
            if count >= 3:
                try:
                    if add_personal_word(word):
                        res["learned_words_promoted"].append(word)
                except Exception:
                    pass

        res["frequent_user_words"] = candidates
        res["sample_devrik_or_conversational"] = devrik_samples[:10]
        conn.close()
    except Exception as e:
        res["db_error"] = str(e)

    return res

def run_learning_cycle() -> Dict[str, Any]:
    """Tam öğrenme ve audit döngüsünü çalıştırır."""
    data_dir = get_appdata_dir()
    log_path = data_dir / "app.log"
    db_path = data_dir / "self_learning.db"

    # Bekleyen kabul ve öğrenme döngüsünü tetikle
    try:
        from src.self_learning import get_self_learning_manager
        mgr = get_self_learning_manager()
        mgr.process_pending_now()
        frequent_phrases = mgr.get_frequent_phrases(min_count=1)
    except Exception:
        frequent_phrases = []

    log_report = analyze_logs(log_path)
    db_report = analyze_corrections(db_path)
    personal_words = list_personal_words()

    return {
        "log_analysis": log_report,
        "database_analysis": db_report,
        "frequent_phrases": frequent_phrases[:12],
        "total_personal_words": len(personal_words),
        "personal_words_sample": personal_words[-15:] if personal_words else []
    }

def print_report():
    report = run_learning_cycle()
    print("=" * 60)
    print(" TÜRKÇE OTO-DÜZELTİCİ: PERİYODİK ÖĞRENME VE HATA ANALİZİ")
    print("=" * 60)
    
    logs = report["log_analysis"]
    print("\n[1] LOG ANALİZİ (app.log)")
    print(f"  Toplam Log Satırı: {logs.get('total_lines', 0)}")
    if logs.get("errors"):
        print("  Hata Dağılımı:")
        for err, cnt in logs["errors"].items():
            print(f"    - {err}: {cnt} kez")
    else:
        print("  Kritik hata tespit edilmedi (Tüm servisler sağlıklı).")

    db = report["database_analysis"]
    print("\n[2] KULLANICI DÜZELTME & ÖĞRENME VERİTABANI (self_learning.db)")
    print(f"  Kayıtlı Düzeltme Olayı: {db.get('total_corrections', 0)}")
    
    if db.get("learned_words_promoted"):
        print(f"  Sözlüğe Yeni Eklenen Kelimeler: {', '.join(db['learned_words_promoted'])}")
    else:
        print("  Bu turda eşiği aşan yeni aday kelime yok (Mevcut kelimeler korundu).")

    if db.get("frequent_user_words"):
        print("  Kullanıcının Sık Kullandığı Özel/Argo Adaylar:")
        for cand in db["frequent_user_words"][:8]:
            print(f"    - '{cand['word']}': {cand['frequency']} kez görüldü")

    if db.get("sample_devrik_or_conversational"):
        print("\n[3] İNCELENEN DEVRİK VE GÜNLÜK CÜMLELERDEN ÖRNEKLER:")
        for orig, corr in db["sample_devrik_or_conversational"][:5]:
            print(f"    * Girdi : \"{orig}\"")
            print(f"      Sonuç : \"{corr}\"")

    if report.get("frequent_phrases"):
        print("\n[4] ÖĞRENİLEN VE TEKRARLANAN CÜMLE KALIPLARI (N-Gram Tamlamalar):")
        for phr, cnt in report["frequent_phrases"][:6]:
            print(f"    - \"{phr}\" ({cnt} kez)")

    print("\n[5] KİŞİSEL SÖZLÜK DURUMU")
    print(f"  Toplam Kişisel Kelime: {report['total_personal_words']}")
    if report["personal_words_sample"]:
        print(f"  Son Eklenenler: {', '.join(report['personal_words_sample'])}")
    print("=" * 60)

if __name__ == "__main__":
    print_report()
