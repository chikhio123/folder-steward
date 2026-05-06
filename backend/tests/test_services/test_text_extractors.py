import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from app.services.text_extractors.txt_extractor import TxtExtractor
from app.services.text_extractors.pdf_extractor import PdfExtractor
from app.services.text_extractors.docx_extractor import DocxExtractor

def test_txt_extractor_utf8(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello, world!", encoding="utf-8")
    extractor = TxtExtractor()
    res = extractor.extract(f)
    assert res.text == "Hello, world!"
    assert not res.warnings

def test_txt_extractor_gbk(tmp_path):
    f = tmp_path / "test.txt"
    f.write_bytes("你好，世界！".encode("gbk"))
    extractor = TxtExtractor()
    res = extractor.extract(f)
    assert res.text == "你好，世界！"
    assert not res.warnings

def test_txt_extractor_truncation(tmp_path):
    f = tmp_path / "test.txt"
    # Write a file slightly larger than 1M characters
    content = "A" * 1_000_010
    f.write_text(content, encoding="utf-8")

    extractor = TxtExtractor()
    res = extractor.extract(f)
    assert len(res.text) == 1_000_000
    assert any("truncated" in w for w in res.warnings)

def test_txt_extractor_file_too_large(tmp_path, monkeypatch):
    f = tmp_path / "test.txt"
    f.write_text("A", encoding="utf-8")

    class FakeStat:
        st_size = 20 * 1024 * 1024 # 20MB

    monkeypatch.setattr(Path, "stat", lambda self: FakeStat())

    extractor = TxtExtractor()
    res = extractor.extract(f)
    assert res.text == ""
    assert any("too large" in w for w in res.warnings)

@patch("app.services.text_extractors.pdf_extractor.PdfReader")
def test_pdf_extractor_success(mock_reader_cls, tmp_path):
    f = tmp_path / "test.pdf"
    f.write_bytes(b"dummy")

    mock_reader = MagicMock()
    mock_reader.is_encrypted = False
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page 1 Content"
    mock_reader.pages = [mock_page]
    mock_reader_cls.return_value = mock_reader

    extractor = PdfExtractor()
    res = extractor.extract(f)
    assert res.text == "Page 1 Content"
    assert res.metadata.get("total_pages") == 1
    assert not res.warnings

@patch("app.services.text_extractors.pdf_extractor.PdfReader")
def test_pdf_extractor_encrypted(mock_reader_cls, tmp_path):
    f = tmp_path / "test.pdf"
    f.write_bytes(b"dummy")

    mock_reader = MagicMock()
    mock_reader.is_encrypted = True
    mock_reader_cls.return_value = mock_reader

    extractor = PdfExtractor()
    res = extractor.extract(f)
    assert res.text == ""
    assert any("encrypted" in w for w in res.warnings)

@patch("app.services.text_extractors.docx_extractor.docx.Document")
def test_docx_extractor_success(mock_doc_cls, tmp_path):
    f = tmp_path / "test.docx"
    f.write_bytes(b"dummy")

    mock_doc = MagicMock()
    mock_para = MagicMock()
    mock_para.text = "Docx Content"
    mock_doc.paragraphs = [mock_para]
    mock_doc.tables = []
    mock_doc_cls.return_value = mock_doc

    extractor = DocxExtractor()
    res = extractor.extract(f)
    assert res.text == "Docx Content"
    assert not res.warnings

@patch("app.services.text_extractors.docx_extractor.docx.Document")
def test_docx_extractor_early_break(mock_doc_cls, tmp_path):
    f = tmp_path / "test.docx"
    f.write_bytes(b"dummy")

    mock_doc = MagicMock()
    mock_para = MagicMock()
    # Create a string that exceeds 1M chars
    mock_para.text = "A" * 1_000_010
    mock_doc.paragraphs = [mock_para]
    mock_doc.tables = []
    mock_doc_cls.return_value = mock_doc

    extractor = DocxExtractor()
    res = extractor.extract(f)
    assert len(res.text) == 1_000_000
    assert any("truncated" in w for w in res.warnings)
