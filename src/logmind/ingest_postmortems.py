import glob
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter

from logmind.store import get_vectorstore


def ingest_postmortems(input_dir: str) -> int:
    """Chunk and embed every postmortem markdown file into the vector store.

    This is a plain sequential pass on purpose. The postmortem library is
    small by nature (a handful of documents written by humans after each
    incident), so there's nothing here that benefits from Spark the way
    the raw log analysis does.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    store = get_vectorstore()

    texts, metadatas, ids = [], [], []
    for path in glob.glob(os.path.join(input_dir, "*.md")):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        name = os.path.basename(path)
        for i, chunk in enumerate(splitter.split_text(content)):
            texts.append(chunk)
            metadatas.append({"source": name})
            ids.append(f"{name}::{i}")

    if texts:
        store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    return len(texts)
