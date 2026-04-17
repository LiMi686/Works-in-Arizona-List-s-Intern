# Analysis Index

This folder now contains two separate analysis projects that share the same SQLite workbench.

## Project 1: Activist Codes / Tags Governance

- `activist_codes_requirements_notebook.ipynb`
  Jupyter Notebook walkthrough of the governance questions.
- `activist_codes_requirements_report.md`
  Evidence summary and findings.
- `activist_codes_decision_memo.md`
  Team-facing memo for decisions and next steps.
- `tag_activist_code_exact_overlaps.csv`
  Exact overlap list between `Tags.name` and `Activist Codes.long_name`.
- `figures/activist_codes_definition_by_type.svg`
- `figures/activist_codes_application_by_type.svg`
- `figures/activist_codes_usage_buckets.svg`
- `figures/activist_tags_governance_signals.svg`

## Project 2: Lapsed Donor Reactivation

- `lapsed_donor_reactivation/`
  Separate subproject for identifying consistent-but-lapsed donors and exporting recapture lists in Jupyter-friendly notebook form.

## Shared Supporting Workbench

- `../scripts/build_everyaction_workbench.py`
  Imports the datasets, normalizes them, and builds the SQLite workbench.
- `../workbench/everyaction_workbench.sqlite`
  Shared SQLite database used by both analysis projects.

## Tables Used Most Directly

- `../workbench/normalized_csv/activist_codes_list_xlsx.csv`
- `../workbench/normalized_csv/all_activist_codes_applied.csv`
- `../workbench/normalized_csv/tags_list.csv`
- `all_contributions_ever` in `../workbench/everyaction_workbench.sqlite`
