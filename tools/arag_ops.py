import os
import shutil
import zipfile

import globals
from .helpers import get_files, is_packaged, get_file_from_arag

CONTENT_LIST = globals.CONTENT_LIST

def create(arag_path, arag_name):
    """
    Create a new .arag directory with the '-arag' suffix.
    
    Args:
        arag_path (str): Path to the parent directory.
        arag_name (str): Name of the new .arag directory.
    """
    # Define paths with '-arag' suffix
    full_path = os.path.join(arag_path, arag_name + '-arag')
    content_path = os.path.join(full_path, 'content')
    
    # Check if the directory already exists
    if os.path.exists(full_path):
        if os.path.isdir(full_path):
            print(f"Arag {arag_name}-arag already exists at {arag_path}")
        else:
            print(f"A file {arag_name}-arag already exists at {arag_path}, cannot create directory")
    else:
        os.makedirs(full_path)
        os.makedirs(content_path)
        print(f"Created arag {arag_name}-arag at {arag_path}")

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
    content_list = get_file_from_arag(arag_path, CONTENT_LIST).splitlines()
    print(f"Contents of arag {arag_path}:")
    for file in content_list:
        print(file.strip())

def package(arag_path):
    """
    Package the .arag directory into a .arag file, compressing only the 'content' folder.
    
    Args:
        arag_path (str): Path to the .arag directory.
    """
    if not os.path.isdir(arag_path):
        print(f"{arag_path} is not a directory")
        return
    # Replace '-arag' with '.arag' for the output file
    if arag_path.endswith('-arag'):
        output_path = arag_path[:-5] + '.arag'
    else:
        output_path = arag_path + '.arag'  # Fallback for unexpected naming
    if os.path.exists(output_path):
        print(f"Output path {output_path} already exists")
        return
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(arag_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, arag_path)
                if arcname.startswith('content/'):
                    # Compress files in 'content' folder
                    zipf.write(file_path, arcname)
                else:
                    # Store other files without compression
                    zipf.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
    print(f"Packaged {arag_path} to {output_path}")

def unpackage(packaged_arag_path):
    """
    Unpackage the .arag file into a directory with '-arag' suffix.
    
    Args:
        packaged_arag_path (str): Path to the packaged .arag file.
    """
    if not os.path.isfile(packaged_arag_path):
        print(f"{packaged_arag_path} is not a file")
        return
    # Replace '.arag' with '-arag' for the output directory
    if packaged_arag_path.endswith('.arag'):
        output_dir = packaged_arag_path[:-5] + '-arag'
    else:
        output_dir = packaged_arag_path + '-arag'  # Fallback for unexpected naming
    if os.path.exists(output_dir):
        print(f"Output directory {output_dir} already exists")
        return
    with zipfile.ZipFile(packaged_arag_path, 'r') as zipf:
        zipf.extractall(output_dir)
    print(f"Unpackaged {packaged_arag_path} to {output_dir}")