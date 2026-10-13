# Timestamp alignment and extraction execution report

Executed 13 October 2026. AI-generated code for student review. Sources are preserved; outputs are isolated in this directory.

## Inspected

Read the user instruction attachment, the supplied root gust_timestamp_audit.md, the audit under convectives/audit and its supporting findings. Inspected README provenance, the sounding computation scripts and seasonal row-position pipeline, raw EGLL records, neighboring records around the timestamp conflict, and the strongest EGLL main gusts.

## Implemented and executed

- Parsed all 349,995 EGLL archive records.
- Accepted 349,985 retrospective report records; quarantined 10 unresolved records. These report exclusions are not discarded hourly samples.
- Retained 7,662 observed gust reports, including 3,450 reports >=28 knots.
- Built 175,320 hourly origins: **2,817 positive**, **171,955 negative**, **548 unknown**. No hourly origin was dropped. Unknown labels are blank.
- Verified :20/:50 routine cadence in 240 months. Full two-slot coverage is stricter than the old audit's count of empty hours, explaining the larger unknown count.
- Rechecked 80 Heathrow source NetCDF time coordinates across four variables and 20 years, including units/calendar decoding. Cross-checked all 20 annual sounding filename-date sequences.
- Matched 175,320 sounding/target keys with one-to-one outer-join checks and no unmatched keys, duplicate dates or missing expected NetCDF dates.
- Created timestamped hot/cold seasonal key exports that reference the unchanged annual feature values. Full feature matrices were intentionally not rebuilt for this minimal baseline.
- Matched METAR candidates backward within a provisional 60-minute tolerance. 111 origins have no candidate within that tolerance; 12 have recent unresolved-record flags. No future observation is matched to an earlier origin.
- Kept target/coverage, past cloud indicators and wind candidate columns in separate outputs.

## Verified

34 executed checks passed. They cover observed versus forecast/remarks gusts, missing numeric gusts and routine reports, AUTO/COR, identical duplicates and conflicting corrections, conversions, suspicious values, inclusive 28-knot threshold, exact left/right endpoints, month/year/leap boundaries, archive truncation, shuffled/missing/duplicate source rows, predictor age/time bounds and source manifest hashes. Actual report-gust counts, threshold-report counts and the complete set of positive hourly origins were also reconstructed independently from raw main-wind strings.

Actual examples and provenance are in raw_to_parsed_examples.csv. Boundary and version-conflict cases absent from the local archive were exercised synthetically, not presented as observed records. Verification results are in verification_results.json.

## Remains unresolved

The ten quarantined records contain malformed headers/winds, missing main wind and one archive/header date disagreement. The disagreement is EGLL source line 27441: archive 2006-07-29 03:00 versus reconstructed header 2006-07-30 03:50. Neighboring rows and a separate record near the candidate header time show a suspicious archive entry, but no download manifest or authoritative receipt provenance establishes which timestamp should be accepted. Both possible target origins are flagged; the record is excluded from accepted predictors and targets.

There are 296,455 correction-marked records. Receipt and revision timestamps are absent, so operational predictor availability remains unverified. In addition, same-hour ERA5 features are retrospective inputs rather than operationally available forecasts. These limitations prevent a defensible claim of deployable one-hour forecast performance.

No independent-event count has been calculated; the 2,817 positive hours can include adjacent hours of the same storm. Existing cloud-label metrics were not used. No model was trained.

The 2024-12-31 23:00 origin is positive based on observed 29/30-knot gust reports; its endpoint-coverage flag remains false because 2025-01-01 00:00 is beyond the supplied archive. No extrapolation of outcomes is used.

Original source hashes were checked again after execution and matched the manifest. Source values were not edited, repaired, capped or replaced.
