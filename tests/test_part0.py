from __future__ import annotations

import pytest

from engcalcs_as1170.part0 import combination_factors, run_combinations, run_robustness


def test_table_4_1_distributed_office_factors() -> None:
    assert combination_factors("office", "distributed_floor") == {
        "psi_s": 0.7,
        "psi_l": 0.4,
        "psi_c": 0.4,
        "psi_e": 0.3,
    }


def test_table_4_1_concentrated_domestic_factors() -> None:
    assert combination_factors("residential", "concentrated_floor") == {
        "psi_s": 1.0,
        "psi_l": 0.4,
        "psi_c": 0.4,
        "psi_e": 0.3,
    }


def test_strength_combinations_match_independent_office_fixture() -> None:
    result = run_combinations(
        {
            "situation": "strength",
            "occupancy": "office",
            "imposed_action_kind": "distributed_floor",
            "action_effects": {"G": 4.0, "Q": 3.0, "W_u": 2.0, "E_u": 1.0, "S_u": 2.0},
        }
    )
    by_id = {case["id"]: case["action_effect"] for case in result["cases"]}
    assert by_id["strength_permanent"] == pytest.approx(5.4)
    assert by_id["strength_permanent_imposed"] == pytest.approx(9.3)
    assert by_id["strength_long_term_imposed"] == pytest.approx(6.6)
    assert by_id["strength_wind"] == pytest.approx(8.0)
    assert by_id["strength_wind_reversal"] == pytest.approx(5.6)
    assert by_id["strength_earthquake"] == pytest.approx(5.9)
    assert by_id["strength_snow"] == pytest.approx(8.0)
    assert result["full_standard_compliance"] is False


def test_destabilizing_stability_combinations_include_eccentric_cases() -> None:
    result = run_combinations(
        {
            "situation": "stability",
            "stability_state": "destabilizing",
            "occupancy": "storage",
            "imposed_action_kind": "distributed_floor",
            "action_effects": {"G": 10.0, "Q": 5.0, "W_u": -8.0, "E_u": 2.0, "S_u": 1.0},
        }
    )
    by_id = {case["id"]: case["action_effect"] for case in result["cases"]}
    assert by_id["stability_permanent"] == pytest.approx(13.5)
    assert by_id["stability_permanent_imposed"] == pytest.approx(19.5)
    assert by_id["stability_wind"] == pytest.approx(7.0)
    assert by_id["stability_earthquake"] == pytest.approx(15.0)
    assert by_id["stability_snow"] == pytest.approx(16.0)


def test_stabilizing_stability_uses_reduced_permanent_action() -> None:
    result = run_combinations(
        {
            "situation": "stability",
            "stability_state": "stabilizing",
            "occupancy": "office",
            "imposed_action_kind": "distributed_floor",
            "action_effects": {"G": 10.0},
        }
    )
    assert result["cases"][0]["coefficients"] == {"G": 0.9}
    assert result["cases"][0]["action_effect"] == pytest.approx(9.0)


def test_sls_and_fire_cases_apply_the_selected_psi_factors() -> None:
    common = {
        "occupancy": "office",
        "imposed_action_kind": "distributed_floor",
        "action_effects": {"G": 4.0, "Q": 3.0, "W_s": 2.0, "E_s": 1.0, "fire_thermal": 5.0},
    }
    sls = run_combinations({**common, "situation": "serviceability"})
    sls_effects = {case["id"]: case["action_effect"] for case in sls["cases"]}
    assert sls_effects["serviceability_short_term"] == pytest.approx(6.1)
    assert sls_effects["serviceability_long_term"] == pytest.approx(5.2)
    assert sls_effects["serviceability_wind"] == pytest.approx(8.1)
    assert sls_effects["serviceability_earthquake"] == pytest.approx(5.9)

    fire = run_combinations({**common, "situation": "fire"})
    assert fire["cases"][0]["action_effect"] == pytest.approx(10.2)


def test_special_action_factors_are_reported_as_separate_cases() -> None:
    result = run_combinations(
        {
            "situation": "strength",
            "occupancy": "office",
            "imposed_action_kind": "distributed_floor",
            "action_effects": {"G": 10.0},
            "special_actions": {
                "liquid_pressure_known": 4.0,
                "rainwater_ponding": 3.0,
                "earth_pressure_uls_method": 5.0,
                "ice": 2.0,
            },
        }
    )
    by_id = {case["id"]: case["action_effect"] for case in result["cases"]}
    assert by_id["liquid_pressure_known"] == pytest.approx(4.8)
    assert by_id["rainwater_ponding"] == pytest.approx(3.6)
    assert by_id["earth_pressure_uls_method"] == pytest.approx(5.0)
    assert by_id["ice"] == pytest.approx(2.4)


def test_missing_stability_state_is_rejected() -> None:
    with pytest.raises(ValueError, match="stability_state"):
        run_combinations(
            {
                "situation": "stability",
                "occupancy": "office",
                "imposed_action_kind": "distributed_floor",
            }
        )


@pytest.mark.parametrize(
    ("height", "expected_ratio"),
    [(15.0, 0.015), (15.01, 0.01)],
)
def test_minimum_robustness_actions_switch_at_fifteen_metres(
    height: float, expected_ratio: float
) -> None:
    result = run_robustness(
        {
            "height_m": height,
            "per_level_permanent_action_kn": 100.0,
            "per_level_imposed_action_kn": 50.0,
            "occupancy": "office",
            "imposed_action_kind": "distributed_floor",
        }
    )
    assert result["basis_action_kn_per_level"] == pytest.approx(120.0)
    assert result["lateral_resistance_ratio"] == expected_ratio
    assert result["minimum_lateral_resistance_kn_per_level"] == pytest.approx(
        120.0 * expected_ratio
    )
    assert result["minimum_connection_or_tie_action_kn"] == pytest.approx(6.0)
    assert result["minimum_wall_anchorage_action_kn"] == pytest.approx(5.0)
