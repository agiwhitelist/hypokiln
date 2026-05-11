# HypoKiln one-line installer (Windows / PowerShell).
#
# Usage (from inside a cloned repo):
#   .\install.ps1
#
# Or one-shot from the web:
#   irm https://raw.githubusercontent.com/agiwhitelist/hypokiln/main/install.ps1 | iex
#
# When invoked outside a clone, the script auto-clones into .\hypokiln\ and
# re-execs itself from inside the clone.
#
# What it does (idempotent):
#   0. clones the repo if invoked via irm|iex outside a checkout
#   1. checks Python 3.12+, Node 20+
#   2. creates .venv and installs Python deps including [control]
#   3. installs Node deps for web\
#   4. copies .env.example -> .env if missing
#   5. seeds four demo runs
#   6. tells you what to run next

$ErrorActionPreference = 'Stop'

$RepoUrl   = $env:HYPOKILN_REPO_URL  ; if (-not $RepoUrl)   { $RepoUrl   = 'https://github.com/agiwhitelist/hypokiln.git' }
$Branch    = $env:HYPOKILN_BRANCH    ; if (-not $Branch)    { $Branch    = 'main' }
$CloneDir  = $env:HYPOKILN_CLONE_DIR ; if (-not $CloneDir)  { $CloneDir  = 'hypokiln' }

function Write-Title($msg) { Write-Host "`n$msg" -ForegroundColor White }
function Write-Ok($msg)    { Write-Host "[OK] $msg"   -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[!] $msg"    -ForegroundColor Yellow }
function Write-Fail($msg)  { Write-Host "[X] $msg"    -ForegroundColor Red; exit 1 }
function Have($exe)        { return [bool](Get-Command $exe -ErrorAction SilentlyContinue) }

# ── 0. self-bootstrap from irm|iex ─────────────
$InRepo = (Test-Path 'pyproject.toml') -and (Test-Path '.github') -and
          ((Get-Content 'pyproject.toml' -Raw -ErrorAction SilentlyContinue) -match '"hypokiln"')
if (-not $InRepo) {
    if (-not (Have 'git')) { Write-Fail 'git is required to bootstrap HypoKiln.' }
    if (Test-Path "$CloneDir\.git") {
        Write-Host "  reusing existing clone at .\$CloneDir" -ForegroundColor DarkGray
    } else {
        Write-Title "Cloning $RepoUrl -> .\$CloneDir"
        git clone --depth=1 --branch $Branch $RepoUrl $CloneDir
        if ($LASTEXITCODE -ne 0) { Write-Fail 'git clone failed.' }
    }
    Set-Location $CloneDir
    & powershell -ExecutionPolicy Bypass -File .\install.ps1
    exit $LASTEXITCODE
}

# ── 1. preflight ───────────────────────────────
Write-Title '1/6  Checking prerequisites'

$PythonBin = $null
foreach ($cand in @('python3.12','python3.13','python','python3')) {
    if (Have $cand) {
        $ver = & $cand -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>$null
        if ($ver) {
            $parts = $ver.Split('.')
            if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 12) {
                $PythonBin = $cand
                Write-Ok "python: $cand ($ver)"
                break
            }
        }
    }
}
if (-not $PythonBin) { Write-Fail 'Python 3.12+ not found. Install from https://www.python.org/downloads/' }

if (-not (Have 'node')) { Write-Fail 'node not found. Install Node 20+ from https://nodejs.org/' }
$nodeVer  = (& node --version).TrimStart('v')
$nodeMajor = [int]$nodeVer.Split('.')[0]
if ($nodeMajor -lt 20) { Write-Fail "Node $nodeVer is too old; need Node 20+." }
Write-Ok "node: v$nodeVer"

if (-not (Have 'npm')) { Write-Fail 'npm not found (ships with Node).' }

$cliFound = @()
foreach ($bin in @('codex','claude','gemini')) { if (Have $bin) { $cliFound += $bin } }
if ($cliFound.Count -eq 0) {
    Write-Warn 'No coding CLI on PATH (codex / claude / gemini). HypoKiln installs anyway,'
    Write-Warn 'but `kiln build` needs one. See README for login.'
} else {
    Write-Ok ("coding CLI: " + ($cliFound -join ' '))
}

# ── 2. python venv + deps ──────────────────────
Write-Title '2/6  Setting up Python virtualenv'
if (-not (Test-Path '.venv')) {
    & $PythonBin -m venv .venv
    Write-Ok 'created .venv\'
} else {
    Write-Ok '.venv\ already exists'
}

$VenvPip    = '.\.venv\Scripts\pip.exe'
$VenvPython = '.\.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPip)) { Write-Fail 'venv pip missing — venv creation failed.' }

Write-Host '  upgrading pip' -ForegroundColor DarkGray
& $VenvPython -m pip install --quiet --upgrade pip
Write-Host '  installing hypokiln + control plane deps' -ForegroundColor DarkGray
& $VenvPip install --quiet -e '.[dev,control]'
Write-Ok 'python deps installed'

# ── 3. node deps for web\ ──────────────────────
Write-Title '3/6  Installing web dashboard deps'
Push-Location web
try {
    npm install --no-audit --no-fund --loglevel=error
    if ($LASTEXITCODE -ne 0) { Write-Fail 'npm install failed in web\' }
} finally { Pop-Location }
Write-Ok 'web\ deps installed'

# ── 4. .env ────────────────────────────────────
Write-Title '4/6  Bootstrapping .env'
if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Ok '.env created from template'
} else {
    Write-Ok '.env already exists (not overwritten)'
}

# ── 5. seed demo runs ──────────────────────────
Write-Title '5/6  Seeding demo ideas'
$env:HYPOKILN_SKIP_SKILLS = '1'
& $VenvPython scripts\seed_demo.py
Write-Ok 'demo ideas seeded under .hypokiln\state\'

# ── 6. final message ──────────────────────────
Write-Title '6/6  Done.'
@"

  Next steps:

    make dev                          start FastAPI + Next.js in parallel
                                        FastAPI on   http://localhost:8765
                                        dashboard on http://localhost:3000

    kiln build "<your idea here>"     spawn a new pipeline from the CLI
    kiln capability-scan              browse fresh AI wedges
    kiln status                       list every idea + stage progress

  Activate the venv in new shells with:  .\.venv\Scripts\Activate.ps1

"@ | Write-Host
