@echo off
rem Gera main.pdf com pdflatex + bibtex (MiKTeX ou TeX Live no Windows).
rem Uso: duplo clique neste arquivo, ou "compilar.bat" no Prompt/PowerShell.
cd /d "%~dp0"
where pdflatex >nul 2>nul || (echo pdflatex nao encontrado. Instale o MiKTeX: https://miktex.org & goto erro)
echo [1/4] pdflatex
pdflatex -interaction=nonstopmode main.tex >nul || goto erro
echo [2/4] bibtex
rem O bibtex retorna codigo diferente de zero tambem para avisos.
bibtex main >nul
echo [3/4] pdflatex
pdflatex -interaction=nonstopmode main.tex >nul || goto erro
echo [4/4] pdflatex
pdflatex -interaction=nonstopmode main.tex >nul || goto erro
echo.
echo PDF gerado: %~dp0main.pdf
if /i not "%~1"=="--sem-pausa" start "" "%~dp0main.pdf"
goto fim
:erro
echo.
echo Erro na compilacao. Se o PDF estiver aberto em outro programa, feche-o.
echo Detalhes em: %~dp0main.log
findstr /b /c:"!" main.log 2>nul
:fim
if /i not "%~1"=="--sem-pausa" pause
