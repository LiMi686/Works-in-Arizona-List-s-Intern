# Activist Codes Decision Memo

Prepared for team discussion based on the August 20, 2025 email thread and the current EveryAction exports reviewed on April 16, 2026.

## Purpose

We need a team decision on how Arizona List will use `Activist Codes` and `Tags` going forward, before more lists are uploaded and the current naming inconsistencies become harder to unwind.

This memo is intended to answer four practical questions:

1. What should Activist Codes be used for?
2. What should Tags be used for?
3. How should uploaded lists be labeled going forward?
4. What cleanup should we do now versus later?

## Executive Recommendation

Adopt the following operating model:

- Use `Activist Codes` as atomic, record-level labels.
- Use `Tags` as roll-up, hierarchical groupings across related Activist Codes and other code systems.
- Stop creating new blended codes that combine too many ideas in one label when those ideas can be represented separately.
- Standardize new uploads with a small set of reusable dimensions:
  role, geography, year, and source.
- Create one canonical Activist Code dictionary and treat it as the official source of truth.

In short:

- `Activist Codes` should answer: "What is true about this record?"
- `Tags` should answer: "How do we group related efforts for reporting and tracking?"

## Recommended Team Decisions

### Decision 1

Approve the rule that new uploaded lists may receive more than one Activist Code when the list contains more than one meaningful attribute.

Recommended answer: `Yes`

Why:

- This is already consistent with how the system is being used.
- The current data is dominated by `Back End` and `Bulk` application workflows.
- Many real list use cases naturally contain more than one dimension, such as role plus geography.

### Decision 2

Approve the rule that Activist Codes should be atomic rather than mixed-purpose whenever possible.

Recommended answer: `Yes`

Why:

- Mixed codes become hard to search, audit, reuse, and retire.
- Atomic codes let us combine labels flexibly without creating a new code for every scenario.

### Decision 3

Approve the rule that Tags should be used for roll-up categories, not as a replacement for Activist Codes.

Recommended answer: `Yes`

Why:

- This matches the product guidance Linda quoted.
- It also creates a cleaner separation between operational labeling and broader reporting.

### Decision 4

Approve a short-term cleanup project for both Activist Codes and Tags now.

Recommended answer: `Yes`

Why:

- We now have both the Activist Code and Tag exports needed to start a real cleanup.
- The overlap between the two systems is already large enough that waiting will only increase governance debt.

## What the Data Shows

The current Activist Code system is heavily used and worth governing rather than replacing.

Key facts from the current exports:

- `260` Activist Code definitions are present in the refreshed Excel dictionary export.
- `123,962` Activist Code applications are present in the applied export.
- `332` Tags are present in the Tag export.
- `Constituency` is the dominant type in both the code catalog and actual usage.
- `97.23%` of distinct applied codes can be matched back to the refreshed dictionary by `type + long name`.
- `32` duplicate short-name groups exist, with `65` extra rows involved in those collisions.
- `14` defined codes in the refreshed dictionary do not appear in the applied export.
- `7` applied code names are not exact long-name matches in the refreshed dictionary. These include formatting and renamed variants such as `January 2`, `January1`, and `HRC EList or  PP`.
- `1` duplicate Tag name exists: `EDU`.
- `191` Tag names exactly overlap with Activist Code names.
- `264` of `332` Tags already use hierarchical paths.
- Usage is concentrated:
  the top `10` codes account for `40.61%` of all applications, and the top `20` account for `59.91%`.

Bottom line:

- The system is workable.
- The core issue is governance, not lack of adoption.
- The highest risk is inconsistent naming and lack of a formal canonical dictionary.

## Recommended Operating Model

### Activist Codes

Use Activist Codes for record-level, searchable facts that may need to drive targeting, forms, or outreach.

Good Activist Code examples:

- `Role: Precinct Committee`
- `Geo: Maricopa County`
- `Year: 2025`
- `Source: Upload`
- `Volunteer: House Party`
- `Donor: $50+`

What makes these good:

- Each code has one meaning.
- Each code can be reused across many lists.
- Each code can be combined with other codes without creating a new naming mess.

### Tags

Use Tags for roll-up reporting and hierarchical grouping across related operational labels.

Good Tag examples:

- `DemLeadership`
- `DemLeadership > PCs`
- `Membership`
- `County Leadership`

