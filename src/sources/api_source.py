from typing import Iterable

from src.models import Task
from src.utils.logger_config import get_logger

logger = get_logger(__name__)


class ApiTaskSource:
    """
    API-источник задач (заглушка).
    
    Роль: поставщик задач, имитирующий внешнее API
    Контракт: имеет метод get_tasks()
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        logger.info(f"ApiTaskSource created for user: {user_id}")
    
    def get_tasks(self) -> Iterable[Task]:
        """
        Имитирует получение задач из API.
        
        Returns:
            Iterable[Task]: Список тестовых задач
        """
        logger.info(f"Fetching tasks from API for user {self.user_id}")
        
        tasks = [
            Task(
                id=101,
                description=f"API задача 1 (user:{self.user_id})",
                priority=3
            ),
            Task(
                id=102,
                description=f"API задача 2 (user:{self.user_id})",
                priority=2
            ),
            Task(
                id=103,
                description=f"API задача 3 (user:{self.user_id})",
                priority=1
            ),
        ]
        
        logger.info(f"Retrieved {len(tasks)} tasks from API")
        return tasks