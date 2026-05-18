# Safe Web Search Implementation

## Overview
Implementing a safe web search involves filtering out harmful or inappropriate content (e.g., pornography, violence, hate speech) from search results. This can be achieved via API-level safe search flags, custom filtering, or using third‑party safety layers.

## General Strategies
1. **Use built‑in safe search flags** – many search APIs (Google, Bing, DuckDuckGo) offer a `safe` parameter.
2. **Post‑filter results** – run returned snippets/URLs through a content‑classification model or keyword blocklist.
3. **Combine approaches** – enable API safe‑search and run a secondary classifier for defense‑in‑depth.

## Implementation by Language

### Python (Google Custom Search JSON API)
```python
import requests
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")  # your custom search engine ID

def safe_google_search(query: str, num_results: int = 10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": num_results,
        "safe": "high",  # options: off, medium, high
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])
```

### JavaScript (Node.js) – Bing Search API
```javascript
const axios = require('axios');

async function safeBingSearch(query, count = 10) {
  const key = process.env.BING_SEARCH_KEY;
  const endpoint = "https://api.bing.microsoft.com/v7.0/search";
  
  const response = await axios.get(endpoint, {
    params: {
      q: query,
      count: count,
      safeSearch: 'Strict', // options: Off, Moderate, Strict
    },
    headers: { 'Ocp-Apim-Subscription-Key': key },
  });
  
  return response.data.webPages?.value || [];
}
```

### PHP – Using DuckDuckGo Instant Answer API (with safe search)
```php
function safeDuckDuckGoSearch($query) {
  $url = 'https://api.duckduckgo.com/';
  $params = [
    'q' => $query,
    'format' => 'json',
    'safe_search' => 'On', // options: Off, Moderate, On
  ];
  
  $ch = curl_init();
  curl_setopt($ch, CURLOPT_URL, $url . '?' . http_build_query($params));
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
  $result = curl_exec($ch);
  curl_close($ch);
  
  return json_decode($result, true);
}
```

## Defense‑in‑Depth Tips
1. **Enable API safe‑search** (`safe=high`, `strict`, etc.).
2. **Run a secondary classifier** (e.g., Perspective API, OpenAI moderation, or a lightweight NSFW model) on snippets before displaying.
3. **Block known bad domains** via a local deny‑list.
4. **Log and audit** queries that trigger filters for tuning.
5. **Rate‑limit** to avoid abuse of the safe‑search endpoint.

## Testing
- Verify with known adult keywords (e.g., "porn", "xxx") that results are filtered.
- Check benign queries (e.g., "cats", "news") still return expected results.
- Monitor false positives/negatives and adjust thresholds.

## References
- Google Custom Search JSON API: https://developers.google.com/custom-search/v1/overview
- Bing Search v7: https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/overview
- DuckDuckGo Instant Answer API: https://duckduckgo.com/api