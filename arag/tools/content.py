import os
import shutil
import zipfile

import globals
from .helpers import get_files, get_file_from_arag

CONTENT_LIST = globals.CONTENT_LIST

def updateContentList(arag_path):
    """
    Refresh the content list file in the .arag directory.
    
    Args:
        arag_path (str): Path to the .arag directory.
    """
    
    # Define paths
    content_path = os.path.join(arag_path, 'content')
    content_list = os.path.join(arag_path, CONTENT_LIST)
    
    # Get the list of files in the content directory
    files = get_files(content_path)

    # Remove the existing content list file contents and write the new list
    with open(content_list, 'w') as list_file:
        for file in files:
            list_file.write(file + '\n')
            
    print(f"Updated content list in arag {arag_path}")     

def add(arag_path, input_path):
    """
    Add a file or directory to the .arag/content/ directory.
    
    Args:
        arag_path (str): Path to the .arag directory.
        input_path (str): Path to the file or directory to add.
    """
    
    # Define paths
    content_path = os.path.join(arag_path, 'content')
    
    # Determine if input is a file or directory
    if os.path.isfile(input_path):
        shutil.copy(input_path, content_path)
        print(f"Copied file {input_path} into arag {arag_path}")
    elif os.path.isdir(input_path):
        dest_dir = os.path.join(content_path, os.path.basename(input_path))
        if os.path.exists(dest_dir):
            print(f"Directory {os.path.basename(input_path)} already exists in arag {arag_path}")
        else:
            shutil.copytree(input_path, dest_dir)
            print(f"Copied directory {input_path} into arag {arag_path}")
    else:
        print(f"Error: {input_path} does not exist or is neither a file nor a directory")

    # Update the content list
    updateContentList(arag_path)  

def delete(arag_path, target):
    """
    Delete a file or directory from the .arag/content/ directory.
    
    Args:
        arag_path (str): Path to the .arag
        target (str): Name of the file or directory to delete.
    """
    
    # Define paths
    content_path = os.path.join(arag_path, 'content')
    target_path = os.path.join(content_path, target)
    
    # Check if target is within the content directory
    if not os.path.abspath(target_path).startswith(os.path.abspath(content_path)):
        print("Error: Target is outside the content folder")
        return
    
    # Check if target exists
    if not os.path.exists(target_path):
        print(f"Target {target} does not exist in arag {arag_path}")
    elif os.path.isfile(target_path):
        os.remove(target_path)
        print(f"Deleted file {target} from arag {arag_path}")
        updateContentList(arag_path)
    elif os.path.isdir(target_path):
        shutil.rmtree(target_path)
        print(f"Deleted directory {target} from arag {arag_path}")
        updateContentList(arag_path)
    else:
        print(f"Target {target} is not a file or directory")

def listContents(arag_path):
    """
    Recursively list the contents of the .arag/content/ directory.
    
    Args:
        arag_path (str): Path to the .arag directory or packaged file.
    """
    content_list_str = get_file_from_arag(arag_path, CONTENT_LIST)
    if content_list_str is None:
        print(f"Content list file {CONTENT_LIST} not found in arag {arag_path}")
        return
    content_list = content_list_str.splitlines()
    print(f"Contents of arag {arag_path}:")
    for file in content_list:
        print(file.strip())

