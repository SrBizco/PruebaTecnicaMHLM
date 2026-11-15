$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Primero crea .venv e instala requirements.txt.' }
& $pythonExe -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Fallo al instalar herramientas de compilacion.' }
& $pythonExe -m PyInstaller --noconfirm --clean --onefile --windowed --name ARCA-RPA --collect-all playwright --hidden-import win32cred launcher.py
if ($LASTEXITCODE -ne 0) { throw 'Fallo al crear el ejecutable.' }
Write-Host 'Ejecutable: dist\ARCA-RPA.exe'
