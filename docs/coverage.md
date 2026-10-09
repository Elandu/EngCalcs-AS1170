# Edition and calculation coverage

Edition status was checked against the Standards Australia catalogue on 5 October 2026. Only the current edition is targeted for each part. Standard PDFs are licensed source material and are not included in this repository.

| Part | Current edition basis | Implemented in this first cycle | Source boundary |
| --- | --- | --- | --- |
| 1170.0 | AS/NZS 1170.0:2002, Amendments 1-5 | Selected ULS and SLS combinations, special action factors, fire combination, minimum lateral/tie/wall-anchorage actions | Does not perform structural analysis, annual-probability mapping, confirmation methods, detailed load-path design or whole-building compliance |
| 1170.1 | AS/NZS 1170.1:2002, Amendments 1-2 | Self-weight from supplied unit weight, movable-partition allowance, selected Table 3.1 floor actions and Clause 3.4.2 reduction, the conditional independent stair tread/landing line action, Table 3.2 roof actions, Clause 3.5.2 person action for specified roof/ceiling elements, Table 3.3 barrier actions, machinery/crane fallback factors, carpark and grandstand actions, liquid/groundwater/ponding and supplied earth-pressure profiles | Table 3.1 use cases are a selected subset; material unit weights, machinery/vendor actions, ponding depth and geotechnical pressure profiles are user inputs |
| 1170.3 | AS/NZS 1170.3:2003, Amendment 2:2017 | Not implemented yet | Current licensed source was not present in the supplied standards directory |
| 1170.4 | AS 1170.4:2024 | Not implemented yet | Only a superseded AS 1170.4:2007 copy was present; the 2024 edition must be reviewed before implementation |
| 1170.2 | Wind actions | Excluded | Wind action generation stays out of this package. Part 0 combinations accept externally supplied wind effects where required. |

The current Part 0 and Part 1 calculations are clause-traced and deliberately report `full_standard_compliance: false`. A calculation result is not a whole-structure design, engineering approval, or NCC compliance assessment.
