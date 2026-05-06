import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.suggestion_service import SuggestionService
from app.models.file_record import FileRecord
from app.models.rule import Rule
from app.services.rule_engine_service import RuleMatch

class TestSuggestionService:
    @patch("app.services.suggestion_service.RuleEngineService")
    @patch("app.services.suggestion_service.FileContentRepository")
    @patch("app.services.suggestion_service.SuggestionRepository")
    @patch("app.services.suggestion_service.FileRepository")
    def test_generate_suggestions_creates_records(self, mock_file_repo, mock_sug_repo, mock_content_repo, mock_rule_engine):
        svc = SuggestionService()

        # Setup mocks
        mock_file_repo_inst = MagicMock()
        mock_file_repo_inst.list_paginated.return_value = ([
            FileRecord(id=1, filename="test.pdf", current_path="D:/test.pdf", extension=".pdf")
        ], 1)
        svc.file_repo = mock_file_repo_inst

        mock_rule_engine_inst = MagicMock()
        mock_rule_engine_inst.match.return_value = RuleMatch(
            rule=Rule(name="PDF Rule", target_dir="Documents/PDF"),
            confidence=0.8,
            reason="Match"
        )
        mock_rule_engine_inst.build_target_path.return_value = Path("D:/Archive/Documents/PDF/test.pdf")
        svc.rule_engine = mock_rule_engine_inst

        mock_sug_repo_inst = MagicMock()
        svc.sug_repo = mock_sug_repo_inst

        mock_content_repo_inst = MagicMock()
        mock_content_repo_inst.get_by_file_id.return_value = None
        svc.content_repo = mock_content_repo_inst

        # Fake get_connection
        with patch("app.services.suggestion_service.get_connection") as mock_conn:
            created, skipped = svc.generate_suggestions("D:/Archive")

            assert created == 1
            assert skipped == 0
            mock_sug_repo_inst.create.assert_called_once()

            # Check suggestion arguments
            suggestion = mock_sug_repo_inst.create.call_args[0][0]
            assert suggestion.file_id == 1
            assert suggestion.target_path == str(Path("D:/Archive/Documents/PDF/test.pdf"))
            assert suggestion.confidence == 0.8
            assert suggestion.reason == "Match"
