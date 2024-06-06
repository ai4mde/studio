FROM python:3.8.18 AS venv

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # pip:
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry:
    POETRY_VERSION=1.7.1 \
    POETRY_VIRTUALENVS_IN_PROJECT="true" \
    POETRY_NO_INTERACTION=1 \
    PATH="$PATH:/root/.local/bin"

RUN pip install pipx
RUN pipx install "poetry==$POETRY_VERSION"
RUN pipx ensurepath

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-root --no-interaction --no-ansi

FROM python:3.8.18
WORKDIR /usr/src/app

COPY --from=venv /.venv /usr/src/.venv

ENV PATH="/usr/src/.venv/bin:$PATH"

RUN python -c "import nltk; nltk.download('punkt')"
RUN python -c "import nltk; nltk.download('wordnet')"

COPY src /usr/src/app/src

CMD ["python3", "-m", "uvicorn", "--host", "0.0.0.0", "--port", "8000", "--reload", "src.main:app"]
