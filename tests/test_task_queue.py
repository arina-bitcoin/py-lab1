# tests/test_task_queue.py
import pytest
from typing import Iterable
from src.models import Task, TaskStatus, TaskPriority
from src.contracts import TaskSource
from src.task_queue import TaskQueue


class FixedTaskSource(TaskSource):
    """Источник с фиксированным списком задач, считает вызовы."""
    def __init__(self, tasks: list[Task]):
        self.tasks = tasks
        self.call_count = 0

    def get_tasks(self) -> Iterable[Task]:
        self.call_count += 1
        return self.tasks


@pytest.fixture
def sample_tasks() -> list[Task]:
    return [
        Task(1, "Task 1", priority=TaskPriority.LOW, status=TaskStatus.PENDING),
        Task(2, "Task 2", priority=TaskPriority.MEDIUM, status=TaskStatus.PENDING),
        Task(3, "Task 3", priority=TaskPriority.HIGH, status=TaskStatus.COMPLETED),
        Task(4, "Task 4", priority=TaskPriority.CRITICAL, status=TaskStatus.IN_PROGRESS),
        Task(5, "Task 5", priority=TaskPriority.LOW, status=TaskStatus.PENDING),
    ]


@pytest.fixture
def task_source(sample_tasks) -> FixedTaskSource:
    return FixedTaskSource(sample_tasks)


@pytest.fixture
def task_queue(task_source) -> TaskQueue:
    return TaskQueue(task_source)


def test_init_with_task_source(task_source):
    queue = TaskQueue(task_source)
    assert queue._factory == task_source.get_tasks


def test_init_with_callable(sample_tasks):
    def factory():
        return sample_tasks
    queue = TaskQueue(factory)
    assert queue._factory == factory


def test_init_with_invalid_source():
    with pytest.raises(TypeError, match="source должен быть TaskSource или callable"):
        TaskQueue("not a source")  # type: ignore


def test_iteration_returns_all_tasks(task_queue, sample_tasks):
    result = list(task_queue)
    assert len(result) == len(sample_tasks)
    assert [t.id for t in result] == [1, 2, 3, 4, 5]


def test_repeated_iteration_calls_factory_again(task_source, sample_tasks):
    queue = TaskQueue(task_source)
    first = list(queue)
    second = list(queue)
    assert first == second
    assert task_source.call_count == 2


def test_empty_source():
    source = FixedTaskSource([])
    queue = TaskQueue(source)
    assert list(queue) == []


def test_generator_as_source():
    def gen():
        for i in range(3):
            yield Task(i, f"Gen{i}")
    queue = TaskQueue(gen)
    assert len(list(queue)) == 3
    assert len(list(queue)) == 3


def test_filter_by_status(task_queue):
    pending = task_queue.filter_by_status(TaskStatus.PENDING)
    result = list(pending)
    assert len(result) == 3
    assert all(t.status == TaskStatus.PENDING for t in result)
    assert [t.id for t in result] == [1, 2, 5]

    completed = task_queue.filter_by_status(TaskStatus.COMPLETED)
    assert len(list(completed)) == 1
    assert list(completed)[0].id == 3


def test_filter_by_status_returns_new_queue(task_queue):
    q1 = task_queue.filter_by_status(TaskStatus.PENDING)
    q2 = task_queue.filter_by_status(TaskStatus.COMPLETED)
    assert q1 is not q2
    assert q1._factory != q2._factory


def test_filter_by_status_preserves_laziness(task_source):
    queue = TaskQueue(task_source)
    filtered = queue.filter_by_status(TaskStatus.PENDING)
    assert task_source.call_count == 0   # ещё не обходили
    list(filtered)
    assert task_source.call_count == 1   # обошли только после итерации


def test_filter_by_priority(task_queue):
    high = task_queue.filter_by_priority(TaskPriority.HIGH)
    result = list(high)
    assert len(result) == 2  
    assert all(t.priority >= TaskPriority.HIGH for t in result)

    medium = task_queue.filter_by_priority(TaskPriority.MEDIUM)
    assert len(list(medium)) == 3

    critical = task_queue.filter_by_priority(TaskPriority.CRITICAL)
    assert len(list(critical)) == 1
    assert list(critical)[0].id == 4


def test_filter_by_priority_accepts_int(task_queue):
    # 3 = HIGH
    high = task_queue.filter_by_priority(3)
    assert len(list(high)) == 2


def test_filter_by_priority_chaining(task_queue):
    # Сначала оставляем только PENDING, затем из них те, у кого приоритет >= MEDIUM
    pending = task_queue.filter_by_status(TaskStatus.PENDING)
    pending_high = pending.filter_by_priority(TaskPriority.MEDIUM)
    result = list(pending_high)
    # pending: задачи 1 (LOW), 2 (MEDIUM), 5 (LOW)
    # приоритет >= MEDIUM остаётся только задача 2
    assert len(result) == 1
    assert result[0].id == 2


# ----- Повторный обход отфильтрованных очередей -----

def test_filtered_queue_reiterates(task_source):
    queue = TaskQueue(task_source)
    pending = queue.filter_by_status(TaskStatus.PENDING)
    first = list(pending)
    second = list(pending)
    assert first == second
    assert task_source.call_count == 2   # фабрика вызывалась при каждом проходе

def test_compatible_with_for_loop(task_queue):
    ids = []
    for task in task_queue:
        ids.append(task.id)
    assert ids == [1, 2, 3, 4, 5]


def test_compatible_with_list(task_queue):
    lst = list(task_queue)
    assert len(lst) == 5


def test_compatible_with_sum(task_queue):
    total_ids = sum(task.id for task in task_queue)
    assert total_ids == 1 + 2 + 3 + 4 + 5


def test_compatible_with_any_all(task_queue):
    assert any(t.id == 3 for t in task_queue)
    assert all(isinstance(t, Task) for t in task_queue)


def test_lazy_processing_does_not_materialize_all():
    created_count = 0
    def large_generator():
        nonlocal created_count
        for i in range(100_000):
            created_count += 1
            yield Task(i, f"Task{i}", priority=TaskPriority((i % 3) + 1))
    
    queue = TaskQueue(large_generator)
    filtered = queue.filter_by_priority(TaskPriority.HIGH)
    first_five = []
    for i, task in enumerate(filtered):
        if i >= 5:
            break
        first_five.append(task.id)
    assert len(first_five) == 5
    assert created_count < 100, f"Создано задач: {created_count}, ленивость нарушена"


def test_repr(task_queue):
    rep = repr(task_queue)
    assert rep.startswith("TaskQueue(factory=")
    assert task_queue._factory.__name__ in rep