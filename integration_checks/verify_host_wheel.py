# SPDX-License-Identifier: AGPL-3.0-only
"""Validate the installed AS1170 distribution against an immutable EngCalcs host."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import entry_points, version
from math import isclose
from pathlib import Path

import engcalcs_as1170

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "examples" / "office-floor.json").read_text(encoding="utf-8"))
CALCULATION_ID = "structural.as1170.part1.floor_action"


def verify_fixture(result: dict) -> None:
    for key, expected in FIXTURE["expected_summary"].items():
        assert isclose(result[key], expected, rel_tol=0, abs_tol=1e-9), (
            key,
            result[key],
            expected,
        )
    assert result["full_standard_compliance"] is False
    assert result["standard"]["designation"] == "AS/NZS 1170.1:2002"


def verify_wheel() -> None:
    imported_path = Path(engcalcs_as1170.__file__).resolve()
    assert not imported_path.is_relative_to(ROOT / "src"), (
        f"Imported checkout source rather than installed wheel: {imported_path}"
    )
    assert version("engcalcs-as1170") == engcalcs_as1170.__version__

    plugins = []
    for group in ("engcalcs.plugins", "opencalcs.plugins"):
        matches = [ep for ep in entry_points(group=group) if ep.name == "as1170"]
        assert len(matches) == 1, (group, matches)
        plugins.append(matches[0].load()())

    assert all(plugin.id == "structural.as1170" for plugin in plugins)
    descriptors = [plugin.descriptor() for plugin in plugins]
    assert all(len(plugin.calculations) == 16 for plugin in plugins)
    assert all(
        descriptor["license"] == "AGPL-3.0-only"
        for descriptor in descriptors
    )
    assert {item["id"] for item in descriptors[0]["calculations"]} == {
        item["id"] for item in descriptors[1]["calculations"]
    }
    assert all(
        item["standard"]["full_standard_compliance"] is False
        for item in descriptors[0]["calculations"]
    )
    assert {item["standard"]["designation"] for item in descriptors[0]["calculations"]} == {
        "AS/NZS 1170.0:2002", "AS/NZS 1170.1:2002"
    }
    calc = next(item for item in plugins[0].calculations if item.id == CALCULATION_ID)
    verify_fixture(calc.run(FIXTURE["inputs"]))


def verify_host() -> None:
    from engcalcs.api import create_app
    from engcalcs.auth import AllowAllAuthenticator
    from engcalcs.registry import CalculationRegistry
    from fastapi.testclient import TestClient

    registry = CalculationRegistry()
    assert any(plugin.id == "structural.as1170" for plugin in registry.plugins)
    verify_fixture(registry.run(CALCULATION_ID, FIXTURE["inputs"]))

    with TestClient(create_app(registry=registry, authenticator=AllowAllAuthenticator())) as client:
        descriptor = client.get(f"/api/v1/calculations/{CALCULATION_ID}")
        response = client.post(
            f"/api/v1/calculations/{CALCULATION_ID}/run",
            json={"inputs": FIXTURE["inputs"]},
        )
        modules = client.get("/api/v1/modules")
        links = client.get("/api/v1/connections", params={"calculation_id": CALCULATION_ID})

    assert descriptor.status_code == response.status_code == 200
    assert modules.status_code == links.status_code == 200
    verify_fixture(response.json())
    provenance = response.json()["_provenance"]
    assert provenance["engine"]["id"] == "structural.as1170"
    assert provenance["calculation"]["id"] == CALCULATION_ID
    assert provenance["standard"]["designation"] == "AS/NZS 1170.1:2002"

    module = next(item for item in modules.json() if item["id"] == "structural.as1170")
    assert module["installed"] is True
    assert CALCULATION_ID in module["calculation_ids"]

    link = next(item for item in links.json() if item["id"] == "as1170-actions-to-frame")
    assert link["mode"] == "adapter_required"
    assert link["requires_adapter"] is True
    assert link["requires_engineer_review"] is True
    assert link["direct_link_ready"] is False
    assert link["automated_transfer_allowed"] is False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-host", action="store_true")
    args = parser.parse_args()
    verify_wheel()
    if args.with_host:
        verify_host()
    print("Installed AS1170 wheel and host contracts verified.")
