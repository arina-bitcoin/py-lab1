from datetime import datetime
from typing import Optional, Any
from enum import IntEnum
import json

from src.descriptors import (
    ReadOnlyIdDescriptor,
    ValidatedPriorityDescriptor,
    ValidatedStatusDescriptor,
    NonDataDescriptionDescriptor,
)
from src.exceptions import (
    InvalidPriorityError,
    InvalidStatusError,
    EmptyDescriptionError,
    InvalidTaskIdError,   
)
from src.utils.logger_config import get_logger

logger = get_logger(__name__)


class TaskPriority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __str__(self) -> str:
        return self.name.title()


class TaskStatus(IntEnum):
    PENDING = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5

    def __str__(self) -> str:
        return self.name.replace('_', ' ').title()


class Task:
    """
    Модель задачи с использованием data и non-data дескрипторов.
    - id, priority, status — data дескрипторы (есть __set__)
    - description — non-data дескриптор (нет __set__)
    """

    id = ReadOnlyIdDescriptor()
    priority = ValidatedPriorityDescriptor()
    status = ValidatedStatusDescriptor()
    description = NonDataDescriptionDescriptor()

    def __init__(
        self,
        id: int,
        description: str,
        priority: TaskPriority = TaskPriority.LOW,
        status: TaskStatus = TaskStatus.PENDING,
        created_at: Optional[datetime] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None
    ):
        # Валидация описания (вызывается до установки)
        self._validate_description(description)

        # Установка через data-дескрипторы с обработкой ошибок
        try:
            self.id = id
        except InvalidTaskIdError as e:
            logger.error(f"Ошибка создания задачи: {e}")
            raise

        try:
            self.priority = priority
        except InvalidPriorityError as e:
            logger.error(f"Некорректный приоритет {priority}: {e}")
            raise

        try:
            self.status = status
        except InvalidStatusError as e:
            logger.error(f"Некорректный статус {status}: {e}")
            raise

        # Установка description через non-data дескриптор:
        # создаётся атрибут экземпляра, который перекрывает дескриптор
        self.description = description
        # Для внутреннего использования (если дескриптор не найдёт атрибут)
        self._description = description

        self.created_at = created_at or datetime.now()
        self.tags = tags or []
        self.metadata = metadata or {}

        logger.debug(f"Задача создана: id={self.id}, описание={description[:30]}...")

    def _validate_description(self, description: str) -> None:
        if not description or not isinstance(description, str):
            raise EmptyDescriptionError(f"Описание не может быть пустым. Получено: {description}")
        if not description.strip():
            raise EmptyDescriptionError("Описание не может состоять только из пробелов")

    @property
    def task_priority(self) -> TaskPriority:
        """Геттер для приоритета (демонстрация работы дескриптора)."""
        return self.priority

    @task_priority.setter
    def task_priority(self, value: TaskPriority) -> None:
        """Сеттер, использующий data-дескриптор priority."""
        try:
            self.priority = value
            logger.info(f"Приоритет задачи {self.id} изменён на {value.name}")
        except InvalidPriorityError as e:
            logger.error(f"Не удалось изменить приоритет: {e}")
            raise

    @property
    def task_status(self) -> TaskStatus:
        return self.status

    @task_status.setter
    def task_status(self, value: TaskStatus) -> None:
        try:
            self.status = value
            logger.info(f"Статус задачи {self.id} изменён на {value.name}")
        except InvalidStatusError as e:
            logger.error(f"Не удалось изменить статус: {e}")
            raise

    def update_description(self, new_description: str, force_instance_attr: bool = True) -> None:
        """
        Обновляет описание задачи, демонстрируя работу non-data дескриптора.
        Если force_instance_attr=True (по умолчанию) — создаётся атрибут экземпляра,
        который перекрывает дескриптор. Если False — удаляет атрибут экземпляра,
        чтобы дескриптор вернул значение из хранилища (self._description).
        """
        self._validate_description(new_description)
        if force_instance_attr:
            self.description = new_description
            logger.debug(f"Описание задачи {self.id} переопределено в экземпляре")
        else:
            if 'description' in self.__dict__:
                del self.description   # удаляем атрибут экземпляра
            self._description = new_description
            logger.debug(f"Описание задачи {self.id} сохранено через дескриптор")

    def _get_description_value(self) -> str:
        """
        Возвращает актуальное описание с учётом возможного переопределения.
        Используется для сериализации.
        """
        if 'description' in self.__dict__:
            return self.__dict__['description']
        return getattr(self, '_description', '')


    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def is_pending(self) -> bool:
        return self.status == TaskStatus.PENDING

    @property
    def is_in_progress(self) -> bool:
        return self.status == TaskStatus.IN_PROGRESS

    @property
    def age_seconds(self) -> float:
        if self.created_at:
            return (datetime.now() - self.created_at).total_seconds()
        return 0.0

    @property
    def age_formatted(self) -> str:
        seconds = self.age_seconds
        if seconds < 60:
            return f"{seconds:.0f} сек"
        if seconds < 3600:
            return f"{seconds / 60:.0f} мин"
        return f"{seconds / 3600:.1f} ч"

    @property
    def is_urgent(self) -> bool:
        return self.priority in (TaskPriority.HIGH, TaskPriority.CRITICAL)


    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self._id,
            'description': self._get_description_value(),
            'priority': self._priority.value,
            'status': self._status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'tags': self.tags,
            'metadata': self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Task':
        """Создаёт задачу из словаря с обработкой ошибок."""
        try:
            # Валидация обязательных полей
            if 'id' not in data:
                raise KeyError("Отсутствует обязательное поле 'id'")
            if 'description' not in data:
                raise KeyError("Отсутствует обязательное поле 'description'")

            task_id = data['id']
            description = data['description']

            # Преобразование created_at
            created_at = None
            if data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(data['created_at'])
                except ValueError as e:
                    logger.warning(f"Некорректный формат даты: {data['created_at']}, будет установлено текущее время")
                    created_at = None

            # Преобразование priority
            priority_raw = data.get('priority', 1)
            try:
                priority = TaskPriority(priority_raw)
            except ValueError as e:
                logger.warning(f"Некорректное значение приоритета {priority_raw}, используется LOW")
                priority = TaskPriority.LOW

            # Преобразование status
            status_raw = data.get('status', 1)
            try:
                status = TaskStatus(status_raw)
            except ValueError as e:
                logger.warning(f"Некорректное значение статуса {status_raw}, используется PENDING")
                status = TaskStatus.PENDING

            return cls(
                id=task_id,
                description=description,
                priority=priority,
                status=status,
                created_at=created_at,
                tags=data.get('tags', []),
                metadata=data.get('metadata', {})
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Ошибка создания задачи из словаря {data}: {e}")
            raise

    @classmethod
    def from_json(cls, json_str: str) -> 'Task':
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка разбора JSON: {e}")
            raise


    def __str__(self) -> str:
        return f"Task[{self._id}]: {self._get_description_value()[:50]}... [{self._priority.name}]"

    def __repr__(self) -> str:
        return (f"Task(id={self._id}, desc='{self._get_description_value()[:20]}...', "
                f"priority={self._priority.name}, status={self._status.name})")

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Task):
            return False
        return self._id == other._id


