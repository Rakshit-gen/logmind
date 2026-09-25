import os

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from logmind.config import CHROMA_DIR, EMBEDDING_MODEL


def get_vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"})
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
