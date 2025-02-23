import argparse
import sys
import shlex
import os
import shutil
import zipfile
import tempfile
import json

from tools.corpus import corpify, clean
from tools.arag_ops import add, create, delete, listContents, package, unpackage
from tools.index import index
from tools.retrieval import query
from tools.helpers import is_packaged

import globals

def main():
    # Set up the main argument parser
    parser = argparse.ArgumentParser(description="CLI tool 'arag' for managing .arag files")
    subparsers = parser.add_subparsers(dest='subcommand', required=True, help="Available commands")

    # 'create' subcommand
    create_parser = subparsers.add_parser('create', help="Create a new .arag file")
    create_parser.add_argument('arag_name', help="Name of the .arag file to create")
    create_parser.add_argument('path', help="Directory path where the .arag file will be created")

    # 'content' subcommand
    content_parser = subparsers.add_parser('content', help="Manage content in the .arag file")
    content_subparsers = content_parser.add_subparsers(dest='content_subcommand', required=True, help="Content commands")

    # 'content add'
    add_parser = content_subparsers.add_parser('add', help="Add a file or directory to the .arag file")
    add_parser.add_argument('path', help="Path to a file or directory to add")
    add_parser.add_argument('--arag', help="Path to the .arag file")

    # 'content del'
    del_parser = content_subparsers.add_parser('del', help="Delete a file or directory from the .arag file")
    del_parser.add_argument('target', help="File or directory to delete, relative to .arag/content/")
    del_parser.add_argument('--arag', help="Path to the .arag file")

    # 'content ls'
    ls_parser = content_subparsers.add_parser('ls', help="List contents of the .arag file")
    ls_parser.add_argument('--arag', help="Path to the .arag file")

    # 'content clean'
    clean_parser = content_subparsers.add_parser('clean', help="Clean the content folder by removing files not in corpus.db")
    clean_parser.add_argument('--arag', help="Path to the .arag file")

    # 'content corpify'
    corpify_parser = content_subparsers.add_parser('corpify', help="Corpify the content in the .arag file")
    corpify_parser.add_argument('--arag', help="Path to the .arag file")
    corpify_parser.add_argument('--chunk-size', type=int, default=1024*32, help="Chunk size in bytes")
    corpify_parser.add_argument('--force', action='store_true', help="Force removal of existing corpus folder")
    corpify_parser.add_argument('-y', '--yes', action='store_true', help="Assume yes to all prompts")



    # 'open' subcommand
    open_parser = subparsers.add_parser('open', help="Open an .arag file and enter interactive mode")
    open_parser.add_argument('arag_path', help="Path to the .arag file to open")

    # 'index' subcommand
    index_parser = subparsers.add_parser('index', help="Generate the index in the .arag file")
    index_parser.add_argument('--arag', help="Path to the .arag file")
    index_parser.add_argument('--method', choices=['openai', 'local'], default='local', help="Embedding generation method")
    index_parser.add_argument('--model', help="Embedding model name")
    index_parser.add_argument('--api-key', help="OpenAI API key")
    index_parser.add_argument('--force', action='store_true', help="Force reindexing by removing existing embeddings")

    # 'query' subcommand
    query_parser = subparsers.add_parser('query', help="Vector query the corpus with a string")
    query_parser.add_argument('--arag', help="Path to the .arag file")
    query_parser.add_argument('--topk', type=int, default=1, help="Number of top results to return")
    query_parser.add_argument('--api-key', help="OpenAI API key (required if index uses 'openai' method)")
    query_parser.add_argument('query_string', help="The query string")

    # 'package' subcommand
    package_parser = subparsers.add_parser('package', help="Package an .arag directory into a .arag file")
    package_parser.add_argument('arag_path', nargs='?', help="Path to the .arag directory to package")

    # 'unpackage' subcommand
    unpackage_parser = subparsers.add_parser('unpackage', help="Unpackage a .arag file into a .arag directory")
    unpackage_parser.add_argument('arag_path', nargs='?', help="Path to the .arag file to unpackage")

    # Check if invoked with a single .arag file argument
    if len(sys.argv) == 2 and sys.argv[1].endswith('.arag') and os.path.isfile(sys.argv[1]):
        # Treat as 'open <file>' command
        args = argparse.Namespace(subcommand='open', arag_path=sys.argv[1])
    else:
        # Parse arguments normally
        if len(sys.argv) == 1:
            parser.print_help()
            return
        args = parser.parse_args()
    
    # Handle the 'open' subcommand to enter interactive mode
    if args.subcommand == 'open':
        arag_path = args.arag_path
        if os.path.isdir(arag_path) or os.path.isfile(arag_path):
            active_arag = arag_path
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
            print(f"Arag {arag_path} does not exist")
    else:
        # Handle standalone commands
        execute_command(args, active_arag=None)

