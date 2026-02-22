"""Shared test fixtures for RAG system tests"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import List, Dict, Any
import tempfile
import os

from models import Course, Lesson, CourseChunk
from config import Config


@pytest.fixture
def test_config():
    """Create a test configuration with temporary database path"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        config.CHROMA_PATH = os.path.join(tmpdir, "test_chroma_db")
        config.ANTHROPIC_API_KEY = "test-api-key-12345"
        config.CHUNK_SIZE = 800
        config.CHUNK_OVERLAP = 100
        config.MAX_RESULTS = 5
        config.MAX_HISTORY = 2
        yield config


@pytest.fixture
def sample_course():
    """Create a sample course with lessons"""
    return Course(
        title="Test Course: Introduction to Testing",
        course_link="https://example.com/test-course",
        instructor="Test Instructor",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Getting Started",
                lesson_link="https://example.com/test-course/lesson-0"
            ),
            Lesson(
                lesson_number=1,
                title="Writing Your First Test",
                lesson_link="https://example.com/test-course/lesson-1"
            ),
            Lesson(
                lesson_number=2,
                title="Advanced Testing Patterns",
                lesson_link="https://example.com/test-course/lesson-2"
            ),
        ]
    )


@pytest.fixture
def sample_course_chunks(sample_course):
    """Create sample course chunks for testing"""
    return [
        CourseChunk(
            content="This is the introduction to testing. Testing is important for software quality.",
            course_title=sample_course.title,
            lesson_number=0,
            chunk_index=0
        ),
        CourseChunk(
            content="In this lesson, we'll write our first unit test. Unit tests verify individual components.",
            course_title=sample_course.title,
            lesson_number=1,
            chunk_index=1
        ),
        CourseChunk(
            content="Advanced patterns include mocking, fixtures, and parameterized tests.",
            course_title=sample_course.title,
            lesson_number=2,
            chunk_index=2
        ),
    ]


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store"""
    mock_store = Mock()
    mock_store.search_courses.return_value = [
        {
            "content": "This is test content about testing frameworks.",
            "metadata": {
                "course_title": "Test Course: Introduction to Testing",
                "lesson_number": 0,
                "course_link": "https://example.com/test-course",
                "lesson_link": "https://example.com/test-course/lesson-0"
            }
        }
    ]
    mock_store.get_course_count.return_value = 1
    mock_store.get_existing_course_titles.return_value = ["Test Course: Introduction to Testing"]
    mock_store.add_course_metadata.return_value = None
    mock_store.add_course_content.return_value = None
    mock_store.clear_all_data.return_value = None
    return mock_store


@pytest.fixture
def mock_ai_generator():
    """Create a mock AI generator"""
    mock_gen = Mock()
    mock_gen.generate_response.return_value = "This is a test response from the AI."
    return mock_gen


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager"""
    mock_manager = Mock()
    mock_manager.create_session.return_value = "test-session-123"
    mock_manager.get_conversation_history.return_value = []
    mock_manager.add_exchange.return_value = None
    return mock_manager


@pytest.fixture
def mock_document_processor():
    """Create a mock document processor"""
    mock_processor = Mock()

    def process_document(file_path):
        course = Course(
            title="Test Course: Introduction to Testing",
            course_link="https://example.com/test-course",
            instructor="Test Instructor",
            lessons=[Lesson(lesson_number=0, title="Getting Started")]
        )
        chunks = [
            CourseChunk(
                content="Test content",
                course_title=course.title,
                lesson_number=0,
                chunk_index=0
            )
        ]
        return course, chunks

    mock_processor.process_course_document.side_effect = process_document
    return mock_processor


@pytest.fixture
def mock_tool_manager():
    """Create a mock tool manager"""
    mock_manager = Mock()
    mock_manager.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search for relevant course content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "course_name": {"type": "string", "description": "Optional course name filter"},
                    "lesson_number": {"type": "integer", "description": "Optional lesson number filter"}
                },
                "required": ["query"]
            }
        }
    ]
    mock_manager.get_last_sources.return_value = [
        {
            "text": "Test Course: Introduction to Testing - Lesson 0: Getting Started",
            "link": "https://example.com/test-course/lesson-0"
        }
    ]
    mock_manager.reset_sources.return_value = None
    mock_manager.execute_tool.return_value = "Search results: test content"
    return mock_manager


@pytest.fixture
def mock_rag_system(
    mock_vector_store,
    mock_ai_generator,
    mock_session_manager,
    mock_document_processor,
    mock_tool_manager
):
    """Create a mock RAG system with all dependencies"""
    mock_rag = Mock()
    mock_rag.vector_store = mock_vector_store
    mock_rag.ai_generator = mock_ai_generator
    mock_rag.session_manager = mock_session_manager
    mock_rag.document_processor = mock_document_processor
    mock_rag.tool_manager = mock_tool_manager

    # Mock the query method
    def query_side_effect(query, session_id=None):
        return (
            "This is a test response from the AI.",
            [
                {
                    "text": "Test Course: Introduction to Testing - Lesson 0: Getting Started",
                    "link": "https://example.com/test-course/lesson-0"
                }
            ]
        )
    mock_rag.query.side_effect = query_side_effect

    # Mock get_course_analytics
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 1,
        "course_titles": ["Test Course: Introduction to Testing"]
    }

    # Mock add_course_folder
    mock_rag.add_course_folder.return_value = (1, 3)

    return mock_rag


@pytest.fixture
def sample_query_response():
    """Sample API query response"""
    return {
        "answer": "This is a test response from the AI.",
        "sources": [
            {
                "text": "Test Course: Introduction to Testing - Lesson 0: Getting Started",
                "link": "https://example.com/test-course/lesson-0"
            }
        ],
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_course_stats():
    """Sample course statistics response"""
    return {
        "total_courses": 1,
        "course_titles": ["Test Course: Introduction to Testing"]
    }
