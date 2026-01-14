# Batch Processing Error Handling Guide

## Overview
The batch comparison mode now has robust error handling that allows partial success scenarios where some CVs process successfully while others fail.

## Error Scenarios

### 1. Full Success ✅
- All CVs process without errors
- Dashboard displays comparison for all candidates
- Results view shows full batch comparison with 3-panel dashboard

### 2. Partial Success ⚠️
- Some CVs process successfully, others fail
- **User sees:** Warning message with count of failed CVs (e.g., "⚠️ 2 von 5 CVs konnten nicht verarbeitet werden")
- **User can:** Still view results for successful CVs with full dashboard and comparison
- **Failed CVs:** Displayed in expandable "Failed" section showing:
  - CV filename
  - Specific error message (e.g., "PDF extraction failed", "API timeout")
  - Console logs for debugging

### 3. Full Failure ❌
- All CVs fail to process
- **User sees:** Error message "Alle CVs konnten nicht verarbeitet werden"
- **No results view:** Cannot proceed to results display
- **Debugging:** Check console output for detailed error messages

## Error Messages

### Console Logging (stderr)
Each CV processing step logs to console:
```
📄 Processing CV: candidate1.pdf
✅ Successfully processed: candidate1.pdf
❌ Processing failed: candidate2.pdf - PDF extraction timeout
❌ Exception processing candidate3.pdf:
  Traceback: ...
```

### Result Error Details
Each failed result includes:
- `candidate_name`: Name extracted from filename
- `cv_file`: Original filename
- `error`: Specific error message explaining what went wrong
- `success`: false flag

Example failure result:
```json
{
  "success": false,
  "candidate_name": "Max_Mustermann",
  "cv_file": "max_mustermann.pdf",
  "error": "Pipeline error: PDF extraction failed after 3 retries",
  "job_profile": {...}
}
```

## Common Error Causes

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| "PDF extraction failed" | Invalid/corrupted PDF | Verify PDF is readable in browser |
| "API timeout" | OpenAI API unresponsive | Check API key, retry processing |
| "Job profile format invalid" | Malformed JSON | Validate job profile structure |
| "Missing required fields" | Incomplete CV data | CV lacks essential information |
| "Model not found" | Wrong MODEL_NAME in .env | Check .env configuration |

## Implementation Details

### batch_comparison.py
- `run_batch_comparison()`: Orchestrates multi-CV processing
  - Reads job profile once for all CVs
  - Loops through each CV file
  - Captures both success and error results
  - Returns list of all results (mixed success/failure)

### app.py Batch Result Handling
```python
if is_batch and results.get("batch_results"):
    successful = [r for r in batch_results if r.get("success")]
    failed = [r for r in batch_results if not r.get("success")]
    
    if successful:
        # Partial success: show warning, allow results view
        st.warning(f"⚠️ {len(failed)} von {len(batch_results)} CVs failed")
    else:
        # Full failure: show error, no results view
        st.error("Alle CVs konnten nicht verarbeitet werden")
```

### batch_results_display.py
- `display_batch_results()`: Shows results with failure handling
  - Counts successful vs failed results
  - Creates expandable "Failed" section if errors exist
  - Shows each failure with error message
  - Only displays dashboard for successful CVs

## User Workflow for Failed CVs

1. **User uploads 5 CVs** for batch comparison
2. **System processes:** 3 succeed, 2 fail
3. **User sees:** Warning message with count
4. **User can:**
   - Click "Ergebnisse anzeigen" to view successful results
   - See 3-candidate comparison dashboard
   - Review failed CVs in expandable section
5. **Debugging:**
   - Check browser console for detailed logs
   - Retry failed CVs individually in Mode 2
   - Fix issues and re-upload

## Best Practices

### For Users
1. ✅ Verify all PDFs are valid and readable
2. ✅ Ensure job profile JSON is properly formatted
3. ✅ Check API key is valid in settings
4. ✅ Start with small batch (2-3 CVs) to test
5. ✅ Check console logs if CVs fail

### For Developers
1. ✅ Always check `result.get("success")` before accessing data fields
2. ✅ Log processing steps to stderr for debugging
3. ✅ Include specific error messages (not generic "failed")
4. ✅ Handle partial success gracefully
5. ✅ Test with mixed success/failure scenarios

## Testing Error Handling

### Unit Tests
All existing 45 tests pass with error handling improvements:
- ✅ No regressions in single CV modes (1-3)
- ✅ Syntax validation complete
- ✅ Pre-commit hooks validated

### Manual Testing Checklist
- [ ] Test with 1 valid CV (should succeed)
- [ ] Test with 1 invalid PDF (should fail gracefully)
- [ ] Test with 3 valid + 1 invalid (partial success)
- [ ] Test with all invalid CVs (full failure)
- [ ] Verify error messages are clear and helpful
- [ ] Check console logs contain useful debugging info
- [ ] Verify results view appears for partial success
- [ ] Verify failed CV details in expander

## Future Improvements

Potential enhancements:
- [ ] Retry button for failed CVs in results view
- [ ] Error categorization (retriable vs permanent)
- [ ] Email notification with failure summary
- [ ] Automatic retry with exponential backoff
- [ ] Batch error report generation
- [ ] Failed CV quarantine for inspection
