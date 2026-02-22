"""Unit tests for Pydantic models"""

import pytest
from pydantic import ValidationError
from models import Lesson, Course, CourseChunk


@pytest.mark.unit
class TestLessonModel:
    """Tests for Lesson model"""

    def test_lesson_creation_with_all_fields(self):
        """Test creating a lesson with all fields"""
        lesson = Lesson(
            lesson_number=1,
            title="Introduction to Testing",
            lesson_link="https://example.com/lesson-1"
        )

        assert lesson.lesson_number == 1
        assert lesson.title == "Introduction to Testing"
        assert lesson.lesson_link == "https://example.com/lesson-1"

    def test_lesson_creation_without_optional_link(self):
        """Test creating a lesson without optional link"""
        lesson = Lesson(
            lesson_number=0,
            title="Getting Started"
        )

        assert lesson.lesson_number == 0
        assert lesson.title == "Getting Started"
        assert lesson.lesson_link is None

    def test_lesson_requires_lesson_number(self):
        """Test that lesson_number is required"""
        with pytest.raises(ValidationError) as exc_info:
            Lesson(title="Test Lesson")

        assert "lesson_number" in str(exc_info.value)

    def test_lesson_requires_title(self):
        """Test that title is required"""
        with pytest.raises(ValidationError) as exc_info:
            Lesson(lesson_number=1)

        assert "title" in str(exc_info.value)

    def test_lesson_number_type_validation(self):
        """Test that lesson_number must be an integer"""
        with pytest.raises(ValidationError):
            Lesson(lesson_number="not an int", title="Test")


@pytest.mark.unit
class TestCourseModel:
    """Tests for Course model"""

    def test_course_creation_with_all_fields(self):
        """Test creating a course with all fields"""
        lessons = [
            Lesson(lesson_number=0, title="Intro"),
            Lesson(lesson_number=1, title="Advanced")
        ]

        course = Course(
            title="Complete Testing Course",
            course_link="https://example.com/course",
            instructor="Jane Doe",
            lessons=lessons
        )

        assert course.title == "Complete Testing Course"
        assert course.course_link == "https://example.com/course"
        assert course.instructor == "Jane Doe"
        assert len(course.lessons) == 2

    def test_course_creation_with_minimal_fields(self):
        """Test creating a course with only required fields"""
        course = Course(title="Minimal Course")

        assert course.title == "Minimal Course"
        assert course.course_link is None
        assert course.instructor is None
        assert course.lessons == []

    def test_course_requires_title(self):
        """Test that title is required"""
        with pytest.raises(ValidationError) as exc_info:
            Course(instructor="John Doe")

        assert "title" in str(exc_info.value)

    def test_course_with_empty_lessons_list(self):
        """Test course can have empty lessons list"""
        course = Course(
            title="Course Without Lessons",
            lessons=[]
        )

        assert len(course.lessons) == 0

    def test_course_lessons_validation(self):
        """Test that lessons must be valid Lesson objects"""
        with pytest.raises(ValidationError):
            Course(
                title="Test Course",
                lessons=[{"not": "a lesson object"}]
            )


@pytest.mark.unit
class TestCourseChunkModel:
    """Tests for CourseChunk model"""

    def test_chunk_creation_with_all_fields(self):
        """Test creating a chunk with all fields"""
        chunk = CourseChunk(
            content="This is test content about unit testing.",
            course_title="Testing Course",
            lesson_number=1,
            chunk_index=0
        )

        assert chunk.content == "This is test content about unit testing."
        assert chunk.course_title == "Testing Course"
        assert chunk.lesson_number == 1
        assert chunk.chunk_index == 0

    def test_chunk_creation_without_lesson_number(self):
        """Test creating a chunk without lesson number"""
        chunk = CourseChunk(
            content="Generic course content",
            course_title="Test Course",
            chunk_index=5
        )

        assert chunk.content == "Generic course content"
        assert chunk.course_title == "Test Course"
        assert chunk.lesson_number is None
        assert chunk.chunk_index == 5

    def test_chunk_requires_content(self):
        """Test that content is required"""
        with pytest.raises(ValidationError) as exc_info:
            CourseChunk(
                course_title="Test Course",
                chunk_index=0
            )

        assert "content" in str(exc_info.value)

    def test_chunk_requires_course_title(self):
        """Test that course_title is required"""
        with pytest.raises(ValidationError) as exc_info:
            CourseChunk(
                content="Test content",
                chunk_index=0
            )

        assert "course_title" in str(exc_info.value)

    def test_chunk_requires_chunk_index(self):
        """Test that chunk_index is required"""
        with pytest.raises(ValidationError) as exc_info:
            CourseChunk(
                content="Test content",
                course_title="Test Course"
            )

        assert "chunk_index" in str(exc_info.value)

    def test_chunk_with_empty_content(self):
        """Test chunk can be created with empty string content"""
        chunk = CourseChunk(
            content="",
            course_title="Test Course",
            chunk_index=0
        )

        assert chunk.content == ""

    def test_chunk_index_type_validation(self):
        """Test that chunk_index must be an integer"""
        with pytest.raises(ValidationError):
            CourseChunk(
                content="Test",
                course_title="Course",
                chunk_index="not an int"
            )


@pytest.mark.unit
class TestModelIntegration:
    """Integration tests for models working together"""

    def test_course_with_multiple_lessons(self, sample_course):
        """Test course with multiple lessons"""
        assert len(sample_course.lessons) == 3
        assert sample_course.lessons[0].lesson_number == 0
        assert sample_course.lessons[1].lesson_number == 1
        assert sample_course.lessons[2].lesson_number == 2

    def test_chunks_for_course(self, sample_course, sample_course_chunks):
        """Test chunks associated with a course"""
        course_title = sample_course.title

        for chunk in sample_course_chunks:
            assert chunk.course_title == course_title

        # Verify chunk indices are sequential
        indices = [chunk.chunk_index for chunk in sample_course_chunks]
        assert indices == [0, 1, 2]

    def test_model_serialization(self, sample_course):
        """Test that models can be serialized to dict"""
        course_dict = sample_course.model_dump()

        assert "title" in course_dict
        assert "lessons" in course_dict
        assert isinstance(course_dict["lessons"], list)

        if len(course_dict["lessons"]) > 0:
            assert "lesson_number" in course_dict["lessons"][0]
            assert "title" in course_dict["lessons"][0]

    def test_model_json_serialization(self, sample_course):
        """Test that models can be serialized to JSON"""
        course_json = sample_course.model_dump_json()

        assert isinstance(course_json, str)
        assert sample_course.title in course_json

    def test_model_from_dict(self):
        """Test creating models from dictionaries"""
        course_dict = {
            "title": "Test Course",
            "course_link": "https://example.com",
            "instructor": "Test Instructor",
            "lessons": [
                {
                    "lesson_number": 0,
                    "title": "Introduction",
                    "lesson_link": "https://example.com/intro"
                }
            ]
        }

        course = Course(**course_dict)

        assert course.title == "Test Course"
        assert len(course.lessons) == 1
        assert course.lessons[0].title == "Introduction"
