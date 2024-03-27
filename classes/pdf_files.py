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
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTFigure, LTImage
from requests import Session
from requests.exceptions import RequestException
import spacy


# Constants
BAD_OCR_PATTERN = r'\(cid\:[0-9]+\)|\x0c'
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_BASE_DIR = BASE_DIR / 'original_pdf'
OCR_BASE_DIR = BASE_DIR / 'ocr_text'
PDF_INVALID_URL = 'Invalid URL provided'
PDF_INVALID_FILE_NAME = 'invalid_file.pdf'
SUPPORTED_LANGUAGES = ['fr', 'en', 'es']


# Classes
class MissingSessionException(TypeError):
    """
    This Exception is raised whenever someone tries to pass an object other
    than a requests.Session where one is needed.
    """

    def __init__(self, wrong_object):
        """
        Exception constructor

        :param wrong_object:    The invalid object passed as a session.
        :type wrong_object:     Any
        :param message:         The message returned from the Exception.
        :type message:          str
        """
        self.message = f"requests.Session object expected. Got " + \
            f"{type(wrong_object)} instead."
        super(MissingSessionException, self).__init__(self.message)


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
        if not isinstance(url, str):
            raise TypeError("url must be a valid string.")

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
    def create_from_url(cls, url: str, session: Session):
        """
        The method makes sure the URL sent is a valid URL and sets the URL,
        file_name and txt_file_name object properties if it is. If the URL or
        the file it points to are invalid, the method sends dummy values to
        the class constructor.

        :param url:         The URL address of the .pdf file.
        :type url:          str
        :param session:     A Requests session.
        :type session:      requests.Session
        """
        if not isinstance(session, Session):
            raise MissingSessionException(session)

        init_dir = OCR_BASE_DIR

        if not (is_valid_url(url, session) and url.lower().endswith('.pdf')):
            init_url = PDF_INVALID_URL
            init_file_name = PDF_INVALID_FILE_NAME
        else:
            init_url = url
            url_parts = url.split('/')
            init_file_name = url_parts[-1]
            init_dir = init_dir / url_parts[-2]

        txt_file = init_file_name.lower().replace('.pdf', '.txt')
        return cls(init_url, init_file_name, init_dir / txt_file)


# Utility functions
def is_valid_url(url: str, session: Session) -> bool:
    """
    This function sends a HEAD request to a given URL and if it receives
    an 'ok' signal, it returns True.

    :param url:         The URL that needs validation.
    :type url:          str
    :param session:     A Requests Session.
    :type session:      Session
    :return:            True or False
    """
    if not isinstance(url, str):
        raise TypeError("URL must be a valid string.")

    if not isinstance(session, Session):
        raise MissingSessionException(session)

    valid = False

    try:
        with session.head(url) as response:
            if response.ok:
                valid = True
    except (RequestException, Exception) as e:
        msg = f"Could not validate URL : {e}"
        logging.warning(msg)
    finally:
        return valid


def download_file(url: str, session: Session) -> tuple[bool, BytesIO]:
    """
    This function downloads a .pdf file from a website, saves it in memory and
    returns a success flag and the binary object as a tuple.

    :param url:         The URL to get the .pdf file.
    :type url:          str
    :param session:     A Requests Session.
    :type session:      requests.Session
    :return:            (Success flag, BytesIO object)
    """
    if not isinstance(session, Session):
        raise MissingSessionException(session)
    if not is_valid_url(url, session):
        raise ValueError(f"Invalid URL : {url}")

    success = False
    binary_object = BytesIO()

    try:
        with session.get(url, stream=True) as response:
            response.raise_for_status()
            bytes_object = b''
            for chunk in response.iter_content(chunk_size=1024):
                bytes_object += chunk
        success = True
        binary_object = BytesIO(bytes_object)
    except (RequestException, Exception) as e:
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
    for _ in document:
        counter += 1

    return counter


def extract_content(binary_object: BytesIO) -> tuple[list, list]:
    """
    This function extract all text and image contents from a .pdf file and
    returns a tuple of lists.
    :param binary_object:   The binary object representing the .pdf file.
    :type binary_object:    BytesIO
    :return:                ([Text content], [Images])
    """
    if not isinstance(binary_object, BytesIO):
        msg = f"Expecting BytesIO object. Got {type(binary_object)} instead."
        raise TypeError(msg)

    page_text = []
    page_images = []

    try:
        pages = extract_pages(binary_object)
        for page in pages:
            text = ''
            for element in page:
                if isinstance(element, LTTextContainer):
                    text += element.get_text()
                if isinstance(element, LTFigure):
                    for figure in element:
                        if isinstance(figure, LTImage):
                            page_images.append(figure)
            page_text.append(text)
    except Exception as e:
        msg = "pdfminer could not extract content because of {e}"
        logging.warning(msg)
    finally:
        return page_text, page_images


def sanitize_text(raw_text: str | list) -> tuple[str, float]:
    """
    This function strips text fetched from a .pdf file's OCR of its bad
    characters and extra white spaces and returns a tuple containing the
    sanitized text and an OCR quality metric based solely on the presence
    of bad characters.

    :param raw_text:    The text fetched from the .pdf file's OCR
    :type raw_text:     str | list
    :return:            (Sanitized text, OCR quality metric)
    """
    if not isinstance(raw_text, (str, list)):
        msg = f"raw_text must be string or list. {type(raw_text)} received."
        raise TypeError(msg)

    if isinstance(raw_text, list):
        text = '\n'.join(raw_text)
    else:
        text = raw_text

    no_extra_spaces_text = re.subn(r'( )+', ' ', text)[0]
    sanitized_text = re.subn(BAD_OCR_PATTERN, '', no_extra_spaces_text)[0]
    ocr_quality = len(sanitized_text) / len(no_extra_spaces_text)

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

    if len(text) > 1000000:
        msg = f"Text too long to parse and will be truncated to 1M characters."
        logging.warning(msg)
        text = text[:1000000]

    model = '_core_news_sm'
    if language == 'en':
        model = 'en_core_web_sm'
    else:
        model = language + model

    nlp_model = spacy.load(model)
    doc = nlp_model(text)

    return len(doc)


def analyze(pdf_file: PDFFile, session: Session) -> PDFFile:
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
    if not isinstance(session, Session):
        raise MissingSessionException(session)
    if not isinstance(pdf_file, PDFFile):
        msg = f"PDFFile object expected. {type(pdf_file)} received instead."
        raise TypeError(msg)
    if not pdf_file.language:
        raise AttributeError("Language attribute hasn't been assigned yet.")

    try:
        msg = f"Analyzing {pdf_file.file_name}..."
        logging.info(msg)
        success, pdf_file.buffered_file = download_file(pdf_file.url, session)
        if success:
            # new analysis starts here
            page_text, page_images = extract_content(pdf_file.buffered_file)
            pdf_file.pages = len(page_text)
            # Here, insert pytesseract
            pdf_file.ocr, pdf_file.ocr_quality = sanitize_text(page_text)
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
