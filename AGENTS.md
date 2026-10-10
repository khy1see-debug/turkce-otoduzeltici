# Agent Guidelines & Context Contract

## Project Overview
- Purpose: Offline Turkish spelling, word segmentation, and sentence correction CLI/library.
- Target Environment: Linux (x86_64).

## Key Entry Points
- CLI: `src/cli.py` (`python3 -m src.cli` or installed `turkce-duzelt` command).
- Repeated desktop corrections: `src/daemon.py` keeps the dictionary loaded in a user service; `src/daemon_client.py` is the hotkey client.
- Main correction pipeline: `src/grammar.py` and its focused modules (`speller.py`, `segmenter.py`, `deasciifier.py`, `syntax.py`, `slang.py`).
- Dictionary loading and local user dictionary: `src/dictionary.py`.
- Optional local GGUF inference: `src/ai_engine.py`; it is not part of the default CLI path.
- Project metadata and install command: `pyproject.toml`.

## Useful Commands
- Install as a user command: `uv tool install .`.
- Correct one phrase: `python3 -m src.cli "sendemigeliyorusn"`.
- Interactive CLI: `python3 -m src.cli --interactive`.
- Test suite command documented by the project: `PYTHONPATH=. pytest tests/`.

## Context Selection
- Read the README and `pyproject.toml` for user-facing behavior and packaging; inspect only the modules directly involved in a task.
- Keep the default corrector offline and API-free. Do not make optional AI code part of the default path without an explicit requirement.
- Preserve Turkish characters and UTF-8 text handling; keep personal dictionary data local.
- Treat `data/turkish_words.txt.gz` as runtime source data, not a disposable build artifact.

## Architecture & Layout
- Root: Contains project source code, configuration manifests, and documentation.
- Configurations: Follow standard project conventions per ecosystem.

## Key Rules for AI Agents (Space Bunny Protocol)
1. **Symbol Targeting:** Inspect specific functions, classes, or code blocks rather than reading entire files when making edits.
2. **Lazy Exploration:** Inspect only files directly relevant to the current objective. Avoid crawling unrelated modules.
3. **Minimal Footprint:** Choose solutions that modify the minimum necessary lines and files. Avoid unnecessary refactors.
4. **Bounded Output:** Keep answers concise, factual, and actionable. Provide focused diffs and verify test results.
5. **Security & Secrets:** Never commit API keys, tokens, or credential files. Maintain sensitive values in local environment variables.
