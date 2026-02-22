"""API endpoint tests for the RAG system

Tests the FastAPI endpoints without mounting static files to avoid
import issues in the test environment.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional
from unittest.mock import Mock, patch


# Define Pydantic models (mirroring app.py)
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None


class Source(BaseModel):
    """Source citation with optional link"""
    text: str
    link: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[Source]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


def create_test_app(mock_rag_system):
    """Create a test FastAPI app without static file mounting"""
    app = FastAPI(title="Course Materials RAG System - Test", root_path="")

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Store mock RAG system in app state
    app.state.rag_system = mock_rag_system

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            rag_system = app.state.rag_system

            # Create session if not provided
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()

            # Process query using RAG system
            answer, sources = rag_system.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            rag_system = app.state.rag_system
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}

    return app


@pytest.fixture
def test_app(mock_rag_system):
    """Create test app with mock RAG system"""
    return create_test_app(mock_rag_system)


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.mark.api
class TestQueryEndpoint:
    """Tests for /api/query endpoint"""

    def test_query_without_session_id(self, client, mock_rag_system):
        """Test query creates new session when session_id is not provided"""
        response = client.post(
            "/api/query",
            json={"query": "What is testing?"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["answer"] == "This is a test response from the AI."
        assert data["session_id"] == "test-session-123"
        assert len(data["sources"]) > 0

        # Verify RAG system methods were called
        mock_rag_system.session_manager.create_session.assert_called_once()
        mock_rag_system.query.assert_called_once_with("What is testing?", "test-session-123")

    def test_query_with_session_id(self, client, mock_rag_system):
        """Test query uses provided session_id"""
        response = client.post(
            "/api/query",
            json={
                "query": "Explain unit tests",
                "session_id": "existing-session-456"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should return the session_id that was provided in the request
        assert data["session_id"] == "existing-session-456"

        # Verify session manager was not called to create new session
        mock_rag_system.session_manager.create_session.assert_not_called()
        mock_rag_system.query.assert_called_once_with("Explain unit tests", "existing-session-456")

    def test_query_missing_required_field(self, client):
        """Test query endpoint rejects request without query field"""
        response = client.post(
            "/api/query",
            json={"session_id": "test-123"}
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_query_with_empty_string(self, client, mock_rag_system):
        """Test query with empty string is accepted (validation at service layer)"""
        response = client.post(
            "/api/query",
            json={"query": ""}
        )

        assert response.status_code == 200
        mock_rag_system.query.assert_called_once()

    def test_query_response_structure(self, client):
        """Test query response has correct structure"""
        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

        # Verify source structure
        if len(data["sources"]) > 0:
            source = data["sources"][0]
            assert "text" in source
            assert "link" in source

    def test_query_error_handling(self, client, mock_rag_system):
        """Test query endpoint handles errors gracefully"""
        # Make the query method raise an exception
        mock_rag_system.query.side_effect = Exception("Test error")

        response = client.post(
            "/api/query",
            json={"query": "Test query"}
        )

        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]

    def test_query_with_special_characters(self, client, mock_rag_system):
        """Test query handles special characters correctly"""
        special_query = "What is @testing? How do I use #fixtures & $mocks?"

        response = client.post(
            "/api/query",
            json={"query": special_query}
        )

        assert response.status_code == 200
        mock_rag_system.query.assert_called_once()
        call_args = mock_rag_system.query.call_args[0]
        assert special_query in call_args[0]


@pytest.mark.api
class TestCoursesEndpoint:
    """Tests for /api/courses endpoint"""

    def test_get_course_stats_success(self, client, mock_rag_system):
        """Test successful course statistics retrieval"""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 1
        assert len(data["course_titles"]) == 1
        assert "Test Course: Introduction to Testing" in data["course_titles"]

        # Verify RAG system method was called
        mock_rag_system.get_course_analytics.assert_called_once()

    def test_get_course_stats_response_structure(self, client):
        """Test course stats response has correct structure"""
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert all(isinstance(title, str) for title in data["course_titles"])

    def test_get_course_stats_empty_catalog(self, client, mock_rag_system):
        """Test course stats when no courses exist"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert data["total_courses"] == 0
        assert len(data["course_titles"]) == 0

    def test_get_course_stats_error_handling(self, client, mock_rag_system):
        """Test course stats endpoint handles errors gracefully"""
        mock_rag_system.get_course_analytics.side_effect = Exception("Database error")

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    def test_get_course_stats_multiple_courses(self, client, mock_rag_system):
        """Test course stats with multiple courses"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 3,
            "course_titles": [
                "Test Course: Introduction to Testing",
                "Advanced Testing: Patterns and Practices",
                "Testing in Production: Best Practices"
            ]
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert data["total_courses"] == 3
        assert len(data["course_titles"]) == 3


@pytest.mark.api
class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint returns healthy status"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.api
class TestCORSConfiguration:
    """Tests for CORS configuration"""

    def test_cors_headers_on_query(self, client, mock_rag_system):
        """Test CORS headers are present on query endpoint"""
        response = client.post(
            "/api/query",
            json={"query": "Test query"},
            headers={"Origin": "https://example.com"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_headers_on_courses(self, client):
        """Test CORS headers are present on courses endpoint"""
        response = client.get(
            "/api/courses",
            headers={"Origin": "https://example.com"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


@pytest.mark.api
class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_query_with_very_long_text(self, client, mock_rag_system):
        """Test query with very long text"""
        long_query = "What is testing? " * 1000  # Very long query

        response = client.post(
            "/api/query",
            json={"query": long_query}
        )

        assert response.status_code == 200
        mock_rag_system.query.assert_called_once()

    def test_query_with_unicode_characters(self, client, mock_rag_system):
        """Test query with Unicode characters"""
        unicode_query = "What is testing in 日本語? 测试 тестирование"

        response = client.post(
            "/api/query",
            json={"query": unicode_query}
        )

        assert response.status_code == 200
        mock_rag_system.query.assert_called_once()

    def test_malformed_json(self, client):
        """Test endpoint rejects malformed JSON"""
        response = client.post(
            "/api/query",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_query_with_null_session_id(self, client, mock_rag_system):
        """Test query explicitly passing null session_id"""
        response = client.post(
            "/api/query",
            json={
                "query": "Test query",
                "session_id": None
            }
        )

        assert response.status_code == 200
        # Should create new session when null is provided
        mock_rag_system.session_manager.create_session.assert_called_once()
