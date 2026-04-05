"""Exa search collector — company background, industry context, and deep intelligence."""

from __future__ import annotations

from exa_py import Exa

from .base import BaseCollector, CollectorResult, TargetCompany


class ExaCollector(BaseCollector):
    name = "exa"

    def __init__(self, api_key: str, num_results: int = 10):
        self.api_key = api_key
        self.num_results = num_results

    async def collect(self, target: TargetCompany) -> CollectorResult:
        if not self.api_key:
            return CollectorResult(
                source=self.name, success=False, error="Exa API key not configured"
            )

        try:
            exa = Exa(api_key=self.api_key)
            raw_texts: list[str] = []
            urls: list[str] = []

            # Query 1: core company search
            query1 = f"{target.name}"
            if target.city:
                query1 += f" {target.city}"
            if target.country:
                query1 += f" {target.country}"

            results1 = exa.search_and_contents(
                query1,
                type="auto",
                num_results=self.num_results,
                text={"max_characters": 3000},
                summary=True,
            )
            for r in results1.results:
                chunk = f"=== EXA RESULT: {r.title} ({r.url}) ===\n"
                if r.summary:
                    chunk += f"Summary: {r.summary}\n"
                if r.text:
                    chunk += r.text[:3000]
                raw_texts.append(chunk)
                urls.append(r.url)

            # Query 2: technology stack & platform (e.g. Wialon, CMSV6)
            query2 = f"{target.name} platform technology software"
            if target.website:
                domain = target.website.replace("https://", "").replace("http://", "").rstrip("/")
                query2 += f" site:{domain}"

            results2 = exa.search_and_contents(
                query2,
                type="auto",
                num_results=5,
                text={"max_characters": 2000},
                summary=True,
            )
            for r in results2.results:
                if r.url not in urls:
                    chunk = f"=== EXA RESULT: {r.title} ({r.url}) ===\n"
                    if r.summary:
                        chunk += f"Summary: {r.summary}\n"
                    if r.text:
                        chunk += r.text[:2000]
                    raw_texts.append(chunk)
                    urls.append(r.url)

            # Query 3: legal entity & corporate info
            query3 = f"{target.name} empresa sociedad S.A. de C.V. RFC"
            if target.country:
                query3 += f" {target.country}"

            results3 = exa.search_and_contents(
                query3,
                type="auto",
                num_results=5,
                text={"max_characters": 2000},
                summary=True,
            )
            for r in results3.results:
                if r.url not in urls:
                    chunk = f"=== EXA RESULT: {r.title} ({r.url}) ===\n"
                    if r.summary:
                        chunk += f"Summary: {r.summary}\n"
                    if r.text:
                        chunk += r.text[:2000]
                    raw_texts.append(chunk)
                    urls.append(r.url)

            return CollectorResult(
                source=self.name, success=True, raw_texts=raw_texts, urls=urls
            )
        except Exception as e:
            return CollectorResult(
                source=self.name, success=False, error=str(e)
            )
