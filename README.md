# The Abstractor : OAI-PMH repository scraper and .pdf file text extractor

_[Work In Progress]_

This script/module stands on the shoulders of two other one-off scripts:
the [PDF OCR Inspector](https://github.com/metalogueur/pdf_ocr_inspector) and
the [Genizer](https://github.com/metalogueur/genizer).

Its main function is to scrape datasets from an OAI-PMH repository, download
.pdf files into memory, extract the OCR from the files and save the abstract
portion of the extracted text on disk in order to import it later on
into the repository.