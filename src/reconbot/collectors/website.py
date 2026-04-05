"""Website collector — deep crawls the target company's website."""

from __future__ import annotations

import asyncio
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .base import BaseCollector, CollectorResult, TargetCompany

# High-value subpage path keywords — prioritize these over random links
_PRIORITY_PATHS = (
    "about", "acerca", "nosotros", "empresa", "company",
    "servic", "product", "solucion", "solution",
    "contact", "precio", "price", "plan",
    "platform", "plataforma", "tecnolog", "tech",
    "partner", "client", "caso", "case",
    "login", "acceso", "portal",
)


class WebsiteCollector(BaseCollector):
    name = "website"

    def __init__(self, timeout: int = 30, max_pages: int = 10):
        self.timeout = timeout
        self.max_pages = max_pages

    async def collect(self, target: TargetCompany) -> CollectorResult:
        if not target.website:
            return CollectorResult(
                source=self.name, success=False, error="No website URL provided"
            )

        base_url = target.website
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        visited: set[str] = set()
        raw_texts: list[str] = []
        urls: list[str] = []

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ReconBot/1.0)"},
            ) as client:
                sub_links = await self._fetch_page(
                    client, base_url, visited, raw_texts, urls
                )

                # Prioritize high-value subpages
                prioritized = sorted(
                    sub_links,
                    key=lambda u: any(kw in u.lower() for kw in _PRIORITY_PATHS),
                    reverse=True,
                )

                tasks = []
                for link in prioritized[: self.max_pages - 1]:
                    tasks.append(
                        self._fetch_page(client, link, visited, raw_texts, urls)
                    )
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    # Crawl second-level links from priority pages
                    second_level: list[str] = []
                    for r in results:
                        if isinstance(r, list):
                            second_level.extend(r)

                    remaining_budget = self.max_pages - len(visited)
                    if remaining_budget > 0 and second_level:
                        second_prioritized = sorted(
                            second_level,
                            key=lambda u: any(kw in u.lower() for kw in _PRIORITY_PATHS),
                            reverse=True,
                        )
                        extra_tasks = []
                        for link in second_prioritized[:remaining_budget]:
                            if link.rstrip("/") not in visited:
                                extra_tasks.append(
                                    self._fetch_page(client, link, visited, raw_texts, urls)
                                )
                        if extra_tasks:
                            await asyncio.gather(*extra_tasks, return_exceptions=True)

            return CollectorResult(
                source=self.name, success=True, raw_texts=raw_texts, urls=urls
            )
        except Exception as e:
            return CollectorResult(
                source=self.name, success=False, error=str(e)
            )

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        visited: set[str],
        raw_texts: list[str],
        urls: list[str],
    ) -> list[str]:
        """Fetch a single page, extract text and links. Returns discovered sub-links."""
        normalized = url.rstrip("/")
        if normalized in visited:
            return []
        visited.add(normalized)

        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception:
            return []

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Extract meta info (often contains platform clues)
        meta_info = ""
        for meta in soup.find_all("meta"):
            name = meta.get("name", "") or meta.get("property", "")
            content = meta.get("content", "")
            if name and content and len(content) > 10:
                meta_info += f"META[{name}]: {content}\n"

        text = soup.get_text(separator="\n", strip=True)
        if text:
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            page_text = f"=== PAGE: {title} ({url}) ===\n"
            if meta_info:
                page_text += meta_info
            page_text += text[:6000]
            raw_texts.append(page_text)
            urls.append(url)

        # Discover internal links (including subdomains of same root domain)
        base_domain = urlparse(url).netloc
        root_domain = ".".join(base_domain.split(".")[-2:])
        sub_links: list[str] = []
        seen_normalized: set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(url, href)
            parsed = urlparse(full_url)
            link_domain = parsed.netloc
            link_root = ".".join(link_domain.split(".")[-2:])
            norm = full_url.rstrip("/")

            if (
                link_root == root_domain
                and parsed.scheme in ("http", "https")
                and norm not in visited
                and norm not in seen_normalized
                and not any(ext in parsed.path.lower() for ext in (".pdf", ".jpg", ".png", ".zip", ".mp4"))
                and "#" not in parsed.path
            ):
                sub_links.append(full_url)
                seen_normalized.add(norm)

        return sub_links
