#!/usr/bin/env python3
"""
Çevrimdışı Türkçe Otomatik Düzeltici CLI Arayüzü (0 Token).
Kullanım:
  python3 -m src.cli "sendemigeliyorusn"
  python3 -m src.cli --interactive
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="0-Token Çevrimdışı Türkçe Otomatik Düzeltici (Bitişik kelimeleri ve imlayı düzeltir)"
    )
    parser.add_argument(
        "text",
        nargs="?",
        type=str,
        help="Düzeltilecek ham metin (örn: 'sendemigeliyorusn')"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="İnteraktif canlı terminal modu"
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

    # Import correction data only after parsing. This keeps --help and invalid
    # command-line invocations from decompressing/loading the large dictionary.
    from src.grammar import fix_sentence

    if args.interactive or not args.text:
        print("=" * 60)
        print("🇹🇷 Çevrimdışı Türkçe Otomatik Düzeltici (0-Token)")
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

if __name__ == "__main__":
    main()
