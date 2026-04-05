"""Base class for all intelligence collectors."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TargetCompany:
    """Input data about the company to research."""
    name: str
    website: str = ""
    country: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    industry: str = ""


@dataclass
class CollectorResult:
    """Output from a single collector."""
    source: str                              # collector name (e.g. "website", "exa")
    success: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    raw_texts: list[str] = field(default_factory=list)  # raw text chunks for LLM
    urls: list[str] = field(default_factory=list)        # source URLs
    error: str = ""


class BaseCollector(abc.ABC):
    """Abstract base class for intelligence collectors."""

    name: str = "base"

    @abc.abstractmethod
    async def collect(self, target: TargetCompany) -> CollectorResult:
        """Collect intelligence about the target company."""
        ...
