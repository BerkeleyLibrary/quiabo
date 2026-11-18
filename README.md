# ![quiabo logo](quiabo/static/quiabo.png) quiabo

`quiabo` is a backend web service for running OCR jobs implemented as a Flask and Celery application.

## Dependencies

Python dependencies are declared in `pyproject.toml`.

## Development

Spin up the application using Docker Compose. There are number of dependencies (Postgres and Redis) as well as Flask/Celery app components (`app`, `worker`, and optionially `flower`). Redis serves as the Celery broker (source of jobs) and Postgres is the Celery results backend.

In order to run Quiabo on the same system as [Mokelumne](https://github.com/BerkeleyLibrary/mokelumne) for development or integration testing, you need to symlink the `tmp` directory to Mokelumne's.  Otherwise, you will need to create an empty `tmp` directory before starting Quiabo.

```bash
# assuming mokelumne is installed in this project's parent...
ln -s ../mokelumne/tmp tmp

# or, if you do not have mokelumne installed locally, make an empty tmp directory:
# mkdir tmp

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

## Testing & Linting

Once the stack is started, execute the tests by running `pytest` in one
of the running containers. Note that testing and linting dependencies are
not installed by default, so you'll need to do that too.

```bash
# Install the testing and linting dependencies
docker compose exec app pip install --no-cache-dir -e '.[test,lint]'

# Run all the tests
docker compose exec app pytest

# Run tests with a specific marker
# Example: only run the unit tests
docker compose exec app pytest -m unit
```

Test results/reports are written to `./artifacts/pytest`.

```bash
# pylint
docker compose exec app python -m pylint --persistent=n quiabo test

# pydoclint
docker compose exec app pydoclint quiabo test

# mypy
docker compose exec app python -m mypy --explicit-package-bases quiabo test
```

## Configuration

`quiabo`'s configuration is handled by environment variables using Flask's
[`from_prefixed_env()`](https://flask.palletsprojects.com/en/stable/config/#configuring-from-environment-variables) method, using `QUIABO` as the
prefix. Celery configuration is set using the same method. At a minimum,
you will need to set the following:

| Environment variable | Purpose | Example |
| -------------------- | ------- | ------- |
| `QUIABO_CELERY__broker_url` | Connection URL for the Celery broker (e.g. Redis) | `redis://redis:6379` |
| `QUIABO_CELERY__result_backend` | SQLAlchemy connection URL for the Celery result backend (e.g. Postgres) | `db+postgresql://postgres:postgres@db:5432/quiabo` |

## Performance Logging

Quiabo creates JSON logs for OCR jobs, including performance metrics and error information. These logs can be collected by AWS CloudWatch to monitor OCR processing across multiple Celery workers.

Each completed OCR task creates an `ocr_job_finished` event with the following fields:

| Field | Description |
| --- | --- |
| `job_id` | Celery task ID |
| `correlation_id` | Optional identifier supplied by the calling application |
| `event` | Event name (`ocr_job_finished`) |
| `status` | Job outcome (`success` or `failure`) |
| `duration_seconds` | Total task execution time, including validation, OCR, and post-processing |
| `tesseract_seconds` | Time spent running Tesseract |
| `queue_wait_seconds` | Time between job submission and worker execution |
| `image_count` | Number of images in the input filelist |
| `languages` | OCR languages requested |
| `worker_hostname` | Celery worker hostname |
| `error_type` | Exception class name on failure; otherwise `null` |

The `queue_wait_seconds` metric is calculated using a UTC timestamp attached when the job is submitted. If the timestamp is missing or invalid, the metric is `null` and OCR processing continues normally.

Performance metrics are emitted for both successful and failed tasks. These structured events can be queried and aggregated in CloudWatch Logs Insights to analyze processing times, queue delays, worker activity, and failures.