What makes these good:

- They summarize broader efforts.
- They reduce the need to search many separate codes one by one.
- They are a better fit for hierarchy than Activist Codes.

## Practical Rule for New Uploads

For new list uploads, assign Activist Codes by dimension.

Recommended upload rule:

- Always ask: what is the role, geography, year, and source of this list?
- Apply one code per meaningful dimension.
- Do not create a new one-off combined code unless the dimension cannot be represented any other way.

Example:

For `Maricopa County PCs` in `2025`, the preferred structure is:

- Activist Code: `Role: Precinct Committee`
- Activist Code: `Geo: Maricopa County`
- Optional Activist Code: `Year: 2025`
- Optional Activist Code: `Source: Upload`
- Tag: `DemLeadership > PCs`

This is better than a single combined label because:

- the geography is reusable,
- the role is reusable,
- the year is reusable,
- and the same records can be reported under a broader leadership tag.

## What We Should Stop Doing

- Stop treating `short` or `medium` names as meaningful identifiers.
- Stop creating new labels that combine multiple concepts when reusable atomic codes already exist.
- Stop using Tags as a substitute for Activist Codes on records that need operational targeting.
- Stop adding new codes before checking whether the concept already exists in the dictionary.

## Immediate Cleanup to Approve Now

The current evidence supports a manageable first-phase cleanup across both systems.

Approve these immediate actions:

1. Freeze naming conventions for all new Activist Codes.
2. Create one canonical Activist Code dictionary with:
   code owner, purpose, status, and preferred long name.
3. Review the `32` short-name conflicts and stop relying on short names operationally.
4. Review the `14` unused or not-currently-applied dictionary entries in the refreshed export and classify each as:
   keep, rename, retire, or merge.
5. Resolve the current name mismatches between the refreshed dictionary and the applied export, including `Administrative / Former Intern` and the renamed or reformatted constituency entries.
6. Review the duplicate Tag `EDU`.
7. Triage the `191` exact Tag/Activist-Code name overlaps into:
   keep as Tag only, keep as Activist Code only, keep both with clarified purpose, or retire one side.
8. Add a lightweight pre-upload review so new lists use the agreed atomic dimensions.

## What Should Wait for Phase 2

These items are still important, but are better done after the core naming rules are approved:

- Full Tag usage audit, if assignment-level Tag data can be exported
- Automated similarity matching for near-duplicate labels
- Upload-time recommender logic

## Proposed Ownership

To keep this moving, the team should assign three roles:

- Business owner:
  final decision-maker on naming conventions and what counts as a reusable category
- Data steward:
  person responsible for maintaining the canonical dictionary
- Upload operator:
  person responsible for applying the agreed labeling rules during list imports

If one person must own the cleanup project, the work is still feasible, but the business owner should approve naming rules first so cleanup does not drift.

## Risks If We Do Nothing

- More uploaded lists will create more naming drift.
- Tags and Activist Codes will continue to overlap inconsistently.
- Searchability and reporting quality will decline over time.
- Future cleanup will take longer because more codes will need manual reconciliation.

## Decision Request

The team should confirm the following in the next discussion:

1. `Activist Codes` will be used for atomic record-level labels.
2. `Tags` will be used for hierarchical roll-up groupings.
3. New uploads may receive multiple Activist Codes when multiple dimensions matter.
4. The team will begin immediate Activist Code and Tag cleanup now.
5. The team will review exact Tag/Code overlaps as a first governance pass.

## Recommended Next 30 Days

Week 1:

- Approve the operating model.
- Approve the upload rule for multi-code labeling.
- Assign an owner for the canonical dictionary.

Week 2:

- Build the first version of the canonical dictionary.
- Review the short-name conflicts.
- Review unused and unmatched codes.

Week 3:

- Define the approved reusable dimensions for uploads:
  role, geography, year, source, donor segment, volunteer segment.

Week 4:

- Start applying the new convention to all new uploads.
- Review duplicate and overlapping Tags against the canonical dictionary.

## Final Recommendation

The team should not try to decide between Activist Codes and Tags as if only one should survive.

The better decision is:

- keep both,
- give them distinct jobs,
- standardize Activist Codes as atomic operational labels,
- use Tags as the reporting and hierarchy layer,
- and clean the existing dictionary now before additional list uploads make the system harder to govern.
