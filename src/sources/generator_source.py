from typing import Iterable

from src.models import Task
from src.utils.logger_config import get_logger

logger = get_logger(__name__)


class GeneratorTaskSource:
    """
    Генератор задач.
    
    Роль: программное создание задач для тестирования
    Контракт: имеет метод get_tasks()
    """
    
    def __init__(self, count: int = 5, prefix: str = "Gen"):
        self.count = count
        self.prefix = prefix
        self._counter = 0
        logger.info(f"GeneratorTaskSource created: {count} tasks, prefix '{prefix}'")
    
    def get_tasks(self) -> Iterable[Task]:
        """
        Генерирует задачи с циклическим приоритетом.
        
        Returns:
            Iterable[Task]: Список сгенерированных задач
        """
        logger.info(f"Generating {self.count} tasks")
        tasks = []
        
        for i in range(self.count):
            self._counter += 1
            priority = (i % 3) + 1  # 1,2,3,1,2,3,...
            
            task = Task(
                id=self._counter,
                description=f"{self.prefix} задача #{self._counter}",
                priority=priority,
                tags=["generated"]
            )
            tasks.append(task)
            logger.debug(f"Generated task {task.id}")
        
        logger.info(f"Generated {len(tasks)} tasks")
        return tasks