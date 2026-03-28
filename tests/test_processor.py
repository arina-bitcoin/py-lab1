from typing import Iterable

import pytest

from src.processor import TaskProcessor, TaskProcessingError, SourceError, process_multiple_sources, high_priority_handler, critical_priority_handler, log_handler
from src.models import Task, TaskPriority, TaskStatus
from src.contracts import TaskSource


class GoodSource:
    def __init__(self, tasks: list[Task]):
        self._tasks = tasks

    def get_tasks(self) -> Iterable[Task]:
        return list(self._tasks)


class BadReturnSource:
    def get_tasks(self):
        # Not an Iterable[Task]
        return 123


class ErrorSource:
    def get_tasks(self):
        raise RuntimeError("boom")


class NonTaskSource:
    def get_tasks(self):
        return ["not task"]


def test_process_source_successful_flow():
    tasks = [
        Task(id=1, description="one", priority=TaskPriority.LOW),
        Task(id=2, description="two", priority=TaskPriority.HIGH),
    ]
    src = GoodSource(tasks)
    processor = TaskProcessor("test")

    # Register handlers to exercise handler logic
    processor.register_handler(TaskPriority.HIGH, high_priority_handler)
    processor.register_handler(TaskPriority.CRITICAL, critical_priority_handler)
    processor.register_handler(TaskPriority.LOW, log_handler)

    stats = processor.process_source(src)

    assert stats["total_tasks"] == 2
    assert stats["processed_tasks"] == 2
    assert stats["failed_tasks"] == 0
    assert processor.processed_count == 2
    assert processor.failed_count == 0

    # Each task should be marked completed
    assert all(t.status == TaskStatus.COMPLETED for t in tasks)


def test_process_source_with_non_task_items():
    src = NonTaskSource()
    processor = TaskProcessor("non_task")

    stats = processor.process_source(src)  # type: ignore[arg-type]

    assert stats["total_tasks"] == 1
    assert stats["processed_tasks"] == 0
    assert stats["failed_tasks"] == 1
    assert processor.failed_count == 1


def test_process_source_with_bad_return_type():
    src = BadReturnSource()
    processor = TaskProcessor("bad_return")

    with pytest.raises(SourceError):
        processor.process_source(src)  # type: ignore[arg-type]


def test_process_source_with_source_exception():
    src = ErrorSource()
    processor = TaskProcessor("err_src")

    with pytest.raises(SourceError):
        processor.process_source(src)  # type: ignore[arg-type]


def test_process_single_task_raises_task_processing_error(monkeypatch):
    task = Task(id=10, description="will fail")
    processor = TaskProcessor("single")

    # Эмуляция ошибки внутри _process_single_task (процессор ловит ошибки в обработчиках,
    # поэтому подменяем _apply_handlers, чтобы исключение пробросилось в _process_single_task)
    def _apply_handlers_that_raises(_task: Task) -> None:
        raise RuntimeError("handler fail")

    monkeypatch.setattr(processor, "_apply_handlers", _apply_handlers_that_raises)

    with pytest.raises(TaskProcessingError):
        processor._process_single_task(task)  # type: ignore[protected-access]


def test_process_multiple_sources_mixed_results():
    good_src = GoodSource([Task(id=1, description="ok")])
    bad_src = BadReturnSource()

    processor = TaskProcessor("multi")
    results = process_multiple_sources(processor, [good_src, bad_src])  # type: ignore[arg-type]

    assert len(results) == 2
    assert "error" not in results[0]
    assert "error" in results[1]


def test_process_source_empty_returns_early():
    empty_src = GoodSource([])
    processor = TaskProcessor("empty")
    stats = processor.process_source(empty_src)
    assert stats["total_tasks"] == 0
    assert stats["processed_tasks"] == 0
    assert stats["failed_tasks"] == 0


def test_processor_clear_handlers():
    processor = TaskProcessor("clear")
    processor.register_handler(TaskPriority.LOW, log_handler)
    processor.clear_handlers(TaskPriority.LOW)
    assert processor._handlers.get(TaskPriority.LOW, []) == []
    processor.register_handler(TaskPriority.HIGH, log_handler)
    processor.clear_handlers()
    assert len(processor._handlers) == 0


def test_processor_get_statistics_before_any_processing():
    processor = TaskProcessor("fresh")
    stats = processor.get_statistics()
    assert stats["total_processed"] == 0
    assert stats["successful"] == 0
    assert stats["failed"] == 0
    assert stats["success_rate"] == 0


def test_processor_print_report(capsys):
    processor = TaskProcessor("report")
    processor.process_source(GoodSource([Task(id=1, description="x")]))
    processor.print_report()
    out = capsys.readouterr().out
    assert "ОТЧЕТ ПРОЦЕССОРА" in out
    assert "report" in out
    assert "Всего обработано" in out


def test_processor_handler_exception_logged_not_raised():
    """Ошибка в обработчике логируется, обработка задачи продолжается."""
    task = Task(id=1, description="ok", priority=TaskPriority.LOW)
    processor = TaskProcessor("hand_err")

    def failing_handler(t: Task) -> None:
        raise ValueError("handler boom")

    processor.register_handler(TaskPriority.LOW, failing_handler)
    stats = processor.process_source(GoodSource([task]))
    assert stats["processed_tasks"] == 1
    assert task.status == TaskStatus.COMPLETED


def test_critical_priority_handler_called():
    task = Task(id=99, description="critical", priority=TaskPriority.CRITICAL)
    processor = TaskProcessor("crit")
    processor.register_handler(TaskPriority.CRITICAL, critical_priority_handler)
    processor.process_source(GoodSource([task]))
    assert task.status == TaskStatus.COMPLETED


def test_log_failure_called_on_task_processing_error(monkeypatch):
    """При TaskProcessingError процессор вызывает _log_failure (покрытие ветки и логирования)."""
    task = Task(id=2, description="fail")
    processor = TaskProcessor("logfail")

    def _process_raise(_t: Task) -> None:
        raise TaskProcessingError(_t.id, "simulated")

    monkeypatch.setattr(processor, "_process_single_task", _process_raise)
    stats = processor.process_source(GoodSource([task]))
    assert stats["failed_tasks"] == 1
    assert stats["processed_tasks"] == 0

def test_processor_get_last_processing():
    proc = TaskProcessor("test")
    assert proc.get_last_processing() is None
    src = GoodSource([Task(id=1, description="x")])
    proc.process_source(src)
    last = proc.get_last_processing()
    assert last is not None
    assert last["total_tasks"] == 1


def test_processor_statistics_after_processing():
    proc = TaskProcessor("stats")
    src = GoodSource([Task(id=1, description="a"), Task(id=2, description="b")])
    proc.process_source(src)
    stats = proc.get_statistics()
    assert stats["total_processed"] == 2
    assert stats["successful"] == 2
    assert stats["failed"] == 0

