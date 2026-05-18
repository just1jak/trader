---
name: web-scrape-python
description: "Python script to perform DuckDuckGo search and scrape top result pages. Use when you need programmatic web data without browser tooling."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, web, scraping, python]
    related_skills: [web-scrape]
---
# Web Scrape Python Skill

## Purpose
Fetch search results from DuckDuckGo and scrape the first few pages for plain‑text content. Designed for quick data gathering when no API is available.

## Usage
1. Call the bundled script `scripts/scrape.py` with a query string.
2. The script returns JSON with each URL and a cleaned text snippet.
3. Optionally pipe the output to a file for further processing.

## Example
```bash
python scripts/scrape.py "example query" > results.json
```

## Limitations
- Limited to 5 pages by default.
- May be blocked by sites with bot protection.
- Relies on DuckDuckGo HTML layout; may need updates if changed.

## Files
- `scripts/scrape.py` – core implementation.
