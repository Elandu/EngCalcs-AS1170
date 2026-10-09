"""Optional integration checks against an installed EngCalcs host."""

import json
from importlib.metadata import entry_points
from pathlib import Path

import pytest

PLUGIN_ENTRY = next(
    (item for item in entry_points(group="engcalcs.plugins") if item.name == "as1170"),
    None,
)
if PLUGIN_ENTRY is None:
    pytest.skip(
        "Install this wheel and the EngCalcs host to run integration checks.",
        allow_module_level=True,
    )

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = json.loads((ROOT / "examples" / "office-floor.json").read_text(encoding="utf-8"))
CALCULATION_ID = "structural.as1170.part1.floor_action"
EXPECTED_REDUCED_ACTION_KPA = 2.7


def test_entry_point_registers_calculations_and_registry_runs_example() -> None:
    pytest.importorskip("engcalcs")
    from engcalcs.registry import CalculationRegistry

    plugin = PLUGIN_ENTRY.load()()
    assert plugin.id == "structural.as1170"
    assert len(plugin.calculations) == 16

    registry = CalculationRegistry()
    result = registry.run(CALCULATION_ID, EXAMPLE["inputs"])
    assert result["reduced_uniform_action_kpa"] == pytest.approx(EXPECTED_REDUCED_ACTION_KPA)
    assert result["_provenance"]["engine"]["id"] == "structural.as1170"
    assert result["_provenance"]["calculation"]["id"] == CALCULATION_ID


def test_host_http_catalog_and_calculation_run() -> None:
    pytest.importorskip("engcalcs")
    from engcalcs.api import create_app
    from engcalcs.auth import AllowAllAuthenticator
    from fastapi.testclient import TestClient

    with TestClient(create_app(authenticator=AllowAllAuthenticator())) as client:
        descriptor = client.get(f"/api/v1/calculations/{CALCULATION_ID}")
        response = client.post(
            f"/api/v1/calculations/{CALCULATION_ID}/run",
            json={"inputs": EXAMPLE["inputs"]},
        )

    assert descriptor.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert body["reduced_uniform_action_kpa"] == pytest.approx(EXPECTED_REDUCED_ACTION_KPA)
    assert body["_provenance"]["standard"]["designation"] == "AS/NZS 1170.1:2002"
