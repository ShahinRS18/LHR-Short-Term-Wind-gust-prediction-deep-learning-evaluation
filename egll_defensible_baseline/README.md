# EGLL conservative preprocessing baseline

The specified target is an accepted observed main-wind gust >=28 knots during **(t,t+1 hour]**, for hourly Heathrow UTC origins in 2005–2024. This is a retrospective data baseline; no model was trained.

| Hourly target state | Count |
|---|---:|
| Positive | 2,817 |
| Negative | 171,955 |
| Unknown | 548 |
| Total | 175,320 |

## Read first

- target_specification.md: fixed target, verified cadence, provisional policies and availability limits.
- timestamp_alignment_report.md: inspected/implemented/executed/verified work and unresolved cases.

## Data outputs

- hourly_gust_targets.csv: all hourly labels, boundaries, coverage, accepted maxima/times and source IDs. Unknown target_y cells are blank.
- report_extraction_quality.csv.gz: every raw report, extraction values, native/converted units, timestamp alternatives, source file/line, parser/quality/version/availability status. Gzip-compressed CSV can be opened directly with pandas or decompressed with an archive tool.
- unresolved_case_ledger.csv: ten quarantined report records, adjacent raw text and possible affected origins.
- monthly_reporting_cadence.csv: 240 month-level cadence checks.
- netcdf_sounding_alignment.csv: 80 source-file time-unit/calendar and matching checks.
- weather_feature_keys.csv and weather_feature_keys_hot/cold.csv: verified validity keys with pointers to unchanged annual sounding CSVs; no copied feature matrix.
- metar_predictor_candidates.csv: backward wind observation candidates; observation times <=t and ages <=60 minutes. Receipt/revision availability is unverified.
- cloud_indicator_candidates.csv: separate past cloud indicators, not the gust target or proof of convective causation.
- unknown_hourly_windows.csv and yearly_target_counts.csv: eligibility review and annual counts.
- raw_to_parsed_examples.csv: actual examples.
- source_manifest.csv: source-file hashes.
- execution_summary.json and verification_results.json: executed counts and 34 passed checks.

The report counts (7,662 gust reports and 3,450 threshold reports), positive hourly samples (2,817) and independent events are different quantities. Independent events are not defined/countable from this output without an explicit grouping rule.

## Reproduction and student review

build_baseline.py and verify_baseline.py are AI-generated and must be reviewed by the student. They use the existing local Python dependencies, do not train models, and write only into this output directory. Run build_baseline.py then verify_baseline.py from this workspace. Audit examples and these human-readable summaries reflect this executed run.

A full feature export, model training and operational availability validation remain outside this minimal baseline. See the availability limitations before using these inputs in a forecasting dissertation.
