"""Unit tests for RAGSystem orchestrator"""

import pytest
from unittest.mock import Mock, patch, call
from rag_system import RAGSystem


@pytest.mark.unit
class TestRAGSystemInitialization:
    """Tests for RAG system initialization"""

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.ToolManager')
    @patch('rag_system.CourseSearchTool')
    @patch('rag_system.CourseOutlineTool')
    def test_rag_system_initializes_all_components(
        self,
        mock_outline_tool,
        mock_search_tool,
        mock_tool_manager,
        mock_session_manager,
        mock_ai_generator,
        mock_vector_store,
        mock_document_processor,
        test_config
    ):
        """Test RAG system initializes all required components"""
        rag_system = RAGSystem(test_config)

        # Verify all components were initialized
        assert rag_system.document_processor is not None
        assert rag_system.vector_store is not None
        assert rag_system.ai_generator is not None
        assert rag_system.session_manager is not None
        assert rag_system.tool_manager is not None
        assert rag_system.search_tool is not None

        # Verify components were initialized with correct parameters
        mock_document_processor.assert_called_once_with(
            test_config.CHUNK_SIZE,
            test_config.CHUNK_OVERLAP
        )
        mock_vector_store.assert_called_once_with(
            test_config.CHROMA_PATH,
            test_config.EMBEDDING_MODEL,
            test_config.MAX_RESULTS
        )
        mock_ai_generator.assert_called_once_with(
            test_config.ANTHROPIC_API_KEY,
            test_config.ANTHROPIC_MODEL
        )
        mock_session_manager.assert_called_once_with(test_config.MAX_HISTORY)


@pytest.mark.unit
class TestRAGSystemQuery:
    """Tests for query processing"""

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.ToolManager')
    @patch('rag_system.CourseSearchTool')
    @patch('rag_system.CourseOutlineTool')
    def test_query_without_session_creates_no_session(
        self,
        mock_outline_tool,
        mock_search_tool,
        mock_tool_manager,
        mock_session_manager_cls,
        mock_ai_generator_cls,
        mock_vector_store,
        mock_document_processor,
        test_config
    ):
        """Test query without session_id works correctly"""
        # Setup mocks
        mock_ai = Mock()
        mock_ai.generate_response.return_value = "Test answer"
        mock_ai_generator_cls.return_value = mock_ai

        mock_session = Mock()
        mock_session.get_conversation_history.return_value = []
        mock_session_manager_cls.return_value = mock_session

        mock_tools = Mock()
        mock_tools.get_tool_definitions.return_value = []
        mock_tools.get_last_sources.return_value = []
        mock_tool_manager.return_value = mock_tools

        rag_system = RAGSystem(test_config)

        # Query without session
        answer, sources = rag_system.query("What is testing?")

        assert answer == "Test answer"
        assert sources == []

        # Verify AI generator was called
        mock_ai.generate_response.assert_called_once()

        # Verify session manager was NOT asked for history (no session_id)
        mock_session.get_conversation_history.assert_not_called()
        mock_session.add_exchange.assert_not_called()

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.ToolManager')
    @patch('rag_system.CourseSearchTool')
    @patch('rag_system.CourseOutlineTool')
    def test_query_with_session_uses_history(
        self,
        mock_outline_tool,
        mock_search_tool,
        mock_tool_manager,
        mock_session_manager_cls,
        mock_ai_generator_cls,
        mock_vector_store,
        mock_document_processor,
        test_config
    ):
        """Test query with session_id uses conversation history"""
        # Setup mocks
        mock_ai = Mock()
        mock_ai.generate_response.return_value = "Test answer with context"
        mock_ai_generator_cls.return_value = mock_ai

        mock_session = Mock()
        mock_history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        mock_session.get_conversation_history.return_value = mock_history
        mock_session_manager_cls.return_value = mock_session

        mock_tools = Mock()
        mock_tools.get_tool_definitions.return_value = []
        mock_tools.get_last_sources.return_value = [{"text": "Source 1", "link": "http://example.com"}]
        mock_tool_manager.return_value = mock_tools

        rag_system = RAGSystem(test_config)

        # Query with session
        answer, sources = rag_system.query("Follow-up question", session_id="test-session-123")

        assert answer == "Test answer with context"
        assert len(sources) == 1

        # Verify session history was retrieved
        mock_session.get_conversation_history.assert_called_once_with("test-session-123")

        # Verify conversation was updated
        mock_session.add_exchange.assert_called_once_with(
            "test-session-123",
            "Follow-up question",
            "Test answer with context"
        )

        # Verify AI generator received history
        call_args = mock_ai.generate_response.call_args
        assert call_args[1]["conversation_history"] == mock_history

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.ToolManager')
    @patch('rag_system.CourseSearchTool')
    @patch('rag_system.CourseOutlineTool')
    def test_query_resets_sources_after_retrieval(
        self,
        mock_outline_tool,
        mock_search_tool,
        mock_tool_manager,
        mock_session_manager_cls,
        mock_ai_generator_cls,
        mock_vector_store,
        mock_document_processor,
        test_config
    ):
        """Test that sources are reset after each query"""
        # Setup mocks
        mock_ai = Mock()
        mock_ai.generate_response.return_value = "Answer"
        mock_ai_generator_cls.return_value = mock_ai

        mock_session = Mock()
        mock_session_manager_cls.return_value = mock_session

        mock_tools = Mock()
        mock_tools.get_tool_definitions.return_value = []
        mock_tools.get_last_sources.return_value = [{"text": "Source", "link": "http://test.com"}]
        mock_tool_manager.return_value = mock_tools

        rag_system = RAGSystem(test_config)

        # Execute query
        rag_system.query("Test query")

        # Verify sources were retrieved and then reset
        mock_tools.get_last_sources.assert_called_once()
        mock_tools.reset_sources.assert_called_once()


