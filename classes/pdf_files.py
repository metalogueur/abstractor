"""
pdf_files.py

Module for handling .pdf files

TODO: create a validate_path_to_pdf function.
"""

# Imports
from pathlib import Path
import re
import warnings
from pdfminer.high_level import extract_pages, extract_text
import requests
import spacy

# Constants
BAD_OCR_PATTERN = r'\(cid\:[0-9]+\)|\x0c'
BASE_DIR = Path(__file__).resolve().parent.parent
MINIMUM_LANGUAGE_SCORE = 0.714281
PDF_BASE_DIR = BASE_DIR / 'original_pdf'
OCR_BASE_DIR = BASE_DIR / 'ocr_text'
SUPPORTED_LANGUAGES = ['fr', 'en', 'es']


# Utility functions
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

    request = requests.head(url)
    if request.ok:
        return True
    return False


def download_file(url: str, destination_path: Path) -> tuple:
    """
    This function downloads a .pdf file from a website, saves it locally and
    returns an appropriate message.
    :param url:                 The URL to get the .pdf file.
    :type url:                  str
    :param destination_path:    The full path to the downloaded local file.
    :type destination_path:     Path
    :return:                    (True or False, and a message.)
    """
    if not is_valid_url(url):
        raise ValueError("Invalid URL.")

    if not isinstance(destination_path, Path):
        raise TypeError("destination_path must be a valid Path.")

    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
        return True, f"File downloaded to {destination_path}."

    except Exception as e:
        return False, f"Error downloading file : {e}"


def get_page_count(path_to_file: Path) -> int:
    """
    This function extracts the pages from a .pdf file, counts the number of
    pages and returns the count.

    :param path_to_file:    The full path to the .pdf file.
    :type path_to_file:     Path
    :return:                The file's page count.
    """
    if not isinstance(path_to_file, Path):
        raise TypeError("path_to_file must be a valid Path.")

    if not path_to_file.name.lower().endswith('.pdf'):
        raise ValueError("File must be a .pdf file.")

    document = extract_pages(path_to_file)
    counter = 0
    for page in document:
        counter += 1

    return counter


def extract_ocr(path_to_file: Path) -> tuple:
    """
    This function extracts text from a .pdf file, sanitizes the text and
    returns the cleaned text with an 'OCR quality' metric.
    :param path_to_file:    The path to the .pdf file.
    :type path_to_file:     Path
    :return:                (The sanitized text, the OCR quality metric)
    """
    if not isinstance(path_to_file, Path):
        raise TypeError("path_to_file must be a valid Path.")

    if not path_to_file.name.lower().endswith('.pdf'):
        raise ValueError("File must be a .pdf file.")

    sanitized_text = ''
    ocr_quality = 0.0

    try:
        raw_text = extract_text(path_to_file)
        no_extra_spaces_text = re.subn(r'( )+', ' ', raw_text)[0]
        sanitized_text = re.subn(BAD_OCR_PATTERN, '', no_extra_spaces_text)[0]
        ocr_quality = len(no_extra_spaces_text) / len(sanitized_text)
    except Exception as e:
        msg = f"pdfminer could not extract OCR due to {e}"
        warnings.warn(msg)
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
    def __init__(self, url: str,
                 pdf_file_path: Path,
                 txt_file_path: Path):
        """
        Class constructor.
        """
        self.url = url
        self.pdf_file_path = pdf_file_path
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
    def pdf_file_path(self) -> Path:
        """
        Returns the file name.
        """
        return self.__pdf_file_path

    @pdf_file_path.setter
    def pdf_file_path(self, file_path: Path):
        """
        Sets the name property.

        :param file_path:    The .pdf file's full path.
        :type file_path:     Path
        """
        if not isinstance(file_path, Path):
            raise TypeError("file_path must be a valid Path.")

        if not file_path.name.lower().endswith('.pdf'):
            raise ValueError("File must be a .pdf file.")

        self.__pdf_file_path = file_path

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
        return cls(url,
                   PDF_BASE_DIR / directory / file_name,
                   OCR_BASE_DIR / directory / txt_file)

    def analyze(self):
        """
        Things that need to be done here:

        1. Count the pages. DONE!
        2. Extract text from .pdf file. DONE!
        3. Sanitize text: DONE!
          a) Strip unnecessary white spaces;
          b) Strip BAD_OCR_PATTERN from text;
          c) Calculate OCR quality.
        4. Count the number of word tokens in the text. DONE!
        """
        self.pages = get_page_count(self.pdf_file_path)
        self.ocr, self.ocr_quality = extract_ocr(self.pdf_file_path)
        self.tokens = get_token_count(self.ocr, self.language)

    def save_ocr(self):
        """
        This method saves the OCR text in a .txt file.
        """
        pass

    def delete_file(self):
        """
        This methods erases the
        :return:
        """
