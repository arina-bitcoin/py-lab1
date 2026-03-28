import json
from pathlib import Path
from typing import Iterable, Union

from src.models import Task
from src.utils.logger_config import get_logger

logger = get_logger(__name__)


class FileTaskSource:
    """Источник задач из JSON-файла."""
    
    def __init__(self, filepath: Union[str, Path]):
        self.filepath = Path(filepath)
        logger.info(f"FileSource: {self.filepath}")
    
    def get_tasks(self) -> Iterable[Task]:
        """Прочитать задачи из файла."""
        logger.info(f"Reading from {self.filepath}")
        
        if not self.filepath.exists():
            logger.warning(f"File not found")
            return []
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tasks = []
            for item in data:
                if 'id' not in item or 'description' not in item:
                    continue
                
                task = Task(
                    id=item['id'],
                    description=item['description'],
                    priority=item.get('priority', 1)
                )
                tasks.append(task)
            
            logger.info(f"Read {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return []