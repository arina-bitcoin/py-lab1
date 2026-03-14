from pathlib import Path

import pytest

from src.contracts import TaskSource, is_task_source, assert_is_task_source, get_source_info
from src.models import Task
from src.utils.logger_config import setup_logging, get_logger


class DummySource:
    def get_tasks(self):
        return []


def test_task_source_protocol_and_helpers():
    src = DummySource()
    assert isinstance(src, TaskSource)
    assert is_task_source(src) is True

    info = get_source_info(src)
    assert info["source_type"] == "DummySource"
    assert info["has_get_tasks"] is True
    assert info["get_tasks_callable"] is True


def test_assert_is_task_source_raises_for_invalid_object():
    with pytest.raises(TypeError):
        assert_is_task_source(object())


def test_setup_logging_and_get_logger(tmp_path: Path):
    log_file = tmp_path / "app.log"
    setup_logging(log_file=log_file)
    logger = get_logger(__name__)

    logger.info("test message")
    # Ensure log file was created and not empty
    assert log_file.exists()
    contents = log_file.read_text(encoding="utf-8")
    assert "test message" in contents

