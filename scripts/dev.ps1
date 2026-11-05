<#
.SYNOPSIS
    Sobe o SUAP V2 para desenvolvimento local.

.DESCRIPTION
    Verifica o ambiente (scripts\verificar-ambiente.ps1), inicia o processador da fila de tarefas
    (manage.py qcluster) quando o Django-Q2 estiver configurado e sobe o servidor de
    desenvolvimento. Ctrl+C encerra o servidor e a fila.

.PARAMETER Porta
    Porta do servidor web em 127.0.0.1.

.PARAMETER SemVerificacao
    Não executa scripts\verificar-ambiente.ps1 antes de subir.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 -Porta 8001 -SemVerificacao
#>
[CmdletBinding()]
param(
    [int]$Porta = 8000,
    [switch]$SemVerificacao
)

$Raiz = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Raiz '.venv\Scripts\python.exe'

if (-not $SemVerificacao) {
    & (Join-Path $PSScriptRoot 'verificar-ambiente.ps1')
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Corrija as falhas acima ou rode com -SemVerificacao.' -ForegroundColor Red
        exit 1
    }
}

Push-Location $Raiz
$fila = $null
try {
    # A fila só existe depois que o Django-Q2 entrar em INSTALLED_APPS (prevista para a E3).
    $filaConfigurada = Select-String -Path 'config\settings\base.py' -Pattern '"django_q"' -SimpleMatch -Quiet
    if ($filaConfigurada) {
        $fila = Start-Process -FilePath $Python -ArgumentList 'manage.py', 'qcluster' -NoNewWindow -PassThru
        Write-Host "Fila de tarefas (qcluster) iniciada, PID $($fila.Id)." -ForegroundColor Cyan
    } else {
        Write-Host 'Fila de tarefas (Django-Q2) ainda não configurada: subindo só o servidor web.' -ForegroundColor Yellow
    }

    Write-Host "Servidor em http://127.0.0.1:$Porta/  (saúde: /healthz). Ctrl+C para encerrar." -ForegroundColor Cyan
    & $Python manage.py runserver "127.0.0.1:$Porta"
} finally {
    if ($fila -and -not $fila.HasExited) {
        # O qcluster cria processos filhos: encerra a árvore inteira.
        & taskkill.exe /PID $fila.Id /T /F *> $null
    }
    Pop-Location
}
