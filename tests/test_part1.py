from __future__ import annotations

import pytest

from engcalcs_as1170.part1 import (
    run_barrier_action,
    run_carpark_action,
    run_crane_rail_action,
    run_crane_vertical_action,
    run_earth_pressure_resultant,
    run_floor_action,
    run_grandstand_action,
    run_groundwater_pressure,
    run_partition_allowance,
    run_rainwater_ponding,
    run_roof_action,
    run_roof_person_action,
    run_self_weight,
    run_static_liquid_pressure,
)


def test_office_floor_action_with_area_reduction_reference_fixture() -> None:
    result = run_floor_action({"row_id": "B_OFFICE", "supported_area_m2": 25.0})
    assert result["characteristic_uniform_action_kpa"] == pytest.approx(3.0)
    assert result["area_reduction_factor_psi_a"] == pytest.approx(0.9)
    assert result["reduced_uniform_action_kpa"] == pytest.approx(2.7)
    assert result["concentrated_action_kn"] == pytest.approx(2.7)


def test_reduction_is_not_applied_to_crowd_or_traffic_categories() -> None:
    c5 = run_floor_action({"row_id": "C5_ASSEMBLY", "supported_area_m2": 400.0})
    f = run_floor_action({"row_id": "F_LIGHT_VEHICLE", "supported_area_m2": 400.0})
    assert c5["area_reduction_factor_psi_a"] == 1.0
    assert f["area_reduction_factor_psi_a"] == 1.0


def test_storage_actions_use_height_and_exemption_threshold() -> None:
    reduced = run_floor_action(
        {"row_id": "E_GENERAL_STORAGE", "supported_area_m2": 64.0, "storage_height_m": 2.0}
    )
    unreduced = run_floor_action(
        {"row_id": "E_GENERAL_STORAGE", "supported_area_m2": 64.0, "storage_height_m": 3.0}
    )
    assert reduced["characteristic_uniform_action_kpa"] == pytest.approx(4.8)
    assert reduced["area_reduction_factor_psi_a"] == pytest.approx(0.675)
    assert unreduced["characteristic_uniform_action_kpa"] == pytest.approx(7.2)
    assert unreduced["area_reduction_factor_psi_a"] == 1.0


def test_one_way_slab_and_specific_machinery_disallow_area_reduction() -> None:
    slab = run_floor_action(
        {"row_id": "B_OFFICE", "supported_area_m2": 100.0, "one_way_slab": True}
    )
    machinery = run_floor_action(
        {
            "row_id": "B_OFFICE",
            "supported_area_m2": 100.0,
            "specific_machinery_allowance": True,
        }
    )
    assert slab["area_reduction_factor_psi_a"] == 1.0
    assert machinery["area_reduction_factor_psi_a"] == 1.0


def test_roof_action_includes_large_roof_patch_case() -> None:
    result = run_roof_action(
        {"roof_type": "R2", "element": "structural_element", "plan_area_supported_m2": 400.0}
    )
    assert result["uniform_action_kpa"] == pytest.approx(0.25)
    assert result["concentrated_action_kn"] == pytest.approx(1.4)
    assert result["uniform_action_cases"] == [
        {"id": "reference_uniform_roof_action", "uniform_action_kpa": 0.25, "area_m2": None},
        {
            "id": "large_roof_patch_action",
            "uniform_action_kpa": 0.25,
            "area_m2": 200.0,
            "note": "Apply over the 200 m2 region producing the most adverse effect.",
        },
    ]


def test_house_roof_and_r1_access_actions() -> None:
    house = run_roof_action(
        {
            "roof_type": "R2",
            "element": "structural_element",
            "plan_area_supported_m2": 30.0,
            "house_roof": True,
        }
    )
    r1 = run_roof_action(
        {
            "roof_type": "R1",
            "element": "cladding",
            "plan_area_supported_m2": 15.0,
            "accessible_from_adjacent": True,
        }
    )
    assert house["uniform_action_kpa"] == 0.25
    assert house["concentrated_action_kn"] == 1.1
    assert r1["uniform_action_kpa"] == 1.5


def test_stairs_include_point_load_area_and_conditional_independent_tread_case() -> None:
    result = run_floor_action({"row_id": "A1_STAIRS", "supported_area_m2": 4.0})
    assert result["concentrated_action_kn"] == pytest.approx(2.7)
    assert result["concentrated_load_area_mm2"] == 350
    assert result["conditional_load_cases"] == [
        {
            "id": "independent_stair_tread_or_landing_line_action",
            "condition": "The tread or landing is structurally independent of adjoining elements.",
            "line_action_kn_m": 2.2,
        }
    ]


