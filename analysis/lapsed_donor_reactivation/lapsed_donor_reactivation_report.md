# Lapsed Donor Reactivation Analysis

## Data Check

| contribution_rows | distinct_vanids | distinct_contact_names | first_gift_date | latest_gift_date |
| --- | --- | --- | --- | --- |
| 53022 | 7770 | 7707 | 2004-01-15 | 2026-04-09 |

## Rules Used

As of 2026-04-16: keep person-like names only (`Last, First`), require at least 3 giving years and a longest consecutive streak of at least 3 years, and define `priority_250_plus` as at least one giving year at $250+.

## Mailing Address but No Email

| total_people | people_with_complete_mailing_address | people_with_no_email | mailing_address_but_no_email | share_of_all_people | share_of_people_with_mailing_address | mailing_address_but_no_email_and_mailable |
| --- | --- | --- | --- | --- | --- | --- |
| 79830 | 54579 | 19319 | 16638 | 20.84 | 30.48 | 16438 |

Interpretation: 16,638 `Person` records have a complete mailing address but no email on file. That is 20.84% of all people and 30.48% of people with a complete mailing address. 16,438 of those records are not flagged `nomail`, so they remain usable for direct-mail outreach. A cross-check against `addresses_report` returns 16,651, only 13 higher than the `database_list` result.

## People Added Since January for Possible Postcard Outreach

Assumption used: `since January` means `date_created >= 2026-01-01` (that is, since 2026-01-01).

| people_added_since_january | people_added_since_january_with_complete_address | people_added_since_january_with_no_email | people_added_since_january_with_address_but_no_email | people_added_since_january_postcard_candidates | share_of_people_added_since_january | share_of_people_added_since_january_with_complete_address |
| --- | --- | --- | --- | --- | --- | --- |
| 1378 | 303 | 128 | 6 | 6 | 0.44 | 1.98 |

Interpretation: 6 people added since January have a complete mailing address, no email on file, and are not flagged `nomail`. That is 0.44% of all people added since January and 1.98% of those with a complete address.

| vanid | contact_name | address | city | state_province | zip_postal | date_created | origincodename |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 131942803 | Calderone, Dawna P | 518 E Tuckey Ln | Phoenix | AZ | 85012 | 2026-03-30 | 26Sponsor |
| 131448005 | Melendez, Deanna | 5736 Taragon Ln | Prescott | AZ | 86305 | 2026-02-26 | 2023 Direct Mail |
| 131448040 | Movahed, Reza | 6119 N Pinchot Rd | Tucson | AZ | 85750 | 2026-02-26 |  |
| 130742680 | Bradford Coleman, Karyn | 9420 Covenant Ln | Little Rock | AR | 72204 | 2026-01-19 |  |
| 130742681 | Figuroa, Lauren | 14109 N 83rd Ave Apt 307 | Peoria | AZ | 85381 | 2026-01-19 |  |
| 130742679 | Jewel, Jasmine | 404 W Santa Fe Ave Apt 102 | Flagstaff | AZ | 86001 | 2026-01-19 |  |

## Donor Universe vs Leadership Council

| total_donors | person_like_donors | total_lc_members | lc_members_in_person_like_donor_base | lc_members_outside_person_like_donor_base | lc_share_of_person_like_donors |
| --- | --- | --- | --- | --- | --- |
| 7770 | 7401 | 248 | 247 | 1 | 3.34 |

Interpretation: the chart below visualizes total donors against Leadership Council members inferred from activist codes `19LCPin` and `20LCPin`, whose descriptions reference LC pin mailings. The detailed table also shows that 247 of the 248 LC-coded records fall inside the person-like donor universe used elsewhere in this analysis.

![Donors vs Leadership Council](./figures/donor_vs_leadership_council.svg)

## Summary

| candidate_count | candidate_250plus_count | tier_1_count | tier_2_count | tier_3_count | tier_4_count | avg_giving_years | avg_longest_streak | avg_lifetime_amount | avg_max_annual_amount |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 353 | 210 | 85 | 125 | 54 | 89 | 7.41 | 5.27 | 3057.02 | 883.75 |

