# Full local verification routine (docs/REMAINING-TASKS.md "Routine after any registry edit"). Writes .verify.log.
$ErrorActionPreference = "Continue"
Set-Location C:\Claude\Projects\apgi-lake
$log = "C:\Claude\Projects\apgi-lake\.verify.log"
function Run($name, $block) { "=== $name ===" | Out-File -Encoding utf8 -Append $log; (& $block 2>&1 | Out-String -Width 300) | Out-File -Encoding utf8 -Append $log; "--- exit $LASTEXITCODE" | Out-File -Encoding utf8 -Append $log }
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
Run "extract" { python verification\python\extract_sources.py --corpus C:\Claude\Projects\Neuro-Brain\Neuro-Input --corpus C:\Claude\Projects\apgi-lake\docs\apgi-v-1-2 --write }
Run "generate_lean" { python verification\python\generate_lean.py }
Run "lake" { lake build --wfail }
Run "consistency" { python verification\python\check_consistency.py }
Run "manifest" { python verification\python\make_release_manifest.py }
Run "traceability" { python verification\python\make_traceability.py }
Set-Location verification\python
$env:APGI_IMPL_PATH = "C:\Claude\Projects\apgi-implementation"
Run "pytest" { python -m pytest -q -rxs -p no:cacheprovider }
Remove-Item Env:APGI_IMPL_PATH
$env:APGI_VALIDATION_PATH = "C:\Claude\Projects\apgi-validation"
Run "pytest-validation" { python -m pytest -q -rxs -p no:cacheprovider test_production_validation.py }
Remove-Item Env:APGI_VALIDATION_PATH
"END $(Get-Date -Format o)" | Out-File -Encoding utf8 -Append $log