@pytest.mark.unit
class TestRAGSystemDocumentOperations:
    """Tests for document ingestion operations"""

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.ToolManager')
    @patch('rag_system.CourseSearchTool')
    @patch('rag_system.CourseOutlineTool')
    def test_add_course_document_success(
        self,
        mock_outline_tool,
        mock_search_tool,
        mock_tool_manager,
        mock_session_manager,
        mock_ai_generator,
        mock_vector_store_cls,
        mock_document_processor_cls,
        test_config,
        sample_course,
        sample_course_chunks
    ):
        """Test successful course document addition"""
        # Setup mocks
        mock_processor = Mock()
        mock_processor.process_course_document.return_value = (sample_course, sample_course_chunks)
        mock_document_processor_cls.return_value = mock_processor

        mock_store = Mock()
        mock_vector_store_cls.return_value = mock_store

        rag_system = RAGSystem(test_config)

        # Add course document
        course, num_chunks = rag_system.add_course_document("/path/to/course.txt")

        assert course.title == sample_course.title
        assert num_chunks == len(sample_course_chunks)

        # Verify vector store operations
        mock_store.add_course_metadata.assert_called_once_with(sample_course)
        mock_store.add_course_content.assert_called_once_with(sample_course_chunks)

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.ToolManager')
    @patch('rag_system.CourseSearchTool')
    @patch('rag_system.CourseOutlineTool')
    def test_add_course_document_handles_errors(
        self,
        mock_outline_tool,
        mock_search_tool,
        mock_tool_manager,
        mock_session_manager,
        mock_ai_generator,
        mock_vector_store_cls,
        mock_document_processor_cls,
        test_config
    ):
        """Test error handling in course document addition"""
        # Setup mocks
        mock_processor = Mock()
        mock_processor.process_course_document.side_effect = Exception("Parse error")
        mock_document_processor_cls.return_value = mock_processor

        mock_store = Mock()
        mock_vector_store_cls.return_value = mock_store

        rag_system = RAGSystem(test_config)

        # Add course document (should handle error gracefully)
        course, num_chunks = rag_system.add_course_document("/path/to/bad_course.txt")

        assert course is None
        assert num_chunks == 0

        # Verify vector store was not called
        mock_store.add_course_metadata.assert_not_called()
        mock_store.add_course_content.assert_not_called()


@pytest.mark.unit
class TestRAGSystemAnalytics:
    """Tests for analytics and statistics"""

    @patch('rag_system.DocumentProcessor')
    @patch('rag_system.VectorStore')
    @patch('rag_system.AIGenerator')
    @patch('rag_system.SessionManager')
    @patch('rag_system.ToolManager')
    @patch('rag_system.CourseSearchTool')
    @patch('rag_system.CourseOutlineTool')
    def test_get_course_analytics(
        self,
        mock_outline_tool,
        mock_search_tool,
        mock_tool_manager,
        mock_session_manager,
        mock_ai_generator,
        mock_vector_store_cls,
        mock_document_processor,
        test_config
    ):
        """Test retrieving course analytics"""
        # Setup mocks
        mock_store = Mock()
        mock_store.get_course_count.return_value = 3
        mock_store.get_existing_course_titles.return_value = [
            "Course 1",
            "Course 2",
            "Course 3"
        ]
        mock_vector_store_cls.return_value = mock_store

        rag_system = RAGSystem(test_config)

        # Get analytics
        analytics = rag_system.get_course_analytics()

        assert analytics["total_courses"] == 3
        assert len(analytics["course_titles"]) == 3
        assert "Course 1" in analytics["course_titles"]

        # Verify vector store methods were called
        mock_store.get_course_count.assert_called_once()
        mock_store.get_existing_course_titles.assert_called_once()
