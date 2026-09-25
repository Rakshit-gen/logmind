import os

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
# chromadb pulls in onnxruntime even though we never use its default
# embedding function. onnxruntime's telemetry worker thread crashes on
# exit on macOS (SIGABRT from a mutex re-lock during interpreter
# shutdown) unless this is set before onnxruntime gets imported.
os.environ.setdefault("ORT_DISABLE_TELEMETRY_EVENTS", "1")

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from logmind.config import CHROMA_DIR, EMBEDDING_MODEL


def get_vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"})
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
