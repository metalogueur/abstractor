"""
test_pdf_files.py

Tests everything in the classes.pdf_files module.
"""

# Imports
from io import BytesIO
from pathlib import Path
import pytest
import classes.pdf_files as pdf


class TestPDFFile:
    """
    Test suite for the PDFFile class
    """
    def test_create_from_url(self):
        invalid_url = 'https://www.exemple.com/gontrand.pdf'
        invalid_url_pdf = pdf.PDFFile.create_from_url(invalid_url)
        assert invalid_url_pdf.url == pdf.PDF_INVALID_URL
        assert invalid_url_pdf.file_name == pdf.PDF_INVALID_FILE_NAME
        not_pdf_url = 'https://www.hec.ca/biblio/'
        not_pdf_pdf = pdf.PDFFile.create_from_url(not_pdf_url)
        assert not_pdf_pdf.url == pdf.PDF_INVALID_URL
        assert not_pdf_pdf.file_name == pdf.PDF_INVALID_FILE_NAME
        valid_url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        file_name = valid_url.split('/')[-1]
        pdf_file = pdf.PDFFile.create_from_url(valid_url)
        directory = valid_url.split('/')[-2]
        txt_file = file_name.lower().replace('.pdf', '.txt')
        assert isinstance(pdf_file, pdf.PDFFile)
        assert pdf_file.url == valid_url
        assert pdf_file.file_name == file_name
        assert pdf_file.txt_file_path == pdf.OCR_BASE_DIR / directory / txt_file

    def test_property_exceptions(self):
        valid_url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        with pytest.raises(TypeError):
            pdf.PDFFile(valid_url, Path('memoires/name.pdf'), Path('.'))
        with pytest.raises(TypeError):
            pdf.PDFFile(valid_url, 'name.pdf', 'memoires/name.pdf')
        with pytest.raises(ValueError):
            pdf.PDFFile(valid_url, 'name.txt', Path('.'))


class TestUtilityFunctions:
    """
    Test suite for the pdf_file module's utility functions.
    """
    def test_is_valid_url(self):
        with pytest.raises(TypeError):
            pdf.is_valid_url(42)

    def test_download_file(self):
        file_name = 'gontrand.pdf'
        invalid_url = 'https://www.exemple.com/'
        valid_url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        with pytest.raises(ValueError):
            pdf.download_file(invalid_url + file_name)
        success_flag, binary_object = pdf.download_file(valid_url)
        assert success_flag
        assert isinstance(binary_object, BytesIO)

    def test_get_page_count(self):
        url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        success, buffer = pdf.download_file(url)
        assert success
        page_count = pdf.get_page_count(buffer)
        assert page_count == 5
        with pytest.raises(TypeError):
            pdf.get_page_count('not a buffer')

    def test_extract_ocr(self):
        with pytest.raises(TypeError):
            pdf.extract_ocr('not a buffer')
        url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        success, buffer = pdf.download_file(url)
        assert success
        text, ocr_quality = pdf.extract_ocr(buffer)
        assert isinstance(text, str)
        assert len(text) > 0
        assert isinstance(ocr_quality, float)
        assert ocr_quality > 0.0

    def test_get_token_count(self):
        with pytest.raises(TypeError):
            pdf.get_token_count(42, 'fr')
        with pytest.raises(ValueError):
            pdf.get_token_count('Ich möchte ein kühles Bier.', 'de')
        token_count = pdf.get_token_count('I am a programmer.', 'en')
        assert isinstance(token_count, int)
        assert token_count == 5
        fr_token_count = pdf.get_token_count('Je suis un programmeur.', 'fr')
        assert token_count == 5

    def test_analyze(self):
        with pytest.raises(TypeError):
            pdf.analyze('not a file')
        url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        path_to_txt_file = Path(__file__).resolve().parent / 'test.txt'
        pdf_file = pdf.PDFFile.create_from_url(url)
        pdf_file.txt_file_path = path_to_txt_file
        with pytest.raises(AttributeError):
            pdf.analyze(pdf_file)
        pdf_file.language = 'fr'
        pdf_file = pdf.analyze(pdf_file)
        assert isinstance(pdf_file, pdf.PDFFile)
        assert pdf_file.pages == 5
        assert len(pdf_file.ocr) > 0
        assert pdf_file.ocr_quality > 0.0
        assert pdf_file.tokens > 0
        assert pdf_file.txt_file_path.exists()
        assert pdf_file.buffered_file is None

