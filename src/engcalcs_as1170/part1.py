# SPDX-License-Identifier: AGPL-3.0-only

"""AS/NZS 1170.1 permanent, imposed and other action calculations."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from engcalcs_as1170.part0 import OCCUPANCY_FACTORS
from engcalcs_as1170.standards import STANDARD_1
from engcalcs_as1170.validation import positive_number, validate_inputs


def _schema(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


def _prop_number(
    *, minimum: float | None = None, exclusive_minimum: float | None = None
) -> dict[str, Any]:
    result: dict[str, Any] = {"type": "number"}
    if minimum is not None:
        result["minimum"] = minimum
    if exclusive_minimum is not None:
        result["exclusiveMinimum"] = exclusive_minimum
    return result


_OCCUPANCY_GROUP = {"type": "string", "enum": sorted(OCCUPANCY_FACTORS)}


# Row identifiers are stable API values; descriptions are short labels, not copied table text.
FLOOR_ACTIONS: dict[str, dict[str, Any]] = {
    "A1_DWELLING_GENERAL": {
        "category": "A",
        "label": "A1 dwelling general",
        "q": 1.5,
        "Q": 1.8,
        "point_area_mm2": 350,
    },
    "A1_BALCONY_LOW": {"category": "A", "label": "A1 low balcony edge", "q": 1.5, "line": 1.5},
    "A1_BALCONY": {
        "category": "A",
        "label": "A1 balcony",
        "q": 2.0,
        "Q": 1.8,
        "point_area_mm2": 350,
    },
    "A1_STAIRS": {
        "category": "A",
        "label": "A1 stairs and landings",
        "q": 2.0,
        "Q": 2.7,
        "point_area_mm2": 350,
    },
    "A2_NONHABITABLE_ROOF": {
        "category": "A",
        "label": "A2 non-habitable dwelling roof space",
        "q": 0.5,
        "Q": 1.4,
        "point_area_mm2": 350,
    },
    "A2_GENERAL": {
        "category": "A",
        "label": "A2 residential general",
        "q": 2.0,
        "Q": 1.8,
        "point_area_mm2": 350,
    },
    "A2_COMMUNAL_KITCHEN": {"category": "A", "label": "A2 communal kitchen", "q": 3.0, "Q": 2.7},
    "A2_COMMUNITY_BALCONY": {
        "category": "A",
        "label": "A2 community-access balcony",
        "q_rule": "access_area_min_4",
        "Q": 1.8,
    },
    "B_OPERATING_ROOM": {
        "category": "B",
        "label": "B operating or utility room",
        "q": 3.0,
        "Q": 4.5,
    },
    "B_LIGHT_WORKROOM": {
        "category": "B",
        "label": "B light industrial workroom",
        "q": 3.0,
        "Q": 3.5,
    },
    "B_OFFICE": {"category": "B", "label": "B office", "q": 3.0, "Q": 2.7, "point_area_mm2": 350},
    "B_COMMUNAL_KITCHEN": {"category": "B", "label": "B communal kitchen", "q": 3.0, "Q": 2.7},
    "B_COMMERCIAL_KITCHEN": {
        "category": "B",
        "label": "B commercial or institutional kitchen",
        "q": 5.0,
        "Q": 4.5,
    },
    "B_LAUNDRY": {"category": "B", "label": "B laundry", "q": 3.0, "Q": 4.5},
    "B_LABORATORY": {"category": "B", "label": "B laboratory", "q": 3.0, "Q": 4.5},
    "B_FACTORY": {"category": "B", "label": "B factory or workshop", "q": 5.0, "Q": 4.5},
    "B_BALCONY": {
        "category": "B",
        "label": "B balcony or roof used for floor activity",
        "q_rule": "access_area_min_4",
        "Q": 1.8,
    },
    "B_FLY_GALLERY": {"category": "B", "label": "B fly gallery", "line": 4.5},
    "B_STAGE_GRID": {"category": "B", "label": "B stage grid", "q": 2.8},
    "C1_DINING": {"category": "C1", "label": "C1 dining area", "q": 2.0, "Q": 2.7},
    "C1_READING": {
        "category": "C1",
        "label": "C1 reading room without book storage",
        "q": 2.5,
        "Q": 4.5,
    },
    "C1_CLASSROOM": {"category": "C1", "label": "C1 classroom", "q": 3.0, "Q": 2.7},
    "C2_INSTITUTIONAL_ASSEMBLY": {
        "category": "C2",
        "label": "C2 institutional assembly with fixed seating",
        "q": 3.0,
        "Q": 2.7,
    },
    "C2_PUBLIC_ASSEMBLY": {
        "category": "C2",
        "label": "C2 public assembly with fixed seating",
        "q": 4.0,
        "Q": 2.7,
    },
    "C2_WORSHIP": {"category": "C2", "label": "C2 place of worship", "q": 4.0, "Q": 2.7},
    "C3_CORRIDOR": {
        "category": "C3",
        "label": "C3 corridor without wheeled traffic",
        "q": 4.0,
        "Q": 4.5,
    },
    "C3_WHEELED_CORRIDOR": {
        "category": "C3",
        "label": "C3 corridor with wheeled traffic",
        "q": 5.0,
        "Q": 4.5,
    },
    "C3_GROUND_FOOTPATH": {
        "category": "C3",
        "label": "C3 ground-level footpath with vehicle access",
        "q": 5.0,
        "Q": 31.0,
        "point_area_m2": 0.025,
    },
    "C3_MUSEUM": {"category": "C3", "label": "C3 museum or gallery floor", "q": 4.0, "Q": 4.5},
    "C3_BALCONY": {
        "category": "C3",
        "label": "C3 balcony or roof used for floor activity",
        "q_rule": "access_area_min_4",
        "Q": 1.8,
    },
    "C4_DANCE_GYM": {"category": "C4", "label": "C4 dance hall or gymnasium", "q": 5.0, "Q": 3.6},
    "C4_DRILL_HALL": {"category": "C4", "label": "C4 drill hall", "q": 5.0, "Q": 9.0},
    "C5_ASSEMBLY": {
        "category": "C5",
        "label": "C5 assembly susceptible to overcrowding",
        "q": 5.0,
        "Q": 3.6,
    },
    "C5_STAGE": {"category": "C5", "label": "C5 public assembly stage", "q": 7.5, "Q": 4.5},
    "D_SHOP": {"category": "D", "label": "D shopping area", "q": 4.0, "Q": 3.6},
    "E_READING_BOOKS": {
        "category": "E",
        "label": "E reading room with book storage",
        "q": 4.0,
        "Q": 4.5,
    },
    "E_GENERAL_STORAGE": {
        "category": "E",
        "label": "E general storage by height",
        "height_factor": 2.4,
        "Q": 7.0,
    },
    "E_OFFICE_COMPACTUS": {
        "category": "E",
        "label": "E free-rolling office compactus by height",
        "height_factor": 3.0,
        "Q_rule": "input",
    },
    "E_FILE_ROOM": {"category": "E", "label": "E file room or strongroom", "q": 5.0, "Q": 4.5},
    "E_BOOK_STACKS": {
        "category": "E",
        "label": "E book stacks by height",
        "height_factor": 3.3,
        "Q": 7.0,
    },
    "E_PAPER_STORAGE": {
        "category": "E",
        "label": "E paper storage by height",
        "height_factor": 4.0,
        "Q": 9.0,
    },
    "E_MOBILE_STACKING": {
        "category": "E",
        "label": "E mobile stacking storage",
        "height_factor": 4.0,
        "q_min": 10.0,
        "Q_rule": "input",
    },
    "E_COLD_STORAGE": {
        "category": "E",
        "label": "E cold storage by height",
        "height_factor": 4.5,
        "q_min": 15.0,
        "Q": 9.0,
    },
    "E_PLANT_ROOM": {"category": "E", "label": "E plant or fan room", "q": 5.0, "Q": 4.5},
    "E_BOILER_ROOM": {
        "category": "E",
        "label": "E boiler room around equipment",
        "q": 5.0,
        "Q": 4.5,
    },
    "F_LIGHT_VEHICLE": {"category": "F", "label": "F light vehicle area", "q": 2.5, "Q": 13.0},
    "G_MEDIUM_VEHICLE": {
        "category": "G",
        "label": "G medium vehicle area",
        "q": 5.0,
        "Q": 31.0,
        "point_area_m2": 0.025,
    },
}


def _floor_occupancy(row: Mapping[str, Any]) -> str:
    category = str(row["category"])
    if category == "A":
        return "residential"
    if category == "B":
        return "office"
    if category == "D":
        return "retail"
    if category == "E":
        return "storage"
    if category == "F":
        return "parking"
    return "other"


def run_self_weight(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(SELF_WEIGHT_INPUT_SCHEMA, inputs)
    unit_weight = positive_number(inputs, "unit_weight_kn_m3", allow_zero=True)
    thickness = positive_number(inputs, "thickness_m", allow_zero=True)
    area = positive_number(inputs, "area_m2", allow_zero=True)
    q = unit_weight * thickness
    return {
        "calculation": "structural.as1170.part1.self_weight",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["2.1", "2.2", "Appendix A"],
        "unit_weight_kn_m3": unit_weight,
        "thickness_m": thickness,
        "area_m2": area,
        "permanent_action_kpa": q,
        "permanent_action_kn": q * area,
        "full_standard_compliance": False,
        "assumptions": [
            "Unit weight is supplied by the user from an applicable material source "
            "or project specification."
        ],
    }


def run_partition_allowance(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(PARTITION_INPUT_SCHEMA, inputs)
    area = positive_number(inputs, "area_m2", allow_zero=True)
    q = 0.5
    return {
        "calculation": "structural.as1170.part1.movable_partition_allowance",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["2.3"],
        "allowance_kpa": q,
        "area_m2": area,
        "permanent_action_kn": q * area,
        "full_standard_compliance": False,
        "notes": [
            "Use the actual partition layout and weight when known; this is the "
            "minimum uniform allowance for movable partitions."
        ],
    }


def run_floor_action(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(FLOOR_ACTION_INPUT_SCHEMA, inputs)
    row_id = str(inputs["row_id"])
    row = FLOOR_ACTIONS[row_id]
    supported_area = positive_number(inputs, "supported_area_m2")
    q = row.get("q")
    if "height_factor" in row:
        storage_height = positive_number(inputs, "storage_height_m")
        q = float(row["height_factor"]) * storage_height
        if "q_min" in row:
            q = max(q, float(row["q_min"]))
    if row.get("q_rule") == "access_area_min_4":
        q = max(4.0, positive_number(inputs, "adjacent_access_q_kpa", allow_zero=True))

    point_load = row.get("Q")
    if row.get("Q_rule") == "input":
        raw = inputs.get("provided_concentrated_action_kn")
        point_load = (
            None if raw is None else positive_number(inputs, "provided_concentrated_action_kn")
        )
    elif point_load is not None:
        point_load = float(point_load)

    reduction_restricted = (
        row["category"] in {"C3", "C4", "C5", "F", "G"}
        or bool(inputs.get("one_way_slab", False))
        or bool(inputs.get("specific_machinery_allowance", False))
        or (q is not None and float(q) > 5.0)
    )
    psi_a = (
        1.0
        if reduction_restricted or q is None
        else min(1.0, max(0.5, 0.3 + 3.0 / math.sqrt(supported_area)))
    )
    reduced_q = None if q is None else float(q) * psi_a
    conditional_load_cases = (
        [
            {
                "id": "independent_stair_tread_or_landing_line_action",
                "condition": (
                    "The tread or landing is structurally independent of adjoining elements."
                ),
                "line_action_kn_m": 2.2,
            }
        ]
        if row_id == "A1_STAIRS"
        else []
    )
    factors = {
        "A": "residential",
        "B": "office",
        "D": "retail",
        "E": "storage",
        "F": "parking",
        "G": "parking",
    }
    return {
        "calculation": "structural.as1170.part1.floor_action",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["3.1", "3.2", "3.3", "3.4.1", "3.4.2", "Table 3.1"],
        "row_id": row_id,
        "category": row["category"],
        "label": row["label"],
        "characteristic_uniform_action_kpa": q,
        "area_reduction_factor_psi_a": psi_a,
        "reduction_restricted": reduction_restricted,
        "reduced_uniform_action_kpa": reduced_q,
        "concentrated_action_kn": point_load,
        "uniform_line_action_kn_m": row.get("line"),
        "concentrated_load_area_mm2": row.get("point_area_mm2"),
        "conditional_load_cases": conditional_load_cases,
        "supported_area_m2": supported_area,
        "occupancy_factor_class": factors.get(row["category"], "other"),
        "full_standard_compliance": False,
        "notes": [
            "The area reduction is for uniformly distributed floor actions only; "
            "concentrated and line actions are not reduced.",
            "C3-C5, F-G, storage actions exceeding 5 kPa, one-way slabs and "
            "specifically allowed machinery actions are not reduced.",
            "A user-supplied concentrated action is required where the reference "
            "row marks that value as project-calculated.",
        ],
    }


def run_roof_action(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(ROOF_ACTION_INPUT_SCHEMA, inputs)
    roof_type = str(inputs["roof_type"])
    element = str(inputs["element"])
    area = positive_number(inputs, "plan_area_supported_m2")
    house_roof = bool(inputs.get("house_roof", False))
    if roof_type == "R1":
        if "accessible_from_adjacent" not in inputs:
            raise ValueError("accessible_from_adjacent is required for an R1 roof")
        accessible_from_adjacent = bool(inputs["accessible_from_adjacent"])
        q = 1.5 if accessible_from_adjacent else 1.0
        point = 1.8
    elif element == "maintenance_surface":
        q = None
        point = 0.5
    elif house_roof and element == "structural_element":
        q = 0.25
        point = 1.1
    else:
        q = max(1.8 / math.sqrt(area) + 0.12, 0.25)
        point = 1.4 if element == "structural_element" else 1.1

    cases = []
    if q is not None:
        cases.append(
            {"id": "reference_uniform_roof_action", "uniform_action_kpa": q, "area_m2": None}
        )
    if roof_type == "R2" and element == "structural_element" and area > 200.0 and not house_roof:
        cases.append(
            {
                "id": "large_roof_patch_action",
                "uniform_action_kpa": 0.25,
                "area_m2": 200.0,
                "note": "Apply over the 200 m2 region producing the most adverse effect.",
            }
        )
    return {
        "calculation": "structural.as1170.part1.roof_action",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["3.5.1", "3.5.2", "Table 3.2"],
        "roof_type": roof_type,
        "element": element,
        "plan_area_supported_m2": area,
        "uniform_action_kpa": q,
        "concentrated_action_kn": point,
        "uniform_action_cases": cases,
        "full_standard_compliance": False,
        "notes": [
            "Use the floor action calculator for roofs used for floor-type activities.",
            "The large-roof patch action is a separate adverse load case, not "
            "additive to the full-area case.",
            "Roof shape, wind, snow and ponding actions are not generated here.",
        ],
    }


def run_roof_person_action(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Return the Part 1 person action for a specified roof or ceiling component."""

    validate_inputs(ROOF_PERSON_ACTION_INPUT_SCHEMA, inputs)
    element_description = str(inputs["element_description"]).strip()
    if not element_description:
        raise ValueError("element_description must not be empty")
    return {
        "calculation": "structural.as1170.part1.roof_person_action",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["3.5.2"],
        "element_description": element_description,
        "separate_load_cases": [
            {"id": "person_concentrated_action", "concentrated_action_kn": 1.4}
        ],
        "full_standard_compliance": False,
        "notes": [
            "Applies when the component is required to support a person for any purpose.",
            "This action is separate from the Table 3.2 maintenance roof actions.",
        ],
    }


