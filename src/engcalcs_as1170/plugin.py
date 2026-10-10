# SPDX-License-Identifier: LicenseRef-EngCalcs-Proprietary

"""Installed EngCalcs plugin descriptors for the AS/NZS 1170 action calculations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from engcalcs_as1170 import __version__
from engcalcs_as1170.part0 import (
    COMBINATION_INPUT_SCHEMA,
    ROBUSTNESS_INPUT_SCHEMA,
    run_combinations,
    run_robustness,
)
from engcalcs_as1170.part1 import (
    BARRIER_ACTION_INPUT_SCHEMA,
    CARPARK_INPUT_SCHEMA,
    CRANE_RAIL_INPUT_SCHEMA,
    CRANE_VERTICAL_INPUT_SCHEMA,
    EARTH_PRESSURE_INPUT_SCHEMA,
    FLOOR_ACTION_INPUT_SCHEMA,
    FLUID_PRESSURE_INPUT_SCHEMA,
    GRANDSTAND_INPUT_SCHEMA,
    GROUNDWATER_INPUT_SCHEMA,
    PARTITION_INPUT_SCHEMA,
    PONDING_INPUT_SCHEMA,
    ROOF_ACTION_INPUT_SCHEMA,
    ROOF_PERSON_ACTION_INPUT_SCHEMA,
    SELF_WEIGHT_INPUT_SCHEMA,
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
from engcalcs_as1170.standards import STANDARD_0, STANDARD_1, WIND_SCOPE_NOTICE, StandardReference

OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["calculation", "standard", "clauses", "full_standard_compliance"],
    "properties": {
        "calculation": {"type": "string"},
        "standard": {"type": "object"},
        "clauses": {"type": "array", "items": {"type": "string"}},
        "full_standard_compliance": {"const": False},
    },
    "additionalProperties": True,
}


@dataclass(frozen=True)
class Calculation:
    id: str
    name: str
    description: str
    input_schema: dict[str, Any]
    runner: Callable[[Mapping[str, Any]], dict[str, Any]]
    standard: StandardReference

    def run(self, inputs: Mapping[str, Any]) -> dict[str, Any]:
        return self.runner(inputs)

    def descriptor(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "discipline": "structural",
            "category": "design-actions",
            "jurisdiction": "AU",
            "version": "1",
            "standard": self.standard.descriptor(),
            "input_schema": deepcopy(self.input_schema),
            "output_schema": deepcopy(OUTPUT_SCHEMA),
        }


def _calculations() -> tuple[Calculation, ...]:
    return (
        Calculation(
            "structural.as1170.part0.combinations",
            "AS/NZS 1170.0 action combinations",
            "Generates strength, stability, serviceability and fire action "
            "combinations for supplied signed action effects.",
            COMBINATION_INPUT_SCHEMA,
            run_combinations,
            STANDARD_0,
        ),
        Calculation(
            "structural.as1170.part0.robustness",
            "AS/NZS 1170.0 minimum robustness actions",
            "Calculates minimum per-level lateral resistance, connection/tie "
            "action and wall anchorage action.",
            ROBUSTNESS_INPUT_SCHEMA,
            run_robustness,
            STANDARD_0,
        ),
        Calculation(
            "structural.as1170.part1.self_weight",
            "Permanent action from self-weight",
            "Calculates self-weight from user-supplied unit weight, thickness and supported area.",
            SELF_WEIGHT_INPUT_SCHEMA,
            run_self_weight,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.movable_partition_allowance",
            "Movable partition allowance",
            "Calculates the minimum uniform permanent action allowance for movable partitions.",
            PARTITION_INPUT_SCHEMA,
            run_partition_allowance,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.floor_action",
            "Imposed floor action",
            "Selects a Table 3.1 reference row and applies the permitted loaded-area "
            "reduction to the uniform action.",
            FLOOR_ACTION_INPUT_SCHEMA,
            run_floor_action,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.roof_action",
            "Maintenance roof action",
            "Calculates Table 3.2 maintenance actions for R1 and R2 roofs, including "
            "the large-roof patch case.",
            ROOF_ACTION_INPUT_SCHEMA,
            run_roof_action,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.roof_person_action",
            "Roof and ceiling person action",
            "Returns the Clause 3.5.2 concentrated action for a specified roof or ceiling "
            "component.",
            ROOF_PERSON_ACTION_INPUT_SCHEMA,
            run_roof_person_action,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.barrier_action",
            "Barrier imposed action",
            "Returns separate top-edge and infill load cases from Table 3.3.",
            BARRIER_ACTION_INPUT_SCHEMA,
            run_barrier_action,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.crane_vertical_action",
            "Vertical machinery dynamic action",
            "Applies the Part 1 fallback dynamic factor when manufacturer or "
            "referenced-standard data are unavailable.",
            CRANE_VERTICAL_INPUT_SCHEMA,
            run_crane_vertical_action,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.crane_rail_action",
            "Crane rail horizontal actions",
            "Calculates transverse and longitudinal crane rail actions from static wheel actions.",
            CRANE_RAIL_INPUT_SCHEMA,
            run_crane_rail_action,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.carpark_action",
            "Carpark vehicle and barrier actions",
            "Calculates vehicle braking and the light-/medium-traffic barrier impact cases.",
            CARPARK_INPUT_SCHEMA,
            run_carpark_action,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.grandstand_action",
            "Grandstand crowd action",
            "Calculates the separate seated or unseated crowd movement action cases.",
            GRANDSTAND_INPUT_SCHEMA,
            run_grandstand_action,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.static_liquid_pressure",
            "Static liquid pressure",
            "Calculates hydrostatic pressure and the resultant action on a vertical wall.",
            FLUID_PRESSURE_INPUT_SCHEMA,
            run_static_liquid_pressure,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.groundwater_pressure",
            "Groundwater pressure",
            "Calculates hydrostatic groundwater pressure for a user-selected design water level.",
            GROUNDWATER_INPUT_SCHEMA,
            run_groundwater_pressure,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.rainwater_ponding",
            "Rainwater ponding action",
            "Calculates the water action from a supplied ponding depth that includes "
            "the assessed roof sag.",
            PONDING_INPUT_SCHEMA,
            run_rainwater_ponding,
            STANDARD_1,
        ),
        Calculation(
            "structural.as1170.part1.earth_pressure_resultant",
            "Retained earth pressure resultant",
            "Integrates a user-supplied linear soil pressure profile; the "
            "geotechnical pressure method is external.",
            EARTH_PRESSURE_INPUT_SCHEMA,
            run_earth_pressure_resultant,
            STANDARD_1,
        ),
    )


@dataclass(frozen=True)
class AS1170Plugin:
    id: str = "structural.as1170"
    name: str = "EngCalcs Structural Actions"
    version: str = __version__
    revision: str | None = None
    license: str = "LicenseRef-EngCalcs-Proprietary"
    source: str = "https://github.com/Elandu/EngCalcs-AS1170"
    calculations: tuple[Calculation, ...] = field(default_factory=_calculations)

    def descriptor(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "revision": self.revision,
            "license": self.license,
            "source": self.source,
            "scope_notice": WIND_SCOPE_NOTICE,
            "calculations": [item.descriptor() for item in self.calculations],
        }


def get_plugin() -> AS1170Plugin:
    """Return the plugin descriptor without starting a service or solver."""
    return AS1170Plugin()
