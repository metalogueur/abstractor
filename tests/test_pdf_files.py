"""
test_pdf_files.py

Tests everything in the classes.pdf_files module.
"""

# Imports
from io import BytesIO
from pathlib import Path
from pdfminer.layout import LTImage
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

    def test_extract_content(self):
        with pytest.raises(TypeError):
            pdf.extract_content('not a buffer')
        url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        success, buffer = pdf.download_file(url)
        assert success
        text, images = pdf.extract_content(buffer)
        assert isinstance(text, list)
        assert isinstance(images, list)
        assert len(text) == len(images)
        assert len(text) == 5
        for element in text:
            assert isinstance(element, str)
        for element in images:
            assert isinstance(element, (list, type(None)))
        # TODO : find .pdf with images and continue test

    def test_sanitize_text(self):
        with pytest.raises(TypeError):
            pdf.sanitize_text(42)
        url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        success, buffer = pdf.download_file(url)
        assert success
        text, images = pdf.extract_content(buffer)
        first_page_text = text[0]
        assert isinstance(first_page_text, str)
        sanitized_first_page, page_ocr_quality = pdf.sanitize_text(first_page_text)
        assert isinstance(page_ocr_quality, float)
        assert (page_ocr_quality >= 0.0) & (page_ocr_quality <= 1.0)
        assert isinstance(sanitized_first_page, str)
        sanitized_document, ocr_quality = pdf.sanitize_text(text)
        assert (ocr_quality >= 0.0) & (ocr_quality <= 1.0)
        assert isinstance(sanitized_document, str)
        assert sanitized_document.startswith(sanitized_first_page)

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
        # TODO : find a text longer than 1M characters and do another test

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
        # old tests below : replace with new ones
        pdf_file = pdf.analyze(pdf_file)
        assert isinstance(pdf_file, pdf.PDFFile)
        assert pdf_file.pages == 5
        assert len(pdf_file.ocr) > 0
        assert pdf_file.ocr_quality > 0.0
        assert pdf_file.tokens > 0
        assert pdf_file.txt_file_path.exists()
        assert pdf_file.buffered_file is None