BARRIER_ACTIONS: dict[str, dict[str, Any]] = {
    "A_SINGLE_DWELLING": {
        "top_horizontal": 0.35,
        "top_vertical": 0.35,
        "top_point": 0.6,
        "infill_kpa": 0.5,
        "infill_point": 0.25,
    },
    "A_OTHER_RESIDENTIAL": {
        "top_horizontal": 0.75,
        "top_vertical": 0.75,
        "top_point": 0.6,
        "infill_kpa": 1.0,
        "infill_point": 0.5,
    },
    "BE_NARROW_ACCESS": {
        "top_horizontal": 0.22,
        "top_vertical": 0.22,
        "top_point": 0.6,
        "infill_kpa": None,
        "infill_point": None,
    },
    "BE_FIXED_ACCESS": {
        "top_horizontal": 0.35,
        "top_vertical": 0.35,
        "top_point": 0.6,
        "infill_kpa": None,
        "infill_point": None,
    },
    "BE_GENERAL": {
        "top_horizontal": 0.75,
        "top_vertical": 0.75,
        "top_point": 0.6,
        "infill_kpa": 1.0,
        "infill_point": 0.5,
    },
    "C1_C2": {
        "top_horizontal": 1.5,
        "top_vertical": 0.75,
        "top_point": 0.6,
        "infill_kpa": 1.5,
        "infill_point": 1.5,
    },
    "C3": {
        "top_horizontal": 0.75,
        "top_vertical": 0.75,
        "top_point": 0.6,
        "infill_kpa": 1.0,
        "infill_point": 0.5,
    },
    "C5": {
        "top_horizontal": 3.0,
        "top_vertical": 0.75,
        "top_point": 0.6,
        "infill_kpa": 1.5,
        "infill_point": 1.5,
    },
    "D_RETAIL": {
        "top_horizontal": 1.5,
        "top_vertical": 0.75,
        "top_point": 0.6,
        "infill_kpa": 1.5,
        "infill_point": 1.5,
    },
    "FG_PEDESTRIAN": {
        "top_horizontal": 1.5,
        "top_vertical": 0.75,
        "top_point": 0.6,
        "infill_kpa": 1.5,
        "infill_point": 1.5,
    },
}


