#!/bin/bash
# Run all quality checks without modifying files

echo "Running code quality checks..."
echo ""

echo "1. Ruff linting..."
cd backend && uv run ruff check .
RUFF_EXIT=$?

echo ""
echo "2. Ruff format check (no changes)..."
uv run ruff format --check .
FORMAT_EXIT=$?

echo ""
echo "3. MyPy type checking (informational)..."
uv run mypy . || true

echo ""
if [ $RUFF_EXIT -eq 0 ] && [ $FORMAT_EXIT -eq 0 ]; then
    echo "✓ All checks passed!"
    exit 0
else
    echo "✗ Some checks failed. Run ./quality_fix.sh to auto-fix issues."
    exit 1
fi