def execute_command(args, active_arag=None):
    """Execute the parsed command, using the active .arag file if applicable."""
    if args.subcommand == 'content':
        content_subcommand = args.content_subcommand
        arag_path = args.arag if args.arag else active_arag
        if arag_path is None:
            print("Error: --arag is required or open an arag first")
            return
        if not (os.path.isdir(arag_path) or os.path.isfile(arag_path)):
            print(f"Arag {arag_path} does not exist")
            return
        if content_subcommand in ['add', 'del', 'corpify', 'clean']:
            if is_packaged(arag_path):
                print("Error: Modification is not supported for packaged .arag files")
                return
        if content_subcommand == 'add':
            add(arag_path, args.path)
        elif content_subcommand == 'del':
            delete(arag_path, args.target)
        elif content_subcommand == 'ls':
            listContents(arag_path)
        elif content_subcommand == 'clean':
            clean(arag_path)
        elif content_subcommand == 'corpify':
            options = {
                'chunk_size': args.chunk_size,
                'force': args.force,
                'yes': args.yes
            }
            corpify(arag_path, options)
    elif args.subcommand == 'create':
        if not os.path.isdir(args.path):
            print(f"Path {args.path} does not exist or is not a directory")
            return
        create(args.path, args.arag_name)
    elif args.subcommand == 'index':
        arag_path = args.arag if args.arag else active_arag
        if arag_path is None:
            print("Error: --arag is required or open an arag first")
            return
        if not (os.path.isdir(arag_path) or os.path.isfile(arag_path)):
            print(f"Arag {arag_path} does not exist")
            return
        if is_packaged(arag_path):
            print("Error: Modification is not supported for packaged .arag files")
            return
        options = {'method': args.method, 'model': args.model, 'api_key': args.api_key, 'force': args.force}
        index(arag_path, options)
    elif args.subcommand == 'query':
        arag_path = args.arag if args.arag else active_arag
        if arag_path is None:
            print("Error: --arag is required or open an arag first")
            return
        if not (os.path.isdir(arag_path) or os.path.isfile(arag_path)):
            print(f"Arag {arag_path} does not exist")
            return
        query(arag_path, args.query_string, args.topk, api_key=args.api_key)
    elif args.subcommand == 'package':
        # Use provided arag_path or active_arag if in interactive mode and it's a directory
        arag_path = args.arag_path if args.arag_path is not None else active_arag
        if arag_path is None:
            print("Error: arag_path is required, either pass it or open an arag first")
            return
        if not os.path.isdir(arag_path):
            print(f"{arag_path} is not a directory")
            return
        package(arag_path)
    elif args.subcommand == 'unpackage':
        arag_path = args.arag_path if args.arag_path is not None else active_arag
        if arag_path is None:
            print("Error: arag_path is required")
            return
        if not os.path.isfile(arag_path):
            print(f"{arag_path} is not a file")
            return
        unpackage(arag_path)
    elif args.subcommand == 'open':
        print("Already in interactive mode, use 'close' to exit")
    else:
        print("Unknown subcommand")

if __name__ == '__main__':
    main()