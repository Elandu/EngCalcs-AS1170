# SPDX-License-Identifier: LicenseRef-EngCalcs-Proprietary

"""Input validation shared by the calculation families."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jsonschema import Draft202012Validator


def validate_inputs(schema: dict[str, Any], inputs: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(inputs)), key=lambda err: list(err.path)
    )
    if errors:
        error = errors[0]
        path = ".".join(str(item) for item in error.path) or "inputs"
        raise ValueError(f"Invalid {path}: {error.message}")


def positive_number(inputs: Mapping[str, Any], name: str, *, allow_zero: bool = False) -> float:
    value = inputs.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    result = float(value)
    if result < 0 or (result == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {qualifier}")
    return result


def action_value(inputs: Mapping[str, Any], name: str) -> float:
    value = inputs.get(name, 0.0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"action_effects.{name} must be a number")
    return float(value)