def run_barrier_action(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(BARRIER_ACTION_INPUT_SCHEMA, inputs)
    row_id = str(inputs["barrier_class"])
    row = BARRIER_ACTIONS[row_id]
    return {
        "calculation": "structural.as1170.part1.barrier_action",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["3.6", "Table 3.3"],
        "barrier_class": row_id,
        "separate_load_cases": {
            "top_edge_horizontal_line_kn_m": row["top_horizontal"],
            "top_edge_vertical_line_kn_m": row["top_vertical"],
            "top_edge_concentrated_kn": row["top_point"],
            "infill_uniform_pressure_kpa": row["infill_kpa"],
            "infill_concentrated_kn": row["infill_point"],
        },
        "infill_concentrated_loaded_area_mm2": 2000,
        "full_standard_compliance": False,
        "notes": [
            "The line, infill uniform and infill concentrated actions are "
            "separate, non-additive load cases.",
            "The 0.6 kN top-edge point action acts inwards, outwards or downwards "
            "for the adverse position.",
            "Do not combine these imposed actions concurrently with wind or "
            "earthquake actions under this clause.",
        ],
    }


VERTICAL_DYNAMIC_FACTORS: dict[str, tuple[float, str]] = {
    "lift_moving_components": (2.0, "moving components supported by lift structure"),
    "electric_overhead_crane_gantry": (
        1.25,
        "static crane wheel loads on gantry girders and connections",
    ),
    "hand_operated_crane_gantry": (
        1.1,
        "static crane wheel loads on gantry girders and connections",
    ),
    "non_reciprocating_machinery": (1.2, "machinery self-weight on supports"),
    "reciprocating_machinery": (1.5, "machinery self-weight on supports"),
}


def run_crane_vertical_action(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(CRANE_VERTICAL_INPUT_SCHEMA, inputs)
    machine = str(inputs["machine_type"])
    static_action = positive_number(inputs, "static_action_kn", allow_zero=True)
    factor, basis = VERTICAL_DYNAMIC_FACTORS[machine]
    return {
        "calculation": "structural.as1170.part1.crane_vertical_action",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["3.7.1", "3.7.2", "Table 3.4"],
        "machine_type": machine,
        "dynamic_factor": factor,
        "factor_basis": basis,
        "static_action_kn": static_action,
        "design_action_kn": factor * static_action,
        "full_standard_compliance": False,
        "notes": [
            "Use manufacturer or referenced machinery-standard actions when "
            "available; this factor method is the fallback."
        ],
    }


def run_crane_rail_action(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(CRANE_RAIL_INPUT_SCHEMA, inputs)
    crane = str(inputs["crane_type"])
    transverse_factor, parallel_factor = (
        (0.2, 0.1) if crane == "electric_overhead" else (0.05, 0.05)
    )
    transverse_base = positive_number(inputs, "combined_crab_and_lifted_load_kn", allow_zero=True)
    parallel_base = positive_number(inputs, "static_rail_wheel_load_kn", allow_zero=True)
    return {
        "calculation": "structural.as1170.part1.crane_rail_action",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["3.7.3.1", "3.7.3.2", "3.7.3.3"],
        "crane_type": crane,
        "transverse_factor": transverse_factor,
        "transverse_action_kn": transverse_factor * transverse_base,
        "parallel_factor": parallel_factor,
        "parallel_action_kn": parallel_factor * parallel_base,
        "acting_level": "rail-head level",
        "full_standard_compliance": False,
        "notes": [
            "Consider transverse and parallel actions together with the vertical "
            "load; buffer actions are determined under AS 1418."
        ],
    }


def run_carpark_action(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(CARPARK_INPUT_SCHEMA, inputs)
    mass = positive_number(inputs, "gross_vehicle_mass_kg")
    if mass > 10000.0:
        raise ValueError("AS/NZS 1170.1 Clause 3.8 classes used here stop at 10 000 kg gross mass")
    traffic = "light" if mass <= 2500.0 else "medium"
    impact = 30.0 if traffic == "light" else 40.0
    height = 0.5 if traffic == "light" else 1.0
    ramp_length = positive_number(
        {"downward_ramp_length_m": inputs.get("downward_ramp_length_m", 0.0)},
        "downward_ramp_length_m",
        allow_zero=True,
    )
    ramp_case = (
        traffic == "light" and bool(inputs.get("downward_travel", False)) and ramp_length > 20.0
    )
    if ramp_case:
        impact = 240.0
    gross_weight = mass * 9.80665 / 1000.0
    return {
        "calculation": "structural.as1170.part1.carpark_action",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["3.8", "Table 3.1"],
        "gross_vehicle_mass_kg": mass,
        "traffic_class": traffic,
        "gross_vehicle_weight_kn": gross_weight,
        "braking_action_kn": 0.5 * gross_weight,
        "barrier_impact_action_kn": impact,
        "impact_distribution_length_m": 1.5,
        "impact_height_above_floor_m": height,
        "special_downward_ramp_case": ramp_case,
        "full_standard_compliance": False,
        "notes": [
            "Vehicle braking and barrier impact are separate action cases. "
            "Vehicle actions above 10 000 kg need project-specific design."
        ],
    }


def run_grandstand_action(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(GRANDSTAND_INPUT_SCHEMA, inputs)
    area = positive_number(inputs, "plan_area_m2", allow_zero=True)
    seat_length = positive_number(inputs, "seat_length_m", allow_zero=True)
    if inputs["seating"]:
        if seat_length == 0.0:
            raise ValueError("seat_length_m must be positive for a seated grandstand")
        cases = [
            {"id": "crowd_along_seats", "line_action_kn_m": 0.35, "loaded_length_m": seat_length},
            {"id": "crowd_across_seats", "line_action_kn_m": 0.15, "loaded_length_m": seat_length},
        ]
    else:
        cases = [
            {"id": "crowd_on_unseated_platform", "uniform_action_kpa": 0.25, "plan_area_m2": area}
        ]
    return {
        "calculation": "structural.as1170.part1.grandstand_action",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["3.9"],
        "seating": bool(inputs["seating"]),
        "separate_load_cases": cases,
        "full_standard_compliance": False,
        "notes": [
            "The seated crowd cases are alternatives, not simultaneous; these "
            "actions need not be concurrent with earthquake action."
        ],
    }


def run_static_liquid_pressure(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(FLUID_PRESSURE_INPUT_SCHEMA, inputs)
    depth = positive_number(inputs, "liquid_depth_m", allow_zero=True)
    unit_weight = positive_number(inputs, "unit_weight_kn_m3")
    width = positive_number(inputs, "wall_width_m", allow_zero=True)
    base_pressure = unit_weight * depth
    resultant = 0.5 * unit_weight * depth**2
    return {
        "calculation": "structural.as1170.part1.static_liquid_pressure",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["4.1", "4.2"],
        "liquid_depth_m": depth,
        "unit_weight_kn_m3": unit_weight,
        "base_pressure_kpa": base_pressure,
        "resultant_action_kn_per_m_width": resultant,
        "resultant_action_kn": resultant * width,
        "resultant_height_above_base_m": depth / 3.0 if depth else 0.0,
        "full_standard_compliance": False,
        "assumptions": [
            "Static fluid pressure varies linearly from zero at the free surface "
            "to the calculated base pressure."
        ],
    }


def run_groundwater_pressure(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(GROUNDWATER_INPUT_SCHEMA, inputs)
    depth = positive_number(inputs, "water_head_m", allow_zero=True)
    width = positive_number(inputs, "wall_width_m", allow_zero=True)
    unit_weight = float(inputs.get("water_unit_weight_kn_m3", 9.81))
    base_pressure = unit_weight * depth
    resultant = 0.5 * unit_weight * depth**2
    return {
        "calculation": "structural.as1170.part1.groundwater_pressure",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["4.1", "4.3"],
        "water_head_m": depth,
        "water_unit_weight_kn_m3": unit_weight,
        "base_pressure_kpa": base_pressure,
        "resultant_action_kn_per_m_width": resultant,
        "resultant_action_kn": resultant * width,
        "resultant_height_above_base_m": depth / 3.0 if depth else 0.0,
        "full_standard_compliance": False,
        "notes": [
            "Select the water level at ground level or the appropriate 1-in-50 "
            "annual probability level; the level is a project input."
        ],
    }


def run_rainwater_ponding(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(PONDING_INPUT_SCHEMA, inputs)
    depth = positive_number(inputs, "design_ponding_depth_including_sag_m", allow_zero=True)
    area = positive_number(inputs, "ponded_area_m2", allow_zero=True)
    unit_weight = float(inputs.get("water_unit_weight_kn_m3", 9.81))
    q = depth * unit_weight
    return {
        "calculation": "structural.as1170.part1.rainwater_ponding",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["4.1", "4.4"],
        "design_ponding_depth_including_sag_m": depth,
        "water_unit_weight_kn_m3": unit_weight,
        "action_kpa": q,
        "ponded_area_m2": area,
        "action_kn": q * area,
        "full_standard_compliance": False,
        "notes": [
            "Supply a ponding depth from the drainage and short-/long-term "
            "deflection assessment; this function does not solve ponding instability."
        ],
    }


def run_earth_pressure_resultant(inputs: Mapping[str, Any]) -> dict[str, Any]:
    validate_inputs(EARTH_PRESSURE_INPUT_SCHEMA, inputs)
    height = positive_number(inputs, "retained_height_m", allow_zero=True)
    width = positive_number(inputs, "wall_width_m", allow_zero=True)
    top = positive_number(inputs, "pressure_at_top_kpa", allow_zero=True)
    bottom = positive_number(inputs, "pressure_at_base_kpa", allow_zero=True)
    resultant_per_m = 0.5 * (top + bottom) * height
    centroid = (
        0.0 if top + bottom == 0.0 else height * (2.0 * top + bottom) / (3.0 * (top + bottom))
    )
    return {
        "calculation": "structural.as1170.part1.earth_pressure_resultant",
        "standard": STANDARD_1.descriptor(),
        "clauses": ["4.1", "4.5"],
        "retained_height_m": height,
        "pressure_at_top_kpa": top,
        "pressure_at_base_kpa": bottom,
        "resultant_action_kn_per_m_width": resultant_per_m,
        "resultant_action_kn": resultant_per_m * width,
        "resultant_height_above_base_m": centroid,
        "full_standard_compliance": False,
        "notes": [
            "The soil pressure profile must be determined by an appropriate "
            "geotechnical method; this function integrates the supplied linear "
            "profile only."
        ],
    }


def _positive_property(minimum: float | None = None) -> dict[str, Any]:
    return (
        _prop_number(minimum=minimum)
        if minimum is not None
        else _prop_number(exclusive_minimum=0.0)
    )


SELF_WEIGHT_INPUT_SCHEMA = _schema(
    ["unit_weight_kn_m3", "thickness_m", "area_m2"],
    {
        "unit_weight_kn_m3": _prop_number(minimum=0),
        "thickness_m": _prop_number(minimum=0),
        "area_m2": _prop_number(minimum=0),
    },
)
PARTITION_INPUT_SCHEMA = _schema(["area_m2"], {"area_m2": _prop_number(minimum=0)})
FLOOR_ACTION_INPUT_SCHEMA = _schema(
    ["row_id", "supported_area_m2"],
    {
        "row_id": {"type": "string", "enum": sorted(FLOOR_ACTIONS)},
        "supported_area_m2": _positive_property(),
        "storage_height_m": _positive_property(),
        "adjacent_access_q_kpa": _prop_number(minimum=0),
        "one_way_slab": {"type": "boolean"},
        "specific_machinery_allowance": {"type": "boolean"},
        "provided_concentrated_action_kn": _prop_number(minimum=0),
    },
)
ROOF_ACTION_INPUT_SCHEMA = _schema(
    ["roof_type", "element", "plan_area_supported_m2"],
    {
        "roof_type": {"enum": ["R1", "R2"]},
        "element": {"enum": ["structural_element", "cladding", "maintenance_surface"]},
        "plan_area_supported_m2": _positive_property(),
        "accessible_from_adjacent": {"type": "boolean"},
        "house_roof": {"type": "boolean"},
    },
)
ROOF_PERSON_ACTION_INPUT_SCHEMA = _schema(
    ["element_description"],
    {"element_description": {"type": "string", "minLength": 1}},
)
BARRIER_ACTION_INPUT_SCHEMA = _schema(
    ["barrier_class"], {"barrier_class": {"type": "string", "enum": sorted(BARRIER_ACTIONS)}}
)
CRANE_VERTICAL_INPUT_SCHEMA = _schema(
    ["machine_type", "static_action_kn"],
    {
        "machine_type": {"enum": sorted(VERTICAL_DYNAMIC_FACTORS)},
        "static_action_kn": _prop_number(minimum=0),
    },
)
CRANE_RAIL_INPUT_SCHEMA = _schema(
    ["crane_type", "combined_crab_and_lifted_load_kn", "static_rail_wheel_load_kn"],
    {
        "crane_type": {"enum": ["electric_overhead", "hand_operated"]},
        "combined_crab_and_lifted_load_kn": _prop_number(minimum=0),
        "static_rail_wheel_load_kn": _prop_number(minimum=0),
    },
)
CARPARK_INPUT_SCHEMA = _schema(
    ["gross_vehicle_mass_kg"],
    {
        "gross_vehicle_mass_kg": _positive_property(),
        "downward_travel": {"type": "boolean"},
        "downward_ramp_length_m": _prop_number(minimum=0),
    },
)
GRANDSTAND_INPUT_SCHEMA = _schema(
    ["seating", "plan_area_m2", "seat_length_m"],
    {
        "seating": {"type": "boolean"},
        "plan_area_m2": _prop_number(minimum=0),
        "seat_length_m": _prop_number(minimum=0),
    },
)
FLUID_PRESSURE_INPUT_SCHEMA = _schema(
    ["liquid_depth_m", "unit_weight_kn_m3", "wall_width_m"],
    {
        "liquid_depth_m": _prop_number(minimum=0),
        "unit_weight_kn_m3": _positive_property(),
        "wall_width_m": _prop_number(minimum=0),
    },
)
GROUNDWATER_INPUT_SCHEMA = _schema(
    ["water_head_m", "wall_width_m"],
    {
        "water_head_m": _prop_number(minimum=0),
        "wall_width_m": _prop_number(minimum=0),
        "water_unit_weight_kn_m3": _positive_property(),
    },
)
PONDING_INPUT_SCHEMA = _schema(
    ["design_ponding_depth_including_sag_m", "ponded_area_m2"],
    {
        "design_ponding_depth_including_sag_m": _prop_number(minimum=0),
        "ponded_area_m2": _prop_number(minimum=0),
        "water_unit_weight_kn_m3": _positive_property(),
    },
)
EARTH_PRESSURE_INPUT_SCHEMA = _schema(
    ["retained_height_m", "wall_width_m", "pressure_at_top_kpa", "pressure_at_base_kpa"],
    {
        "retained_height_m": _prop_number(minimum=0),
        "wall_width_m": _prop_number(minimum=0),
        "pressure_at_top_kpa": _prop_number(minimum=0),
        "pressure_at_base_kpa": _prop_number(minimum=0),
    },
)
