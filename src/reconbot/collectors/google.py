"""Google Custom Search collector — social media, supplementary data."""

from __future__ import annotations

import httpx

from .base import BaseCollector, CollectorResult, TargetCompany

_GOOGLE_API = "https://www.googleapis.com/customsearch/v1"


class GoogleCollector(BaseCollector):
    name = "google"

    def __init__(self, api_key: str, cx: str, num_results: int = 10):
        self.api_key = api_key
        self.cx = cx
        self.num_results = num_results

    async def collect(self, target: TargetCompany) -> CollectorResult:
        if not self.api_key or not self.cx:
            return CollectorResult(
                source=self.name,
                success=False,
                error="Google Search API key or CX not configured",
            )

        try:
            raw_texts: list[str] = []
            urls: list[str] = []

            queries = [
                f"{target.name} {target.country} {target.city}".strip(),
                f"{target.name} social media Facebook LinkedIn",
            ]

            async with httpx.AsyncClient(timeout=30) as client:
                for query in queries:
                    params = {
                        "key": self.api_key,
                        "cx": self.cx,
                        "q": query,
                        "num": min(self.num_results, 10),
                    }
                    resp = await client.get(_GOOGLE_API, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("items", []):
                        url = item.get("link", "")
                        if url in urls:
                            continue
                        chunk = (
                            f"=== GOOGLE: {item.get('title', '')} ({url}) ===\n"
                            f"{item.get('snippet', '')}"
                        )
                        raw_texts.append(chunk)
                        urls.append(url)

            return CollectorResult(
                source=self.name, success=True, raw_texts=raw_texts, urls=urls
            )
        except Exception as e:
            return CollectorResult(
                source=self.name, success=False, error=str(e)
            )
