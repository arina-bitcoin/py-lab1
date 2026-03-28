
from typing import Any, Optional
from src.exceptions import (
    InvalidTaskIdError,
    InvalidPriorityError,
    InvalidStatusError,
    EmptyDescriptionError,
    ImmutableAttributeError,
)


class ReadOnlyIdDescriptor:
    """
    Data descriptor для неизменяемого идентификатора задачи.
    
    ОСОБЕННОСТИ (data descriptor):
    - Имеет метод __set__, поэтому является DATA дескриптором
    - Приоритет выше, чем атрибуты в __dict__ объекта
    - Не может быть переопределён на уровне экземпляра
    
    ПОВЕДЕНИЕ:
    - Установить ID можно только один раз (при создании)
    - После установки значение становится read-only
    - Выполняется валидация типа и значения
    """
    
    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Any:
        """
        Получение значения ID.
        
        Args:
            obj: Экземпляр объекта (или None при доступе через класс)
            objtype: Тип объекта (для доступа через класс)
            
        Returns:
            Значение ID
        """
        if obj is None:
            return self
        return getattr(obj, '_id', None)
    
    def __set__(self, obj: Any, value: Any) -> None:
        """
        Установка значения ID с валидацией и защитой от изменения.
        
        Args:
            obj: Экземпляр объекта
            value: Новое значение ID
            
        Raises:
            ImmutableAttributeError: При попытке изменить уже установленный ID
            InvalidTaskIdError: При некорректном значении ID
        """
        # Проверка: можно установить только один раз
        if hasattr(obj, '_id'):
            raise ImmutableAttributeError(
                f"Невозможно изменить ID задачи с {obj._id} на {value}. "
                f"ID является неизменяемым атрибутом."
            )
        
        # Валидация типа
        if not isinstance(value, int):
            raise InvalidTaskIdError(
                f"ID должен быть целым числом, получен {type(value).__name__}"
            )
        
        # Валидация значения
        if value < 0:
            raise InvalidTaskIdError(
                f"ID не может быть отрицательным: {value}"
            )
        
        # Установка значения
        obj._id = value
    
    def __delete__(self, obj: Any) -> None:
        """
        Запрет удаления ID.
        
        Raises:
            ImmutableAttributeError: Всегда, так как ID нельзя удалить
        """
        raise ImmutableAttributeError("Невозможно удалить ID задачи")


# ============================================================================
# DATA DESCRIPTOR #2: Validated Priority
# ============================================================================

class ValidatedPriorityDescriptor:
    """
    Data descriptor для валидации приоритета задачи.
    
    ОСОБЕННОСТИ (data descriptor):
    - Имеет метод __set__, поэтому является DATA дескриптором
    - Выполняет валидацию при каждой установке значения
    - Автоматически конвертирует int в TaskPriority
    
    ПОВЕДЕНИЕ:
    - Принимает int или TaskPriority
    - Валидирует допустимость значения
    - Сохраняет значение как TaskPriority
    """
    
    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Any:
        """
        Получение значения приоритета.
        
        Args:
            obj: Экземпляр объекта
            objtype: Тип объекта
            
        Returns:
            TaskPriority: Текущий приоритет
        """
        if obj is None:
            return self
        return getattr(obj, '_priority', None)
    
    def __set__(self, obj: Any, value: Any) -> None:
        """
        Установка приоритета с валидацией.
        
        Args:
            obj: Экземпляр объекта
            value: Новое значение приоритета (int или TaskPriority)
            
        Raises:
            InvalidPriorityError: При некорректном значении
        """
        from src.models import TaskPriority
        
        # Определяем целевое значение
        if isinstance(value, TaskPriority):
            priority_value = value
        elif isinstance(value, int):
            try:
                priority_value = TaskPriority(value)
            except ValueError:
                raise InvalidPriorityError(
                    f"Некорректное значение приоритета: {value}. "
                    f"Допустимые значения: {[p.value for p in TaskPriority]} "
                    f"({[p.name for p in TaskPriority]})"
                )
        else:
            raise InvalidPriorityError(
                f"Приоритет должен быть TaskPriority или int, "
                f"получен {type(value).__name__}"
            )
        
        # Сохраняем значение
        obj._priority = priority_value
    
    def __delete__(self, obj: Any) -> None:
        """
        Запрет удаления приоритета.
        
        Raises:
            InvalidPriorityError: Всегда, так как приоритет не может быть удалён
        """
        raise InvalidPriorityError("Невозможно удалить приоритет задачи")


# ============================================================================
# DATA DESCRIPTOR #3: Validated Status
# ============================================================================

