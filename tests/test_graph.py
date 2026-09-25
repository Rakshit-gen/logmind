from logmind.graph import route_after_retrieval


def test_routes_to_clarification_when_no_anomalies():
    state = {"anomalies": []}
    assert route_after_retrieval(state) == "ask_clarification"


def test_routes_to_synthesis_when_anomalies_found():
    state = {"anomalies": [{"service": "checkout-api", "message": "boom", "error_count": 5}]}
    assert route_after_retrieval(state) == "synthesize_report"
