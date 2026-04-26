from src.models import Task, TaskStatus, TaskPriority
from src.contracts import TaskSource
from src.utils.logger_config import get_logger
from typing import Union, Callable, Iterable, Iterator

logger = get_logger(__name__)

class TaskQueue:
    def __init__(self, source: Union[TaskSource, Callable[[], Iterable[Task]]]):
        if isinstance(source, TaskSource):
            self._factory = source.get_tasks
        elif callable(source):
            self._factory = source
        else:
            raise TypeError(
                f"source должен быть TaskSource или callable, получен {type(source).__name__}"
            )
        logger.debug(f"TaskQueue создана с фабрикой {self._factory.__name__}")
        
    def __iter__(self) -> Iterator[Task]:
        return iter(self._factory())

    def __repr__(self) -> str:
        return f"TaskQueue(factory={self._factory.__name__})"

    def filter_by_status(self, status) -> "TaskQueue":
        """Возвращает новую очередь с задачами, у которых данный статус"""
        def factory():
            for task in self:
                if task.status == status:
                    yield task
        logger.info(f"Фильтр по статусу {status}")
        return TaskQueue(factory)

    def filter_by_priority(self, priority) -> "TaskQueue":
        """Вернуть новую очередь с приоритетом >= указанного"""
        def factory():
            for task in self:
                if task.priority >= priority:
                    yield task
        logger.info(f"Фильтр по приоритету {priority}")
        return TaskQueue(factory)
