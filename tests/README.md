# Testing

## Quick Start

```powershell
# Run unit tests only (fast, no network required) - DEFAULT
uv run pytest

# Run ALL tests including integration tests (slow, hits real website)
uv run pytest --run-integration

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_simple.py -v
```

## Test Categories

### Unit Tests (`test_simple.py`, `test_browser.py`)

- ✅ Fast (< 2 seconds)
- ✅ No network required (except `test_browser.py`)
- ✅ Always run in CI/CD
- Tests: Imports, data structures, Playwright availability

### Integration Tests (`test_client.py`)

- ⚠️ Slow (5-10 seconds per test)
- ⚠️ Requires internet connection
- ⚠️ Hits real kleinanzeigen.de website
- ⚠️ Skipped by default (use `--run-integration` flag)
- Tests: Search, listing details, filters, error handling

## Test Results

```bash
# Default (unit tests only)
5 passed, 13 skipped in 2.5s

# With --run-integration (all tests)
18 passed in ~60 seconds
```

## What Was Fixed

The integration tests were timing out because:

1. **Missing User-Agent**: Website blocked headless browsers
   - ✅ Fixed: Added realistic Chrome user agent
2. **No wait strategy**: Page loads waited for everything
   - ✅ Fixed: Changed to `wait_until="domcontentloaded"`
3. **Too long timeouts**: 120 seconds caused hangs
   - ✅ Fixed: Reduced to 30 seconds with proper error handling

## Debugging Failed Tests

If integration tests fail:

1. Check internet connection
2. Verify kleinanzeigen.de is accessible: `curl https://www.kleinanzeigen.de`
3. Check if website structure changed (inspect HTML)
4. Run browser tests first: `uv run pytest tests/test_browser.py -v`
5. Review Playwright logs with `-s` flag: `uv run pytest -s -v`
