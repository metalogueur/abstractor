"""
test_pdf_files.py

Tests everything in the classes.pdf_files module.
"""

# Imports
from pathlib import Path
import pytest
import classes.pdf_files as pdf


class TestPDFFile:
    """
    Test suite for the PDFFile class
    """
    def test_create_from_url(self):
        invalid_url = 'https://www.exemple.com/gontrand.pdf'
        with pytest.raises(ValueError):
            pdf.PDFFile.create_from_url(invalid_url)
        not_pdf_url = 'https://www.hec.ca/biblio/'
        with pytest.raises(ValueError):
            pdf.PDFFile.create_from_url(not_pdf_url)
        valid_url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        file_name = valid_url.split('/')[-1]
        pdf_file = pdf.PDFFile.create_from_url(valid_url)
        directory = valid_url.split('/')[-2]
        txt_file = file_name.lower().replace('.pdf', '.txt')
        assert isinstance(pdf_file, pdf.PDFFile)
        assert pdf_file.url == valid_url
        assert pdf_file.pdf_file_path == pdf.PDF_BASE_DIR / directory / file_name
        assert pdf_file.txt_file_path == pdf.OCR_BASE_DIR / directory / txt_file

    def test_fail_utility_functions(self):
        with pytest.raises(TypeError):
            pdf.is_valid_url(42)

    def test_property_exceptions(self):
        invalid_url = 'https://www.exemple.com/gontrand.pdf'
        with pytest.raises(ValueError):
            pdf.PDFFile(invalid_url, Path('name.pdf'), Path('.'))
        valid_url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        with pytest.raises(TypeError):
            pdf.PDFFile(valid_url, 'invalid_name', Path('.'))
        with pytest.raises(TypeError):
            pdf.PDFFile(valid_url, Path('name.pdf'), 'memoires/name.pdf')
        with pytest.raises(ValueError):
            pdf.PDFFile(valid_url, Path('name.txt'), Path('.'))


class TestUtilityFunctions:
    """
    Test suite for the pdf_file module's utility functions.
    """
    def test_download_file(self):
        file_name = 'gontrand.pdf'
        path = Path(__file__).resolve().parent
        invalid_url = 'https://www.exemple.com/'
        valid_url = 'https://www.hec.ca/biblio/a-propos/Reglement-bibliotheque_2016.pdf'
        with pytest.raises(ValueError):
            pdf.download_file(invalid_url + file_name, path / file_name)
        with pytest.raises(TypeError):
            pdf.download_file(valid_url, file_name)
        success_flag, message = pdf.download_file(valid_url, path / file_name)
        assert success_flag
        assert message.startswith('File downloaded to')
        assert Path(path / file_name).exists()
        assert Path(path / file_name).is_file()


