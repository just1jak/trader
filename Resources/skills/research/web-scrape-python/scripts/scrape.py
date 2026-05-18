import sys, json, urllib.parse, urllib.request, re, html

def duckduckgo_search(query, max_results=5):
    encoded = urllib.parse.quote_plus(query)
    url = f"https://duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; HermesAgent/1.0)"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        html_content = resp.read().decode('utf-8', errors='ignore')
    # Find result links
    links = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"', html_content):
        raw_href = urllib.parse.unquote(m.group(1))
        # Extract the real URL from DuckDuckGo redirect parameter 'uddg' if present
        try:
            parsed = urllib.parse.urlparse(raw_href)
            query = urllib.parse.parse_qs(parsed.query)
            if 'uddg' in query:
                real = query['uddg'][0]
                real = urllib.parse.unquote(real)
            else:
                real = raw_href
        except Exception:
            real = raw_href
        # Ensure the URL has a scheme
        if real.startswith('//'):
            real = 'https:' + real
        elif not real.startswith('http'):
            real = 'https://' + real
        links.append(real)
        if len(links) >= max_results:
            break
    return links

def fetch_and_clean(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; HermesAgent/1.0)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode('utf-8', errors='ignore')
        # Remove scripts/styles
        raw = re.sub(r"<script.*?</script>", "", raw, flags=re.DOTALL|re.IGNORECASE)
        raw = re.sub(r"<style.*?</style>", "", raw, flags=re.DOTALL|re.IGNORECASE)
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", " ", raw)
        # Unescape entities
        text = html.unescape(text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1000]  # limit snippet size
    except Exception as e:
        return f"[Error fetching {url}: {e}]"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No query provided"}))
        sys.exit(1)
    query = ' '.join(sys.argv[1:])
    urls = duckduckgo_search(query)
    results = []
    for u in urls:
        snippet = fetch_and_clean(u)
        results.append({"url": u, "snippet": snippet})
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
