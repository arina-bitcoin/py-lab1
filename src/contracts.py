
from typing import Protocol, runtime_checkable, Iterable, Optional, Any
from models import Task


@runtime_checkable
class TaskSource(Protocol):
    """
    ПОВЕДЕНЧЕСКИЙ КОНТРАКТ для всех источников задач.
    
    Это определение протокола (интерфейса), который должны реализовывать
    все источники задач в системе. Класс считается соответствующим протоколу,
    если он имеет метод get_tasks() с правильной сигнатурой - НАСЛЕДОВАНИЕ
    НЕ ТРЕБУЕТСЯ! Это и есть суть утиной типизации.
    
    Декоратор @runtime_checkable позволяет использовать isinstance() для
    проверки соответствия протоколу во время выполнения программы.
    
    Примеры классов, соответствующих контракту:
        class FileSource:
            def get_tasks(self) -> Iterable[Task]:
                # реализация...
                
        class ApiSource:
            def get_tasks(self) -> Iterable[Task]:
                # реализация...
    
    Метод get_tasks() должен возвращать итерируемый объект (Iterable) с задачами.
    Это может быть список, генератор, кортеж и т.д.
    """
    
    def get_tasks(self) -> Iterable[Task]:
        """
        Получить все задачи из источника.
        
        Returns:
            Iterable[Task]: Последовательность задач. Может быть пустой.
            
        Raises:
            SourceError: Может выбрасывать специфические исключения (опционально)
        """
        ...  


@runtime_checkable
class ConfigurableTaskSource(Protocol):
    """
    Расширенный контракт для источников, которые можно настраивать.
    
    Показывает, что протоколы могут включать несколько методов.
    """
    
    def get_tasks(self) -> Iterable[Task]:
        """Базовый метод получения задач."""
        ...
    
    def configure(self, config: dict) -> None:
        """
        Настроить источник задач.
        
        Args:
            config: Словарь с параметрами настройки
        """
        ...


@runtime_checkable
class CloseableTaskSource(Protocol):
    """
    Контракт для источников, требующих явного закрытия (файлы, сетевые соединения).
    """
    
    def get_tasks(self) -> Iterable[Task]:
        """Базовый метод получения задач."""
        ...
    
    def close(self) -> None:
        """Закрыть источник, освободить ресурсы."""
        ...


def is_task_source(obj: Any) -> bool:
    """
    Проверить, соответствует ли объект контракту TaskSource.
    
    Это обертка над isinstance с более понятным именем.
    Демонстрирует практическое использование runtime_checkable.
    
    Args:
        obj: Любой объект для проверки
        
    Returns:
        bool: True если объект соответствует контракту, иначе False
    """
    return isinstance(obj, TaskSource)


def assert_is_task_source(obj: Any, custom_message: Optional[str] = None) -> None:
    """
    Проверить соответствие контракту и выбросить исключение в случае несоответствия.
    
    Args:
        obj: Проверяемый объект
        custom_message: Пользовательское сообщение об ошибке
        
    Raises:
        TypeError: Если объект не соответствует контракту TaskSource
    """
    if not is_task_source(obj):
        message = custom_message or (
            f"Объект типа {type(obj).__name__} не соответствует контракту TaskSource. "
            f"Убедитесь, что у него есть метод get_tasks(), возвращающий Iterable[Task]."
        )
        raise TypeError(message)


def get_source_info(source: TaskSource) -> dict:
    """
    Получить информацию об источнике задач (для отладки).
    
    Args:
        source: Источник задач, соответствующий контракту
        
    Returns:
        dict: Словарь с информацией об источнике
    """
    return {
        "source_type": type(source).__name__,
        "has_get_tasks": hasattr(source, "get_tasks"),
        "get_tasks_callable": callable(getattr(source, "get_tasks", None)),
        "module": type(source).__module__,
        "docstring": type(source).__doc__,
    }




