from setuptools import setup, find_packages
import globals

setup(
    name='arag',
    version=globals.VERSION,
    description='A CLI tool for creating, managing, and a custom file type called .arag.',
    author='John Luke Melovich (jmelovich)',
    packages=find_packages(),  # Automatically includes all packages found
    py_modules=['arag', 'globals'],  # Top-level modules
    install_requires=[
        'apsw',     # Required for SQLite with custom VFS
        'numpy',    # Used in retrieval.py
        'openai',    # Dependency for OpenAI embeddings
        'pypdf',    # Required for PDF parsing
        'Spire.Doc'    # Required for DOCX parsing
    ],
    extras_require={
        'local_embeddings': ['sentence-transformers']  # Optional dependency
    },
    entry_points={
        'console_scripts': [
            'arag = arag:main',  # Creates the 'arag' command linked to arag.py's main()
        ],
    },
)
