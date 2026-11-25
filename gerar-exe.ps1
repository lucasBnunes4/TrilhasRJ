$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    py -3.13 -m venv .venv-build
    if ($LASTEXITCODE -ne 0) { throw "Instale o Python 3.13 para Windows com o Python Launcher (py)." }

    $python = ".\.venv-build\Scripts\python.exe"
    & $python -m pip install requests tzdata pyinstaller
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependÃªncias." }

    & $python -m PyInstaller --clean --noconfirm --onefile --name TrilhasRJ `
        --collect-data tzdata `
        --add-data "trilhas.csv:." `
        --add-data "ponto_interesse.csv:." `
        --add-data "vinculos-aprovados.csv:." `
        --add-data "observacao-piloto.csv:." `
        --add-data "inventario-estacoes-pluviometricas-rj.csv:." `
        --add-data "conhecimento:conhecimento" `
        --add-data "gpx:gpx" `
        --add-data "src/assets:src/assets" `
        src/abrir_trilhas.py
    if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar o executÃ¡vel." }

    @"
TRILHAS RJ
Extraia todos os arquivos do ZIP e clique duas vezes em TrilhasRJ.exe.
Mantenha a janela do aplicativo aberta. A interface abre no navegador.
Se o navegador nÃ£o abrir, digite o endereÃ§o mostrado na janela.
Use internet para consultar os dados meteorolÃ³gicos.
Feche a janela do aplicativo para encerrar.
"@ | Set-Content -Encoding UTF8 dist/LEIA-ME.txt

    Compress-Archive -Path dist/TrilhasRJ.exe, dist/LEIA-ME.txt -DestinationPath dist/TrilhasRJ-Windows.zip -Force
    Write-Host "Pacote de entrega: dist/TrilhasRJ-Windows.zip"
}
finally {
    Pop-Location
}

