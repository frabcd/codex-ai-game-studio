[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $EditionArguments
)

$launcher = Join-Path $PSScriptRoot "edition.py"
$py = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $py) {
    & $py.Source -3 $launcher @EditionArguments
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    Write-Error "Python 3 is required. Install it separately, then rerun this launcher."
    exit 2
}

& $python.Source $launcher @EditionArguments
exit $LASTEXITCODE
