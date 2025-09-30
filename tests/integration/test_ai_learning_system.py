"""Integration tests for the AI learning system."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.ai_service.application.services.ai_learning_service import AILearningService
from src.ai_service.core.config.settings import Settings
from src.ai_service.domain.entities.ai_training_data import (
    AITrainingData,
    FeedbackType,
    ProcessingStatus,
)
from src.ai_service.infrastructure.database.ai_training_repository import (
    MongoDBTrainingRepository,
)
from src.main import app


class TestAILearningSystemIntegration:
    """Integration tests for the complete AI learning system."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock(spec=Settings)
        settings.mongodb_url = "mongodb://localhost:27017"
        settings.mongodb_database = "test_ai_service"
        settings.use_llama = True
        settings.llama_base_url = "http://localhost:11434"
        return settings

    @pytest.fixture
    async def mock_training_repository(self):
        """Create mock training repository."""
        repo = AsyncMock(spec=MongoDBTrainingRepository)
        repo.save = AsyncMock()
        repo.find_by_id = AsyncMock()
        repo.get_category_mapping_insights = AsyncMock(
            return_value={
                "accommodation": "Travel",
                "hotel": "Travel",
                "restaurant": "Food & Dining",
            }
        )
        repo.get_accuracy_stats = AsyncMock(
            return_value={
                "total_cases": 100,
                "avg_accuracy": 0.85,
                "avg_confidence": 0.78,
                "success_rate": 0.92,
                "avg_processing_time": 1250.0,
            }
        )
        repo.count_by_status = AsyncMock(
            return_value={"success": 85, "failed_validation": 10, "pending_review": 5}
        )
        repo.get_common_error_patterns = AsyncMock(
            return_value=[
                {
                    "error_pattern": "Invalid currency format",
                    "count": 15,
                    "languages": ["th", "en"],
                },
                {"error_pattern": "Missing amount", "count": 8, "languages": ["en"]},
            ]
        )
        return repo

    @pytest.fixture
    async def ai_learning_service(self, mock_training_repository):
        """Create AI learning service with mocked dependencies."""
        return AILearningService(mock_training_repository)

    @pytest.mark.asyncio
    async def test_record_ai_interaction_success(
        self, ai_learning_service, mock_training_repository
    ):
        """Test recording successful AI interaction."""
        # Arrange
        input_text = "จองโรงแรมที่โอซาก้า 1 คืน 4000 บาท ด้วยบัตรเครดิต"
        language = "th"
        raw_response = (
            '{"amount": 4000, "currency": "THB", "category": "accommodation"}'
        )
        parsed_data = {"amount": 4000, "currency": "THB", "category": "accommodation"}
        confidence = 0.85
        processing_time = 1200

        # Act
        training_data = await ai_learning_service.record_ai_interaction(
            input_text=input_text,
            language=language,
            raw_ai_response=raw_response,
            parsed_ai_data=parsed_data,
            ai_confidence=confidence,
            processing_time_ms=processing_time,
            model_version="llama3.2:3b",
        )

        # Assert
        assert training_data.input_text == input_text
        assert training_data.language == language
        assert training_data.raw_ai_response == raw_response
        assert training_data.parsed_ai_data == parsed_data
        assert training_data.ai_confidence.value == confidence
        assert training_data.processing_time_ms == processing_time
        assert training_data.status == ProcessingStatus.SUCCESS
        mock_training_repository.save.assert_called_once_with(training_data)

    @pytest.mark.asyncio
    async def test_record_processing_failure(
        self, ai_learning_service, mock_training_repository
    ):
        """Test recording processing failure."""
        # Arrange
        input_text = "invalid spending text"
        language = "en"
        error_message = "Failed to parse spending data"
        validation_errors = ["Missing amount", "Invalid format"]

        # Act
        training_data = await ai_learning_service.record_processing_failure(
            input_text=input_text,
            language=language,
            error_message=error_message,
            raw_ai_response="",
            validation_errors=validation_errors,
        )

        # Assert
        assert training_data.input_text == input_text
        assert training_data.language == language
        assert training_data.status == ProcessingStatus.FAILED_VALIDATION
        assert training_data.error_message == error_message
        assert training_data.validation_errors == validation_errors
        mock_training_repository.save.assert_called_once_with(training_data)

    @pytest.mark.asyncio
    async def test_add_user_feedback(
        self, ai_learning_service, mock_training_repository
    ):
        """Test adding user feedback to training data."""
        # Arrange
        training_data_id = "test-training-id"
        corrected_data = {
            "category": "Travel",
            "amount": 4500.0,
            "merchant": "Osaka Hotel",
        }

        existing_training_data = AITrainingData(
            input_text="จองโรงแรมที่โอซาก้า 1 คืน 4000 บาท",
            language="th",
            parsed_ai_data={"category": "accommodation", "amount": 4000.0},
        )

        mock_training_repository.find_by_id.return_value = existing_training_data

        # Act
        success = await ai_learning_service.add_user_feedback(
            training_data_id=training_data_id,
            feedback_type=FeedbackType.USER_CORRECTION,
            corrected_data=corrected_data,
            admin_notes="User corrected category and amount",
        )

        # Assert
        assert success is True
        assert existing_training_data.feedback_provided is True
        assert existing_training_data.feedback_type == FeedbackType.USER_CORRECTION
        assert existing_training_data.corrected_data == corrected_data
        mock_training_repository.save.assert_called_once_with(existing_training_data)

    @pytest.mark.asyncio
    async def test_get_dynamic_category_mapping(
        self, ai_learning_service, mock_training_repository
    ):
        """Test getting dynamic category mappings."""
        # Act
        mappings = await ai_learning_service.get_dynamic_category_mapping()

        # Assert
        assert mappings == {
            "accommodation": "Travel",
            "hotel": "Travel",
            "restaurant": "Food & Dining",
        }
        mock_training_repository.get_category_mapping_insights.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_processing_insights(
        self, ai_learning_service, mock_training_repository
    ):
        """Test getting comprehensive processing insights."""
        # Act
        insights = await ai_learning_service.get_processing_insights()

        # Assert
        assert "overall_stats" in insights
        assert "status_distribution" in insights
        assert "common_errors" in insights
        assert "learned_category_mappings" in insights
        assert insights["overall_stats"]["avg_accuracy"] == 0.85
        assert insights["status_distribution"]["success"] == 85
        assert len(insights["common_errors"]) == 2

    @pytest.mark.asyncio
    async def test_get_improvement_suggestions(
        self, ai_learning_service, mock_training_repository
    ):
        """Test getting AI improvement suggestions."""
        # Arrange
        mock_training_repository.find_low_accuracy_cases.return_value = [
            AITrainingData(input_text="test1", language="en"),
            AITrainingData(input_text="test2", language="en"),
        ]
        mock_training_repository.find_failed_cases.return_value = [
            AITrainingData(input_text="test3", language="th")
        ]
        mock_training_repository.find_by_language.return_value = [
            AITrainingData(
                input_text="test4",
                language="th",
                status=ProcessingStatus.FAILED_VALIDATION,
            ),
            AITrainingData(
                input_text="test5", language="th", status=ProcessingStatus.SUCCESS
            ),
        ]

        # Act
        suggestions = await ai_learning_service.get_improvement_suggestions()

        # Assert
        assert len(suggestions) >= 2
        accuracy_suggestion = next(
            (s for s in suggestions if s["type"] == "accuracy_improvement"), None
        )
        error_suggestion = next(
            (s for s in suggestions if s["type"] == "error_reduction"), None
        )

        assert accuracy_suggestion is not None
        assert accuracy_suggestion["cases_count"] == 2
        assert error_suggestion is not None
        assert error_suggestion["cases_count"] == 1

    @pytest.mark.asyncio
    async def test_find_similar_successful_cases(
        self, ai_learning_service, mock_training_repository
    ):
        """Test finding similar successful cases."""
        # Arrange
        similar_cases = [
            AITrainingData(
                input_text="จองโรงแรม 3000 บาท",
                language="th",
                status=ProcessingStatus.SUCCESS,
            ),
            AITrainingData(
                input_text="โรงแรมในกรุงเทพ 2500 บาท",
                language="th",
                status=ProcessingStatus.SUCCESS,
            ),
        ]
        mock_training_repository.find_similar_inputs.return_value = similar_cases

        # Act
        result = await ai_learning_service.find_similar_successful_cases(
            "จองโรงแรมที่โอซาก้า 4000 บาท", "th"
        )

        # Assert
        assert len(result) == 2
        assert all(case.status == ProcessingStatus.SUCCESS for case in result)
        mock_training_repository.find_similar_inputs.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_data(
        self, ai_learning_service, mock_training_repository
    ):
        """Test cleaning up old training data."""
        # Arrange
        mock_training_repository.delete_old_data.return_value = 25

        # Act
        deleted_count = await ai_learning_service.cleanup_old_data(days_to_keep=180)

        # Assert
        assert deleted_count == 25
        mock_training_repository.delete_old_data.assert_called_once_with(180)

    @pytest.mark.asyncio
    async def test_confidence_calibration_report(
        self, ai_learning_service, mock_training_repository
    ):
        """Test getting confidence calibration report."""
        # Act
        report = await ai_learning_service.get_confidence_calibration_report()

        # Assert
        assert "average_confidence" in report
        assert "average_accuracy" in report
        assert "confidence_accuracy_gap" in report
        assert "recommendation" in report
        assert report["average_confidence"] == 0.78
        assert report["average_accuracy"] == 0.85


