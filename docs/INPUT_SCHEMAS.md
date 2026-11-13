# Input schemas for optional reply analysis

These are schemas, not deposited observations.

`data/replies.csv`: `response_id`, `scenario_id`, `model`, `condition`, `coding_split`, `response_text`. One row per generated reply. Conditions are `campus`, `procedure`, `boundary`, `procedure_boundary`. The calibration split is excluded.

`data/labels.csv`: `response_id`, `coder`, followed by the 13 coded fields in `metadata/codebook.json`. Coders are `single`, `coder_a`, `coder_b`. Values are 0 (absent), 1 (explicitly present) or an empty string (uncertain/missing). The two derived conjunctions are computed, not separate input labels.

`data/scenarios.csv`: `id`, `category`, `difficulty`, `source_module`, `text`. The available public input is `prompts/scenarios.csv`; it can be copied into the private input directory. Scenarios are constructed disclosures, not respondents' conversations.

Keep private inputs outside the public tree or under the ignored `private_inputs/` directory. Local analysis outputs belong under `generated/`. Neither location is part of the publication inventory.
