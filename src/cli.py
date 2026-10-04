#!/usr/bin/env python3
"""
Çevrimdışı Türkçe Otomatik Düzeltici CLI Arayüzü (0 Token).
Kullanım:
  python3 -m src.cli "sendemigeliyorusn"
  python3 -m src.cli --interactive
"""

import sys
import argparse
from src.grammar import fix_sentence

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

    args = parser.parse_args()

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
