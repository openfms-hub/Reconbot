"""Base LLM caller — wraps LiteLLM for unified model access."""

from __future__ import annotations

import litellm

from reconbot.config import LLMConfig


async def llm_complete(
    llm_config: LLMConfig,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    """Call LLM and return the response text."""
    model = model or llm_config.default_model
    provider = llm_config.get_provider_for_model(model)

    response = await litellm.acompletion(
        model=model,
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
