# Configuring support in school AI assistants

Research materials for **Configuring Support in School AI Assistants: Procedural Guidance, Human Referral, and Response Structure**, by Zhexi Gu, Runping Zhu, Yaqing Mao, Jianglun Wu and Philip Wing Chan.

This release contains the article's anonymised raw questionnaire item responses, questionnaire results, blank instruments, experimental input prompts and analysis methods. The five forms contain 27,396 records and 43 article-specific AI-attitude items. The original 1-5 item values are retained. These files are an anonymised analysis subset of the source exports, not the untouched survey-platform workbooks.

| Location | Contents |
| --- | --- |
| `data/survey/raw/` | Five anonymised respondent-level item-response CSVs |
| `metadata/` | Chinese and English item wording, scale anchors, seven item pairs, coding definitions and provenance |
| `instruments/` | Complete original blank questionnaires in Chinese, and English translations of the article's 43 items |
| `prompts/` | 60 constructed scenarios, the base prompt and two modules, 240 materialised inputs, and recorded generation settings |
| `scripts/` | Survey reproduction, primary reply statistics and exploratory post-coding methods |
| `results/survey/` | Recomputed questionnaire frequencies, joint distributions, Wilson intervals, Figure 5 data and Appendix Table A4 values |

## Reproduce the questionnaire results

```bash
python -m pip install -r requirements.txt
python scripts/validate_release.py
python scripts/reproduce_survey.py --verify
```

Outputs go to the ignored `generated/survey/` directory. No model, API access or credentials are needed. Survey item marginals and all seven 5-by-5 joint distributions were checked against the article's archived analysis inputs.

## Reply-analysis methods

The code includes the article's primary paired contrasts, agreement statistics, four-state transitions, complete-cell interaction, length/structure and Chinese word-indicator analyses. Running these methods requires separate reply and coding records; see [Methods](docs/METHODS.md) and [Input schemas](docs/INPUT_SCHEMAS.md).

Generated AI replies, original coding records, classifier materials, AI-derived tables/figures and AI output samples are excluded from this public snapshot. Questionnaire records cannot be paired with generated replies: respondents did not see or rate them.

See the [data guide](docs/DATA_GUIDE.md), [privacy and release scope](docs/RELEASE_SCOPE.md), [article mapping](docs/ARTICLE_MAP.md), and `manifest.json` for details and file checksums. The source Chinese instruments define the wording; the English translations cover the items used in this article. Original questionnaire rights remain with their respective rights holders.
