import json
import os
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings

LOG_PATH = Path(settings.BASE_DIR) / "ai_invocations.jsonl"

# M06 Model Routing & Abstraction.
# model_profile -> (provider, concrete model). Mirrors Studio's llm/handler.py defaults.
MODEL_PROFILES = {
    "cheap":  {"provider": "groq",   "model": "llama-3.3-70b-versatile"},
    "strong": {"provider": "openai", "model": "gpt-4o"},
}


def _fake_content(model_profile):
    # Deterministic, no network. Step 6A proves routing without external dependencies.
    return '{"late_risk": "LOW", "reason": "fake deterministic response"}'


def _call_groq(model, prompt):
    from groq import Groq  # lazy: imported only on the real path

    client = Groq()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_openai(model, prompt):
    from openai import OpenAI  # lazy: imported only on the real path

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def call_model(model_profile, prompt):
    """Single routing entrypoint (M06). Returns a dict with the routing decision and the
    provider response content. The provider backend is selected by model_profile; the
    router itself is identical whether the backend is fake or real."""
    spec = MODEL_PROFILES[model_profile]
    provider, model = spec["provider"], spec["model"]
    if os.environ.get("AI_RUNTIME_FAKE") == "1":
        return {"mode": "fake", "provider": provider, "model": model,
                "content": _fake_content(model_profile)}
    if provider == "groq":
        content = _call_groq(model, prompt)
    elif provider == "openai":
        content = _call_openai(model, prompt)
    else:
        raise ValueError(f"unknown provider for profile {model_profile!r}: {provider!r}")
    return {"mode": "real", "provider": provider, "model": model, "content": content}


def _build_min_prompt(ai_config, instance):
    # Step 6 placeholder prompt. The real M01 template render (library_late_risk_v1)
    # arrives at Step 7; here we only need an input so the router can be exercised.
    return (
        f"Classify late risk as one of LOW, MEDIUM, HIGH for "
        f"{instance.__class__.__name__} pk={instance.pk}. Reply with a JSON object."
    )


def invoke(ai_config, instance):
    """Step 6 - M06 routing. Reads ai_config.model_profile, routes through call_model,
    logs the routing decision + response, and returns None (NO write-back yet; that is
    Step 7). The generated hook contract `from ai_runtime import invoke` is unchanged."""
    model_profile = ai_config.get("model_profile")
    prompt = _build_min_prompt(ai_config, instance)
    result = call_model(model_profile, prompt)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "invoke_routed",
        "model": instance.__class__.__name__,
        "pk": instance.pk,
        "model_profile": model_profile,
        "mode": result["mode"],
        "provider": result["provider"],
        "routed_model": result["model"],
        "write_back": ai_config.get("output", {}).get("write_back"),
        "ai_config_version": ai_config.get("ai_config_version"),
        "response_preview": (result.get("content") or "")[:200],
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return None  # Step 6: routing only, no parse/write-back