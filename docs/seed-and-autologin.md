# Seed & Auto-Login

This document explains how demo data seeding and automatic login work in Studio prototypes.

---

## Gemini API Key

The Gemini API key is required for two features:

- **UI candidate generation** — generating layout/component candidates from a UML diagram via LLM
- **Interface patch** — prompt-based edits to an existing interface ("make this a table", etc.)

### Setup

1. Copy `config/secrets.env.example` to `config/secrets.env` (never commit this file).
2. Set the key:

```env
# Use this for the UI candidate generation
GEMINI_API_KEY="your-key-here"
```

3. Restart the API container so the environment is picked up:

```bash
docker compose restart studio-api
```

### Where it is used

| Feature | File |
|---|---|
| LLM candidate generation | `api/model/llm/interface_generator/candidate_generation.py` |
| Prompt-based interface patch | `api/model/llm/interface_generator/django_service.py` |
| Generic LLM handler | `api/model/llm/handler.py` |

The code reads `GEMINI_API_KEY` (with `GOOGLE_API_KEY` as a fallback). If neither is set, candidate generation returns an error and the patch endpoint returns HTTP 400.

### Getting a key

Create a key at [Google AI Studio](https://aistudio.google.com/app/apikey). The free tier is sufficient for development. Use a project-scoped key, not a personal one.

---

## `seed_prototype.py`

`seed_prototype.py` is the script that populates a running prototype with demo data so it can be used without manual setup.

### When it runs

The Flask API (`prototypes/backend/api.py`) exposes a `/seed` endpoint. When "Seed" is clicked in the Studio UI, the endpoint calls:

```python
SEED_SCRIPT = '/usr/src/prototypes/backend/seed_prototype.py'
subprocess.run(['python', SEED_SCRIPT, ...])
```

### What it does

1. **Clears existing accounts** — deletes all non-superuser accounts:

```python
User.objects.filter(is_superuser=False).delete()
```

2. **Creates fresh demo users** — one user per actor role defined in the prototype (e.g. `demo-applicant`, `demo-loan-officer`). Each user gets password `demo1234`.

3. **Creates demo data** — seeds model instances so pages have something to display.

> Note: The superuser (admin) account is never deleted.

### Manual run

Inside the prototype container:

```bash
python /usr/src/prototypes/backend/seed_prototype.py
```

---

## Auto-Login

Auto-login lets you open a prototype page without going through the login form. It is injected into every generated prototype by `_patch_autologin` in `prototypes/backend/api.py`.

### How it works

`_patch_autologin` appends an `autologin` view to `authentication/views.py` and registers it at the URL `autologin/` in `authentication/urls.py`.

When the prototype opens, the Studio frontend navigates to:

```
/<role>/autologin?as=demo-<role>&next=/<role>/
```

The view logic:

1. Look up the user by the `as` username (e.g. `demo-applicant`).
2. If no user found but a role field can be inferred → create a minimal account on the fly (fallback, rare).
3. If still no user → take the first non-superuser in the database.
4. Call `django.contrib.auth.login(request, user)` — no password required.
5. Redirect to `next` or the role homepage.

### Normal flow

```
Seed runs → demo accounts created → auto-login finds the account → logs in instantly
```

No password prompt appears. The combination of Seed + Auto-login is what makes the "Open" button in Studio work without credentials.

### Updating a live prototype

If you re-generate or patch an interface, click **Sync Live** in the Studio UI to push the updated `views.py` and `urls.py` (including the auto-login injection) to the running prototype container.
