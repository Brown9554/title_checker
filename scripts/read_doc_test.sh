#!/bin/bash
python3 -c "
from document_reader import read_document
result = read_document('properties/3-Hawthorne/documents/book20119_p538_deed.pdf')
print(result[:2000])
"
