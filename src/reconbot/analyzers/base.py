"""Base LLM caller — wraps LiteLLM for unified model access."""

from __future__ import annotations

import litellm

from reconbot.config import LLMConfig


def _build_model_name(model: str, provider: dict) -> str:
    """Build the LiteLLM model string with a valid provider prefix.

    LiteLLM requires a known provider prefix (e.g. 'openai/', 'deepseek/').
    For custom OpenAI-compatible endpoints, use 'openai/' prefix —
    LiteLLM will route through the OpenAI provider with a custom api_base.
    """
    bare_model = model.split("/", 1)[1] if "/" in model else model
    api_base = provider.get("api_base", "")

    # If we have a custom api_base (not a well-known provider),
    # use openai/ prefix so LiteLLM routes correctly
    if api_base:
        return f"openai/{bare_model}"
    return bare_model


async def llm_complete(
    llm_config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    """Call LLM and return the response text."""
    model = model or llm_config.default_model
    provider = llm_config.get_provider_for_model(model)

    lite_model = _build_model_name(model, provider)

    response = await litellm.acompletion(
        model=lite_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=llm_config.temperature,
        max_tokens=llm_config.max_tokens,
        api_key=provider.get("api_key", ""),
        api_base=provider.get("api_base", ""),
        timeout=300,
    )
    return response.choices[0].message.content or ""
