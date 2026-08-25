from fastapi.testclient import TestClient
from product.backend_api.app.main import app
from product.backend_api.app.services.agent_service import (
    classify_protected_action,
    get_agent_explanation,
)

client = TestClient(app)


def test_agents_explain_contract():
    response = client.post(
        "/api/agents/explain", json={"query": "Why was this model rejected?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert isinstance(data["explanation"], str)
    assert "evidence" in data
    assert isinstance(data["evidence"], list)
    assert "requires_human_review" in data
    assert isinstance(data["requires_human_review"], bool)


def test_rejection_question_is_grounded_in_real_evidence():
    data = get_agent_explanation("Why was this model rejected?")
    assert data["kind"] == "explanation"
    assert data["source"] == "REGISTERED_REFERENCE"
    # The demo ledger contains a real QUARANTINE verification packet.
    refs = [e["ref"] for e in data["evidence"]]
    labels = " ".join(e["label"] for e in data["evidence"])
    assert refs and all(ref for ref in refs)
    assert "QUARANTINE" in labels.upper()


def test_unsafe_promotion_request_is_blocked():
    data = get_agent_explanation("Promote the Load challenger.")
    assert data["kind"] == "blocked_action"
    assert data["authority"] == "Deterministic governance engine"
    assert data["recommended_next_step"] == "Request human review."
    assert data["requires_human_review"] is True


def test_policy_change_request_is_blocked():
    assert classify_protected_action("Change the governance threshold.")
    data = get_agent_explanation("Raise the promotion gate threshold.")
    assert data["kind"] == "blocked_action"


def test_final_test_retrieval_is_blocked():
    for query in (
        "Show me the final test results.",
        "Give me the holdout metrics.",
        "Open the test set.",
    ):
        data = get_agent_explanation(query)
        assert data["kind"] == "blocked_action", query
        assert data["action"] == "access_final_test"


def test_rollback_explanation_is_not_blocked():
    """DEMO 04: explaining a past rollback must remain allowed."""
    data = get_agent_explanation("Explain the rollback decision.")
    assert data["kind"] == "explanation"
    assert data["rule"] == "ROLLBACK_COMPLETED"
    assert len(data["evidence"]) > 0


def test_drift_question_reports_honest_empty_state():
    data = get_agent_explanation("Why did drift trigger investigation?")
    assert data["kind"] == "explanation"
    assert data["rule"] == "NO_DRIFT_EVIDENCE_RECORDED"
    assert data["evidence"] == []


def test_no_write_capabilities_exist_on_agent_module():
    """Guardrail regression: the agent surface exposes no lifecycle mutations."""
    from product.backend_api.app.services import agent_service as mod

    public = [n for n in dir(mod) if not n.startswith("_")]
    forbidden = [
        "promote",
        "rollback_model",
        "retrain",
        "quarantine",
        "approve_deployment",
        "deploy",
        "transition",
    ]
    for name in public:
        lowered = name.lower()
        for bad in forbidden:
            if bad in ("promote", "deploy"):
                assert not lowered.startswith(bad), name
            else:
                assert bad != name, name


def test_empty_query_returns_safe_response():
    data = get_agent_explanation("")
    assert data["rule"] == "NO_MATCHING_EVIDENCE"
