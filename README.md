# Carcassonne AI: Hybrid LLM-MCTS Implementation

Данный проект является практической реализацией дипломной работы по теме "Разработка гибридного алгоритма оптимизации стратегии в игре Каркассон".

## Структура проекта

- `thesis/`: Исходные файлы текста диплома (LaTeX).
- `src/`: Исходный код системы (Python).
    - `logic/`: Игровой движок (Logic Layer).
    - `mcp/`: Реализация Model Context Protocol сервера.
- `demos/`: Скрипты для тестирования и демонстрации работы.
- `docs/`: Используемая литература и справочные материалы.
- `venv/`: Виртуальное окружение Python (3.14+).

## Быстрый запуск

> [!IMPORTANT]
> Все команды должны выполняться из корня проекта: `/Users/dzmitryurbanovich/Desktop/диплом/diplom-latex/diplom`.

### 1. Подготовка окружения
Убедитесь, что у вас установлен Python 3.14+.
```bash
# Активация окружения
source venv/bin/activate
# Установка зависимостей (если не установлены)
pip install mcp httpx
```

### 2. Запуск MCP-сервера
Сервер обеспечивает интерфейс между игровым движком и ИИ.
```bash
PYTHONPATH=. venv/bin/python src/mcp/server.py
```

### 3. Запуск демо с Ollama
Для работы этого демо должна быть запущена [Ollama](https://ollama.com/) с моделью `gemma3:latest`.
```bash
PYTHONPATH=. venv/bin/python demos/ollama_agent.py
```

## Развертывание в облако (Hugging Face Spaces)

Для того чтобы сервер был доступен 24/7 по публичному URL:

1.  Создайте новый **Space** на [Hugging Face](https://huggingface.co/spaces).
2.  Выберите тип **Docker**.
3.  Загрузите файлы проекта (или подключите GitHub-репозиторий).
4.  После сборки ваш сервер будет доступен по адресу: `https://<your-username>-<space-name>.hf.space/sse`.

Этот URL можно использовать в качестве "Remote MCP Server" в любых совместимых клиентах.

## Тестирование
Для проверки корректности работы всех слоев используйте:
```bash
# Тест логики движка
PYTHONPATH=. venv/bin/python demos/demo_engine.py

# Тест MCP интерфейса (JSON-RPC)
PYTHONPATH=. venv/bin/python demos/test_mcp_client.py
```

Подробные инструкции по каждому разделу находятся в соответствующих папках.
