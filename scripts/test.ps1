<#
.SYNOPSIS
    Roda todas as verificações de qualidade do SUAP V2.

.DESCRIPTION
    Executa, em ordem: lint (ruff check), formatação (ruff format --check), segurança do código
    (bandit), testes com cobertura (pytest) e vulnerabilidades das dependências (pip-audit).
    Todas as etapas rodam mesmo que uma falhe; no fim, mostra um resumo e termina com código 1
    se alguma falhou.

.PARAMETER Rapido
    Pula os testes de navegador (marcador e2e) e o pip-audit, que consulta a internet.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\test.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\test.ps1 -Rapido
#>
[CmdletBinding()]
param(
    [switch]$Rapido
)

$Raiz = Split-Path -Parent $PSScriptRoot
$Bin = Join-Path $Raiz '.venv\Scripts'
$argsPytest = if ($Rapido) { @('-m', 'not e2e') } else { @() }

$etapas = @(
    @{ Nome = 'Lint (ruff check)'; Comando = { & "$Bin\ruff.exe" check . } },
    @{ Nome = 'Formatação (ruff format --check)'; Comando = { & "$Bin\ruff.exe" format --check . } },
    @{ Nome = 'Segurança do código (bandit)'; Comando = { & "$Bin\bandit.exe" -q -c pyproject.toml -r apps config dominio manage.py } },
    @{ Nome = 'Testes com cobertura (pytest)'; Comando = { & "$Bin\python.exe" -m pytest --cov @argsPytest } }
)
if (-not $Rapido) {
    $etapas += @{ Nome = 'Vulnerabilidades das dependências (pip-audit)'; Comando = {
            & "$Bin\pip-audit.exe" -r requirements.txt -r requirements-dev.txt --progress-spinner off } }
}

Push-Location $Raiz
try {
    $resumo = foreach ($etapa in $etapas) {
        Write-Host "`n=== $($etapa.Nome) ===" -ForegroundColor Cyan
        & $etapa.Comando | Out-Host
        [pscustomobject]@{ Etapa = $etapa.Nome; Resultado = if ($LASTEXITCODE -eq 0) { 'OK' } else { 'FALHA' } }
    }
} finally {
    Pop-Location
}

Write-Host "`n=== Resumo ===" -ForegroundColor Cyan
$resumo | Format-Table -AutoSize | Out-Host
if ($resumo.Resultado -contains 'FALHA') {
    Write-Host 'Há etapas com falha.' -ForegroundColor Red
    exit 1
}
Write-Host 'Todas as etapas passaram.' -ForegroundColor Green
exit 0
