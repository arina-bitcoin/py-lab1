import pytest
from datetime import datetime
from src.models import Task, TaskPriority, TaskStatus
from src.exceptions import (
    InvalidTaskIdError,
    InvalidPriorityError,
    InvalidStatusError,
    EmptyDescriptionError,
    ImmutableAttributeError,
)


class TestReadOnlyIdDescriptor:
    """Тесты для read-only ID дескриптора."""
    
    def test_id_creation_valid(self):
        """Тест: создание с корректным ID."""
        task = Task(id=1, description="Test")
        assert task.id == 1
        assert task._id == 1
    
    def test_id_creation_negative_raises_error(self):
        """Тест: создание с отрицательным ID вызывает ошибку."""
        with pytest.raises(InvalidTaskIdError, match="не может быть отрицательным"):
            Task(id=-1, description="Test")
    
    def test_id_creation_non_int_raises_error(self):
        """Тест: создание с не-int ID вызывает ошибку."""
        with pytest.raises(InvalidTaskIdError, match="целым числом"):
            Task(id="1", description="Test")
    
    def test_id_cannot_be_changed(self):
        """Тест: ID нельзя изменить после создания."""
        task = Task(id=1, description="Test")
        with pytest.raises(ImmutableAttributeError, match="невозможно изменить"):
            task.id = 2
    
    def test_id_cannot_be_deleted(self):
        """Тест: ID нельзя удалить."""
        task = Task(id=1, description="Test")
        with pytest.raises(ImmutableAttributeError):
            del task.id


class TestValidatedPriorityDescriptor:
    """Тесты для валидации приоритета."""
    
    def test_priority_creation_valid_int(self):
        """Тест: создание с корректным int приоритетом."""
        task = Task(id=1, description="Test", priority=3)
        assert task.priority == TaskPriority.HIGH
        assert task._priority == TaskPriority.HIGH
    
    def test_priority_creation_valid_enum(self):
        """Тест: создание с корректным enum приоритетом."""
        task = Task(id=1, description="Test", priority=TaskPriority.CRITICAL)
        assert task.priority == TaskPriority.CRITICAL
    
    def test_priority_creation_invalid_int_raises_error(self):
        """Тест: создание с некорректным int приоритетом вызывает ошибку."""
        with pytest.raises(InvalidPriorityError, match="Некорректное значение"):
            Task(id=1, description="Test", priority=10)
    
    def test_priority_creation_invalid_type_raises_error(self):
        """Тест: создание с некорректным типом вызывает ошибку."""
        with pytest.raises(InvalidPriorityError, match="должен быть"):
            Task(id=1, description="Test", priority="high")
    
    def test_priority_can_be_changed_valid(self):
        """Тест: приоритет можно изменить на корректный."""
        task = Task(id=1, description="Test", priority=1)
        task.priority = 4
        assert task.priority == TaskPriority.CRITICAL
    
    def test_priority_cannot_be_set_invalid(self):
        """Тест: нельзя установить некорректный приоритет."""
        task = Task(id=1, description="Test", priority=1)
        with pytest.raises(InvalidPriorityError):
            task.priority = 10
        assert task.priority == TaskPriority.LOW  # Значение не изменилось


class TestValidatedStatusDescriptor:
    """Тесты для валидации статуса."""
    
    def test_status_creation_valid_int(self):
        """Тест: создание с корректным int статусом."""
        task = Task(id=1, description="Test", status=3)
        assert task.status == TaskStatus.COMPLETED
    
    def test_status_creation_valid_enum(self):
        """Тест: создание с корректным enum статусом."""
        task = Task(id=1, description="Test", status=TaskStatus.IN_PROGRESS)
        assert task.status == TaskStatus.IN_PROGRESS
    
    def test_status_creation_invalid_int_raises_error(self):
        """Тест: создание с некорректным int статусом вызывает ошибку."""
        with pytest.raises(InvalidStatusError):
            Task(id=1, description="Test", status=99)
    
    def test_status_can_be_changed_valid(self):
        """Тест: статус можно изменить на корректный."""
        task = Task(id=1, description="Test", status=1)
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED
    
    def test_status_cannot_be_set_invalid(self):
        """Тест: нельзя установить некорректный статус."""
        task = Task(id=1, description="Test", status=1)
        with pytest.raises(InvalidStatusError):
            task.status = 99
        assert task.status == TaskStatus.PENDING


