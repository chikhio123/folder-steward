from pathlib import Path

from app.services.suggestion_service import SuggestionService, ExtensionRule, KeywordRule
from app.models.file_record import FileRecord


class TestExtensionRule:
    def test_match_hit(self):
        rule = ExtensionRule([".pdf"], "Documents/PDF")
        file = FileRecord(extension=".pdf", filename="test.pdf")
        assert rule.match(file) == "Documents/PDF"

    def test_match_miss(self):
        rule = ExtensionRule([".pdf"], "Documents/PDF")
        file = FileRecord(extension=".png", filename="test.png")
        assert rule.match(file) is None

    def test_match_case_insensitive(self):
        rule = ExtensionRule([".PDF"], "Documents/PDF")
        file = FileRecord(extension=".pdf", filename="test.pdf")
        assert rule.match(file) == "Documents/PDF"

    def test_match_no_extension(self):
        rule = ExtensionRule([".pdf"], "Documents/PDF")
        file = FileRecord(extension=None, filename="test")
        assert rule.match(file) is None


class TestKeywordRule:
    def test_match_hit_chinese(self):
        rule = KeywordRule(["论文", "毕业"], "University/Thesis")
        file = FileRecord(filename="毕业论文终版.pdf", extension=".pdf")
        assert rule.match(file) == "University/Thesis"

    def test_match_hit_english(self):
        rule = KeywordRule(["thesis", "dissertation"], "University/Thesis")
        file = FileRecord(filename="my_thesis_final.pdf", extension=".pdf")
        assert rule.match(file) == "University/Thesis"

    def test_match_case_insensitive(self):
        rule = KeywordRule(["kant"], "Books/Philosophy")
        file = FileRecord(filename="Kant_CPR.pdf", extension=".pdf")
        assert rule.match(file) == "Books/Philosophy"

    def test_match_miss(self):
        rule = KeywordRule(["thesis"], "University/Thesis")
        file = FileRecord(filename="random.pdf", extension=".pdf")
        assert rule.match(file) is None


class TestSuggestionService:
    def test_build_target_keyword_over_extension(self, temp_dir):
        """Keyword rules should take priority over extension rules."""
        svc = SuggestionService()
        archive = temp_dir / "Archive"

        file = FileRecord(filename="Kant_CPR.pdf", extension=".pdf")

        target = svc._build_target(file, archive)

        # Should match "kant" keyword → Books/Philosophy, not Documents/PDF
        # On Windows paths use backslashes, so check for directory name
        parts = list(Path(target).parts)
        assert "Philosophy" in parts or "Philosophy" in str(target)

    def test_build_target_extension_fallback(self, temp_dir):
        svc = SuggestionService()
        archive = temp_dir / "Archive"

        file = FileRecord(filename="photo.png", extension=".png")

        target = svc._build_target(file, archive)

        assert "Images" in str(target)

    def test_build_target_default_others(self, temp_dir):
        svc = SuggestionService()
        archive = temp_dir / "Archive"

        file = FileRecord(filename="unknown.xyz", extension=".xyz")

        target = svc._build_target(file, archive)

        assert "Others" in str(target) and "xyz" in str(target)

    def test_build_target_no_extension(self, temp_dir):
        svc = SuggestionService()
        archive = temp_dir / "Archive"

        file = FileRecord(filename="README", extension=None)

        target = svc._build_target(file, archive)

        assert "Others" in str(target) and "NoExtension" in str(target)

    def test_build_target_pdf_to_documents(self, temp_dir):
        svc = SuggestionService()
        archive = temp_dir / "Archive"

        # "memo" doesn't match any keyword rule, so extension rule applies
        file = FileRecord(filename="memo.pdf", extension=".pdf")

        target = svc._build_target(file, archive)

        assert "Documents" in str(target) and "PDF" in str(target)

    def test_confidence_keyword_higher(self):
        svc = SuggestionService()

        kw_file = FileRecord(filename="毕业论文.docx", extension=".docx")
        ext_file = FileRecord(filename="notes.docx", extension=".docx")

        assert svc._calc_confidence(kw_file) > svc._calc_confidence(ext_file)
