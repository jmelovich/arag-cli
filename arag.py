import argparse
import sys
import shlex
import os
import shutil

# Define the content subdirectory globally
CONTENT_SUBDIR = 'content'
INDEX_SUBDIR = 'index'

def main():
    # Set up the main argument parser
    parser = argparse.ArgumentParser(description="CLI tool 'arag' for managing .arag files")
    subparsers = parser.add_subparsers(dest='subcommand', required=True, help="Available commands")

    # 'create' subcommand
    create_parser = subparsers.add_parser('create', help="Create a new .arag file")
    create_parser.add_argument('arag_name', help="Name of the .arag file to create")
    create_parser.add_argument('path', help="Directory path where the .arag file will be created")

    # 'add' subcommand
    add_parser = subparsers.add_parser('add', help="Add a file or directory to an .arag file")
    add_parser.add_argument('path', help="Path to a file or directory to add")
    add_parser.add_argument('--arag', help="Path to the .arag file")

    # 'ls' subcommand
    ls_parser = subparsers.add_parser('ls', help="List contents of an .arag file")
    ls_parser.add_argument('--arag', help="Path to the .arag file")

    # 'open' subcommand
    open_parser = subparsers.add_parser('open', help="Open an .arag file and enter interactive mode")
    open_parser.add_argument('arag_path', help="Path to the .arag file to open")

    # 'del' subcommand
    del_parser = subparsers.add_parser('del', help="Delete a file or directory from an .arag file")
    del_parser.add_argument('target', help="File or directory to delete, relative to .arag/content/")
    del_parser.add_argument('--arag', help="Path to the .arag file")

    # 'index' subcommand
    index_parser = subparsers.add_parser('index', help="Generate the index in the .arag file")
    index_parser.add_argument('--arag', help="Path to the .arag file")

    # If no arguments are provided, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Parse the command-line arguments
    args = parser.parse_args()

    # Handle the 'open' subcommand to enter interactive mode
    if args.subcommand == 'open':
        if os.path.isdir(args.arag_path):
            active_arag = args.arag_path
            print(f"Opened arag {active_arag}")
            while True:
                try:
                    line = input("> ")
                    if line.strip().lower() == 'quit' or line.strip().lower() == 'close':
                        break
                    command_args = shlex.split(line)
                    if not command_args:
                        continue
                    try:
                        cmd_args = parser.parse_args(command_args)
                        execute_command(cmd_args, active_arag)
                    except SystemExit:
                        print("Invalid command")
                except KeyboardInterrupt:
                    print("\nExiting")
                    break
        else:
            print(f"Arag {args.arag_path} does not exist or is not a directory")
    else:
        # Handle standalone commands
        execute_command(args, active_arag=None)

def execute_command(args, active_arag=None):
    """Execute the parsed command, using the active .arag file if applicable."""
    if args.subcommand == 'create':
        if not os.path.isdir(args.path):
            print(f"Path {args.path} does not exist or is not a directory")
            return
        full_path = os.path.join(args.path, args.arag_name + '.arag')
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                print(f"Arag {args.arag_name}.arag already exists at {args.path}")
            else:
                print(f"A file {args.arag_name}.arag already exists at {args.path}, cannot create directory")
        else:
            os.makedirs(full_path)
            os.makedirs(os.path.join(full_path, CONTENT_SUBDIR))
            print(f"Created arag {args.arag_name}.arag at {args.path}")
    elif args.subcommand == 'add':
        arag_path = args.arag if args.arag else active_arag
        if arag_path is None:
            print("Error: --arag is required or open an arag first")
            return
        if not os.path.isdir(arag_path):
            print(f"Arag {arag_path} does not exist or is not a directory")
            return
        
        content_path = os.path.join(arag_path, CONTENT_SUBDIR)
        # Determine if input is a file or directory
        input_path = args.path  # Assume `args.path` holds either file or directory path

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
    elif args.subcommand == 'ls':
        arag_path = args.arag if args.arag else active_arag
        if arag_path is None:
            print("Error: --arag is required or open an arag first")
            return
        if not os.path.isdir(arag_path):
            print(f"Arag {arag_path} does not exist or is not a directory")
            return
        content_path = os.path.join(arag_path, CONTENT_SUBDIR)
        contents = os.listdir(content_path)
        print(f"Contents of arag {arag_path}:")
        for item in contents:
            print(item)
    elif args.subcommand == 'del':
        arag_path = args.arag if args.arag else active_arag
        if arag_path is None:
            print("Error: --arag is required or open an arag first")
            return
        if not os.path.isdir(arag_path):
            print(f"Arag {arag_path} does not exist or is not a directory")
            return
        content_path = os.path.join(arag_path, CONTENT_SUBDIR)
        target_path = os.path.join(content_path, args.target)
        abs_target_path = os.path.abspath(target_path)
        abs_content_path = os.path.abspath(content_path)
        if not abs_target_path.startswith(abs_content_path):
            print("Error: Target is outside the content folder")
            return
        if not os.path.exists(target_path):
            print(f"Target {args.target} does not exist in arag {arag_path}")
        elif os.path.isfile(target_path):
            os.remove(target_path)
            print(f"Deleted file {args.target} from arag {arag_path}")
        elif os.path.isdir(target_path):
            shutil.rmtree(target_path)
            print(f"Deleted directory {args.target} from arag {arag_path}")
        else:
            print(f"Target {args.target} is not a file or directory")
    elif args.subcommand == 'index':
        arag_path = args.arag if args.arag else active_arag
        if arag_path is None:
            print("Error: --arag is required or open an arag first")
            return
        if not os.path.isdir(arag_path):
            print(f"Arag {arag_path} does not exist or is not a directory")
            return
        content_path = os.path.join(arag_path, CONTENT_SUBDIR)
        contents = os.listdir(content_path)
        index_path = os.path.join(arag_path, 'index.txt')
        #placeholder for index, will use FAISS probably
        with open(index_path, 'w') as index_file:
            for item in contents:
                index_file.write(item + '\n')
        print(f"Generated index at {index_path}")
    elif args.subcommand == 'open':
        print("Already in interactive mode, use 'close' to exit")
    else:
        print("Unknown subcommand")

if __name__ == '__main__':
    main()