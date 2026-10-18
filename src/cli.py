#!/usr/bin/env python3
"""
Çevrimdışı Türkçe Otomatik Düzeltici CLI & GUI Başlatıcı (0-Token).
Kullanım:
  python3 -m src.cli "sendemigeliyorusn"
  python3 -m src.cli --gui
  python3 -m src.cli --interactive
  python3 -m src.cli --deasciify "ogrenci"
  python3 -m src.cli --asciify "şampiyon"
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="0-Token Çevrimdışı Türkçe Otomatik Düzeltici ve Stüdyo"
    )
    parser.add_argument(
        "text",
        nargs="?",
        type=str,
        help="Düzeltilecek veya çevrilecek ham metin (örn: 'sendemigeliyorusn')"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="İnteraktif canlı terminal modu"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Gelişmiş grafiksel stüdyo arayüzünü (GUI) aç"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Tarayıcı tabanlı modern Web Stüdyosunu ve REST API'yi aç"
    )
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Sistem tepsisi (system tray) arka plan servisini başlat (Alt+Q kısayolu)"
    )
    parser.add_argument(
        "--deasciify",
        action="store_true",
        help="Sadece ASCII harfleri Türkçe karakterlere dönüştür"
    )
    parser.add_argument(
        "--asciify",
        action="store_true",
        help="Türkçe karakterleri ASCII harflere dönüştür"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Yapay zeka (NVIDIA NIM / LLM) motorunu kullanarak düzelt"
    )

    dictionary_actions = parser.add_mutually_exclusive_group()
    dictionary_actions.add_argument(
        "--add-word", metavar="KELİME", help="Kelimeyi kişisel sözlüğe ekle"
    )
    dictionary_actions.add_argument(
        "--remove-word", metavar="KELİME", help="Kelimeyi kişisel sözlükten kaldır"
    )
    dictionary_actions.add_argument(
        "--list-words", action="store_true", help="Kişisel sözlükteki kelimeleri göster"
    )

    args = parser.parse_args()

    # Web Stüdyosu Modu
    if args.web:
        from src.web import run_web_studio
        run_web_studio()
        return 0

    # GUI Modu
    if args.gui:
        from src.main_window import main as gui_main
        gui_main()
        return 0

    # Tray Modu
    if args.tray:
        from src.app_tray import main as tray_main
        tray_main()
        return 0

    # Sözlük İşlemleri
    if args.add_word or args.remove_word or args.list_words:
        from src.dictionary import (
            add_personal_word,
            list_personal_words,
            remove_personal_word,
        )

        if args.add_word:
            try:
                changed = add_personal_word(args.add_word)
            except ValueError as exc:
                parser.error(str(exc))
            print("Kelime sözlüğe eklendi." if changed else "Kelime zaten sözlükte.")
        elif args.remove_word:
            changed = remove_personal_word(args.remove_word)
            print("Kelime sözlükten kaldırıldı." if changed else "Kelime sözlükte yok.")
        else:
            print("\n".join(list_personal_words()))
        return 0

    # Deasciify / Asciify
    if args.deasciify:
        from src.deasciifier import deasciify_text
        if args.text:
            print(deasciify_text(args.text))
        else:
            print("Lütfen dönüştürülecek bir metin girin.")
        return 0

    if args.asciify:
        from src.deasciifier import asciify_text
        if args.text:
            print(asciify_text(args.text))
        else:
            print("Lütfen dönüştürülecek bir metin girin.")
        return 0

    # Yapay Zeka ile Düzeltme Modu
    if args.ai:
        from src.ai_engine import NetworkError, PolicyError, fix_with_ai
        from src.grammar import fix_sentence
        target_text = args.text or "sendemigeliyorusn"
        try:
            ai_res = fix_with_ai(target_text)
            if ai_res:
                print(ai_res)
            else:
                print(fix_sentence(target_text))
        except PolicyError as exc:
            print(f"[!] {exc}", file=sys.stderr)
            print(fix_sentence(target_text))
        except NetworkError as exc:
            print(f"[!] AI hizmetine bağlanılamadı: {exc}", file=sys.stderr)
            print(fix_sentence(target_text))
        return 0

    # Genel Metin Düzeltme
    from src.grammar import fix_sentence

    if args.interactive or not args.text:
        print("=" * 60)
        print("🇹🇷 Çevrimdışı Türkçe Otomatik Düzeltici (0-Token)")
        print("Grafiksel arayüz için: python -m src.cli --gui")
        print("Çıkmak için 'q' veya Ctrl+C tuşlayabilirsiniz.")
        print("=" * 60)
        try:
            while True:
                user_input = input("\nYazınız > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("q", "exit", "quit"):
                    print("Görüşmek üzere!")
                    break
                fixed = fix_sentence(user_input)
                print(f"Düzeltildi: ✨ \033[1;32m{fixed}\033[0m")
        except (KeyboardInterrupt, EOFError):
            print("\nÇıkış yapıldı.")
            sys.exit(0)
    else:
        fixed = fix_sentence(args.text)
        print(fixed)

    return 0


if __name__ == "__main__":
    sys.exit(main())
