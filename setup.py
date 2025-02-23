from setuptools import setup, find_packages
import globals

setup(
    name='arag',
    version=globals.VERSION,
    description='A CLI tool for creating, managing, and using .arag files',
    author='John Luke Melovich (jmelovich)',
    packages=find_packages(),  # Automatically includes all packages found
    py_modules=['arag', 'globals'],  # Top-level modules
    install_requires=[
        'apsw',     # Required for SQLite with custom VFS
        'numpy',    # Used in retrieval.py
        'openai'    # Dependency for OpenAI embeddings
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
