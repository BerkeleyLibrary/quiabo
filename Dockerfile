FROM python:3.14-slim AS reqs

ENV APP_USER=quiabo
ENV APP_UID=40098
ENV VIRTUAL_ENV=/venv

RUN apt-get update -y && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libxml2-dev \
        python3-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/

RUN groupadd --system --gid $APP_UID $APP_USER \
    && useradd --home-dir /app --system --uid $APP_UID --gid $APP_USER $APP_USER

RUN mkdir -p /app && mkdir -p /venv

RUN chown -R $APP_USER:$APP_USER /app /venv

USER $APP_USER

RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN python -m pip install -U setuptools

WORKDIR /app

COPY pyproject.toml .

FROM reqs AS app

WORKDIR /app
USER $APP_USER

COPY quiabo quiabo
COPY bin bin
COPY README.md README.md
COPY test test
RUN pip install --no-cache-dir -e . 

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0", "quiabo:app"]

FROM app AS worker

USER root

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-spa \
        tesseract-ocr-deu \
        tesseract-ocr-chi-tra \
        tesseract-ocr-ita \
        tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

USER $APP_USER
