from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests


DEFAULT_REGISTRY_PATH = Path("config/llm/model_hub.json")
ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


class MultiModelRouter:
    def __init__(
        self,
        registry_path: str | Path = DEFAULT_REGISTRY_PATH,
        *,
        agent_id: str = "theme_candidate_mapper",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.registry_path = Path(registry_path)
        self.agent_id = agent_id
        self.timeout_seconds = timeout_seconds
        self.registry = self._load_registry(self.registry_path)
        self.enabled = bool(self.registry.get("enabled", True))
        self.agent_model = self._resolve_agent_model()

    @property
    def available(self) -> bool:
        if not self.enabled or not self.agent_model:
            return False
        config = self._resolve_model(self.agent_model)
        return bool(config and config.get("api_key"))

    def structured_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        fallback_models: list[str] | None = None,
        temperature: float = 0.1,
    ) -> dict[str, Any] | None:
        candidates = [self.agent_model, *(fallback_models or [])]
        for model_ref in candidates:
            if not model_ref:
                continue
            config = self._resolve_model(model_ref)
            if not config or not config.get("api_key"):
                continue
            try:
                payload = self._invoke_provider(
                    config,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                )
            except requests.RequestException:
                continue
            parsed = _extract_json_payload(payload)
            if parsed is not None:
                return parsed
        return None

    def text_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        fallback_models: list[str] | None = None,
        temperature: float = 0.2,
    ) -> str:
        candidates = [self.agent_model, *(fallback_models or [])]
        for model_ref in candidates:
            if not model_ref:
                continue
            config = self._resolve_model(model_ref)
            if not config or not config.get("api_key"):
                continue
            try:
                payload = self._invoke_provider(
                    config,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                )
            except requests.RequestException:
                continue
            text = str(payload or "").strip()
            if text:
                return text
        return ""

    def _resolve_agent_model(self) -> str | None:
        defaults = self.registry.get("agents", {}).get("defaults", {})
        default_model = defaults.get("model", {}).get("primary")
        for item in self.registry.get("agents", {}).get("list", []):
            if item.get("id") == self.agent_id:
                return str(item.get("model") or default_model or "").strip() or None
        return str(default_model or "").strip() or None

    def _resolve_model(self, model_ref: str) -> dict[str, Any] | None:
        provider_name, _, model_id = model_ref.partition("/")
        providers = self.registry.get("models", {}).get("providers", {})
        provider = providers.get(provider_name, {})
        for item in provider.get("models", []):
            if item.get("id") == model_id:
                return {
                    "provider_name": provider_name,
                    "base_url": str(provider.get("baseUrl", "")).rstrip("/"),
                    "api_key": str(provider.get("apiKey", "")).strip(),
                    "api_type": str(provider.get("api", "")).strip(),
                    "model_id": model_id,
                    "max_tokens": int(item.get("maxTokens", 2048) or 2048),
                }
        return None

    def _invoke_provider(
        self,
        config: dict[str, Any],
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> str:
        if config["api_type"] == "openai-completions":
            return self._invoke_openai_compatible(config, system_prompt, user_prompt, temperature)
        if config["api_type"] == "anthropic-messages":
            return self._invoke_anthropic_compatible(config, system_prompt, user_prompt, temperature)
        raise requests.RequestException(f"unsupported api type: {config['api_type']}")

    def _invoke_openai_compatible(
        self,
        config: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> str:
        response = requests.post(
            f"{config['base_url']}/chat/completions",
            headers={
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json",
            },
            json={
                "model": config["model_id"],
                "temperature": temperature,
                "max_tokens": config["max_tokens"],
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        message = ((payload.get("choices") or [{}])[0]).get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
        return str(content)

    def _invoke_anthropic_compatible(
        self,
        config: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> str:
        response = requests.post(
            f"{config['base_url']}/messages",
            headers={
                "x-api-key": config["api_key"],
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": config["model_id"],
                "temperature": temperature,
                "max_tokens": config["max_tokens"],
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("content", [])
        if isinstance(content, list):
            return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
        return str(content)

    @staticmethod
    def _load_registry(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        raw = json.loads(path.read_text(encoding="utf-8"))
        return _resolve_env_placeholders(raw)


def _resolve_env_placeholders(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _resolve_env_placeholders(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_env_placeholders(item) for item in value]
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    return value


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        payload = json.loads(cleaned)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
