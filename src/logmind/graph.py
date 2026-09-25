from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from logmind.config import GROQ_MODEL, require_groq_key
from logmind.log_analysis import run_analysis
from logmind.store import get_vectorstore

REPORT_PROMPT = ChatPromptTemplate.from_template(
    """You are helping an on-call engineer during an active incident.
Write a short incident summary from the information below. Cover: the
most likely cause, which service is affected, which past incidents (if
any) look similar and what fixed them, and two or three concrete next
steps. Be direct, this is being read during an active incident.

Incident description from the engineer:
{incident_description}

Top error signatures found in the logs (service, message, count):
{anomalies}

Similar past incidents:
{similar_incidents}

Incident summary:"""
)


class IncidentState(TypedDict):
    incident_description: str
    log_path: str
    top_n: int
    anomalies: list[dict]
    similar_incidents: list[str]
    report: str
    clarifying_question: str


def analyze_logs_node(state: IncidentState) -> dict:
    anomalies = run_analysis(state["log_path"], top_n=state.get("top_n", 5))
    return {"anomalies": anomalies}


def retrieve_similar_incidents_node(state: IncidentState) -> dict:
    if not state["anomalies"]:
        return {"similar_incidents": []}

    top = state["anomalies"][0]
    query = f"{state['incident_description']} {top['service']} {top['message']}"
    store = get_vectorstore()
    docs = store.similarity_search(query, k=3)
    return {"similar_incidents": [d.page_content for d in docs]}


def route_after_retrieval(state: IncidentState) -> str:
    if not state["anomalies"]:
        return "ask_clarification"
    return "synthesize_report"


def ask_clarification_node(state: IncidentState) -> dict:
    return {
        "clarifying_question": (
            "I didn't find any error spikes in that log file. Can you "
            "confirm the log file actually covers the incident window, "
            "or share a different one?"
        )
    }


def synthesize_report_node(state: IncidentState) -> dict:
    require_groq_key()
    llm = ChatGroq(model=GROQ_MODEL, temperature=0)
    chain = REPORT_PROMPT | llm

    anomalies_text = "\n".join(
        f"- {a['service']}: {a['message']} ({a['error_count']} occurrences)"
        for a in state["anomalies"]
    )
    similar_text = "\n\n".join(state["similar_incidents"]) or "none found"

    result = chain.invoke(
        {
            "incident_description": state["incident_description"],
            "anomalies": anomalies_text,
            "similar_incidents": similar_text,
        }
    )
    return {"report": result.content}


def build_graph():
    builder = StateGraph(IncidentState)
    builder.add_node("analyze_logs", analyze_logs_node)
    builder.add_node("retrieve_similar_incidents", retrieve_similar_incidents_node)
    builder.add_node("synthesize_report", synthesize_report_node)
    builder.add_node("ask_clarification", ask_clarification_node)

    builder.set_entry_point("analyze_logs")
    builder.add_edge("analyze_logs", "retrieve_similar_incidents")
    builder.add_conditional_edges(
        "retrieve_similar_incidents",
        route_after_retrieval,
        {
            "ask_clarification": "ask_clarification",
            "synthesize_report": "synthesize_report",
        },
    )
    builder.add_edge("ask_clarification", END)
    builder.add_edge("synthesize_report", END)

    return builder.compile()


def run(incident_description: str, log_path: str, top_n: int = 5) -> IncidentState:
    graph = build_graph()
    result = graph.invoke(
        {
            "incident_description": incident_description,
            "log_path": log_path,
            "top_n": top_n,
            "anomalies": [],
            "similar_incidents": [],
            "report": "",
            "clarifying_question": "",
        }
    )
    return result
