@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "PORT=8000"
set "URL=http://127.0.0.1:%PORT%/contas/login/?next=/empresas/1/dashboard/"

cd /d "%PROJECT_DIR%"

if not exist "manage.py" (
    echo Nao encontrei o manage.py na raiz do projeto:
    echo %PROJECT_DIR%
    echo.
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo Verificando migracoes...
%PYTHON% manage.py migrate
if errorlevel 1 (
    echo.
    echo Falha ao aplicar migracoes. Verifique se o Python e o Django estao disponiveis.
    echo.
    pause
    exit /b 1
)

echo.
echo Abrindo o sistema em: %URL%
start "" "%URL%"

echo.
echo Servidor iniciado em http://127.0.0.1:%PORT%/
echo Pressione CTRL+C para parar.
echo.
%PYTHON% manage.py runserver 127.0.0.1:%PORT%

endlocal
