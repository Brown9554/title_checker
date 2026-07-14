#!/bin/bash

cd ~/projects/title-checker
python3 -c "
from document_reader import read_document
from entity_extractor import extract_entities

filename = 'properties/3-Hawthorne/documents/book20119_p538_deed.pdf'
raw_text = read_document(filename)
entities = extract_entities(raw_text, filename)
import json
print(json.dumps(entities, indent=2))
"
