# Questionnaire data

Each CSV has one respondent per row, a release-only `record_id`, and the original numeric answers to the article's retained items. `metadata/survey_items.csv` maps each variable to its Chinese wording and English translation. `metadata/survey_scale_anchors.csv` gives each form's 1-5 response options. No scale reversal, normalisation, composite score or imputation has been applied.

| Form | Records | Retained items |
| --- | ---: | ---: |
| Primary students | 9,566 | 8 |
| Middle school students | 3,923 | 12 |
| Parents | 12,266 | 8 |
| Teachers | 1,546 | 11 |
| Principals | 95 | 4 |

The 43 retained items have complete answers in the source exports. Empty CSV cells are reserved for genuinely missing observations; zero is never used for missingness. Seven same-respondent pairs are defined in `metadata/survey_pairs.csv`. Each pair links two answers within one form. The principal form contributes marginal frequencies only. Cross-form respondent or school matching is unavailable.

Agreement means rating 4 or 5; the stricter analysis uses rating 5. Joint counts retain all 25 combinations of the raw 1-5 answers. Wilson intervals are unweighted and do not account for school clustering. Items differ across roles, so their values do not establish a common cross-role scale.

The raw files are a data-minimised extract of the original platform exports. The publication removes identifiers, quasi-identifiers and unrelated items; its row order and identifiers do not preserve source linkage. Provenance records include source-workbook hashes and the transformations, without publishing source records or a re-identification key. Full blank questionnaires are provided as plain text, excluding document comments and metadata.
