from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime
import json
from enum import IntEnum

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
    
    def __str__(self) -> str: #чтоб если что прочитать можно было 
        return self.name.replace('_', ' ').title()

@dataclass
class Task:
    """
    Модель данных, представляющая задачу в системе.
    
    Это центральная модель данных, которую используют все компоненты системы:
    - Источники задач (FileSource, ApiSource, GeneratorSource) создают задачи
    - Процессор (TaskProcessor) обрабатывает задачи
    - Тесты проверяют корректность создания и обработки задач
    
    Использование dataclass дает множество преимуществ:
    - Автоматическая генерация __init__, __repr__, __eq__
    - Явное определение полей с типами
    - Возможность задавать значения по умолчанию
    - Поддержка неизменяемости (frozen=True) при необходимости
    
    Атрибуты:
        id: Уникальный идентификатор задачи
        description: Описание задачи (что нужно сделать)
        created_at: Время создания задачи (автоматически устанавливается текущее)
        priority: Приоритет задачи (по умолчанию LOW)
        status: Статус выполнения (по умолчанию PENDING)
        data: Дополнительные данные задачи (может быть любым типом)
        tags: Теги для категоризации задач
    """
    
    id: int
    description: str
    
    created_at: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.LOW
    status: TaskStatus = TaskStatus.PENDING
    data: Optional[Any] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self._init_defaults()
        self._validate()
        logger.debug(f"Task created: {self}")

    def _init_defaults(self):
        if self.created_at is None:
            self.created_at = datetime.now()
            logger.debug(f"Created_at set to default: {self.created_at}")
            
        if not isinstance(self.priority, TaskPriority):
            try:
                original = self.priority
                self.priority = TaskPriority(self.priority)
                logger.debug(f"Priority converted from {original} to {self.priority}")
            except (ValueError, TypeError):
                logger.debug(f"Status converted from {original} to {self.status}")
        
        if not isinstance(self.status, TaskStatus):
            try:
                original = self.status
                self.status = TaskStatus(self.status)
            except (ValueError, TypeError):
                logger.warning(f"Invalid status value: {self.status}, keeping as is")
    
    def _validate(self) -> None:
        """
        Внутренняя валидация данных задачи.
        
        Raises:
            ValueError: Если данные некорректны
        """
        if self.id < 0:
            logger.error(f"Invalid task ID: {self.id} (negative)")
            raise ValueError(f"ID задачи не может быть отрицательным: {self.id}")
        
        if not self.description or not self.description.strip():
            logger.error(f"Empty description for task {self.id}")
            raise ValueError("Описание задачи не может быть пустым")
        
        if not isinstance(self.priority, TaskPriority):
            try:
                self.priority = TaskPriority(self.priority)
                logger.debug(f"Priority auto-converted to {self.priority}")
            except (ValueError, TypeError):
                logger.error(f"Invalid priority type/value: {self.priority} (type: {type(self.priority).__name__})")
                raise ValueError(f"Некорректный приоритет: {self.priority}")
        
        if not isinstance(self.status, TaskStatus):
            try:
                self.status = TaskStatus(self.status)
                logger.debug(f"Status auto-converted to {self.status}")
            except (ValueError, TypeError):
                logger.error(f"Invalid status type/value: {self.status} (type: {type(self.status).__name__})")
                raise ValueError(f"Некорректный статус: {self.status}")
            
    def __setattr__(self, name: str, value: Any) -> None:
        """Переопределение для валидации при изменении атрибутов."""
        old_value = getattr(self, name, None)
        super().__setattr__(name, value)
        # Валидируем только после полной инициализации (есть id и description),
        # иначе при установке id в __init__ ещё нет description и _validate() падает.
        if name in ('id', 'description', 'priority', 'status') and 'description' in self.__dict__:
            try:
                self._validate()
                if old_value != value:
                    logger.debug(f"Task.{name} changed: {old_value} -> {value}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Validation failed for {name}={value}, rolling back: {e}")
                super().__setattr__(name, old_value)
                raise
    
    @property
    def is_completed(self) -> bool:
        """Проверка, завершена ли задача."""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли задача выполнения."""
        return self.status == TaskStatus.PENDING
    
    @property
    def age_seconds(self) -> float:
        """Возраст задачи в секундах (сколько прошло с создания)."""
        if self.created_at:
            delta = datetime.now() - self.created_at
            return delta.total_seconds()
        return 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """
        Преобразовать задачу в словарь.
        
        Используется для сериализации в JSON, сохранения в БД и т.д.
        
        Returns:
            dict[str, Any]: Словарь с данными задачи
        """
        result = asdict(self)
        # Преобразуем специальные типы в сериализуемые
        result['priority'] = self.priority.value
        result['status'] = self.status.value
        result['created_at'] = self.created_at.isoformat() if self.created_at else None
        return result
    
    def to_json(self) -> str:
        """
        Преобразовать задачу в JSON-строку.
        
        Returns:
            str: JSON-представление задачи
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Task':
        """
        Создать задачу из словаря.
        
        Args:
            data: Словарь с данными задачи
            
        Returns:
            Task: Объект задачи
        """
        # Копируем словарь, чтобы не изменять оригинал
        task_data = data.copy()
        
        # Преобразуем строки обратно в объекты
        if 'created_at' in task_data and isinstance(task_data['created_at'], str):
            try:
                task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
            except ValueError:
                task_data['created_at'] = None
        
        if 'priority' in task_data:
            task_data['priority'] = TaskPriority(task_data['priority'])
        
        if 'status' in task_data:
            task_data['status'] = TaskStatus(task_data['status'])
        
        return cls(**task_data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Task':
        """
        Создать задачу из JSON-строки.
        
        Args:
            json_str: JSON-строка с данными задачи
            
        Returns:
            Task: Объект задачи
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """Краткое строковое представление для пользователя."""
        return (f"Task[{self.id}]: {self.description[:50]}... "
                f"[{self.priority}] [{self.status}]")
    
    def __repr__(self) -> str:
        """Подробное представление для отладки."""
        return (f"Task(id={self.id}, "
                f"desc='{self.description[:20]}...', "
                f"priority={self.priority.name}, "
                f"status={self.status.name})")
    
    def __hash__(self) -> int:
        """Хэш для использования в множествах и как ключи словарей."""
        return hash((self.id, self.created_at))
    
    def __eq__(self, other: Any) -> bool:
        """Сравнение задач (по ID и времени создания)."""
        if not isinstance(other, Task):
            return False
        result = self.id == other.id and self.created_at == other.created_at
        un = '' if result else "un"
        logger.debug(f"Task {self.id} {un}equals task {other.id}")
        return result


class TaskCollection:
    """
    Коллекция задач с удобными методами для работы.
    
    Этот класс не обязателен, но показывает, как можно организовать
    работу с группами задач.
    """
    
    def __init__(self, tasks: Optional[list[Task]] = None):
        """
        Инициализация коллекции.
        
        Args:
            tasks: Начальный список задач
        """
        self._tasks: list[Task] = tasks or []
        self._tasks_by_id: dict[int, Task] = {t.id: t for t in self._tasks}
    
    def add(self, task: Task) -> None:
        """Добавить задачу в коллекцию."""
        if task.id in self._tasks_by_id:
            raise ValueError(f"Задача с ID {task.id} уже существует")
        self._tasks.append(task)
        self._tasks_by_id[task.id] = task
    
    def remove(self, task_id: int) -> None:
        """Удалить задачу по ID."""
        if task_id not in self._tasks_by_id:
            raise KeyError(f"Задача с ID {task_id} не найдена")
        task = self._tasks_by_id.pop(task_id)
        self._tasks.remove(task)
    
    def get(self, task_id: int) -> Optional[Task]:
        """Получить задачу по ID."""
        return self._tasks_by_id.get(task_id)
    
    def get_all(self) -> list[Task]:
        """Получить все задачи."""
        return self._tasks.copy()
    
    def filter(self, **criteria) -> list[Task]:
        """
        Отфильтровать задачи по критериям.
        
        Пример:
            tasks.filter(priority=TaskPriority.HIGH, status=TaskStatus.PENDING)
        """
        result = self._tasks.copy()
        for key, value in criteria.items():
            result = [t for t in result if getattr(t, key, None) == value]
        return result
    
    def __len__(self) -> int:
        """Количество задач в коллекции."""
        return len(self._tasks)
    
    def __iter__(self):
        """Итерация по задачам."""
        return iter(self._tasks)
    
    def __contains__(self, task_id: int) -> bool:
        """Проверка наличия задачи по ID."""
        return task_id in self._tasks_by_id