def test_roof_person_action_is_separate_from_table_3_2() -> None:
    result = run_roof_person_action({"element_description": "roof truss bottom chord"})
    assert result["clauses"] == ["3.5.2"]
    assert result["separate_load_cases"] == [
        {"id": "person_concentrated_action", "concentrated_action_kn": 1.4}
    ]


def test_barrier_cases_are_not_added_together() -> None:
    result = run_barrier_action({"barrier_class": "C5"})
    cases = result["separate_load_cases"]
    assert cases["top_edge_horizontal_line_kn_m"] == 3.0
    assert cases["top_edge_vertical_line_kn_m"] == 0.75
    assert cases["top_edge_concentrated_kn"] == 0.6
    assert cases["infill_uniform_pressure_kpa"] == 1.5
    assert cases["infill_concentrated_kn"] == 1.5


def test_machine_and_crane_dynamic_factors() -> None:
    lift = run_crane_vertical_action(
        {"machine_type": "lift_moving_components", "static_action_kn": 10.0}
    )
    electric = run_crane_rail_action(
        {
            "crane_type": "electric_overhead",
            "combined_crab_and_lifted_load_kn": 50.0,
            "static_rail_wheel_load_kn": 40.0,
        }
    )
    assert lift["design_action_kn"] == 20.0
    assert electric["transverse_action_kn"] == 10.0
    assert electric["parallel_action_kn"] == 4.0


def test_carpark_actions_and_downward_ramp_barrier_case() -> None:
    normal = run_carpark_action({"gross_vehicle_mass_kg": 2000.0})
    ramp = run_carpark_action(
        {
            "gross_vehicle_mass_kg": 2000.0,
            "downward_travel": True,
            "downward_ramp_length_m": 25.0,
        }
    )
    assert normal["braking_action_kn"] == pytest.approx(9.80665)
    assert normal["barrier_impact_action_kn"] == 30.0
    assert ramp["barrier_impact_action_kn"] == 240.0


def test_grandstand_action_returns_alternative_cases() -> None:
    seated = run_grandstand_action({"seating": True, "plan_area_m2": 20.0, "seat_length_m": 12.0})
    unseated = run_grandstand_action({"seating": False, "plan_area_m2": 20.0, "seat_length_m": 0.0})
    assert seated["separate_load_cases"][0]["line_action_kn_m"] == 0.35
    assert seated["separate_load_cases"][1]["line_action_kn_m"] == 0.15
    assert unseated["separate_load_cases"][0]["uniform_action_kpa"] == 0.25


def test_self_weight_and_movable_partition_allowance() -> None:
    weight = run_self_weight({"unit_weight_kn_m3": 24.0, "thickness_m": 0.15, "area_m2": 20.0})
    partition = run_partition_allowance({"area_m2": 20.0})
    assert weight["permanent_action_kpa"] == pytest.approx(3.6)
    assert weight["permanent_action_kn"] == pytest.approx(72.0)
    assert partition["permanent_action_kn"] == pytest.approx(10.0)


def test_liquid_groundwater_and_ponding_pressure_calculations() -> None:
    liquid = run_static_liquid_pressure(
        {"liquid_depth_m": 4.0, "unit_weight_kn_m3": 10.0, "wall_width_m": 2.0}
    )
    groundwater = run_groundwater_pressure({"water_head_m": 2.0, "wall_width_m": 3.0})
    ponding = run_rainwater_ponding(
        {
            "design_ponding_depth_including_sag_m": 0.1,
            "ponded_area_m2": 30.0,
            "water_unit_weight_kn_m3": 10.0,
        }
    )
    assert liquid["base_pressure_kpa"] == 40.0
    assert liquid["resultant_action_kn"] == 160.0
    assert liquid["resultant_height_above_base_m"] == pytest.approx(4.0 / 3.0)
    assert groundwater["base_pressure_kpa"] == pytest.approx(19.62)
    assert groundwater["resultant_action_kn"] == pytest.approx(58.86)
    assert ponding["action_kn"] == 30.0


def test_earth_pressure_resultant_for_linear_profile() -> None:
    result = run_earth_pressure_resultant(
        {
            "retained_height_m": 4.0,
            "wall_width_m": 3.0,
            "pressure_at_top_kpa": 0.0,
            "pressure_at_base_kpa": 30.0,
        }
    )
    assert result["resultant_action_kn_per_m_width"] == 60.0
    assert result["resultant_action_kn"] == 180.0
    assert result["resultant_height_above_base_m"] == pytest.approx(4.0 / 3.0)


def test_invalid_floor_row_and_out_of_scope_vehicle_are_rejected() -> None:
    with pytest.raises(ValueError, match="row_id"):
        run_floor_action({"row_id": "not-a-row", "supported_area_m2": 25.0})
    with pytest.raises(ValueError, match="stop at 10 000 kg"):
        run_carpark_action({"gross_vehicle_mass_kg": 12000.0})
