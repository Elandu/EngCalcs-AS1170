# SPDX-License-Identifier: AGPL-3.0-only

"""AS/NZS 1170.0 action combinations and minimum robustness actions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from engcalcs_as1170.standards import STANDARD_0
from engcalcs_as1170.validation import action_value, positive_number, validate_inputs

OCCUPANCY_FACTORS: dict[str, tuple[float, float, float, float]] = {
    "residential": (0.7, 0.4, 0.4, 0.3),
    "office": (0.7, 0.4, 0.4, 0.3),
    "parking": (0.7, 0.4, 0.4, 0.3),
    "retail": (0.7, 0.4, 0.4, 0.3),
    "storage": (1.0, 0.6, 0.6, 0.6),
    "other": (1.0, 0.6, 0.6, 0.6),
    "floor_roof_activity": (0.7, 0.4, 0.4, 0.3),
    "other_roof": (0.7, 0.0, 0.0, 0.0),
}

COMBINATION_KINDS = {
    "distributed_floor",
    "concentrated_floor",
    "distributed_roof_floor_activity",
    "concentrated_roof_floor_activity",
    "other_roof",
    "barrier",
    "machinery_tare_weight",
}


def combination_factors(occupancy: str, action_kind: str) -> dict[str, float]:
    if occupancy not in OCCUPANCY_FACTORS:
        raise ValueError(f"Unsupported occupancy factor class: {occupancy}")
    if action_kind not in COMBINATION_KINDS:
        raise ValueError(f"Unsupported imposed action kind: {action_kind}")
    if action_kind == "barrier":
        return {"psi_s": 1.0, "psi_l": 0.0, "psi_c": 0.0, "psi_e": 0.0}
    if action_kind == "machinery_tare_weight":
        return {"psi_s": 1.0, "psi_l": 1.0, "psi_c": 1.2, "psi_e": 1.0}
    if action_kind == "other_roof":
        return {"psi_s": 0.7, "psi_l": 0.0, "psi_c": 0.0, "psi_e": 0.0}

    psi_s, psi_l, psi_c, psi_e = OCCUPANCY_FACTORS[occupancy]
    if action_kind in {"concentrated_floor", "concentrated_roof_floor_activity"}:
        psi_s = 1.0
        if occupancy == "residential":
            psi_l = 0.4
        elif occupancy != "other_roof":
            psi_l = 0.6
    return {"psi_s": psi_s, "psi_l": psi_l, "psi_c": psi_c, "psi_e": psi_e}


def _case(
    case_id: str,
    label: str,
    coefficients: Mapping[str, float],
    effects: Mapping[str, Any],
) -> dict[str, Any]:
    result = sum(coeff * action_value(effects, key) for key, coeff in coefficients.items())
    return {
        "id": case_id,
        "label": label,
        "coefficients": dict(coefficients),
        "action_effect": result,
    }


def _special_cases(special: Mapping[str, Any], effects: Mapping[str, Any]) -> list[dict[str, Any]]:
    rules = {
        "liquid_pressure_known": (1.2, "Known liquid type and bounded design height"),
        "liquid_pressure_uncertain": (1.5, "Uncertain liquid type or unbounded design height"),
        "rainwater_ponding": (1.2, "Rainwater ponding"),
        "groundwater_1_in_50": (
            1.2,
            "Groundwater level based on the 1-in-50 annual probability level",
        ),
        "groundwater_at_ground": (1.5, "Groundwater level taken at ground level"),
        "earth_pressure_uls_method": (
            1.0,
            "Earth pressure determined by an ultimate limit states method",
        ),
        "earth_pressure_other_method": (1.5, "Earth pressure determined by another method"),
        "ice": (1.2, "Ice action"),
    }
    cases = []
    for key, (factor, label) in rules.items():
        if key in special:
            cases.append(_case(key, label, {key: factor}, special))
    return cases


def run_combinations(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Generate Part 0 design combinations for supplied action effects.

    Effects are signed results from a separate structural analysis. The runner does not
    determine the adverse sign, structural response, or the wind action itself.
    """

    validate_inputs(COMBINATION_INPUT_SCHEMA, inputs)
    situation = str(inputs["situation"])
    if situation == "stability" and "stability_state" not in inputs:
        raise ValueError("stability_state is required when situation is stability")
    occupancy = str(inputs["occupancy"])
    action_kind = str(inputs["imposed_action_kind"])
    factors = combination_factors(occupancy, action_kind)
    effects = inputs.get("action_effects", {})
    special = inputs.get("special_actions", {})
    psi_c = factors["psi_c"]
    cases: list[dict[str, Any]] = []

    if situation == "strength":
        combinations = (
            ("strength_permanent", "Permanent action", {"G": 1.35}),
            ("strength_permanent_imposed", "Permanent and imposed action", {"G": 1.2, "Q": 1.5}),
            (
                "strength_long_term_imposed",
                "Permanent and long-term imposed action",
                {"G": 1.2, "Q": 1.5 * factors["psi_l"]},
            ),
            (
                "strength_wind",
                "Permanent, externally supplied wind and imposed action",
                {"G": 1.2, "W_u": 1.0, "Q": psi_c},
            ),
            (
                "strength_wind_reversal",
                "Permanent action and wind reversal",
                {"G": 0.9, "W_u": 1.0},
            ),
            (
                "strength_earthquake",
                "Permanent, earthquake and imposed action",
                {"G": 1.0, "E_u": 1.0, "Q": factors["psi_e"]},
            ),
            (
                "strength_snow",
                "Permanent, snow and imposed action",
                {"G": 1.2, "S_u": 1.0, "Q": psi_c},
            ),
        )
        cases.extend(_case(*item, effects) for item in combinations)
    elif situation == "stability":
        state = str(inputs["stability_state"])
        if state == "stabilizing":
            cases.append(
                _case("stability_stabilizing", "Stabilizing permanent action", {"G": 0.9}, effects)
            )
        else:
            combinations = (
                ("stability_permanent", "Destabilizing permanent action", {"G": 1.35}),
                (
                    "stability_permanent_imposed",
                    "Permanent and imposed action",
                    {"G": 1.2, "Q": 1.5},
                ),
                (
                    "stability_wind",
                    "Permanent, externally supplied wind and imposed action",
                    {"G": 1.2, "W_u": 1.0, "Q": psi_c},
                ),
                (
                    "stability_earthquake",
                    "Permanent, earthquake and imposed action",
                    {"G": 1.0, "E_u": 1.0, "Q": factors["psi_e"]},
                ),
                (
                    "stability_snow",
                    "Permanent, snow and imposed action",
                    {"G": 1.2, "S_u": 1.0, "Q": psi_c},
                ),
            )
            cases.extend(_case(*item, effects) for item in combinations)
    elif situation == "serviceability":
        short_term = {"G": 1.0, "Q": factors["psi_s"]}
        long_term = {"G": 1.0, "Q": factors["psi_l"]}
        cases.extend(
            (
                _case("serviceability_permanent", "Permanent action", {"G": 1.0}, effects),
                _case(
                    "serviceability_short_term", "Short-term imposed action", short_term, effects
                ),
                _case("serviceability_long_term", "Long-term imposed action", long_term, effects),
                _case(
                    "serviceability_wind",
                    "Serviceability wind with short-term imposed action",
                    {"G": 1.0, "W_s": 1.0, "Q": factors["psi_s"]},
                    effects,
                ),
                _case(
                    "serviceability_earthquake",
                    "Serviceability earthquake with earthquake combination factor",
                    {"G": 1.0, "E_s": 1.0, "Q": factors["psi_e"]},
                    effects,
                ),
            )
        )
        cases.extend(_special_cases(special, effects))
    else:
        thermal = action_value(effects, "fire_thermal")
        q_factor = factors["psi_l"]
        cases.append(
            _case(
                "fire",
                "Permanent, fire thermal action and long-term imposed action",
                {"G": 1.0, "fire_thermal": 1.0, "Q": q_factor},
                effects,
            )
        )
        if thermal == 0.0 and "fire_thermal" not in effects:
            cases[-1]["note"] = "Supply the fire thermal action effect for a numerical result."

    if situation in {"strength", "stability"}:
        cases.extend(_special_cases(special, effects))

    return {
        "calculation": "structural.as1170.part0.combinations",
        "standard": STANDARD_0.descriptor(),
        "clauses": ["4.2.1", "4.2.2", "4.2.3", "4.2.4", "4.3"],
        "factors": factors,
        "cases": cases,
        "notes": [
            "Select the load cases appropriate to the structural system and limit state.",
            "Action effects are signed values from a separate structural analysis; "
            "assess both directions where relevant.",
            "Wind actions are supplied externally; AS/NZS 1170.2 action generation is excluded.",
        ],
        "full_standard_compliance": False,
    }


