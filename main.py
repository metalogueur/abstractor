"""
main.py

Application's main script
"""

# Imports
from datetime import date
from decouple import config
from progress.bar import Bar
from sickle import Sickle
import spacy
from spacy.language import Language
from spacy_language_detection import LanguageDetector
from classes.dissertations import Dissertation, DissertationList

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

    print("Hello, World!")

    dissertations = get_all_dissertations()
    print(f"Retrieved {len(dissertations)} in total...")

    print("Filtering out dissertations not from Symphony ILS")
    limit_date = date(2001, 6, 1)
    dissertations.data = dissertations.data[
        dissertations.data['publication_date'] <= limit_date
    ]
    print(f"{len(dissertations)} kept...")

    dissertations = detect_dissertation_language(dissertations)


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

    return dissertations


if __name__ == '__main__':
    main()