import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from runner import merge_payloads

def _get_interactor(payload, name):
    for interactor in payload.get("ctx_json", {}).get("interactors", []):
        if interactor.get("primary") == name:
            return interactor
    raise AssertionError(f"Interactor {name} not found")


def test_parallel_arrow_merge_preserves_metadata():
    initial_payload = {
        "ctx_json": {
            "main": {"primary": "MAIN"},
            "interactors": [
                {
                    "primary": "InteractorA",
                    "functions": [{"function": "binds", "direction": "main_to_primary"}],
                },
                {
                    "primary": "InteractorB",
                    "functions": [{"function": "inhibits", "direction": "primary_to_main"}],
                },
            ],
        }
    }

    arrow_fragment_a = {
        "ctx_json": {
            "interactors": [
                {
                    "primary": "InteractorA",
                    "arrow": "activates",
                    "direction": "main_to_primary",
                    "arrows": {"main_to_primary": ["activates"]},
                    "intent": "activation",
                }
            ]
        }
    }

    arrow_fragment_b = {
        "ctx_json": {
            "interactors": [
                {
                    "primary": "InteractorB",
                    "arrow": "represses",
                    "direction": "primary_to_main",
                    "arrows": {"primary_to_main": ["represses"]},
                    "intent": "repression",
                }
            ]
        }
    }

    # Each parallel worker receives the same snapshot of the payload
    payload_update_a = merge_payloads(initial_payload, arrow_fragment_a)
    payload_update_b = merge_payloads(initial_payload, arrow_fragment_b)

    # Simulate the merge loop folding updates as they arrive
    combined = merge_payloads(initial_payload, payload_update_a)
    combined = merge_payloads(combined, payload_update_b)

    interactor_a = _get_interactor(combined, "InteractorA")
    interactor_b = _get_interactor(combined, "InteractorB")

    assert interactor_a["arrow"] == "activates"
    assert interactor_a["direction"] == "main_to_primary"
    assert interactor_a["arrows"] == {"main_to_primary": ["activates"]}

    assert interactor_b["arrow"] == "represses"
    assert interactor_b["direction"] == "primary_to_main"
    assert interactor_b["arrows"] == {"primary_to_main": ["represses"]}

    # The initial payload should remain unchanged by the merge helpers
    original_a = _get_interactor(initial_payload, "InteractorA")
    original_b = _get_interactor(initial_payload, "InteractorB")
    assert "arrow" not in original_a
    assert "arrow" not in original_b
