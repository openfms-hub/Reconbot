"""Configuration loader — reads settings.yaml and company_profile.yaml."""

from __future__ import annotations

import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

import yaml


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = _PROJECT_ROOT / "config"


def _resolve_env_vars(value: str) -> str:
    """Replace ${VAR} patterns with environment variable values."""
    def _replacer(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, "")
    return re.sub(r"\$\{(\w+)\}", _replacer, value)


def _walk_resolve(obj: Any) -> Any:
    """Recursively resolve environment variables in a config dict."""
    if isinstance(obj, str):
        return _resolve_env_vars(obj)
    if isinstance(obj, dict):
        return {k: _walk_resolve(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_resolve(item) for item in obj]
    return obj


@dataclass
class LLMConfig:
    default_model: str = "openai/qwen-max"
    temperature: float = 0.3
    max_tokens: int = 8192
    providers: dict[str, dict[str, str]] = field(default_factory=dict)

    def get_provider_for_model(self, model: str) -> dict[str, str]:
        """Return api_key and api_base for a given model name."""
        model_lower = model.lower()
        if "qwen" in model_lower:
            return self.providers.get("dashscope", {})
        if "moonshot" in model_lower or "kimi" in model_lower:
            return self.providers.get("moonshot", {})
        if "deepseek" in model_lower:
            return self.providers.get("deepseek", {})
        return self.providers.get("dashscope", {})


@dataclass
class CollectorConfig:
    enabled: bool = True
    api_key: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputConfig:
    dir: str = "./reports"
    language: str = "zh"
    template: str = "default"


@dataclass
class Settings:
    llm: LLMConfig
    collectors: dict[str, CollectorConfig]
    output: OutputConfig


@dataclass
class CompanyProfile:
    name: str = ""
    website: str = ""
    industry: str = ""
    target_market: str = ""
    team_size: int = 0
    annual_target: str = ""
    products: list[dict[str, str]] = field(default_factory=list)
    platform: dict[str, Any] = field(default_factory=dict)
    advantages: list[str] = field(default_factory=list)
    pricing_model: str = ""
    partnership_preferences: list[dict[str, str]] = field(default_factory=list)


def load_settings(config_dir: Path | None = None) -> Settings:
    """Load settings.yaml and return a Settings object."""
    config_dir = config_dir or _CONFIG_DIR
    settings_path = config_dir / "settings.yaml"

    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")

    with open(settings_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    raw = _walk_resolve(raw)

    llm_raw = raw.get("llm", {})
    llm = LLMConfig(
        default_model=llm_raw.get("default_model", "openai/qwen-max"),
        temperature=llm_raw.get("temperature", 0.3),
        max_tokens=llm_raw.get("max_tokens", 8192),
        providers=llm_raw.get("providers", {}),
    )

    collectors: dict[str, CollectorConfig] = {}
    for name, cfg in raw.get("collectors", {}).items():
        collectors[name] = CollectorConfig(
            enabled=cfg.get("enabled", True),
            api_key=cfg.get("api_key", ""),
            extra={k: v for k, v in cfg.items() if k not in ("enabled", "api_key")},
        )

    output_raw = raw.get("output", {})
    output = OutputConfig(
        dir=output_raw.get("dir", "./reports"),
        language=output_raw.get("language", "zh"),
        template=output_raw.get("template", "default"),
    )

    return Settings(llm=llm, collectors=collectors, output=output)


def load_company_profile(config_dir: Path | None = None) -> CompanyProfile:
    """Load company_profile.yaml and return a CompanyProfile object."""
    config_dir = config_dir or _CONFIG_DIR
    profile_path = config_dir / "company_profile.yaml"

    if not profile_path.exists():
        raise FileNotFoundError(f"Company profile not found: {profile_path}")

    with open(profile_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    company = raw.get("company", {})
    return CompanyProfile(
        name=company.get("name", ""),
        website=company.get("website", ""),
        industry=company.get("industry", ""),
        target_market=company.get("target_market", ""),
        team_size=company.get("team_size", 0),
        annual_target=company.get("annual_target", ""),
        products=company.get("products", []),
        platform=company.get("platform", {}),
        advantages=company.get("advantages", []),
        pricing_model=company.get("pricing_model", ""),
        partnership_preferences=company.get("partnership_preferences", []),
    )
