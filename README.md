# EngCalcs AS 1170

Standalone EngCalcs plugin for Australian structural design actions under the non-wind parts of the AS/NZS 1170 series. The module is separate from OpenWind. AS/NZS 1170.2 wind-action generation is excluded; Part 0 combination calculations can accept a wind effect supplied by another tool or the engineer.

## First implementation cycle

The current catalogue editions of Parts 0 and 1 are implemented in this first cycle:

- AS/NZS 1170.0:2002 incorporating Amendments 1-5: selected ultimate and serviceability combinations, special action factors, the fire combination and minimum robustness actions.
- AS/NZS 1170.1:2002 incorporating Amendments 1-2: self-weight and movable partition calculations, selected floor actions and the conditional independent stair tread/landing case, Table 3.2 roof actions and the separate roof/ceiling person action, barriers, machinery and crane actions, carparks, grandstands, liquid and groundwater pressure, rainwater ponding and supplied earth-pressure profiles.

The current Part 3 edition is AS/NZS 1170.3:2003 Amendment 2:2017. Part 4 is AS 1170.4:2024. They are not implemented yet because those current licensed PDFs were not present in the provided standards folder; the older local Part 4:2007 copy is superseded. See [the coverage matrix](docs/coverage.md).

## Scope and limitations

Each calculation identifies its edition and clauses, states important assumptions and returns `full_standard_compliance: false`. This package does not analyse a structure or decide which load case governs. Structural response and adverse sign selection remain engineering tasks. User-supplied material unit weights, equipment actions, ponding depths and geotechnical pressure profiles remain traceable inputs where the standard delegates those decisions.

The package does not contain copies, OCR, rendered pages or verbatim extracts of licensed standards. Reference action values are represented only where needed to execute the listed calculation rows. Numerical validation fixtures are independent calculations, not published worked examples.

## Install

```powershell
python -m pip install engcalcs-as1170
```

EngCalcs discovers the plugin through the `engcalcs.plugins` entry-point group as `as1170`.

## Local development

```powershell
python -m pip install -e '.[dev]'
python -m pytest
ruff check .
python -m build
```

Python 3.12 or later is required.