class ValidatedStatusDescriptor:
    """
    Data descriptor для валидации статуса задачи.
    
    ОСОБЕННОСТИ (data descriptor):
    - Имеет метод __set__, поэтому является DATA дескриптором
    - Выполняет валидацию при каждой установке значения
    
    ПОВЕДЕНИЕ:
    - Принимает int или TaskStatus
    - Валидирует допустимость значения
    - Сохраняет значение как TaskStatus
    """
    
    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Any:
        """
        Получение значения статуса.
        
        Args:
            obj: Экземпляр объекта
            objtype: Тип объекта
            
        Returns:
            TaskStatus: Текущий статус
        """
        if obj is None:
            return self
        return getattr(obj, '_status', None)
    
    def __set__(self, obj: Any, value: Any) -> None:
        """
        Установка статуса с валидацией.
        
        Args:
            obj: Экземпляр объекта
            value: Новое значение статуса (int или TaskStatus)
            
        Raises:
            InvalidStatusError: При некорректном значении
        """
        from src.models import TaskStatus
        
        # Определяем целевое значение
        if isinstance(value, TaskStatus):
            status_value = value
        elif isinstance(value, int):
            try:
                status_value = TaskStatus(value)
            except ValueError:
                raise InvalidStatusError(
                    f"Некорректное значение статуса: {value}. "
                    f"Допустимые значения: {[s.value for s in TaskStatus]} "
                    f"({[s.name for s in TaskStatus]})"
                )
        else:
            raise InvalidStatusError(
                f"Статус должен быть TaskStatus или int, "
                f"получен {type(value).__name__}"
            )
        
        # Сохраняем значение
        obj._status = status_value
    
    def __delete__(self, obj: Any) -> None:
        """
        Запрет удаления статуса.
        
        Raises:
            InvalidStatusError: Всегда, так как статус не может быть удалён
        """
        raise InvalidStatusError("Невозможно удалить статус задачи")


# ============================================================================
# NON-DATA DESCRIPTOR: Description
# ============================================================================

class NonDataDescriptionDescriptor:
    """
    Non-data descriptor для описания задачи.
    
    ОСОБЕННОСТИ (non-data descriptor):
    - НЕ имеет метода __set__!
    - Приоритет НИЖЕ, чем атрибуты в __dict__ объекта
    - Может быть переопределён на уровне экземпляра
    
    ДЕМОНСТРАЦИЯ РАЗЛИЧИЙ:
    - В отличие от data descriptors, можно переопределить через obj.__dict__
    - Это демонстрирует разницу в порядке поиска атрибутов
    
    ПОВЕДЕНИЕ:
    - Если в __dict__ объекта есть ключ 'description', возвращаем его
    - Иначе возвращаем сохранённое значение _description
    - Установка значения создаёт запись в __dict__ (не вызывает дескриптор)
    """
    
    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Optional[str]:
        """
        Получение описания задачи.
        
        КЛЮЧЕВОЙ МОМЕНТ: Этот метод проверяет наличие значения в __dict__
        перед возвратом из дескриптора. Это и есть поведение non-data дескриптора.
        
        Args:
            obj: Экземпляр объекта
            objtype: Тип объекта
            
        Returns:
            str: Описание задачи или None
        """
        if obj is None:
            return self
        
        # 🔑 ДЕМОНСТРАЦИЯ NON-DATA DESCRIPTOR:
        # Если в __dict__ объекта есть переопределение, используем его
        # Это возможно потому, что у дескриптора нет __set__
        if 'description' in obj.__dict__:
            return obj.__dict__['description']
        
        # Иначе возвращаем сохранённое значение
        return getattr(obj, '_description', None)
    
    # ⚠️ ОБРАТИТЕ ВНИМАНИЕ: НЕТ МЕТОДА __set__!
    # Это делает этот дескриптор NON-DATA.
    # При установке значения будет создана запись в obj.__dict__,
    # а дескриптор не будет вызван.


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЙ КЛАСС: Validated String
# ============================================================================

class ValidatedStringDescriptor:
    """
    Data descriptor для валидации строковых полей (общий случай).
    
    Этот дескриптор показывает, как можно переиспользовать логику
    валидации для разных строковых атрибутов.
    
    Является DATA дескриптором (есть __set__).
    """
    
    def __init__(self, field_name: str, min_length: int = 1, max_length: int = 1000):
        """
        Инициализация дескриптора.
        
        Args:
            field_name: Имя поля для сообщений об ошибках
            min_length: Минимальная длина строки
            max_length: Максимальная длина строки
        """
        self.field_name = field_name
        self.min_length = min_length
        self.max_length = max_length
        self.storage_name = f"_{field_name}"
    
    def __get__(self, obj: Any, objtype: Optional[type] = None) -> Optional[str]:
        """Получение значения."""
        if obj is None:
            return self
        return getattr(obj, self.storage_name, None)
    
    def __set__(self, obj: Any, value: Any) -> None:
        """
        Установка значения с валидацией.
        
        Args:
            obj: Экземпляр объекта
            value: Новое значение
            
        Raises:
            EmptyDescriptionError: При пустом значении
            TypeError: При некорректном типе
        """
        if value is None:
            raise EmptyDescriptionError(
                f"{self.field_name} не может быть None"
            )
        
        if not isinstance(value, str):
            raise TypeError(
                f"{self.field_name} должен быть строкой, "
                f"получен {type(value).__name__}"
            )
        
        if not value.strip():
            raise EmptyDescriptionError(
                f"{self.field_name} не может быть пустым"
            )
        
        if len(value) < self.min_length:
            raise EmptyDescriptionError(
                f"{self.field_name} слишком короткий: {len(value)} < {self.min_length}"
            )
        
        if len(value) > self.max_length:
            raise EmptyDescriptionError(
                f"{self.field_name} слишком длинный: {len(value)} > {self.max_length}"
            )
        
        setattr(obj, self.storage_name, value.strip())
    
    def __delete__(self, obj: Any) -> None:
        """Запрет удаления."""
        raise AttributeError(f"Невозможно удалить {self.field_name}")