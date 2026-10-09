from __future__ import annotations

from jsonschema import Draft202012Validator

from engcalcs_as1170.plugin import get_plugin


def test_plugin_descriptor_exposes_only_non_wind_calculations() -> None:
    plugin = get_plugin()
    descriptor = plugin.descriptor()
    ids = [item.id for item in plugin.calculations]
    assert plugin.id == "structural.as1170"
    assert len(ids) == 16
    assert all(item.startswith("structural.as1170.part") for item in ids)
    assert "1170.2" in descriptor["scope_notice"]
    assert all("1170.2" not in item["id"] for item in descriptor["calculations"])


def test_calculation_schemas_are_valid_json_schemas() -> None:
    for calculation in get_plugin().calculations:
        Draft202012Validator.check_schema(calculation.input_schema)
        Draft202012Validator.check_schema(calculation.descriptor()["output_schema"])


def test_descriptor_provenance_marks_selected_scope() -> None:
    descriptor = get_plugin().descriptor()
    standards = {item["standard"]["designation"] for item in descriptor["calculations"]}
    assert standards == {"AS/NZS 1170.0:2002", "AS/NZS 1170.1:2002"}
    assert all(
        item["standard"]["full_standard_compliance"] is False for item in descriptor["calculations"]
    )
