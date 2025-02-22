import os

# function that takes in an absolute path and returns a list of all files in the directory and its subdirectories
# each item in the list should be the path to the file, relative to the .arag/content directory
# meaning if a file is at '/home/usr/lmelo/dev/testFile.arag/content/dir1/file1.txt', the path in the list should be 'dir1/file1.txt'
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
