# AGENT.md - Mandatory Testing Protocol

## 🚨 MANDATORY: Run Tests After Every Change

**Rule:** Every code change requires test execution before proceeding.

## Test Commands

### Standard Test Suite
```bash
.venv\Scripts\python test_api.py
.venv\Scripts\python test_sorting.py
.venv\Scripts\python -m py_compile app.py
```

### Quick Smoke Test
```bash
.venv\Scripts\python test_api.py && .venv\Scripts\python test_sorting.py
```

### Verify No Syntax Errors
```bash
.venv\Scripts\python -m py_compile app.py
```

## Test Execution Workflow

### 1. Before Making Changes
- Read current file state
- Understand existing tests
- Identify which tests are affected

### 2. After Making Changes
- **Mandatory:** Run full test suite
- **Mandatory:** Verify no syntax errors
- **Mandatory:** Check logs for errors

### 3. If Tests Fail
- Review error output
- Fix issues
- Re-run tests until passing
- Only proceed when all tests pass

### 4. Before Committing
- Run full test suite
- Verify clean console output
- Document any test failures

## Test Results Verification

### Expected Output
```
Testing API Client...
==================================================
1. Fetching available companies...
   Available companies: ['10X', '14D', ...]
2. Fetching history for '10X'...
   Records found: 30
==================================================
API Client validation complete!

Top gainers test passed
Top losers test passed
Full table sorting test passed

All tests passed!
```

### Failure Indicators
- Syntax errors from `py_compile`
- Import errors
- API connection failures
- Data processing exceptions
- Any output other than expected test messages

## Enforcement Guidelines

### Automated Checks
Before committing code:
1. Run `.venv\Scripts\python -m py_compile app.py`
2. Run `.venv\Scripts\python test_api.py`
3. Run `.venv\Scripts\python test_sorting.py`
4. Verify clean output

### Manual Verification
- Check that no new warnings appear in console
- Verify API calls succeed without errors
- Confirm data processing completes successfully

### Red Flags
- New console warnings (e.g., `use_container_width` deprecation)
- API timeout errors
- Data fetch failures
- Import errors
- Syntax warnings

## Test Coverage

### test_api.py
Tests:
- `get_available_companies()` - API health check
- `get_company_history()` - Symbol data retrieval
- Specific validation for '14D' symbol
- Error handling verification

### test_sorting.py
Tests:
- Top gainers calculation
- Top losers calculation
- Full table sorting logic

## Quick Reference

| Action | Command |
|--------|---------|
| Run all tests | `test_api.py && test_sorting.py` |
| Check syntax | `py_compile app.py` |
| Quick check | `python test_api.py && python test_sorting.py` |
| Full verification | Run all three commands above |

## OS Detection and Command Selection

### Mandatory: Check OS Before Running OS-Specific Commands

**Rule:** Always detect the operating system before executing OS-specific commands.

### Platform Detection Examples

```python
import platform
import sys

# Method 1: Using platform module
system_name = platform.system()
# Returns: 'Windows', 'Linux', or 'Darwin'

# Method 2: Using sys.platform
platform_id = sys.platform
# Returns: 'win32', 'linux', or 'darwin'

# Method 3: Using platform.machine()
arch = platform.machine()
# Returns architecture: 'AMD64', 'x86_64', etc.
```

### OS-Specific Command Examples

**Windows PowerShell:**
- Use `&&` for command chaining (if available in version)
- Use `;` as fallback for PowerShell 5.1
- Use backticks for paths: `` `.venv\Scripts\python script.py` ``
- Use `python -c` for inline commands

**Unix/Linux/macOS Bash/Zsh:**
- Use `&&` for command chaining
- Use `$()` for command substitution
- Use forward slashes for paths: `/home/user/script.py`
- Use `python3` or `python` depending on environment

### Conditional Command Execution

```python
import platform

if platform.system() == 'Windows':
    # Windows-specific commands
    cmd = 'powershell -Command "Get-Process | Select-Object -First 5"'
else:
    # Unix/Linux/macOS commands
    cmd = 'ps aux --sort=-%cpu | head -5'

print(f"Running on {platform.system()}: {cmd}")
```

### Common Pitfalls to Avoid

- **Don't use `&&` in PowerShell 5.1** - Use `;` instead or check PowerShell version first
- **Don't assume `python` exists** - Check `sys.executable` for full path
- **Don't use Unix-style paths on Windows** - Use `pathlib.Path` or `os.path`
- **Don't use `echo` for debugging** - Use `print()` instead

### Safe Command Execution Pattern

```python
import platform
import subprocess

def run_command(cmd, check_os=True):
    """Safely run command with OS detection."""
    if check_os:
        if platform.system() == 'Windows':
            # PowerShell commands
            if '&&' in cmd:
                cmd = cmd.replace('&&', ';')
        else:
            # Unix commands
            pass
    subprocess.run(cmd, shell=True, check=True)
```

## Notes
- Tests run against live API (192.168.0.50:30181)
- Expected latency: 1-2 seconds per test
- Network failures indicate test environment issues
- Empty results indicate API downtime