class TestNonDataDescriptionDescriptor:
    """Тесты для non-data дескриптора описания."""
    
    def test_description_creation(self):
        """Тест: создание с корректным описанием."""
        task = Task(id=1, description="Test description")
        assert task.description == "Test description"
    
    def test_description_can_be_overridden_via_dict(self):
        """Тест: non-data дескриптор можно переопределить через __dict__."""
        task = Task(id=1, description="Original")
        task.__dict__['description'] = "Overridden"
        assert task.description == "Overridden"
    
    def test_description_can_be_set_directly(self):
        """Тест: установка описания создаёт запись в __dict__."""
        task = Task(id=1, description="Original")
        task.description = "New description"
        assert 'description' in task.__dict__
        assert task.description == "New description"


class TestComputedProperties:
    """Тесты для вычисляемых свойств (@property)."""
    
    def test_is_completed(self):
        """Тест: свойство is_completed."""
        task = Task(id=1, description="Test", status=TaskStatus.PENDING)
        assert not task.is_completed
        task.status = TaskStatus.COMPLETED
        assert task.is_completed
    
    def test_is_pending(self):
        """Тест: свойство is_pending."""
        task = Task(id=1, description="Test", status=TaskStatus.PENDING)
        assert task.is_pending
        task.status = TaskStatus.IN_PROGRESS
        assert not task.is_pending
    
    def test_age_seconds(self):
        """Тест: свойство age_seconds."""
        task = Task(id=1, description="Test")
        assert task.age_seconds >= 0
    
    def test_is_urgent(self):
        """Тест: свойство is_urgent."""
        task = Task(id=1, description="Test", priority=TaskPriority.LOW)
        assert not task.is_urgent
        task.priority = TaskPriority.HIGH
        assert task.is_urgent
        task.priority = TaskPriority.CRITICAL
        assert task.is_urgent


class TestTaskSerialization:
    """Тесты для сериализации/десериализации."""
    
    def test_to_dict(self):
        """Тест: преобразование в словарь."""
        task = Task(id=1, description="Test", priority=3, tags=["urgent"])
        data = task.to_dict()
        assert data['id'] == 1
        assert data['priority'] == 3
        assert 'tags' in data
    
    def test_from_dict(self):
        """Тест: создание из словаря."""
        data = {
            'id': 1,
            'description': 'Test',
            'priority': 2,
            'status': 1
        }
        task = Task.from_dict(data)
        assert task.id == 1
        assert task.description == 'Test'
        assert task.priority == TaskPriority.MEDIUM


class TestTaskCollection:
    """Тесты для коллекции задач."""
    
    def test_add_task(self):
        """Тест: добавление задачи в коллекцию."""
        from src.models import TaskCollection
        collection = TaskCollection()
        task = Task(id=1, description="Test")
        collection.add(task)
        assert len(collection) == 1
    
    def test_get_task_by_id(self):
        """Тест: получение задачи по ID."""
        from src.models import TaskCollection
        collection = TaskCollection()
        task = Task(id=1, description="Test")
        collection.add(task)
        assert collection.get(1) == task
    
    def test_filter_tasks(self):
        """Тест: фильтрация задач."""
        from src.models import TaskCollection
        collection = TaskCollection()
        collection.add(Task(id=1, description="Low", priority=1))
        collection.add(Task(id=2, description="High", priority=3))
        
        high_tasks = collection.filter(priority=TaskPriority.HIGH)
        assert len(high_tasks) == 1
        assert high_tasks[0].id == 2