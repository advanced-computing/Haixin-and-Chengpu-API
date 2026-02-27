# Data Profiling Takeaways

**Dataset:** `data.csv` (NYC Film Permits) — 16,122 rows × 14 columns

---

## Finding 1: `EnteredOn` Has 10.7% Missing Values, Suggesting a Schema Change

1,727 records are missing the `EnteredOn` field, making it by far the most incomplete column (10.7%). The second-highest missing rate is `StartDateTime` at just 2.0%. Since the earliest `EnteredOn` value is October 2022 while permits stretch back to January 2023, the field was likely introduced mid-cycle or made mandatory later. This matters because any lead-time analysis — how far in advance permits are filed — depends on `EnteredOn`. The median lead time is 5.5 days, but this calculation only covers 87.5% of records and may be biased toward more recent, better-documented permits.

## Finding 2: 14 Permits Have Negative Durations, Indicating Data Entry Errors

Permit duration (computed as `EndDateTime` minus `StartDateTime`) is negative for 14 records, meaning the end time is recorded before the start time. While this is a small fraction (0.09%), it reveals data entry quality issues. Additionally, the maximum duration is 1,668 hours (~70 days), which is an extreme outlier compared to the median of 15 hours. These records should be flagged and excluded from any time-based analysis, as they would heavily skew averages and distributions.

## Finding 3: Manhattan and Brooklyn Account for 83.4% of All Permits

Manhattan alone holds 50.7% of permits (8,176), followed by Brooklyn at 32.7% (5,267). Queens has 13.0%, while the Bronx (2.7%) and Staten Island (0.8%) are minimally represented. This concentration reflects the geography of NYC's film and TV industry. Borough-level comparisons should account for this imbalance — for example, a raw count of violations or delays in Manhattan will naturally be higher simply due to volume, not necessarily worse compliance.

## Finding 4: Television Dominates Permit Categories, but Theater Is the Second Largest

Television accounts for 42.3% of all permits (6,828), followed by Theater at 19.2% (3,100) and Film at 14.0% (2,252). Notably, "Episodic series" is the top subcategory with 4,195 records — nearly all under Television — reflecting NYC's role as a hub for ongoing TV production.The less common categories (Documentary at 0.9%, Student at 0.5%, Music Video at 0.4%) collectively make up under 2%, so filtering by these categories will return very small result sets.

## Finding 5: Nearly All Permits Are Domestic, With Only 21 International Records

99.87% of permits (16,101) list "United States of America" as the country. Only 21 records come from foreign productions: 7 from the UK, 6 from Canada, 4 from Puerto Rico, 3 from the Netherlands, and 1 from Germany. The `Country` column has virtually zero analytical variance and adds little value to most queries. However, it could be useful for identifying the rare international productions filming in NYC.
