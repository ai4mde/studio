import os

# M06 Model Routing & Abstraction. Mirrors Studio's llm/handler.py defaults.
MODEL_PROFILES = {
    "cheap":  {"provider": "groq",   "model": "llama-3.3-70b-versatile"},
    "strong": {"provider": "openai", "model": "gpt-4o"},
}


def _fake_content(model_profile):
    return '{"late_risk": "LOW", "reason": "fake deterministic response"}'


def _call_groq(model, prompt):
    from groq import Groq

    client = Groq()
    resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content


def _call_openai(model, prompt):
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content


def call_model(model_profile, prompt):
    spec = MODEL_PROFILES[model_profile]
    provider, model = spec["provider"], spec["model"]
    if os.environ.get("AI_RUNTIME_FAKE") == "1":
        return {"mode": "fake", "provider": provider, "model": model, "content": _fake_content(model_profile)}
    if provider == "groq":
        content = _call_groq(model, prompt)
    elif provider == "openai":
        content = _call_openai(model, prompt)
    else:
        raise ValueError(f"unknown provider for profile {model_profile!r}: {provider!r}")
    return {"mode": "real", "provider": provider, "model": model, "content": content}