SYNTHETIC test data written by hand to mimic the data.police.uk response shape.
It is used only by the test-suite. It is NOT real data and is never loaded by the real pipeline
(real raw responses live in data/raw/). It includes deliberate edge cases: a duplicate record across
two tiles, empty persistent_id values, null outcome_status.