class TaskCollection:
    """Коллекция задач с обработкой ошибок."""

    def __init__(self, tasks: Optional[list[Task]] = None):
        self._tasks: list[Task] = tasks or []
        self._tasks_by_id: dict[int, Task] = {t.id: t for t in self._tasks}

    def add(self, task: Task) -> None:
        if task.id in self._tasks_by_id:
            logger.warning(f"Попытка добавить дубликат задачи с ID {task.id}")
            raise ValueError(f"Задача с ID {task.id} уже существует")
        self._tasks.append(task)
        self._tasks_by_id[task.id] = task
        logger.debug(f"Задача {task.id} добавлена в коллекцию")

    def remove(self, task_id: int) -> None:
        if task_id not in self._tasks_by_id:
            logger.error(f"Попытка удалить несуществующую задачу с ID {task_id}")
            raise KeyError(f"Задача с ID {task_id} не найдена")
        task = self._tasks_by_id.pop(task_id)
        self._tasks.remove(task)
        logger.debug(f"Задача {task_id} удалена из коллекции")

    def get(self, task_id: int) -> Optional[Task]:
        return self._tasks_by_id.get(task_id)

    def get_all(self) -> list[Task]:
        return self._tasks.copy()

    def filter(self, **criteria) -> list[Task]:
        """
        Фильтрация задач по критериям.
        Пример: filter(priority=TaskPriority.HIGH, status=TaskStatus.PENDING)
        """
        result = self._tasks.copy()
        for key, value in criteria.items():
            # Проверяем, существует ли атрибут у Task
            if not hasattr(Task, key) and key not in ('priority', 'status', 'description', 'id'):
                logger.warning(f"Неизвестный критерий фильтрации: {key}")
                continue
            result = [t for t in result if getattr(t, key, None) == value]
        logger.debug(f"Фильтрация по {criteria} вернула {len(result)} задач")
        return result

    def __len__(self) -> int:
        return len(self._tasks)

    def __iter__(self):
        return iter(self._tasks)

    def __contains__(self, task_id: int) -> bool:
        return task_id in self._tasks_by_id

    def __getitem__(self, task_id: int) -> Task:
        """Позволяет получать задачу по ID через квадратные скобки."""
        task = self.get(task_id)
        if task is None:
            raise KeyError(f"Задача с ID {task_id} не найдена")
        return task