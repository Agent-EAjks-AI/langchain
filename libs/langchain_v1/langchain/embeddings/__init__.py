"""**Embedding models**  are wrappers around embedding models
from different APIs and services.

**Embedding models** can be LLMs or not.

**Class hierarchy:**

.. code-block::

    Embeddings --> <name>Embeddings  # Examples: OpenAIEmbeddings, HuggingFaceEmbeddings
"""

from langchain.embeddings.base import init_embeddings
from langchain.embeddings.cache import CacheBackedEmbeddings

__all__ = [
    "CacheBackedEmbeddings",
    "init_embeddings",
]
