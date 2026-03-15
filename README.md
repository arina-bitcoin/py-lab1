# py-lab1 — учебный проект

Лабораторная работа на Python: система задач с разными источниками данных и единым процессором обработки

## О чём проект

Небольшая система управления задачами, которая показывает:

- **Модели данных** — задача (`Task`) с приоритетом, статусом, сериализацией в JSON
- **Контракты (Protocol)** — единый интерфейс для источников задач без наследования
- **Источники задач** — файл (JSON), API (заглушка), генератор
- **Процессор** — один процессор обрабатывает задачи из любого источника по одному контракту
- **Логирование и тесты** — pytest, покрытие кода, проверка контрактов

Что сделано: dataclasses, typing (Protocol, runtime_checkable), декораторы, структурированное логирование.

## Структура проекта

```
py-lab1/
├── src/
│   ├── models.py       # Модели Task, коллекция, приоритеты/статусы
│   ├── contracts.py    # Протокол TaskSource (контракт источников)
│   ├── processor.py    # Процессор задач, обработчики, статистика
│   ├── sources/
│   │   ├── file_sourse.py   # Задачи из JSON-файла
│   │   ├── api_source.py   # Задачи из API (заглушка)
│   │   └── generator_source.py  # Генератор задач для тестов
│   └── utils/
│       └── logger_config.py    # Настройка логирования
├── tests/
│   ├── test_models.py              # Тесты моделей и коллекции
│   ├── test_processor.py           # Тесты процессора и источников
│   ├── test_sources.py             # Тесты всех источников
│   └── test_contracts_and_logging.py  # Контракты и логгер
├── pytest.ini        
├── .coveragerc       
├── requirements.txt # pytest, pytest-cov
└── README.md
```

### Начинка

| `src/models.py` | Модели задач и коллекция |
| `src/contracts.py` | Контракт TaskSource (Protocol) |
| `src/processor.py` | Обработка задач из любого источника |
| `src/sources/file_sourse.py` | Задачи из JSON-файла |
| `src/sources/api_source.py` | Задачи из API (заглушка) |
| `src/sources/generator_source.py` | Генератор задач |
| `src/utils/logger_config.py` | Настройка логгера |
| `tests/test_models.py` | Тесты моделей |
| `tests/test_processor.py` | Тесты процессора |
| `tests/test_sources.py` | Тесты источников |
| `tests/test_contracts_and_logging.py` | Тесты контрактов и логов |
| `pytest.ini` | Конфиг pytest и coverage |
| `.coveragerc` | Настройки покрытия кода |
| `requirements.txt` | Зависимости проекта |

## Учебные цели

- Работа с **Protocol** и утиной типизацией
- Разделение моделей, контрактов и реализаций
- Организация тестов и настройка coverage
- Логирование и базовая обработка ошибок

---

*Учебный проект, курс Python.*