def run_robustness(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate the minimum lateral, tie and wall-anchorage action values in Part 0."""

    validate_inputs(ROBUSTNESS_INPUT_SCHEMA, inputs)
    height = positive_number(inputs, "height_m")
    g = positive_number(inputs, "per_level_permanent_action_kn", allow_zero=True)
    q = positive_number(inputs, "per_level_imposed_action_kn", allow_zero=True)
    factors = combination_factors(str(inputs["occupancy"]), str(inputs["imposed_action_kind"]))
    basis = g + factors["psi_c"] * q
    lateral_ratio = 0.01 if height > 15.0 else 0.015
    return {
        "calculation": "structural.as1170.part0.robustness",
        "standard": STANDARD_0.descriptor(),
        "clauses": ["6.2.2", "6.2.3", "6.2.5"],
        "height_m": height,
        "psi_c": factors["psi_c"],
        "basis_action_kn_per_level": basis,
        "minimum_lateral_resistance_kn_per_level": lateral_ratio * basis,
        "minimum_connection_or_tie_action_kn": 0.05 * basis,
        "minimum_wall_anchorage_action_kn": 0.05 * g,
        "lateral_resistance_ratio": lateral_ratio,
        "full_standard_compliance": False,
        "notes": [
            "Lateral resistance is applied at each level in the governing direction; "
            "this is not a global frame analysis.",
            "Connection and wall anchorage actions are minima and do not replace "
            "detailed connection design.",
        ],
    }


def _schema(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


_number_schema = {"type": "number"}
_action_effect_schema = {
    "type": "object",
    "properties": {
        key: _number_schema for key in ("G", "Q", "W_u", "E_u", "S_u", "W_s", "E_s", "fire_thermal")
    },
    "additionalProperties": False,
}
_special_effect_schema = {
    "type": "object",
    "properties": {
        key: _number_schema
        for key in (
            "liquid_pressure_known",
            "liquid_pressure_uncertain",
            "rainwater_ponding",
            "groundwater_1_in_50",
            "groundwater_at_ground",
            "earth_pressure_uls_method",
            "earth_pressure_other_method",
            "ice",
        )
    },
    "additionalProperties": False,
}
COMBINATION_INPUT_SCHEMA = _schema(
    ["situation", "occupancy", "imposed_action_kind"],
    {
        "situation": {"enum": ["stability", "strength", "serviceability", "fire"]},
        "stability_state": {"enum": ["stabilizing", "destabilizing"]},
        "occupancy": {"enum": sorted(OCCUPANCY_FACTORS)},
        "imposed_action_kind": {"enum": sorted(COMBINATION_KINDS)},
        "action_effects": _action_effect_schema,
        "special_actions": _special_effect_schema,
    },
)
ROBUSTNESS_INPUT_SCHEMA = _schema(
    [
        "height_m",
        "per_level_permanent_action_kn",
        "per_level_imposed_action_kn",
        "occupancy",
        "imposed_action_kind",
    ],
    {
        "height_m": {"type": "number", "exclusiveMinimum": 0},
        "per_level_permanent_action_kn": {"type": "number", "minimum": 0},
        "per_level_imposed_action_kn": {"type": "number", "minimum": 0},
        "occupancy": {"enum": sorted(OCCUPANCY_FACTORS)},
        "imposed_action_kind": {"enum": sorted(COMBINATION_KINDS)},
    },
)

COMBINATION_INPUT_SCHEMA["allOf"] = [
    {
        "if": {"properties": {"situation": {"const": "stability"}}, "required": ["situation"]},
        "then": {"required": ["stability_state"]},
    }
]