## Last Gift Year Mix

| last_gift_year | candidate_count | candidate_250plus_count |
| --- | --- | --- |
| 2025 | 69 | 43 |
| 2024 | 101 | 62 |
| 2023 | 90 | 54 |
| 2022 | 53 | 30 |
| 2021 | 40 | 21 |

## Top Priority Examples

| vanid | contact_name | recapture_priority | giving_years | longest_streak | last_gift_date | days_since_last_gift | lifetime_amount | max_annual_amount | years_at_250_plus |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 109454727 | Scheel, Benjamin | Tier 1 | 11 | 11 | 2025-04-16 | 365 | 1390.0 | 260.0 | 1 |
| 127495068 | Sensibar, Judy Rose | Tier 1 | 8 | 4 | 2025-04-11 | 370 | 3141.06 | 1000.0 | 4 |
| 127271587 | Jamieson, Deboah A | Tier 1 | 8 | 5 | 2025-04-06 | 375 | 1850.0 | 500.0 | 4 |
| 109448517 | Young, Harriet Hopkins | Tier 1 | 20 | 16 | 2025-04-04 | 377 | 20283.32 | 2508.32 | 14 |
| 109423500 | Howard, Lucia F | Tier 1 | 14 | 7 | 2025-04-04 | 377 | 4663.45 | 1353.45 | 8 |
| 109467029 | Benatar, Sarah Elena | Tier 1 | 5 | 3 | 2025-03-28 | 384 | 757.19 | 500.0 | 1 |
| 109446375 | Bechtol, Vanessa Lee | Tier 1 | 5 | 5 | 2025-03-28 | 384 | 706.9 | 353.45 | 1 |
| 109421462 | Ward, Dorothy Deuss | Tier 1 | 7 | 4 | 2025-03-17 | 395 | 1100.0 | 510.0 | 2 |
| 119851612 | Quackenbush, LiAnne Michelle | Tier 1 | 5 | 3 | 2025-03-15 | 397 | 5799.15 | 3250.0 | 5 |
| 123657656 | Green, Miles Anthony | Tier 1 | 4 | 3 | 2025-03-07 | 405 | 600.0 | 300.0 | 1 |
| 123657661 | Davis, Lynn K | Tier 1 | 7 | 6 | 2025-03-06 | 406 | 1611.01 | 426.01 | 2 |
| 109457186 | Hatfield, Linda L | Tier 1 | 14 | 8 | 2025-03-06 | 406 | 1320.0 | 260.0 | 1 |
| 109437117 | Bourgois, Leanne McCabe | Tier 1 | 8 | 8 | 2025-03-04 | 408 | 4713.45 | 1900.0 | 7 |
| 109464047 | Heredia, Luis A | Tier 1 | 9 | 5 | 2025-03-02 | 410 | 4746.77 | 2816.32 | 2 |
| 109451848 | Brandt, Judith Barbara | Tier 1 | 18 | 17 | 2025-03-01 | 411 | 4709.28 | 670.0 | 9 |
| 126523141 | Glow, Lisa Lynn | Tier 1 | 15 | 10 | 2025-03-01 | 411 | 3470.15 | 470.0 | 7 |
| 109447186 | Macre, Heather A | Tier 1 | 12 | 5 | 2025-03-01 | 411 | 4484.9 | 1500.0 | 6 |
| 109441519 | Epstein, Mitzi Mitzi | Tier 1 | 13 | 7 | 2025-03-01 | 411 | 2531.77 | 450.0 | 5 |
| 109428772 | Hill, Marian J | Tier 1 | 10 | 4 | 2025-03-01 | 411 | 1981.0 | 470.0 | 4 |
| 109459117 | Thearle, Marie | Tier 1 | 6 | 3 | 2025-03-01 | 411 | 2276.7 | 1025.0 | 3 |

CSV exports: `./lapsed_consistent_donors.csv`, `./lapsed_consistent_donors_250plus.csv`, and `./people_added_since_january_postcard_outreach.csv`