#!/bin/bash

# Скрипт для линтинга и форматирования Python кода
# Используется ruff (заменяет flake8, isort, black)

echo "🚀 Запуск линтинга (Ruff)..."
uv run ruff check . --fix

echo "🎨 Запуск форматирования (Ruff Format)..."
uv run ruff format .

echo "✅ Готово! Код проверен и приведен в порядок."
