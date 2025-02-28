import os
import shutil
import tempfile
import zipfile

from pypdf import PdfReader
from spire.doc import *
from spire.doc.common import *

def get_files(path):
    # Initialize the list of files
    files = []
    
    # Define the base path to which we want relative paths
    base_path = os.path.abspath(path)

    # Get the contents of the directory
    contents = os.listdir(path)
    
    # Loop through the contents
    for content in contents:
        # Get the full path of the content
        content_path = os.path.join(path, content)
        
        # If the content is a file, append its relative path
        if os.path.isfile(content_path):
            # Make sure both paths are absolute before using relpath
            content_path_absolute = os.path.abspath(content_path)
            relative_path = os.path.relpath(content_path_absolute, start=base_path)
            files.append(relative_path)
        
        # If the content is a directory, call the function recursively and aggregate results
        elif os.path.isdir(content_path):
            files.extend(
                [
                    os.path.join(content, file) 
                    for file in get_files(content_path)
                ]
            )
    
    # Return the list of files
    return files

def is_packaged(arag_path):
    return os.path.isfile(arag_path)

def get_file_from_arag(arag_path, filename):
    if is_packaged(arag_path):
        try:
            with zipfile.ZipFile(arag_path, 'r') as zipf:
                with zipf.open(filename) as f:
                    return f.read().decode('utf-8')
        except KeyError:
            return None  # File not found in packaged .arag
    else:
        file_path = os.path.join(arag_path, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        else:
            return None  # File not found in directory .arag

def get_corpus_db_temp(arag_path):
    if is_packaged(arag_path):
        with zipfile.ZipFile(arag_path, 'r') as zipf:
            with zipf.open('corpus.db') as src, tempfile.NamedTemporaryFile(delete=False) as dst:
                shutil.copyfileobj(src, dst)
                return dst.name
    else:
        return os.path.join(arag_path, 'corpus.db')
    

def processFileToText(file_path):
    # this will attempt to process non-UTF8 file types to text
    # such as PDF, DOCX, etc.

    # switch on the file type
    # if PDF, use PyMuPDF
    # if DOCX, use python-docx
    # else return None

    # get file type
    file_type = file_path.split('.')[-1]
    if file_type == 'pdf':
        # process PDF
        return processPDF(file_path)
    elif file_type == 'docx':
        # process DOCX
        return processDOCX(file_path)
    else:
        return None
    

def processPDF(file_path):
    # read the PDF file
    reader = PdfReader(file_path)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def processDOCX(file_path):
    # read the DOCX file
    doc = Document()
    doc.LoadFromFile(file_path)
    
    text = doc.GetText()
    doc.Close()
    return text
