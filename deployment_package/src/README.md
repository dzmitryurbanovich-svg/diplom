# Source Code (Logic & MCP)

Эта папка содержит реализацию программной части диплома.

## Архитектура

Проект разделен на два независимых слоя:

### 1. Logic Layer (`src/logic/`)
Чистая реализация правил игры Каркассон.
- `models.py`: Классы `Tile`, `Side`, `Segment`. Тайлы представлены как графы.
- `engine.py`: Класс `Board` и реализация **DSU (Disjoint Set Union)** для эффективного отслеживания связности объектов на поле.
- `deck.py`: Определение стандартного набора тайлов.

### 2. Integration Layer (`src/mcp/`)
Реализация протокола **Model Context Protocol (MCP)**.
- `server.py`: Сервер, который предоставляет инструменты (`Tools`) для LLM.
- `prompts.py`: Библиотека промптов для реализации стратегий **Tree of Thoughts** и **Reflexion**.

## Технологии
- Python 3.14+
- MCP SDK (Model Context Protocol)
- DSU Algorithm
