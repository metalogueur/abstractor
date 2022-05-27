"""
pdf_files.py

Module for handling .pdf files

TODO: create custom Exception classes.
"""

# Imports
from io import BytesIO
import logging
from pathlib import Path
import re
import warnings
from pdfminer.high_level import extract_pages, extract_text
import requests
import spacy

# Constants
BAD_OCR_PATTERN = r'\(cid\:[0-9]+\)|\x0c'
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_BASE_DIR = BASE_DIR / 'original_pdf'
OCR_BASE_DIR = BASE_DIR / 'ocr_text'
SUPPORTED_LANGUAGES = ['fr', 'en', 'es']


# Utility functions
# (See analyze function after PDFFile class definition.)
def is_valid_url(url: str) -> bool:
    """
    This function sends a HEAD request to a given URL and if it receives
    an 'ok' signal, it returns True.

    :param url:     The URL that needs validation.
    :type url:      str
    :return:        True or False
    """
    if not isinstance(url, str):
        raise TypeError("URL must be a valid string.")

    valid = False

    try:
        request = requests.head(url)
        if request.ok:
            valid = True
    except (requests.exceptions.MissingSchema, Exception) as e:
        msg = f"Could not validate URL : {e}"
        logging.warning(msg)
    finally:
        return valid


def download_file(url: str) -> tuple:
    """
    This function downloads a .pdf file from a website, saves it in memory and
    returns a success flag and the binary object as a tuple.

    :param url:                 The URL to get the .pdf file.
    :type url:                  str
    :return:                    (Success flag, BytesIO object)
    """
    if not is_valid_url(url):
        raise ValueError("Invalid URL.")

    success = False
    binary_object = BytesIO()

    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            bytes_object = b''
            for chunk in response.iter_content(chunk_size=1024):
                bytes_object += chunk
        success = True
        binary_object = BytesIO(bytes_object)
    except (requests.RequestException, Exception) as e:
        msg = f"Could not download file at {url} because of {e}."
        logging.warning(msg)
    finally:
        return success, binary_object


def get_page_count(binary_object: BytesIO) -> int:
    """
    This function extracts the pages from a binary representation of a .pdf
    file, counts the number of pages and returns the count.

    :param binary_object:   The binary object representing the .pdf file.
    :type binary_object:    BytesIO
    :return:                The file's page count.
    """
    if not isinstance(binary_object, BytesIO):
        msg = f"Expecting BytesIO object. Got {type(binary_object)} instead."
        raise TypeError(msg)

    document = extract_pages(binary_object)
    counter = 0
    for page in document:
        counter += 1

    return counter


def extract_ocr(binary_object: BytesIO) -> tuple:
    """
    This function extracts text from a binary representation of a .pdf file,
    sanitizes the text and returns the cleaned text with an 'OCR quality'
    metric.

    :param binary_object:   The binary object representing the .pdf file.
    :type binary_object:    BytesIO
    :return:                (The sanitized text, the OCR quality metric)
    """
    if not isinstance(binary_object, BytesIO):
        msg = f"Expecting BytesIO object. Got {type(binary_object)} instead."
        raise TypeError(msg)

    sanitized_text = ''
    ocr_quality = 0.0

    try:
        raw_text = extract_text(binary_object)
        no_extra_spaces_text = re.subn(r'( )+', ' ', raw_text)[0]
        sanitized_text = re.subn(BAD_OCR_PATTERN, '', no_extra_spaces_text)[0]
        ocr_quality = len(sanitized_text) / len(no_extra_spaces_text)
    except Exception as e:
        msg = f"pdfminer could not extract OCR due to {e}"
        logging.warning(msg)
    finally:
        return sanitized_text, ocr_quality


def get_token_count(text: str, language: str) -> int:
    """
    This function parses text using spacy and returns the number of tokens it
    contains.

    :param text:            The text that will be parsed.
    :type text:             str
    :param language:        The text's language, abbreviated.
    :type language:         str
    :return:                The number of tokens.
    """
    if not isinstance(text, str) or not isinstance(language, str):
        raise TypeError("text and language must be strings.")

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("language is not supported for parsing.")

    model = '_core_news_sm'
    if language == 'en':
        model = 'en_core_web_sm'
    else:
        model = language + model

    nlp_model = spacy.load(model)
    doc = nlp_model(text)

    return len(doc)


