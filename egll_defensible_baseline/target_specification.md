# EGLL defensible baseline target specification

AI-generated implementation and documentation for student review. Executed 13 October 2026. This is a retrospective preprocessing baseline, not a trained model or a demonstrated operational forecast.

## Fixed research choices

- Airport: Heathrow, ICAO EGLL. Hourly UTC origins from 2005-01-01 00:00 to 2024-12-31 23:00 inclusive.
- Threshold: reported main observed wind gust >=28 knots, compared before rounding.
- Horizon and interval: exactly one hour, **t < observation time s <= t+1h**.
- A report at t is excluded from that origin's target; a report at t+1h is included. The user's fixed specification supersedes the older audit's [t,t+1h) suggestion.
- All gust mechanisms are included. CB/TCU indicators are separate; no convective causation is inferred and clouds are not required for a positive label.
- This predicts a reported exceedance, not a continuously measured maximum or the absence of actual gusts between reports.
- Conversion: 1 knot = 1852/3600 m/s. Native values and units are retained; no rounding is used for classification. Missing G groups remain missing numerical gusts.

## Accepted report rule

A recognizable METAR/SPECI header, matching EGLL station, syntactically valid main wind and exact agreement between archive and reconstructed header timestamps are required. The parser handles COR before station and AUTO/COR after header, VRB winds and KT/MPS/KMH units. Only the first main wind group is parsed. TREND and remarks are stored separately and never substitute for observed gusts.

Header full dates are inferred using the nearest valid month-context date among previous/current/next months, including year boundaries. A disagreement is quarantined, never automatically resolved by the nearest-date heuristic. Malformed records are retained with raw text and provenance; recognizable alternative times are used only to flag possibly affected windows.

Syntax acceptance covers the header/main wind, not every field of a complete METAR. A report without a G group may support no *reported* exceedance under the coverage policy, but no numerical zero is inserted.

Identical versions are deduplicated without deleting provenance. A unique correction is preferred for retrospective outcomes; conflicting corrections are quarantined. Correction receipt times are not known. A malformed selected correction must not be replaced with an older valid report to force acceptance. No same-time duplicate/version groups were found in this EGLL execution, so these branches were verified using synthetic examples.

## Three target states

- **Positive:** one or more accepted reports meet the threshold within the target interval. A valid positive is sufficient despite incomplete coverage or another unresolved record.
- **Negative:** no accepted exceedance, both expected routine METAR slots populated with accepted wind reports, established cadence, no unresolved record potentially affecting the window, and no unresolved archive-boundary completeness issue.
- **Unknown:** a negative is not defensible under those conditions. target_y is blank, never zero.

Routine slots are :20 and :50. This was verified for all 240 monthly groups of header-resolved Heathrow METAR records. Additional SPECI records can establish positives but cannot replace a missing routine slot for a negative.

## Provisional policy choices

The two-slot negative policy is a conservative methodological choice supported by the observed cadence, not a guarantee of continuous coverage. Monthly cadence-establishment screens require two modal minutes to account for >=98% of resolved METAR headers and >=90% of potential slots individually. In this dataset the two modal minutes account for all such headers, and all months pass. This policy requires exact slot minutes; no undocumented rounding/tolerance is introduced.

Backward METAR candidate matching permits a maximum age of 60 minutes. This is a methodological default; missing or stale reports are not fabricated. Recent quarantined records create separate quality flags. Candidate reports are matched by observation time, not known receipt time, and are explicitly marked operationally unverified.

An 80-knot speed screen is a provisional manual-review trigger, not a physical ceiling or a statistical outlier deletion rule. Any triggered record retains its native values but is quarantined pending review. Gust below mean and invalid directions are also flagged. No EGLL speed record triggers these review checks; actual valid observed gusts reach 60 knots. The previous audit's 254KT and 151MPS cases are from other airports and remain untouched.

## End-of-archive policy

The archive ends at 2024-12-31 23:50 UTC; no 2025 reports were supplied. The last origin's closed endpoint is 2025-01-01 00:00 UTC. Its boundary completeness flag is false. It is nevertheless positive because its accepted :20 and :50 reports exceed 28 knots (maximum 30 knots). If no accepted exceedance existed, that last window would be unknown; tests verify this branch. No missing 2025 report is fabricated.

## Weather and information availability

Recover sounding validity time from filename, cross-check it against decoded source NetCDF coordinates using units/calendar metadata, and join by station and explicit UTC time with one-to-one validation. The constant annual numeric timestamp is not used for matching or as a predictor.

ERA5 is retrospective reanalysis; equal validity time does not establish information availability at origin t. Therefore weather keys are labelled retrospective and this baseline makes no operational forecast claim. ECMWF documents ERA5/ERA5T availability behind real time: https://confluence.ecmwf.int/pages/viewpage.action?pageId=669811810 .

The local METAR archive has no report receipt/revision timestamps. All matched METAR candidates are marked availability-unverified, particularly the correction-marked records. No revision order or receipt time is invented. This limitation must be resolved or explicitly accepted as a retrospective study assumption before modelling.

## Output separation and scope

hourly_gust_targets.csv holds outcomes and future-window coverage only. metar_predictor_candidates.csv holds backward candidate wind values, timestamps, age and quality/availability flags. cloud_indicator_candidates.csv keeps backward cloud indicators separate. weather_feature_keys.csv and its hot/cold exports retain verified keys and pointers to unchanged annual sounding values; they are not full rebuilt feature matrices. All target/feature joining must use those keys rather than existing seasonal row positions.

No model training, train/test split, feature selection, imputation, balancing or operational predictor release was performed. No independent-event definition/count was inferred. Existing cloud-classification metrics do not evaluate this gust target.
