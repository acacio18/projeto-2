<#
.SYNOPSIS
    Verifica se o ambiente de desenvolvimento do SUAP V2 está pronto.

.DESCRIPTION
    Confere o ambiente virtual (.venv com Python 3.12), se as dependências instaladas batem com
    requirements*.txt, o arquivo .env, o serviço do PostgreSQL, o Chromium do Playwright e,
    pelo comando "manage.py verificar_saude", o banco de dados e o Tesseract com português.
    Termina com código 1 se alguma verificação falhar.

.PARAMETER ServicoPostgres
    Nome do serviço do Windows do PostgreSQL.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\verificar-ambiente.ps1
#>
[CmdletBinding()]
param(
    [string]$ServicoPostgres = 'postgresql-x64-16'
)

$Raiz = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Raiz '.venv\Scripts'
$Python = Join-Path $Venv 'python.exe'
$script:falhas = 0

function Registrar([bool]$Passou, [string]$Descricao, [string]$Dica) {
    if ($Passou) {
        Write-Host "OK    $Descricao" -ForegroundColor Green
    } else {
        Write-Host "FALHA $Descricao" -ForegroundColor Red
        if ($Dica) { Write-Host "      -> $Dica" -ForegroundColor Yellow }
        $script:falhas++
    }
}

Push-Location $Raiz
try {
    $versao = if (Test-Path $Python) { (& $Python --version 2>&1) -join ' ' } else { 'não encontrado' }
    $temPython = $versao -match '^Python 3\.12\.'
    Registrar $temPython "Ambiente virtual .venv com Python 3.12 ($versao)" `
        'Crie com: py -3.12 -m venv .venv ; depois instale as dependências (linha abaixo).'

    if ($temPython) {
        & (Join-Path $Venv 'pip-sync.exe') --dry-run requirements.txt requirements-dev.txt *> $null
        Registrar ($LASTEXITCODE -eq 0) 'Dependências do .venv iguais a requirements.txt e requirements-dev.txt' `
            '.venv\Scripts\pip-sync requirements.txt requirements-dev.txt'
    }

    $arquivoEnv = Join-Path $Raiz '.env'
    $envOk = $false
    if (Test-Path $arquivoEnv) {
        $conteudo = Get-Content $arquivoEnv -Raw
        $envOk = ($conteudo -match '(?m)^DJANGO_SECRET_KEY=\S+') -and ($conteudo -match '(?m)^DATABASE_URL=\S+') `
            -and ($conteudo -notmatch 'troque-por-uma-chave') -and ($conteudo -notmatch ':SENHA@')
    }
    Registrar $envOk 'Arquivo .env com DJANGO_SECRET_KEY e DATABASE_URL preenchidos' `
        'Copie .env.example para .env e preencha a chave secreta e a senha do banco.'

    $servico = Get-Service -Name $ServicoPostgres -ErrorAction SilentlyContinue
    Registrar ($servico -and $servico.Status -eq 'Running') "Serviço do PostgreSQL ($ServicoPostgres) em execução" `
        "Inicie com: Start-Service $ServicoPostgres (requer administrador)"

    $chromium = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'ms-playwright') -Directory -Filter 'chromium-*' -ErrorAction SilentlyContinue
    Registrar ([bool]$chromium) 'Chromium do Playwright instalado (testes de navegador)' `
        '.venv\Scripts\playwright install chromium'

    if ($temPython -and $envOk) {
        Write-Host '--- manage.py verificar_saude ---'
        & $Python manage.py verificar_saude
        Registrar ($LASTEXITCODE -eq 0) 'Banco de dados e Tesseract com português respondem' `
            'Veja as linhas FALHA acima: confira DATABASE_URL e TESSERACT_CMD no .env.'
    }
} finally {
    Pop-Location
}

if ($script:falhas -gt 0) {
    Write-Host "`nAmbiente com $($script:falhas) falha(s)." -ForegroundColor Red
    exit 1
}
Write-Host "`nAmbiente pronto." -ForegroundColor Green
exit 0