# Classes
class PDFFile:
    """
    This class is used to handle a .pdf file's container and content.
    """
    def __init__(self, url: str, pdf_file_name: str, txt_file_path: Path):
        """
        Class constructor.
        """
        self.url = url
        self.file_name = pdf_file_name
        self.buffered_file = BytesIO()
        self.txt_file_path = txt_file_path
        self.language = None
        self.ocr = None
        self.ocr_quality = 0.0
        self.pages = 0
        self.tokens = 0

    @property
    def url(self) -> str:
        """
        Returns the url property
        """
        return self.__url

    @url.setter
    def url(self, url: str):
        """
        Sets the object's URl property.

        :param url:     The URL of the .pdf file.
        :type url:      str
        """
        if not is_valid_url(url):
            raise ValueError("Invalid URL provided.")

        self.__url = url

    @property
    def file_name(self) -> str:
        """
        Returns the file_name property.
        """
        return self.__file_name

    @file_name.setter
    def file_name(self, name: str):
        """
        Sets the object's file_name property
        :param name:    The file's name with extension.
        :type name:     str
        """
        if not isinstance(name, str):
            raise TypeError("name must be a valid string.")

        if not name.lower().endswith('.pdf'):
            raise ValueError("file must be a .pdf file.")

        self.__file_name = name

    @property
    def txt_file_path(self) -> Path:
        """
        Returns the path to the OCR text file.
        """
        return self.__txt_file_path

    @txt_file_path.setter
    def txt_file_path(self, path_to_file: Path):
        """
        Sets the path to the OCR text file.

        :param path_to_file:    The path to the file.
        :type path_to_file:     Path
        """
        if not isinstance(path_to_file, Path):
            raise TypeError("path_to_file must be a valid Path.")

        self.__txt_file_path = path_to_file

    @classmethod
    def create_from_url(cls, url: str):
        """
        The method makes sure the URL sent is a valid URL and sets the URL and
        name object properties if it is.

        :param url:     The URL address of the .pdf file.
        :type url:      str
        """
        if not is_valid_url(url):
            raise ValueError("Invalid URL.")

        if not url.lower().endswith('.pdf'):
            raise ValueError("URL must point to a .pdf file.")

        url_parts = url.split('/')
        file_name = url_parts[-1]
        directory = url_parts[-2]
        txt_file = file_name.lower().replace('.pdf', '.txt')
        return cls(url, file_name, OCR_BASE_DIR / directory / txt_file)


def analyze(pdf_file: PDFFile) -> PDFFile:
    """
    Things that need to be done here:

    0. Download .pdf file into buffer. DONE!
    1. Count the pages. DONE!
    2. Extract text from .pdf file. DONE!
    3. Sanitize text: DONE!
      a) Strip unnecessary white spaces; DONE!
      b) Strip BAD_OCR_PATTERN from text; DONE!
      c) Calculate OCR quality. DONE!
    4. Count the number of word tokens in the text. DONE!
    5. Erase the buffer from memory. DONE!
    6. Save OCR to disk. DONE!
    """
    if not isinstance(pdf_file, PDFFile):
        msg = f"PDFFile object expected. {type(pdf_file)} received instead."
        raise TypeError(msg)

    if not pdf_file.language:
        raise AttributeError("Language attribute hasn't been assigned yet.")

    try:
        msg = f"Analyzing {pdf_file.file_name}..."
        logging.info(msg)
        success, pdf_file.buffered_file = download_file(pdf_file.url)
        if success:
            pdf_file.pages = get_page_count(pdf_file.buffered_file)
            pdf_file.ocr, pdf_file.ocr_quality = extract_ocr(pdf_file.buffered_file)
            language = pdf_file.language
            if language not in SUPPORTED_LANGUAGES:
                language = 'fr'
            pdf_file.tokens = get_token_count(pdf_file.ocr, language)
            pdf_file.buffered_file.close()
            pdf_file.buffered_file = None
            with open(pdf_file.txt_file_path, 'w', encoding='utf8') as f:
                f.write(pdf_file.ocr)
    except (TypeError, AttributeError, Exception) as e:
        msg = f"Could not analyze {pdf_file.file_name} because of {e}."
        logging.warning(msg)
    finally:
        return pdf_file
