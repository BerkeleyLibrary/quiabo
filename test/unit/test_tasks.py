"""Unit tests for the shared task defined in ``tasks.py``."""

from unittest.mock import Mock

from quiabo.tasks import run_tesseract_job


def test_shared_task_is_registered():
    task = run_tesseract_job

    assert task.name
    assert task.app.tasks[task.name].name == task.name
    assert callable(task.run)


def test_shared_task_delay_delegates_to_apply_async(monkeypatch):
    apply_async = Mock(return_value="queued")
    monkeypatch.setattr(run_tesseract_job, "apply_async", apply_async)

    result = run_tesseract_job.delay("filelist.txt", ["eng", "spa"], "output")

    assert result == "queued"
    apply_async.assert_called_once_with(
        ("filelist.txt", ["eng", "spa"], "output"),
        {},
    )


def test_run_tesseract_job_updates_state_and_runs_tesseract(monkeypatch):
    update_state = Mock()
    run = Mock()
    monkeypatch.setattr(run_tesseract_job, "update_state", update_state)
    monkeypatch.setattr("quiabo.tasks.subprocess.run", run)

    result = run_tesseract_job.run(
        "files.txt",
        ["eng", "spa"],
        "output",
    )

    update_state.assert_called_once_with(
        state="STARTED",
        meta={
            "filelist": "files.txt",
            "languages": ["eng", "spa"],
            "output": "output.pdf",
        },
    )
    assert result == {"output": ("output.pdf")}
