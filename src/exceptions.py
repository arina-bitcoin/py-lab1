class TaskInvariantError(Exception):
    """Базовое исключение для всех нарушений инвариантов задачи."""
    pass


class InvalidTaskIdError(TaskInvariantError):
    """Исключение: некорректный идентификатор задачи."""
    pass


class InvalidPriorityError(TaskInvariantError):
    """Исключение: некорректный приоритет задачи."""
    pass


class InvalidStatusError(TaskInvariantError):
    """Исключение: некорректный статус задачи."""
    pass


class EmptyDescriptionError(TaskInvariantError):
    """Исключение: пустое описание задачи."""
    pass


class ImmutableAttributeError(TaskInvariantError):
    """Исключение: попытка изменить неизменяемый атрибут."""
    pass