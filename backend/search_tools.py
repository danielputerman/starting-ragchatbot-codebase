from abc import ABC, abstractmethod
from typing import Any

from vector_store import SearchResults, VectorStore


class Tool(ABC):
    """Abstract base class for all tools"""

    @abstractmethod
    def get_tool_definition(self) -> dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters"""
        pass


class CourseSearchTool(Tool):
    """Tool for searching course content with semantic course name matching"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # Track sources from last search

    def get_tool_definition(self) -> dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        return {
            "name": "search_course_content",
            "description": "Search course materials with smart course name matching and lesson filtering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in the course content",
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')",
                    },
                    "lesson_number": {
                        "type": "integer",
                        "description": "Specific lesson number to search within (e.g. 1, 2, 3)",
                    },
                },
                "required": ["query"],
            },
        }

    def execute(
        self, query: str, course_name: str | None = None, lesson_number: int | None = None
    ) -> str:
        """
        Execute the search tool with given parameters.

        Args:
            query: What to search for
            course_name: Optional course filter
            lesson_number: Optional lesson filter

        Returns:
            Formatted search results or error message
        """

        # Use the vector store's unified search interface
        results = self.store.search(
            query=query, course_name=course_name, lesson_number=lesson_number
        )

        # Handle errors
        if results.error:
            return results.error

        # Handle empty results
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."

        # Format and return results
        return self._format_results(results)

    def _format_results(self, results: SearchResults) -> str:
        """Format search results with course and lesson context"""
        formatted = []
        sources = []  # Track sources for the UI
        seen_sources = set()  # Deduplicate sources using (course_title, lesson_number) tuple

        for doc, meta in zip(results.documents, results.metadata, strict=True):
            course_title = meta.get("course_title", "unknown")
            lesson_num = meta.get("lesson_number")

            # Build context header
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"

            # Track source for the UI with deduplication
            source_key = (course_title, lesson_num)
            if source_key not in seen_sources:
                seen_sources.add(source_key)

                # Build source text
                source_text = course_title
                if lesson_num is not None:
                    source_text += f" - Lesson {lesson_num}"

                # Get lesson link if available
                lesson_link = None
                if lesson_num is not None:
                    lesson_link = self.store.get_lesson_link(course_title, lesson_num)

                # Create structured source object
                source_obj = {"text": source_text, "link": lesson_link}
                sources.append(source_obj)

            formatted.append(f"{header}\n{doc}")

        # Store sources for retrieval
        self.last_sources = sources

        return "\n\n".join(formatted)


class CourseOutlineTool(Tool):
    """Tool for retrieving complete course outline with lesson structure"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # Track sources for UI display

    def get_tool_definition(self) -> dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        return {
            "name": "get_course_outline",
            "description": "Get the complete structure and lesson list for a course. Use this when users ask about course contents, lessons, or course structure. Supports partial course name matching.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_name": {
                        "type": "string",
                        "description": "Course title or partial name (e.g., 'MCP', 'Computer Use', 'Anthropic')",
                    }
                },
                "required": ["course_name"],
            },
        }

    def execute(self, course_name: str) -> str:
        """
        Execute the outline tool with given course name.

        Args:
            course_name: Full or partial course name

        Returns:
            Formatted course outline or error message
        """
        # Reset sources
        self.last_sources = []

        # Resolve course name with fuzzy matching
        resolved_title = self.store._resolve_course_name(course_name)
        if not resolved_title:
            return f"No course found matching '{course_name}'. Please check the course name and try again."

        # Get course metadata
        all_courses = self.store.get_all_courses_metadata()
        course_metadata = None
        for course in all_courses:
            if course.get("title") == resolved_title:
                course_metadata = course
                break

        if not course_metadata:
            return f"Course '{resolved_title}' found but metadata unavailable."

        # Format and return outline
        formatted_outline = self._format_outline(course_metadata)

        # Track source for UI
        course_link = course_metadata.get("course_link")
        self.last_sources = [{"text": resolved_title, "link": course_link}]

        return formatted_outline

    def _format_outline(self, course_metadata: dict[str, Any]) -> str:
        """Format course metadata into readable outline"""
        lines = []

        # Course header
        title = course_metadata.get("title", "Unknown Course")
        lines.append(f"**Course Title: {title}**")

        # Instructor
        instructor = course_metadata.get("instructor")
        if instructor:
            lines.append(f"Instructor: {instructor}")

        # Course link
        course_link = course_metadata.get("course_link")
        if course_link:
            lines.append(f"Course Link: {course_link}")
        else:
            lines.append("Course Link: Not available")

        lines.append("")  # Blank line for spacing

        # Lessons section
        lessons = course_metadata.get("lessons", [])
        if not lessons:
            lines.append("**No lessons available for this course.**")
        else:
            lines.append(f"**Course Lessons:** ({len(lessons)} lessons)")
            for lesson in lessons:
                lesson_num = lesson.get("lesson_number")
                lesson_title = lesson.get("lesson_title", "Untitled")
                lesson_link = lesson.get("lesson_link")

                lesson_str = f"{lesson_num}. {lesson_title}"
                if lesson_link:
                    lesson_str += f" - {lesson_link}"

                lines.append(lesson_str)

        return "\n".join(lines)


class ToolManager:
    """Manages available tools for the AI"""

    def __init__(self):
        self.tools = {}

    def register_tool(self, tool: Tool):
        """Register any tool that implements the Tool interface"""
        tool_def = tool.get_tool_definition()
        tool_name = tool_def.get("name")
        if not tool_name:
            raise ValueError("Tool must have a 'name' in its definition")
        self.tools[tool_name] = tool

    def get_tool_definitions(self) -> list:
        """Get all tool definitions for Anthropic tool calling"""
        return [tool.get_tool_definition() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given parameters"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"

        return self.tools[tool_name].execute(**kwargs)

    def get_last_sources(self) -> list:
        """Get sources from the last search operation"""
        # Check all tools for last_sources attribute
        for tool in self.tools.values():
            if hasattr(tool, "last_sources") and tool.last_sources:
                return tool.last_sources
        return []

    def reset_sources(self):
        """Reset sources from all tools that track sources"""
        for tool in self.tools.values():
            if hasattr(tool, "last_sources"):
                tool.last_sources = []
