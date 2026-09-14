# ![quiabo logo](quiabo/static/quiabo.png) quiabo

`quiabo` is a backend web service for running OCR jobs implemented as a Flask and Celery application.

## Dependencies

Python dependencies are declared in `pyproject.toml`.

## Development

Spin up the application using Docker Compose. There are number of dependencies (Postgres and Redis) as well as Flask/Celery app components (`app`, `worker`, and optionially `flower`). Redis serves as the Celery broker (source of jobs) and Postgres is the Celery results backend.

```bash
# Build the Docker image for app, worker, and flower
docker compose build

# Create the postgres database; only needed the first time
docker compose run --rm app bin/dbinit

# Start the Flask app, which will be running on http://localhost:8000/
docker compose up --detach

# Optionally start Flower, which is a dashboard for the Celery queue and
# will be running on http://localhost:5555/
docker compose up --profile flower --detach
```

## Testing

Once the stack is started, execute the tests by running `pytest` in one
of the running containers. Note that testing and linting dependencies are
not installed by default, so you'll need to do that too.

```bash
# Install the testing and linting dependencies

docker compose exec app pip install --no-cache-dir -e .[test,lint]

# Run all the tests
docker compose exec app pytest

# Run tests with a specific marker
# Example: only run the unit tests
docker compose exec app pytest -m unit
```

Test results/reports are written to `./artifacts/pytest`.

## Configuration

`quiabo`'s configuration is handled by environment variables using Flask's
[`from_prefixed_env()`](https://flask.palletsprojects.com/en/stable/config/#configuring-from-environment-variables) method, using `QUIABO` as the
prefix. Celery configuration is set using the same method. At a minimum,
you will need to set the following:

| Environment variable | Purpose | Example |
| -------------------- | ------- | ------- |
| `QUIABO_CELERY__broker_url` | Connection URL for the Celery broker (e.g. Redis) | `redis://redis:6379` |
| `QUIABO_CELERY__result_backend` | SQLAlchemy connection URL for the Celery result backend (e.g. Postgres) | `db+postgresql://postgres:postgres@db:5432/quiabo` |
