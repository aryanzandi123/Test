from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner import merge_payload_update, parse_json_output


def _base_payload():
    return {
        "ctx_json": {
            "main": "MAIN_PROTEIN",
            "interactors": [
                {
                    "primary": "InteractorA",
                    "functions": [
                        {
                            "function": "activates",
                            "interaction_direction": "main_to_primary",
                            "interaction_effect": "activates",
                        }
                    ],
                },
                {
                    "primary": "InteractorB",
                    "functions": [
                        {
                            "function": "inhibits",
                            "interaction_direction": "primary_to_main",
                            "interaction_effect": "inhibits",
                        }
                    ],
                },
            ],
        }
    }


def test_merge_payload_update_preserves_multiple_arrow_results():
    current_payload = _base_payload()

    arrow_result_a = '{"ctx_json":{"interactors":[{"primary":"InteractorA","arrow":"activates","direction":"main_to_primary","intent":"activation"}]}}'
    arrow_result_b = '{"ctx_json":{"interactors":[{"primary":"InteractorB","arrow":"inhibits","direction":"primary_to_main","intent":"repression"}]}}'

    update_a = parse_json_output(
        arrow_result_a,
        ["ctx_json"],
        previous_payload=deepcopy(current_payload),
    )
    update_b = parse_json_output(
        arrow_result_b,
        ["ctx_json"],
        previous_payload=deepcopy(current_payload),
    )

    merged = merge_payload_update(deepcopy(current_payload), update_a)
    merged = merge_payload_update(merged, update_b)

    interactors = {i["primary"]: i for i in merged["ctx_json"]["interactors"]}

    assert interactors["InteractorA"]["arrow"] == "activates"
    assert interactors["InteractorA"]["direction"] == "main_to_primary"
    assert interactors["InteractorA"]["intent"] == "activation"

    assert interactors["InteractorB"]["arrow"] == "inhibits"
    assert interactors["InteractorB"]["direction"] == "primary_to_main"
    assert interactors["InteractorB"]["intent"] == "repression"

    # Functions remain intact for both interactors
    assert any(fn.get("function") == "activates" for fn in interactors["InteractorA"].get("functions", []))
    assert any(fn.get("function") == "inhibits" for fn in interactors["InteractorB"].get("functions", []))
