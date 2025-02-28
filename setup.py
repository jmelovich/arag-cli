from setuptools import setup

# Read README.md for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='arag',
    version='0.1.0',  # Hardcoded version
    description='A CLI tool for creating, managing, and querying .arag files for RAG applications',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='John Luke Melovich',
    author_email='lmelovich@outlook.com',
    url='https://github.com/jmelovich/arag-cli',
    packages=['arag', 'arag.tools'],
    install_requires=[
        'apsw',     # Required for SQLite with custom VFS
        'numpy',    # Used in retrieval.py
        'openai',   # Dependency for OpenAI embeddings
        'pypdf',    # Required for PDF parsing
        'Spire.Doc' # Required for DOCX parsing
    ],
    extras_require={
        'local_embeddings': ['sentence-transformers']  # Optional dependency
    },
    entry_points={
        'console_scripts': [
            'arag=arag:main',  # Creates the 'arag' command
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: General',
    ],
    python_requires='>=3.10',
)
