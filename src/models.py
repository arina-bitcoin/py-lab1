from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime
import json
from enum import IntEnum


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
    
    def __post_init__(self):
        """
        Инициализация после создания объекта.
        dataclass вызывает этот метод после __init__.
        Здесь мы устанавливаем время создания, если оно не было указано.
        Также можно выполнять валидацию данных.
        """
        self._init_defaults()
        self._validate()

    def _init_defaults(self):
        if self.created_at is None:
            self.created_at = datetime.now()
            
        if not isinstance(self.priority, TaskPriority):
            try:
                self.priority = TaskPriority(self.priority)
            except (ValueError, TypeError):
                pass
        
        if not isinstance(self.status, TaskStatus):
            try:
                self.status = TaskStatus(self.status)
            except (ValueError, TypeError):
                pass
    
    def _validate(self) -> None:
        """
        Внутренняя валидация данных задачи.
        
        Raises:
            ValueError: Если данные некорректны
        """
        if self.id < 0:
            raise ValueError(f"ID задачи не может быть отрицательным: {self.id}")
        
        if not self.description or not self.description.strip():
            raise ValueError("Описание задачи не может быть пустым")
        
        if not isinstance(self.priority, TaskPriority):
            try:
                self.priority = TaskPriority(self.priority)
            except (ValueError, TypeError):
                raise ValueError(f"Некорректный приоритет: {self.priority}")
        
        if not isinstance(self.status, TaskStatus):
            try:
                self.status = TaskStatus(self.status)
            except (ValueError, TypeError):
                raise ValueError(f"Некорректный статус: {self.status}")
            
    def __setattr__(self, name, value):
        """Переопределение для валидации при изменении атрибутов"""
        super().__setattr__(name, value)
        
        # Валидируем после изменения, если объект уже инициализирован
        if hasattr(self, 'id'):  # Проверяем, что объект уже создан
            try:
                if name in ['id', 'description', 'priority', 'status']:
                    self._validate()
            except (ValueError, TypeError) as e:
                # Откатываем изменение в случае ошибки
                super().__setattr__(name, getattr(self, f'_{name}_old', None))
                raise e
    
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
            Dict[str, Any]: Словарь с данными задачи
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
        return self.id == other.id and self.created_at == other.created_at


def create_task(
    id: int,
    description: str,
    priority: TaskPriority = TaskPriority.LOW,
    **kwargs
) -> Task:
    """
    Удобная функция для создания задачи (фабрика).
    
    Args:
        id: ID задачи
        description: Описание
        priority: Приоритет
        **kwargs: Дополнительные аргументы для Task
        
    Returns:
        Task: Созданная задача
    """
    return Task(
        id=id,
        description=description,
        priority=priority,
        **kwargs
    )


def filter_tasks_by_priority(tasks: list[Task], min_priority: TaskPriority) -> list[Task]:
    """
    Отфильтровать задачи по минимальному приоритету.
    
    Args:
        tasks: Список задач
        min_priority: Минимальный приоритет
        
    Returns:
        List[Task]: Задачи с приоритетом >= min_priority
    """
    return [task for task in tasks if task.priority.value >= min_priority.value]


def filter_tasks_by_status(tasks: list[Task], status: TaskStatus) -> list[Task]:
    """
    Отфильтровать задачи по статусу.
    
    Args:
        tasks: Список задач
        status: Статус для фильтрации
        
    Returns:
        List[Task]: Задачи с указанным статусом
    """
    return [task for task in tasks if task.status == status]


def sort_tasks_by_priority(tasks: list[Task], reverse: bool = False) -> list[Task]:
    """
    Отсортировать задачи по приоритету.
    
    Args:
        tasks: Список задач
        reverse: Сортировать по убыванию?
        
    Returns:
        List[Task]: Отсортированный список
    """
    return sorted(tasks, key=lambda t: t.priority.value, reverse=reverse)


def sort_tasks_by_age(tasks: list[Task], reverse: bool = False) -> list[Task]:
    """
    Отсортировать задачи по возрасту (самые старые первые).
    
    Args:
        tasks: Список задач
        reverse: Сортировать по убыванию?
        
    Returns:
        List[Task]: Отсортированный список
    """
    return sorted(tasks, key=lambda t: t.created_at or datetime.min, reverse=reverse)



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


