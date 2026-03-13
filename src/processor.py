from typing import Iterable, Optional, Any, Callable
from datetime import datetime
import logging
from functools import wraps
from src.contracts import TaskSource, assert_is_task_source
from src.models import Task, TaskStatus, TaskPriority


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def log_processing(func: Callable) -> Callable:
    """
    Декоратор для логирования процесса обработки задач.
    
    Args:
        func: Оборачиваемая функция
        
    Returns:
        Callable: Функция с логированием
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Начало обработки: {func.__name__}")
        start_time = datetime.now()
        
        result = func(*args, **kwargs)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Завершение обработки: {func.__name__} (время: {duration:.3f}с)")
        
        return result
    return wrapper


def validate_source(func: Callable) -> Callable:
    """
    Декоратор для проверки соответствия источника контракту.
    
    Args:
        func: Оборачиваемая функция
        
    Returns:
        Callable: Функция с проверкой источника
    """
    @wraps(func)
    def wrapper(self, source: TaskSource, *args, **kwargs):
        # Проверка контракта в рантайме!
        assert_is_task_source(
            source, 
            f"Объект {type(source).__name__} не соответствует контракту TaskSource"
        )
        return func(self, source, *args, **kwargs)
    return wrapper


class ProcessorError(Exception):
    """Базовое исключение для ошибок процессора."""
    pass


class TaskProcessingError(ProcessorError):
    """Ошибка при обработке конкретной задачи."""
    def __init__(self, task_id: int, message: str):
        self.task_id = task_id
        self.message = message
        super().__init__(f"Ошибка обработки задачи {task_id}: {message}")


class SourceError(ProcessorError):
    """Ошибка при работе с источником задач."""
    pass


class TaskProcessor:
    """
    Процессор задач, работающий с любыми источниками через единый контракт.
    
    Этот класс демонстрирует принцип открытости/закрытости (Open/Closed):
    - ОТКРЫТ для расширения: можно добавлять новые источники задач
    - ЗАКРЫТ для изменений: код процессора не требует правок при добавлении
      новых источников
    
    Процессор принимает любой объект, реализующий метод get_tasks() (duck typing),
    и единообразно обрабатывает все полученные задачи.
    
    Attributes:
        processed_count: Общее количество обработанных задач
        failed_count: Количество задач, завершившихся ошибкой
        processing_history: История обработки задач
    """
    
    def __init__(self, name: str = "MainProcessor"):
        """
        Инициализация процессора.
        
        Args:
            name: Имя процессора (для логирования и идентификации)
        """
        self.name = name
        self.processed_count: int = 0
        self.failed_count: int = 0
        self.processing_history: list[dict[str, Any]] = []
        self._start_time: Optional[datetime] = None
        self._handlers: dict[TaskPriority, list[Callable]] = {}
        
        logger.info(f"Создан процессор: {name}")
    

    @validate_source
    @log_processing
    def process_source(self, source: TaskSource) -> dict[str, Any]:
        """
        Обработать все задачи из указанного источника.
        
        ЭТО ГЛАВНЫЙ МЕТОД ПРОЦЕССОРА.
        Здесь происходит:
        1. Проверка контракта (через декоратор @validate_source)
        2. Получение задач из источника
        3. Обработка каждой задачи
        4. Сбор статистики
        
        Args:
            source: Источник задач (любой объект с методом get_tasks())
            
        Returns:
            dict[str, Any]: Статистика обработки:
                - total: всего задач
                - processed: успешно обработано
                - failed: с ошибками
                - source_type: тип источника
                - processing_time: время обработки
            
        Raises:
            TypeError: Если источник не соответствует контракту
            SourceError: Если источник вернул некорректные данные
        """
        logger.info(f"Процессор '{self.name}' начал обработку источника: {type(source).__name__}")
        
        # Получаем задачи из источника
        try:
            tasks_iterable = source.get_tasks()
        except Exception as e:
            raise SourceError(f"Ошибка получения задач из источника: {e}")
        
        # Проверяем, что получили Iterable
        if not isinstance(tasks_iterable, Iterable):
            raise SourceError(
                f"Метод get_tasks() вернул {type(tasks_iterable).__name__}, "
                f"ожидался Iterable[Task]"
            )
        
        # Преобразуем в список для подсчета статистики
        tasks = list(tasks_iterable)
        total_tasks = len(tasks)
        
        logger.info(f"Получено задач: {total_tasks}")
        
        if total_tasks == 0:
            logger.warning(f"Источник {type(source).__name__} не вернул задач")
            return self._create_statistics(source, 0, 0, 0)
        
        # Обрабатываем каждую задачу
        processed = 0
        failed = 0
        
        for task in tasks:
            try:
                # Проверяем, что получен объект Task
                if not isinstance(task, Task):
                    logger.error(f"Получен не Task объект: {type(task).__name__}")
                    failed += 1
                    self.failed_count += 1
                    continue
                
                # Обрабатываем задачу
                self._process_single_task(task)
                processed += 1
                self.processed_count += 1
                
            except TaskProcessingError as e:
                logger.error(f"Ошибка обработки задачи: {e}")
                failed += 1
                self.failed_count += 1
                self._log_failure(task, e)
            except Exception as e:
                logger.exception(f"Неожиданная ошибка при обработке задачи {getattr(task, 'id', 'unknown')}")
                failed += 1
                self.failed_count += 1
        
        # Сохраняем результат обработки в историю
        result = self._create_statistics(source, total_tasks, processed, failed)
        self.processing_history.append(result)
        
        logger.info(f"Обработка завершена: всего={total_tasks}, успешно={processed}, ошибок={failed}")
        
        return result

    def _process_single_task(self, task: Task) -> None:
        """
        Обработать одну задачу.
        
        Args:
            task: Объект задачи для обработки
            
        Raises:
            TaskProcessingError: Если произошла ошибка при обработке
        """
        try:
            # Логируем начало обработки задачи
            logger.debug(f"Обработка задачи {task.id}: {task.description[:50]}...")
            
            # Вызываем обработчики в зависимости от приоритета
            self._apply_handlers(task)
            
            # Базовая "обработка" - просто выводим информацию
            # В реальной системе здесь могла бы быть сложная логика
            print(f"Задача {task.id} [{task.priority.name}]: {task.description}")
            
            # Помечаем задачу как выполненную
            task.status = TaskStatus.COMPLETED
            
            # Логируем успешное завершение
            logger.info(f"Задача {task.id} успешно обработана")
            
        except Exception as e:
            # В случае ошибки помечаем задачу как неудачную
            task.status = TaskStatus.FAILED
            raise TaskProcessingError(task.id, str(e))
    
    def _apply_handlers(self, task: Task) -> None:
        """
        Применить зарегистрированные обработчики для задачи.
        
        Args:
            task: Задача для обработки
        """
        # Получаем обработчики для приоритета задачи
        handlers = self._handlers.get(task.priority, [])
        
        # Применяем каждый обработчик
        for handler in handlers:
            try:
                handler(task)
            except Exception as e:
                logger.warning(f"Обработчик {handler.__name__} вызвал ошибку: {e}")
    
    def _log_failure(self, task: Task, error: Exception) -> None:
        """
        Зарегистрировать информацию об ошибке обработки.
        
        Args:
            task: Задача, вызвавшая ошибку
            error: Исключение
        """
        failure_record = {
            'task_id': task.id,
            'task_description': task.description,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now()
        }
        
        # Здесь можно сохранять в отдельный лог ошибок
        logger.error(f"Ошибка обработки: {failure_record}")
    

    def register_handler(self, priority: TaskPriority, handler: Callable[[Task], None]) -> None:
        """
        Зарегистрировать обработчик для задач определенного приоритета.
        
        Args:
            priority: Приоритет задач
            handler: Функция-обработчик
        """
        if priority not in self._handlers:
            self._handlers[priority] = []
        self._handlers[priority].append(handler)
        logger.info(f"Зарегистрирован обработчик {handler.__name__} для приоритета {priority.name}")
    
    def clear_handlers(self, priority: Optional[TaskPriority] = None) -> None:
        """
        Очистить зарегистрированные обработчики.
        
        Args:
            priority: Если указан, очистить только для этого приоритета
        """
        if priority:
            self._handlers[priority] = []
        else:
            self._handlers.clear()
        logger.info("Обработчики очищены")
    

    def _create_statistics(
        self, 
        source: TaskSource, 
        total: int, 
        processed: int, 
        failed: int
    ) -> dict[str, Any]:
        """
        Создать статистику обработки.
        
        Args:
            source: Источник задач
            total: Всего задач
            processed: Успешно обработано
            failed: С ошибками
            
        Returns:
            dict[str, Any]: Статистика обработки
        """
        return {
            'timestamp': datetime.now(),
            'source_type': type(source).__name__,
            'total_tasks': total,
            'processed_tasks': processed,
            'failed_tasks': failed,
            'success_rate': (processed / total * 100) if total > 0 else 0,
            'processor_name': self.name
        }
    
    
    def get_statistics(self) -> dict[str, Any]:
        """
        Получить общую статистику работы процессора.
        
        Returns:
            dict[str, Any]: Общая статистика
        """
        total_processed = self.processed_count + self.failed_count
        
        return {
            'processor_name': self.name,
            'total_processed': total_processed,
            'successful': self.processed_count,
            'failed': self.failed_count,
            'success_rate': (self.processed_count / total_processed * 100) if total_processed > 0 else 0,
            'history_entries': len(self.processing_history),
            'registered_handlers': {
                p.name: len(h) for p, h in self._handlers.items()
            }
        }
    
    def get_last_processing(self) -> Optional[dict[str, Any]]:
        """
        Получить результат последней обработки.
        
        Returns:
            Optional[dict[str, Any]]: Результат последней обработки или None
        """
        if self.processing_history:
            return self.processing_history[-1]
        return None
    
    def print_report(self) -> None:
        """Вывести отчет о работе процессора."""
        print("\n" + "=" * 60)
        print(f"ОТЧЕТ ПРОЦЕССОРА: {self.name}")
        print("=" * 60)
        
        stats = self.get_statistics()
        print(f"Всего обработано задач: {stats['total_processed']}")
        print(f"  ✓ Успешно: {stats['successful']}")
        print(f"  ✗ С ошибками: {stats['failed']}")
        print(f"  Процент успеха: {stats['success_rate']:.1f}%")
        
        if self.processing_history:
            print(f"\nПоследние 3 обработки:")
            for i, proc in enumerate(self.processing_history[-3:]):
                print(f"  {i+1}. {proc['source_type']}: "
                      f"{proc['processed_tasks']}/{proc['total_tasks']} "
                      f"({proc['success_rate']:.0f}%)")
        
        print("=" * 60)



def high_priority_handler(task: Task) -> None:
    """
    Специальный обработчик для задач с высоким приоритетом.
    
    Args:
        task: Задача для обработки
    """
    print(f"ВЫСОКИЙ ПРИОРИТЕТ: задача {task.id} требует немедленного внимания!")
    # Здесь могла бы быть отправка уведомления, эскалация и т.д.


def critical_priority_handler(task: Task) -> None:
    """
    Обработчик для критических задач.
    
    Args:
        task: Задача для обработки
    """
    print(f"КРИТИЧЕСКАЯ ЗАДАЧА {task.id}: отправка оповещения администратору!")


def log_handler(task: Task) -> None:
    """
    Обработчик для логирования всех задач.
    
    Args:
        task: Задача для обработки
    """
    logger.info(f"Обработчик log_handler: задача {task.id} проходит через систему")


def process_multiple_sources(processor: TaskProcessor, sources: list[TaskSource]) -> list[dict[str, Any]]:
    """
    Обработать несколько источников последовательно.
    
    Args:
        processor: Процессор задач
        sources: Список источников
        
    Returns:
        List[dict[str, Any]]: Список результатов обработки
    """
    results = []
    for i, source in enumerate(sources):
        print(f"\nОбработка источника {i+1}/{len(sources)}")
        try:
            result = processor.process_source(source)
            results.append(result)
        except Exception as e:
            logger.error(f"Ошибка при обработке источника {type(source).__name__}: {e}")
            results.append({'error': str(e), 'source': type(source).__name__})
    
    return results


