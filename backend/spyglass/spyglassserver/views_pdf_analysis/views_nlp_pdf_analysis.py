import os
import spacy
import re
from dateutil.parser import *
import textract
import json

nlp = spacy.load('en_core_web_md')

pdf_path = '../../Data/research_paper/kumar2016.pdf'

def Clean_Text(file):
    text = textract.process(file, method='tesseract')
    text = text.decode('utf-8')
    text = text.replace("\r\n", " ")
    text = re.sub(" +", " ", text)
    return text

def Get_Tag_Position(tag, text, direction = 'forward'):
    tag = tag.lower()
    if direction == 'reverse':
        tag_pos = text.lower().rfind(tag)
    else:
        tag_pos = text.lower().find(tag)
        
    if tag_pos > 0:
        start_pos = tag_pos + len(tag) + 1
    else:
        start_pos = -1
    return start_pos

