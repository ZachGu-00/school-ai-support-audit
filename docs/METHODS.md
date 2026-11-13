# Analysis methods

## Questionnaires

`reproduce_survey.py` recomputes every marginal and joint count from the deposited respondent-level item responses. Benefit and concern are analysed within seven fixed same-respondent pairs. The primary threshold is 4 or 5 and the strict threshold is 5. Conditional proportions retain the observed group denominator; intervals use the Wilson score construction. There are no sampling weights or school-cluster adjustments.

## Reply content

`audit_statistics.py` preserves the archived statistics implementation. `analyse_replies.py` applies it to separately supplied reply and label records. The two versions combine the same singly coded replies with coder A's or coder B's independent labels. Calibration replies are excluded; uncertain labels remain missing. Feature prevalence uses observed labels. Paired contrasts first average matched model differences within each scenario, then average scenarios equally. The bootstrap resamples scenarios 5,000 times using seed 20261011. The two versions share most labels and are not independent replications. Intervals are descriptive and unadjusted for multiplicity.

## Exploratory analyses added after coding

`analyse_reply_states.py` preserves the supplied LaTeX package's algorithms for recognition/procedure states, matched A-to-B transitions, complete scenario-model four-condition interactions, and reply length/structure. `analyse_reply_context.py` preserves the Chinese indicator dictionaries, low-default theme comparison, local recording-context windows, and the sampling procedures for reading indicator matches. Theme prevalence is recomputed from input labels instead of requiring a deposited results table. Paths are configurable; source algorithms and random seeds are retained.

These scripts describe methods and contain no AI response observations or result constants. A holder of the original records can run:

```bash
python scripts/analyse_replies.py --input-dir /path/to/private_package
python scripts/analyse_reply_states.py --input-dir /path/to/private_package
python scripts/analyse_reply_context.py --input-dir /path/to/private_package
```

The input package must contain `data/replies.csv`, `data/labels.csv` and `data/scenarios.csv`, as described in INPUT_SCHEMAS.md. Outputs, including any locally extracted text samples, stay under the ignored `generated/` directory. The public deposit alone reproduces questionnaire results; it cannot independently reproduce reply-level findings without the excluded records.
