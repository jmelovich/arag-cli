# AutoRAG CLI Tool
This tool is being designed to facilitate the easy creation, moficiation, and use of a custom file type called '.arag'. These .arag files contain a document corpus with associated embedding vectors, with eventual plug-in-play compatibility (or easy to implement support) for use with RAG and LLMs.


## Installation

First, clone the repository to a folder of your choosing.

Then, install it with pip:

```pip install .``` (for using openai servers for embeddings only)

or 

```pip install '.[local_embeddings]'``` (to install sentence_transformers to make embeddings locally- recommended)
