"""Tavily search collector — social media, reviews, news, and supplementary data."""

from __future__ import annotations

from tavily import TavilyClient

from .base import BaseCollector, CollectorResult, TargetCompany


class TavilyCollector(BaseCollector):
    name = "tavily"

    def __init__(self, api_key: str, max_results: int = 10):
        self.api_key = api_key
        self.max_results = max_results

    async def collect(self, target: TargetCompany) -> CollectorResult:
        if not self.api_key:
            return CollectorResult(
                source=self.name, success=False, error="Tavily API key not configured"
            )

        try:
            client = TavilyClient(api_key=self.api_key)
            raw_texts: list[str] = []
            urls: list[str] = []

            # Query 1: company overview + services
            query1 = f"{target.name}"
            if target.country:
                query1 += f" {target.country}"
            if target.industry:
                query1 += f" {target.industry}"

            resp1 = client.search(
                query=query1,
                search_depth="advanced",
                max_results=self.max_results,
                include_raw_content=True,
            )
            for r in resp1.get("results", []):
                chunk = f"=== TAVILY: {r.get('title', '')} ({r.get('url', '')}) ===\n"
                content = r.get("raw_content") or r.get("content", "")
                chunk += content[:4000]
                raw_texts.append(chunk)
                urls.append(r.get("url", ""))

            # Query 2: social media presence
            query2 = f"{target.name} Facebook LinkedIn Instagram"
            if target.city:
                query2 += f" {target.city}"

            resp2 = client.search(
                query=query2,
                search_depth="basic",
                max_results=5,
            )
            for r in resp2.get("results", []):
                url = r.get("url", "")
                if url not in urls:
                    chunk = f"=== TAVILY: {r.get('title', '')} ({url}) ===\n"
                    chunk += r.get("content", "")[:2000]
                    raw_texts.append(chunk)
                    urls.append(url)

            # Query 3: reviews and reputation
            query3 = f"{target.name} reviews opiniones reseñas"
            if target.city:
                query3 += f" {target.city}"

            resp3 = client.search(
                query=query3,
                search_depth="basic",
                max_results=5,
            )
            for r in resp3.get("results", []):
                url = r.get("url", "")
                if url not in urls:
                    chunk = f"=== TAVILY: {r.get('title', '')} ({url}) ===\n"
                    chunk += r.get("content", "")[:2000]
                    raw_texts.append(chunk)
                    urls.append(url)

            return CollectorResult(
                source=self.name, success=True, raw_texts=raw_texts, urls=urls
            )
        except Exception as e:
            return CollectorResult(
                source=self.name, success=False, error=str(e)
            )
