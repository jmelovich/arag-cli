import json
import os
from .corpus import corpify
from .index import index
from .content import add
import zipfile

import globals

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

def create_spec(destination_path):
    default_spec = {
        "arag_name": "example",
        "arag_dest": "./example.arag",
        "content_include": [],
        "clean_content": True,
        "chunk_size": 8192,
        "index_method": "local",
        "index_model": "<default>",
        "api_key": "",
        "openai_endpoint": "https://api.openai.com/v1",
        "arag_version": globals.VERSION,
        "should_package": True
    }

    # if the destination path is a folder, append the default spec file name
    if os.path.isdir(destination_path):
        destination_path = os.path.join(destination_path, 'arag_spec.arag-json')
    # if destination_path ends with .json, change it to .arag-json
    elif destination_path.endswith('.json'):
        destination_path = destination_path[:-5] + '.arag-json'
    # if destination_path does not end with .arag-json, append .arag-json
    elif not destination_path.endswith('.arag-json'):
        destination_path += '.arag-json'

    with open(destination_path, 'w') as f:
        json.dump(default_spec, f, indent=4)
    print(f"Created template .arag-json spec file at {destination_path}")

def create_from_spec(spec_file):
    with open(spec_file, 'r') as f:
        spec = json.load(f)
    # Validate spec
    required_fields = ['arag_name', 'arag_dest', 'content_include', 'clean_content', 'chunk_size', 
                       'index_method', 'index_model', 'api_key', 'openai_endpoint', 'arag_version', 
                       'should_package']
    for field in required_fields:
        if field not in spec:
            print(f"Error: Missing field '{field}' in spec file")
            return
    arag_dest = spec['arag_dest']
    arag_name = spec['arag_name']
    dest_dir = os.path.dirname(arag_dest) if arag_dest else '.'
    arag_dir = os.path.join(dest_dir, arag_name + '-arag')
    if os.path.exists(arag_dir):
        print(f"Arag directory {arag_dir} already exists. Please remove it or choose a different name.")
        return
    create(dest_dir, arag_name)  # Creates arag_dir
    for path in spec['content_include']:
        add(arag_dir, path)
    options = {
        'chunk_size': spec['chunk_size'],
        'clean': spec['clean_content'],
        'force': True,
    }
    corpify(arag_dir, options)
    index_options = {
        'method': spec['index_method'],
        'model': spec['index_model'] if spec['index_model'] != '<default>' else None,
        'api_key': spec['api_key'],
        'endpoint': spec['openai_endpoint'],
        'force': True,
    }
    index(arag_dir, index_options)
    if spec['should_package']:
        package(arag_dir, dest_path=arag_dest)
    else:
        print(f"Arag directory created at {arag_dir}")



def package(arag_path, dest_path=None):
    """
    Package the .arag directory into a .arag file, compressing only the 'content' folder.
    
    Args:
        arag_path (str): Path to the .arag directory.
    """
    if not os.path.isdir(arag_path):
        print(f"{arag_path} is not a directory")
        return
    if dest_path is None:
        if arag_path.endswith('-arag'):
            output_path = arag_path[:-5] + '.arag'
        else:
            output_path = arag_path + '.arag'
    else:
        output_path = dest_path
    if os.path.exists(output_path):
        print(f"Output path {output_path} already exists")
        return
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(arag_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, arag_path)
                if arcname.startswith('content/'):
                    zipf.write(file_path, arcname)
                else:
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


