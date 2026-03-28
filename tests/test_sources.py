from pathlib import Path
import json

from src.sources.file_source import FileTaskSource
from src.sources.api_source import ApiTaskSource
from src.sources.generator_source import GeneratorTaskSource
from src.models import Task


def test_file_task_source_file_not_exists(tmp_path: Path):
    src = FileTaskSource(tmp_path / "missing.json")
    tasks = list(src.get_tasks())
    assert tasks == []


def test_file_task_source_reads_tasks(tmp_path: Path):
    data = [
        {"id": 1, "description": "t1", "priority": 2},
        {"id": 2, "description": "t2"},  # default priority
        {"bad": "no id"},  # skipped
    ]
    file_path = tmp_path / "tasks.json"
    file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    src = FileTaskSource(file_path)
    tasks = list(src.get_tasks())

    assert len(tasks) == 2
    assert all(isinstance(t, Task) for t in tasks)
    assert tasks[0].id == 1
    assert tasks[1].id == 2


def test_api_task_source_produces_tasks():
    src = ApiTaskSource(user_id="user-1")
    tasks = list(src.get_tasks())

    assert len(tasks) == 3
    assert all(isinstance(t, Task) for t in tasks)
    ids = {t.id for t in tasks}
    assert ids == {101, 102, 103}


def test_generator_task_source_generates_requested_count():
    src = GeneratorTaskSource(count=4, prefix="P")
    tasks = list(src.get_tasks())
    assert len(tasks) == 4
    assert all(isinstance(t, Task) for t in tasks)
    assert all("P задача #" in t.description for t in tasks)


def test_file_task_source_invalid_json_returns_empty(tmp_path: Path):
    file_path = tmp_path / "bad.json"
    file_path.write_text("not json at all", encoding="utf-8")
    src = FileTaskSource(file_path)
    tasks = list(src.get_tasks())
    assert tasks == []

