import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name != "posix", reason="Wayland shortcut script is POSIX-only")
def test_shortcut_replaces_selection_and_preserves_internal_spaces(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    shortcut = project_root / "desktop-shortcut.sh"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    clipboard = tmp_path / "clipboard"
    primary = tmp_path / "primary"
    selected = tmp_path / "selected"
    document = tmp_path / "document"
    selected.write_text("yanlış   yazım\n", encoding="utf-8")
    document.write_text("önce yanlış   yazım\n sonra", encoding="utf-8")

    stubs = {
        "wl-copy": """#!/bin/bash
if [ "$1" = "--primary" ]; then cat > "$TEST_PRIMARY"; else cat > "$TEST_CLIPBOARD"; fi
""",
        "wl-paste": """#!/bin/bash
if [ "$1" = "--primary" ]; then cat "$TEST_PRIMARY"; else cat "$TEST_CLIPBOARD"; fi
""",
        "ydotool": """#!/bin/bash
case "$*" in
  *46:1*) cat "$TEST_SELECTED" > "$TEST_CLIPBOARD"; cat "$TEST_SELECTED" > "$TEST_PRIMARY" ;;
  *47:1*) /usr/bin/python3 - "$TEST_DOCUMENT" "$TEST_SELECTED" "$TEST_CLIPBOARD" <<'PY'
import pathlib, sys
doc, old, new = (pathlib.Path(p) for p in sys.argv[1:])
text = doc.read_text(encoding="utf-8")
text = text.replace(old.read_text(encoding="utf-8"), new.read_text(encoding="utf-8"), 1)
doc.write_text(text, encoding="utf-8")
PY
  ;;
esac
""",
        "notify-send": "#!/bin/bash\nexit 0\n",
        "paplay": "#!/bin/bash\nexit 0\n",
    }
    for name, body in stubs.items():
        tool = bin_dir / name
        tool.write_text(body, encoding="utf-8")
        tool.chmod(0o755)

    corrector = bin_dir / "turkce-duzelt-fast"
    corrector.write_text("#!/bin/bash\nprintf '<%s>\\n' \"$1\"\n", encoding="utf-8")
    corrector.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env.get('PATH', '')}",
            "TEST_CLIPBOARD": str(clipboard),
            "TEST_PRIMARY": str(primary),
            "TEST_SELECTED": str(selected),
            "TEST_DOCUMENT": str(document),
        }
    )
    subprocess.run(["bash", str(shortcut)], env=env, check=True, timeout=10)

    assert document.read_text(encoding="utf-8") == "önce <yanlış   yazım\n>\n sonra"
