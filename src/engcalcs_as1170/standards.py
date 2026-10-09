"""Edition and clause provenance for supported AS/NZS 1170 calculations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StandardReference:
    designation: str
    amendments: tuple[str, ...]
    status_checked: str
    clauses: tuple[str, ...]

    def descriptor(self) -> dict[str, object]:
        return {
            "designation": self.designation,
            "amendments": list(self.amendments),
            "catalogue_status": "current",
            "status_checked": self.status_checked,
            "clauses": list(self.clauses),
            "full_standard_compliance": False,
        }


STANDARD_0 = StandardReference(
    "AS/NZS 1170.0:2002",
    ("Amendment 1", "Amendment 2", "Amendment 3", "Amendment 4", "Amendment 5"),
    "2026-10-05",
    (
        "4.2.1",
        "4.2.2",
        "4.2.3",
        "4.2.4",
        "4.3",
        "6.2.2",
        "6.2.3",
        "6.2.5",
    ),
)

STANDARD_1 = StandardReference(
    "AS/NZS 1170.1:2002",
    ("Amendment 1", "Amendment 2"),
    "2026-10-05",
    (
        "2.1-2.4",
        "3.1-3.9",
        "4.1-4.5",
        "Appendix A",
        "Appendix B",
    ),
)

WIND_SCOPE_NOTICE = (
    "Wind action generation under AS/NZS 1170.2 is outside this package. The AS/NZS 1170.0 "
    "combination runner accepts a user-supplied wind action effect for "
    "combinations that include it."
)
