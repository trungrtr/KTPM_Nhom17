# LOG-01 through LOG-14 (Table 4.8)

Run: `python -m pytest tests/test_dang_nhap.py -rs`

Dedicated LOG report (PowerShell):
```powershell
python -m pytest tests/test_dang_nhap.py -o addopts= -p no:cacheprovider --html=results/log_report.html --self-contained-html --tb=short -rs
Start-Process .\results\log_report.html
```

Required-field cases require native validation or an ARIA-linked error for each
blank field; disabled controls alone never count as passing validation.
Credential rejection must not be a native/ARIA field-format rejection.
Failure diagnostics are saved as `results/test_LOG_*_diagnostic.json` with input
metadata only (no values, cookies, tokens or full DOM). Messages redact configured
credential environment values. Existing shared screenshot hooks remain unchanged.

Environment verification on 2026-10-31: collection finds all 14 cases, but the
unchanged driver fixture cannot complete `ChromeDriverManager().install()` because
`chmod` of the cached driver under the user's `.wdm` directory raises WinError 5.
A separate read-only Selenium probe using that driver starts Chrome but navigating
to `/login` fails with `tab crashed`. Live DOM, authentication locators and website
behaviour therefore remain unverified; SKIP is not evidence of website correctness.
Run the command above in a normal Windows PowerShell session with access to the
driver cache and Chrome. Do not bypass CAPTCHA or change authentication cookies.

Uses the existing Selenium driver fixture, BasePage explicit waits and
RegisterPage cookie acceptance. CAPTCHA/OTP is never solved or bypassed.
Browser creation/network prerequisites and missing credentials produce SKIP;
missing locators, absent expected responses and assertion failures fail normally.

Configure `.env` (never commit secrets):
- TEST_EMAIL, TEST_PASSWORD: active test account.
- TEST_PHONE: phone bound to that same account/password.
- LOG_NONEXISTENT_EMAIL: confirmed unregistered test address.
- LOG_LOCKOUT_EMAIL, LOG_LOCKOUT_PASSWORD: dedicated disposable active account,
  separate from TEST_EMAIL; LOG-10 deliberately submits five wrong passwords.
- HEADLESS=true for unattended runs.

Defaults: /login and protected /account. Override LOG_LOGIN_PATH and
LOG_ACCOUNT_PATH if needed. Authenticated evidence must only be visible to an
actual signed-in user. Override LOG_AUTHENTICATED_CSS for the deployed account UI.
Other selectors can be configured with LOG_<LOCATOR_NAME>_CSS; see LoginPage.
The default selectors require verification against the actual deployed DOM.

LOG-08 expects surrounding email spaces to be trimmed; LOG-09 expects
case-insensitive email and case-sensitive password. LOG-10 requires visible
protection by the fifth attempt; early CAPTCHA causes SKIP because five attempts
cannot be completed. LOG-14 submits real recovery requests to the test addresses;
it verifies UI acknowledgements, not delivery to an inbox. Unknown accounts may
receive a generic success acknowledgement to avoid account enumeration.

The CSV results/log_test_results.csv has one row per LOG case, includes setup
skips and teardown errors, and is reset only when LOG tests are selected.
REG results are reset only when REG tests are selected. Existing shared HTML/CSV
report hooks continue to operate. Use `-o addopts= --html=results/log_report.html
--self-contained-html` to keep a prior shared HTML report when running LOG.
