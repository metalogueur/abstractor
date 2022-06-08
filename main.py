"""
main.py

Application's main script
"""

# Imports
from datetime import date
import logging
from decouple import config
from progress.bar import Bar
from sickle import Sickle
import spacy
from spacy.language import Language
from spacy_language_detection import LanguageDetector
from classes.dissertations import (Dissertation,
                                   DissertationList,
                                   DISSERTATION_NO_URL_MSG)
from classes.pdf_files import (PDFFile,
                               analyze,
                               PDF_INVALID_URL)

# Constants
REPOSITORY_URL = config('REPOSITORY_URL')


# Functions
def main():
    """
    Things that need to be done here:

    1. Fetch all dissertations from repository: DONE!
    2. Filter out dissertations that don't come from the Symphony ILS: DONE!
    3. Build a DataFrame containing all the dissertations' metadata: DONE!
    5. Fetch and save all .pdf files from the repository: DONE!
    4. For all documents:
       a) detect dissertation language based on its title: DONE!
       b) add the detected language to the DataFrame: DONE!
    6. Inspect OCR for all documents and add its quality to the DataFrame
    7. Extract OCR from documents:
       a) for those with good OCR, use pdfminer.six
       b) for those with bad OCR, use pytesseract
    8. Save OCR results in .txt files
    """

    set_logging()
    print("Hello, World!")

    dissertations = get_all_dissertations()
    print(f"Retrieved {len(dissertations)} in total...")

    start_date = date(2020, 1, 1)
    end_date = date(2020, 12, 31)
    dissertations.data = dissertations.data[
        (dissertations.data['publication_date'] >= start_date) &
        (dissertations.data['publication_date'] <= end_date)
    ]
    print(f"{len(dissertations)} kept...")

    dissertations = detect_dissertation_language(dissertations)
    dissertations = analyze_pdf_files(dissertations)

    print("Saving data in Excel...")
    dissertations.data.to_excel('data_2020.xlsx')
    print("Thank you! Goodnight!")


def get_all_dissertations() -> DissertationList:
    """
    This functions requests all dissertations from the repository and returns
    the list.
    :return:    The list of all dissertations.
    """
    print("Connecting to the repository...")
    sickle = Sickle(REPOSITORY_URL)

    print("Fetching all dissertations from repository...")
    records = sickle.ListRecords(metadataPrefix='oai_dc', set=config('OAI_SET'))

    dissertations = DissertationList()
    print("Creating dissertation list (could be long)...")
    for record in records:
        dissertation = Dissertation.create_from_record(record)
        dissertations.append(dissertation)
    print("Dissertation list created...")

    return dissertations


def detect_dissertation_language(dissertations: DissertationList) -> DissertationList:
    """
    This functions detects the dissertations' language based on their title and
    fills the dissertation list's data with appropriate stats.
    :param dissertations:   A dissertation list.
    :type dissertations:    DissertationList
    :return:                The updated DissertationList.
    """
    if not isinstance(dissertations, DissertationList):
        raise TypeError("dissertations must be a valid DissertationList.")

    if 'title' not in dissertations.data.columns:
        raise KeyError("Title column is missing in the dataframe.")

    def get_lang_detector(nlp, name):
        return LanguageDetector(seed=42)

    print("Adding language columns to dissertation list...")
    dissertations.add_column('language')
    dissertations.add_column('language_score')

    print("Starting language detector...")
    nlp_model = spacy.load('fr_core_news_sm')
    Language.factory('language_detector', func=get_lang_detector)
    nlp_model.add_pipe('language_detector', last=True)

    bar = Bar('Detecting language: ', max=len(dissertations))

    for index, data in dissertations:
        doc = nlp_model(data['title'])
        language = doc._.language
        dissertations.data.at[index, 'language'] = language['language']
        dissertations.data.at[index, 'language_score'] = language['score']
        bar.next()

    print("Language detected in all dissertations...")

    return dissertations


def analyze_pdf_files(dissertations: DissertationList) -> DissertationList:
    """
    This function runs the classes.pdf_files module's analyze() function in all
    pdf files listed in the dissertations list and returns a metrics-annotated
    dissertation list.
    :param dissertations:   The dissertations list that will be analyzed.
    :type dissertations:    DissertationList
    :return:                The annotated dissertation list.
    """
    if not isinstance(dissertations, DissertationList):
        msg = f"DissertationList object expected. {type(dissertations)} received instead."
        raise TypeError(msg)

    dissertations.add_column('pages')
    dissertations.add_column('token_count')
    dissertations.add_column('ocr_quality')
    dissertations.add_column('txt_file_name')

    print("Excluding invalid URLs from dissertations list...")
    d_copy = dissertations
    d_copy.data = d_copy.data[
        (d_copy.data['url'] != DISSERTATION_NO_URL_MSG) |
        (d_copy.data['url'] != PDF_INVALID_URL)
    ]

    print("Starting .pdf files' OCR analysis...")
    bar = Bar("Analyzing .pdfs", max=len(d_copy))
    for index, dissertation in d_copy:
        pdf_file = PDFFile.create_from_url(dissertation['url'])
        pdf_file.language = dissertation['language']
        pdf_file = analyze(pdf_file)
        dissertations.data.at[index, 'pages'] = pdf_file.pages
        dissertations.data.at[index, 'token_count'] = pdf_file.tokens
        dissertations.data.at[index, 'ocr_quality'] = pdf_file.ocr_quality
        dissertations.data.at[index, 'txt_file_name'] = pdf_file.txt_file_path.name
        bar.next()

    print(".pdf file OCR analysis finished...")
    return dissertations


def set_logging():
    """
    This utility function is there just so it can be called outside main()
    function.
    """
    msg_format = '[%(asctime)s - %(levelname)s] %(message)s'
    logging.basicConfig(filename='abstractor.log',
                        filemode='w',
                        encoding='utf8',
                        level=logging.INFO,
                        format=msg_format)


if __name__ == '__main__':
    main()