class TestAILearningAPIIntegration:
    """Integration tests for AI learning API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_ai_learning_service(self):
        """Mock AI learning service."""
        service = AsyncMock(spec=AILearningService)
        service.get_processing_insights.return_value = {
            "overall_stats": {
                "total_cases": 150,
                "avg_accuracy": 0.87,
                "avg_confidence": 0.82,
                "success_rate": 0.94,
                "avg_processing_time": 1100.0,
            },
            "status_distribution": {
                "success": 141,
                "failed_validation": 6,
                "pending_review": 3,
            },
            "common_errors": [
                {"error_pattern": "Invalid currency", "count": 4, "languages": ["th"]}
            ],
            "learned_category_mappings": {
                "accommodation": "Travel",
                "restaurant": "Food & Dining",
            },
            "total_mappings_learned": 2,
        }
        service.get_improvement_suggestions.return_value = [
            {
                "type": "accuracy_improvement",
                "priority": "medium",
                "description": "Found 3 cases with accuracy < 70%",
                "action": "Review and add feedback",
                "cases_count": 3,
            }
        ]
        service.add_user_feedback.return_value = True
        return service

    @patch("src.main.app.state")
    def test_get_ai_insights_endpoint(
        self, mock_app_state, client, mock_ai_learning_service
    ):
        """Test AI insights API endpoint."""
        # Arrange
        mock_app_state.ai_learning_service = mock_ai_learning_service

        # Act
        response = client.get("/api/v1/ai/insights")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "insights" in data
        assert data["insights"]["overall_stats"]["total_cases"] == 150
        assert data["insights"]["status_distribution"]["success"] == 141

    @patch("src.main.app.state")
    def test_get_improvement_suggestions_endpoint(
        self, mock_app_state, client, mock_ai_learning_service
    ):
        """Test improvement suggestions API endpoint."""
        # Arrange
        mock_app_state.ai_learning_service = mock_ai_learning_service

        # Act
        response = client.get("/api/v1/ai/suggestions")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "suggestions" in data
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["type"] == "accuracy_improvement"

    @patch("src.main.app.state")
    def test_add_feedback_endpoint(
        self, mock_app_state, client, mock_ai_learning_service
    ):
        """Test adding feedback via API endpoint."""
        # Arrange
        mock_app_state.ai_learning_service = mock_ai_learning_service
        feedback_data = {
            "training_data_id": "test-id-123",
            "corrected_data": {"category": "Travel", "amount": 4500.0},
            "feedback_type": "user_correction",
            "admin_notes": "User corrected the category",
        }

        # Act
        response = client.post("/api/v1/ai/feedback", json=feedback_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["training_data_id"] == "test-id-123"

    def test_ai_insights_service_unavailable(self, client):
        """Test AI insights endpoint when service is unavailable."""
        # Act
        response = client.get("/api/v1/ai/insights")

        # Assert
        assert response.status_code == 503
        data = response.json()
        assert "AI learning service not available" in data["detail"]


class TestEndToEndAILearningFlow:
    """End-to-end tests for the complete AI learning flow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_complete_ai_learning_flow(self, client):
        """Test the complete flow from text processing to feedback and learning."""
        with patch("src.main.app.state") as mock_app_state:
            # Mock all required services
            mock_llama_client = AsyncMock()
            mock_llama_client.parse_spending_text.return_value = {
                "amount": 4000.0,
                "currency": "THB",
                "merchant": "Osaka Hotel",
                "category": "accommodation",
                "payment_method": "Credit Card",
                "description": "Hotel booking in Osaka",
                "confidence": 0.85,
            }

            mock_spending_repository = AsyncMock()
            mock_spending_repository.save.return_value = None

            mock_ai_learning_service = AsyncMock()
            mock_ai_learning_service.record_ai_interaction.return_value = (
                AITrainingData(
                    input_text="จองโรงแรมที่โอซาก้า 1 คืน 4000 บาท ด้วยบัตรเครดิต",
                    language="th",
                )
            )
            mock_ai_learning_service.get_dynamic_category_mapping.return_value = {
                "accommodation": "Travel"
            }

            mock_app_state.llama_client = mock_llama_client
            mock_app_state.spending_repository = mock_spending_repository
            mock_app_state.ai_learning_service = mock_ai_learning_service

            # Step 1: Process text with AI
            text_data = {
                "text": "จองโรงแรมที่โอซาก้า 1 คืน 4000 บาท ด้วยบัตรเครดิต",
                "language": "th",
            }

            response = client.post("/api/v1/spending/process/text", json=text_data)
            assert response.status_code == 200

            process_data = response.json()
            assert process_data["status"] == "success"
            assert (
                process_data["parsed_data"]["category"] == "Travel"
            )  # Mapped category

            # Verify AI interaction was recorded
            mock_ai_learning_service.record_ai_interaction.assert_called_once()

            # Step 2: Simulate user providing feedback
            feedback_data = {
                "training_data_id": "test-training-id",
                "corrected_data": {
                    "category": "Travel",
                    "amount": 4200.0,  # User correction
                    "merchant": "Osaka Premium Hotel",
                },
                "feedback_type": "user_correction",
                "admin_notes": "User corrected amount and merchant name",
            }

            mock_ai_learning_service.add_user_feedback.return_value = True

            feedback_response = client.post("/api/v1/ai/feedback", json=feedback_data)
            assert feedback_response.status_code == 200

            feedback_result = feedback_response.json()
            assert feedback_result["status"] == "success"

            # Step 3: Verify insights are updated
            mock_ai_learning_service.get_processing_insights.return_value = {
                "overall_stats": {"total_cases": 1, "avg_accuracy": 0.85},
                "status_distribution": {"success": 1},
                "common_errors": [],
                "learned_category_mappings": {"accommodation": "Travel"},
                "total_mappings_learned": 1,
            }

            insights_response = client.get("/api/v1/ai/insights")
            assert insights_response.status_code == 200

            insights_data = insights_response.json()
            assert insights_data["status"] == "success"
            assert insights_data["insights"]["total_mappings_learned"] == 1

    @pytest.mark.asyncio
    async def test_ai_learning_with_processing_failure(self, client):
        """Test AI learning flow when processing fails."""
        with patch("src.main.app.state") as mock_app_state:
            # Mock services with failure scenario
            mock_llama_client = AsyncMock()
            mock_llama_client.parse_spending_text.side_effect = Exception(
                "AI parsing failed"
            )

            mock_ai_learning_service = AsyncMock()
            mock_ai_learning_service.record_processing_failure.return_value = (
                AITrainingData(
                    input_text="invalid text",
                    language="en",
                    status=ProcessingStatus.FAILED_VALIDATION,
                )
            )

            mock_app_state.llama_client = mock_llama_client
            mock_app_state.ai_learning_service = mock_ai_learning_service

            # Process invalid text
            text_data = {"text": "invalid spending text", "language": "en"}

            response = client.post("/api/v1/spending/process/text", json=text_data)

            # Should still return 200 but with fallback processing
            assert response.status_code == 200

            # Verify failure was recorded for learning
            mock_ai_learning_service.record_processing_failure.assert_called_once()
