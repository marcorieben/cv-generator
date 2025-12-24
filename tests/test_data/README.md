# Test Data Directory

This directory contains offline test data to allow running tests without incurring OpenAI API costs.

## How to update test data

1. Run the pipeline normally to generate a valid output:
   ```bash
   python run_pipeline.py
   ```
2. Verify that the output in `output/` is correct.
3. Run the update script to copy the latest run to this directory:
   ```bash
   python scripts/save_latest_run_as_test.py
   ```
4. Commit the changes:
   ```bash
   git add tests/test_data
   git commit -m "test: update offline test data"
   ```

## Contents
- `complete_run/`: Contains a full set of JSON files (CV, Match, Feedback, Stellenprofil) from a successful run.
