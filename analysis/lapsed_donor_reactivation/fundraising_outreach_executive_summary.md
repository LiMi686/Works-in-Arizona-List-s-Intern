# Fundraising / Outreach Executive Summary

As of 2026-04-16, this report summarizes four practical outreach questions and highlights the recommended actions more than the underlying technical method.

## Four Answers at a Glance

| question | result | recommended_action |
| --- | --- | --- |
| 1. How many people are reachable by mail but missing an email address? | 16,438 people | Create a dedicated direct-mail, postcard, and email-acquisition segment. |
| 2. Which people added since January are good postcard candidates? | 6 people | Run a small welcome or reactivation postcard test immediately. |
| 3. How large is Leadership Council within the donor base? | 248 people, equal to 3.34% | Treat LC as a distinct stewardship segment, not a proxy for the general donor base. |
| 4. Which lapsed donors should be prioritized for reactivation? | 210 high-priority people, including 210 with a $250+ giving history | Start with Tier 1 and Tier 2, then expand to Tier 3 and Tier 4. |

## 1. How many people are reachable by mail but missing an email address?

The current database contains 16,438 `Person` records that have a complete mailing address, no email address on file, and no `nomail` flag. This is the clearest direct-mail opportunity pool.

![Direct-mail opportunity](./figures/mailing_no_email_opportunity.svg)

These people account for 20.59% of all `Person` records, which is large enough to justify a dedicated direct-mail, email-capture, or reactivation workflow.

## 2. Which people added since January are good postcard candidates?

Since 2026-01-01, the database has added 1,378 `Person` records. Of those, 6 already meet the criteria for postcard outreach.

![Postcard candidates since January](./figures/people_added_since_january_postcard_opportunity.svg)

Within this group, 5 live in Arizona and 1 live outside the state. Because the list is so small, the best next move is to execute a welcome-postcard or light reactivation test immediately rather than expanding the analysis further.

| vanid | contact_name | city | state_province | date_created | origincodename |
| --- | --- | --- | --- | --- | --- |
| 131942803 | Calderone, Dawna P | Phoenix | AZ | 2026-03-30 | 26Sponsor |
| 131448005 | Melendez, Deanna | Prescott | AZ | 2026-02-26 | 2023 Direct Mail |
| 131448040 | Movahed, Reza | Tucson | AZ | 2026-02-26 |  |
| 130742680 | Bradford Coleman, Karyn | Little Rock | AR | 2026-01-19 |  |
| 130742681 | Figuroa, Lauren | Peoria | AZ | 2026-01-19 |  |
| 130742679 | Jewel, Jasmine | Flagstaff | AZ | 2026-01-19 |  |

## 3. How large is Leadership Council within the donor base?

The inferred Leadership Council population is 248. Of those, 247 fall inside the current donor base, representing just 3.34% of person-like donors.

![Donors vs Leadership Council](./figures/donor_vs_leadership_council.svg)

This shows that LC is an important but very small high-value segment, better handled as its own stewardship, upgrade, or special-care audience.

## 4. Which lapsed donors should be prioritized for reactivation?

The analysis identified 353 consistent-but-lapsed donors. Among them, 210 fall into the high-priority tiers, and 210 have at least one year of `$250+` giving.

![Lapsed donor priority tiers](./figures/lapsed_donor_priority_tiers.svg)

The biggest concentration of recent lapse sits in 2024-2025, with 170 people across those two years. The most promising reactivation audience is not the oldest lapse group, but the people who stopped giving recently after a more stable giving history.

| candidate_count | candidate_250plus_count | tier_1_count | tier_2_count | tier_3_count | tier_4_count |
| --- | --- | --- | --- | --- | --- |
| 353 | 210 | 85 | 125 | 54 | 89 |

## Recommended Next Steps

1. Build a dedicated outreach segment for the `16,438` mail-reachable people who have no email address.
2. Contact the 6 people in `./people_added_since_january_postcard_outreach.csv` and test a welcome or reactivation postcard.
3. Run Leadership Council as its own stewardship cadence for `248` people instead of mixing it into general donor cultivation.
4. Start with Tier 1 and Tier 2 in `./lapsed_consistent_donors_250plus.csv` and `./lapsed_consistent_donors.csv`, covering 210 people.

## Supporting Files

- Technical report: `./lapsed_donor_reactivation_report.md`
- Executive summary: `./fundraising_outreach_executive_summary.md`
- Postcard list: `./people_added_since_january_postcard_outreach.csv`
- Lapsed donor full list: `./lapsed_consistent_donors.csv`
- Lapsed donor $250+ list: `./lapsed_consistent_donors_250plus.csv`