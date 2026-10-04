# Agent Guidelines & Context Contract

## Project Overview
- Purpose: Workspace repository for active development.
- Target Environment: Linux (x86_64).

## Architecture & Layout
- Root: Contains project source code, configuration manifests, and documentation.
- Configurations: Follow standard project conventions per ecosystem.

## Key Rules for AI Agents (Space Bunny Protocol)
1. **Symbol Targeting:** Inspect specific functions, classes, or code blocks rather than reading entire files when making edits.
2. **Lazy Exploration:** Inspect only files directly relevant to the current objective. Avoid crawling unrelated modules.
3. **Minimal Footprint:** Choose solutions that modify the minimum necessary lines and files. Avoid unnecessary refactors.
4. **Bounded Output:** Keep answers concise, factual, and actionable. Provide focused diffs and verify test results.
5. **Security & Secrets:** Never commit API keys, tokens, or credential files. Maintain sensitive values in local environment variables.
