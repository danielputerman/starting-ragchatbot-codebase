#!/bin/bash
# Auto-fix code quality issues

echo "Fixing code quality issues..."
echo ""

echo "1. Auto-fixing with Ruff..."
cd backend && uv run ruff check --fix .

echo ""
echo "2. Formatting with Ruff..."
uv run ruff format .

echo ""
echo "3. Running MyPy (informational)..."
uv run mypy .

echo ""
echo "✓ Auto-fix complete! Review changes with 'git diff'"
