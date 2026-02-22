# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval-Augmented Generation) chatbot system for querying course materials. Uses ChromaDB for vector storage, Anthropic's Claude API with tool calling for intelligent retrieval, and FastAPI for the backend.

## Development Commands

**IMPORTANT: This project uses `uv` as the package manager. Always use `uv` commands - never use `pip` directly.**

**Setup:**
```bash
uv sync                          # Install dependencies
cp .env.example .env            # Then add your ANTHROPIC_API_KEY
```

**Run Application:**
```bash
./run.sh                        # Quick start
# OR
cd backend && uv run uvicorn app:app --reload --port 8000
```

**Run Python Files:**
```bash
uv run python <filename>.py     # Always use uv run, not python directly
```

**Access:**
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Code Quality

**Tools:**
- `ruff` - Fast linter and formatter (replaces Black, isort, flake8)
- `mypy` - Static type checker

**Check Code Quality:**
```bash
./quality_check.sh           # Read-only checks (CI/review)
```

**Auto-Fix Issues:**
```bash
./quality_fix.sh             # Auto-format and fix linting
```

**Manual Commands:**
```bash
cd backend
uv run ruff check .          # Check for issues
uv run ruff check --fix .    # Auto-fix issues
uv run ruff format .         # Format code
uv run mypy .                # Type checking
```

## Architecture

### RAG Pipeline Flow

1. **Document Ingestion** (`document_processor.py`):
   - Parses structured course documents from `docs/` folder
   - Expected format: `Course Title:`, `Course Link:`, `Course Instructor:`, then `Lesson N:` markers
   - Chunks text using **sentence-based chunking** (800 chars, 100 char overlap)
   - Adds contextual prefixes: `"Course {title} Lesson {N} content: {chunk}"`
   - Creates `Course` objects (with lessons) and `CourseChunk` objects

2. **Vector Storage** (`vector_store.py`):
   - **Two ChromaDB collections**:
     - `course_catalog`: Course metadata (title, instructor, lessons as JSON)
     - `course_content`: Text chunks with embeddings
   - Uses `SentenceTransformer` embeddings (`all-MiniLM-L6-v2`)
   - Supports fuzzy course name matching via semantic search on catalog
   - Filters by `course_title` and/or `lesson_number`

3. **Query Processing** (`rag_system.py`):
   - Orchestrates: session management → AI generation → tool execution → response
   - Maintains conversation history (configurable in `config.py`)
   - Tool-based architecture: Claude decides when to search

4. **AI Generation** (`ai_generator.py`):
   - **Tool calling pattern**: Claude can invoke `search_course_content` tool
   - Two-step process:
     1. Initial API call with tools → Claude returns tool use request
     2. Execute tool → Send results back → Final response generation
   - System prompt optimized for educational content (brief, concise answers)

5. **Search Tools** (`search_tools.py`):
   - `CourseSearchTool`: Wraps vector store search
   - Parameters: `query` (required), `course_name` (optional), `lesson_number` (optional)
   - Formats results with course/lesson context headers
   - Tracks sources via `last_sources` for frontend display

### Key Patterns

**Document Processing:**
- Sentence-based chunking preserves semantic boundaries
- Overlap ensures context continuity between chunks
- Lesson prefixes help AI understand source attribution
- Course title used as unique ID (not auto-generated)

**Course Name Resolution:**
- Fuzzy matching: "MCP" → "MCP: Build Rich-Context AI Apps with Anthropic"
- Two-stage search: catalog lookup first, then content search with exact title
- Prevents duplicate courses on re-ingestion (checks existing titles)

**Session Management:**
- Sessions auto-created on first query without session_id
- History limited to `MAX_HISTORY * 2` messages (default: 2 exchanges = 4 messages)
- History injected into system prompt for context

**Tool Execution:**
- Tool manager registers tools and provides definitions to Claude
- Sources tracked separately from search results
- Sources reset after each query to avoid stale data

## Configuration (`config.py`)

**Key Settings:**
- `CHUNK_SIZE: 800` - Characters per chunk
- `CHUNK_OVERLAP: 100` - Overlap for context preservation
- `MAX_RESULTS: 5` - Vector search result limit
- `MAX_HISTORY: 2` - Conversation exchanges to retain
- `ANTHROPIC_MODEL: "claude-sonnet-4-20250514"`
- `EMBEDDING_MODEL: "all-MiniLM-L6-v2"`
- `CHROMA_PATH: "./chroma_db"` - Relative to backend directory

## Data Model

**Course Document Structure:**
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [title]
Lesson Link: [optional url]
[content...]

Lesson 1: [title]
[content...]
```

**Metadata Storage:**
- Lessons serialized as JSON in ChromaDB metadata (workaround for nested objects)
- Chunk IDs: `{course_title.replace(' ', '_')}_{chunk_index}`
- Course IDs: `{course.title}` (title is the primary key)

## Important Notes

**Startup Behavior:**
- `app.py` auto-loads documents from `../docs` on startup
- Uses `clear_existing=False` to avoid re-processing existing courses
- Logs show: `"Added new course: {title} ({N} chunks)"` or `"Course already exists: {title} - skipping"`

**ChromaDB Persistence:**
- Database persists in `backend/chroma_db/` directory
- To rebuild from scratch: delete `chroma_db/` folder or call `add_course_folder(clear_existing=True)`

**Frontend Integration:**
- Static files served from `frontend/` via FastAPI StaticFiles
- API expects: `{"query": str, "session_id": str | null}`
- API returns: `{"answer": str, "sources": list[str], "session_id": str}`
- Markdown rendering via `marked.js` library

**Package Management:**
- **CRITICAL**: Always use `uv` for ALL dependency management - never use `pip` directly
- To add dependencies: `uv add <package>`
- To remove dependencies: `uv remove <package>`
- To sync/install dependencies: `uv sync`
- To run commands: `uv run <command>`

**Python Version:**
- Requires Python 3.13+ (specified in `.python-version` and `pyproject.toml`)
- Uses `uv` as package manager (not pip/poetry)
