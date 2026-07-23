# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder

ARG PDM_VERSION=2.27.0
ENV PDM_CHECK_UPDATE=false \
    PDM_IGNORE_SAVED_PYTHON=1 \
    PDM_VENV_IN_PROJECT=1
WORKDIR /app

RUN pip install --no-cache-dir "pdm==${PDM_VERSION}"

COPY pyproject.toml pdm.lock README.md ./
RUN pdm install --prod --no-editable --frozen-lockfile


FROM python:${PYTHON_VERSION}-slim AS runtime

ENV INKCRE_ENV_FILE="" \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN groupadd --gid 10001 inkcre \
    && useradd --uid 10001 --gid inkcre --create-home inkcre

COPY --from=builder --chown=inkcre:inkcre /app/.venv /app/.venv
COPY --chown=inkcre:inkcre app/ app/
COPY --chown=inkcre:inkcre data/ai/prompts/ data/ai/prompts/
COPY --chown=inkcre:inkcre extensions/ extensions/
COPY --chown=inkcre:inkcre libs/ libs/
COPY --chown=inkcre:inkcre migrations/ migrations/
COPY --chown=inkcre:inkcre scripts/ scripts/
COPY --chown=inkcre:inkcre utils/ utils/
COPY --chown=inkcre:inkcre \
    alembic.ini \
    pdm.lock \
    pyproject.toml \
    run.py \
    ./

RUN install -d -o inkcre -g inkcre /app/data/extensions/twitter

USER inkcre

EXPOSE 8000
ENTRYPOINT ["python", "scripts/container.py"]


FROM runtime AS heroku-runtime

USER root

RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

USER inkcre

ENTRYPOINT []


FROM heroku-runtime AS heroku-release

CMD ["python", "scripts/container.py", "migrate"]


FROM heroku-runtime AS heroku-web

CMD ["python", "scripts/container.py", "web"]


FROM runtime AS artifact

CMD ["web"]
