import json
from datetime import datetime, timedelta

import pytest

from src.models import Task, TaskPriority, TaskStatus, TaskCollection


def test_task_defaults_and_repr():
    task = Task(id=1, description="Test task")

    assert task.id == 1
    assert task.description == "Test task"
    assert task.priority == TaskPriority.LOW
    assert task.status == TaskStatus.PENDING
    assert isinstance(task.created_at, datetime)
    # __str__ / __repr__ should not raise
    assert "Task[1]" in str(task)
    assert "Task(id=1" in repr(task)


def test_task_priority_and_status_conversion():
    task = Task(id=2, description="With numeric priority", priority=2, status=3)
    assert task.priority == TaskPriority.MEDIUM
    assert task.status == TaskStatus.COMPLETED


def test_task_invalid_id_raises():
    with pytest.raises(ValueError):
        Task(id=-1, description="Bad id")


def test_task_empty_description_raises():
    with pytest.raises(ValueError):
        Task(id=3, description="  ")


def test_task_status_validation_on_attribute_change():
    task = Task(id=4, description="Change status")
    task.status = TaskStatus.IN_PROGRESS
    assert task.status == TaskStatus.IN_PROGRESS

    with pytest.raises(ValueError):
        task.status = "invalid_status"  # type: ignore[assignment]


def test_task_to_dict_and_json_roundtrip():
    task = Task(
        id=5,
        description="Serialize me",
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        tags=["a", "b"],
        metadata={"x": 1},
    )
    data = task.to_dict()
    assert data["id"] == 5
    assert data["priority"] == TaskPriority.HIGH.value
    assert data["status"] == TaskStatus.IN_PROGRESS.value
    assert isinstance(data["created_at"], str)

    json_str = task.to_json()
    loaded = Task.from_json(json_str)
    assert loaded.id == task.id
    assert loaded.description == task.description
    assert loaded.priority == task.priority
    assert loaded.status == task.status


def test_task_from_dict_with_datetime_and_enums():
    created_at = datetime.now() - timedelta(hours=1)
    src = {
        "id": 10,
        "description": "dict",
        "created_at": created_at.isoformat(),
        "priority": TaskPriority.CRITICAL.value,
        "status": TaskStatus.FAILED.value,
    }
    task = Task.from_dict(src)
    assert task.id == 10
    assert task.created_at is not None
    assert task.priority == TaskPriority.CRITICAL
    assert task.status == TaskStatus.FAILED


def test_task_eq_and_hash():
    t1 = Task(id=1, description="same")
    t2 = Task(id=1, description="same")
    # Force equal created_at for deterministic equality
    t2.created_at = t1.created_at
    assert t1 == t2
    assert hash(t1) == hash(t2)
    assert (t1 in {t2}) is True


def test_task_collection_basic_operations():
    t1 = Task(id=1, description="one")
    t2 = Task(id=2, description="two", priority=TaskPriority.HIGH)
    coll = TaskCollection([t1])

    assert len(coll) == 1
    coll.add(t2)
    assert len(coll) == 2
    assert coll.get(2) is t2
    assert 1 in coll

    filtered = coll.filter(priority=TaskPriority.HIGH)
    assert filtered == [t2]

    coll.remove(1)
    assert len(coll) == 1
    assert coll.get(1) is None


def test_task_collection_add_duplicate_raises():
    t1 = Task(id=1, description="one")
    coll = TaskCollection([t1])
    with pytest.raises(ValueError):
        coll.add(Task(id=1, description="dup"))


def test_task_is_completed_and_is_pending():
    task = Task(id=1, description="p")
    assert task.is_pending is True
    assert task.is_completed is False
    task.status = TaskStatus.COMPLETED
    assert task.is_completed is True
    assert task.is_pending is False


def test_task_age_seconds():
    task = Task(id=1, description="x")
    assert task.age_seconds >= 0


def test_task_eq_not_equal():
    t1 = Task(id=1, description="a")
    t2 = Task(id=2, description="b")
    assert t1 != t2
    assert t1 != "not a task"


def test_task_from_dict_invalid_created_at():
    """При невалидной дате created_at в from_dict подставляется None, затем __post_init__ ставит now()."""
    data = {"id": 1, "description": "d", "created_at": "invalid-date"}
    task = Task.from_dict(data)
    assert task.id == 1
    assert task.description == "d"
    assert task.created_at is not None  # __post_init__ заполняет по умолчанию


def test_task_collection_remove_missing_raises():
    coll = TaskCollection()
    with pytest.raises(KeyError):
        coll.remove(999)

def test_task_age_formatted(monkeypatch):
    from datetime import datetime, timedelta
    task = Task(id=1, description="test")
    fake_now = datetime.now() + timedelta(seconds=30)
    monkeypatch.setattr("src.models.datetime", lambda: fake_now)  # осторожно с monkeypatch
    # Лучше замокать datetime.now через свободную функцию, но для простоты можно проверить возраст >0
    assert "сек" in task.age_formatted or "мин" in task.age_formatted


