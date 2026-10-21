@echo off
rem ==========================================================================
rem Trae de Overleaf los cambios de los siete TPs (git subtree pull).
rem Usarlo antes de tocar un TP en el repo y antes de cualquier commit o push.
rem Si en Overleaf no hubo cambios, no hace nada.
rem Los proyectos y sus remotos estan en la seccion Overleaf de context.md.
rem ==========================================================================
chcp 65001 >nul
cd /d "%~dp0"

rem git subtree necesita que no haya cambios sin commitear en el repo
git diff --quiet
if errorlevel 1 goto sin_commitear
git diff --cached --quiet
if errorlevel 1 goto sin_commitear

set FALLAS=0
call :traer TP1_OE1_Procedimiento_RE overleaf-tp1
call :traer TP2_OE2_Manual_SDR overleaf-tp2
call :traer TP3_OR3_Reporte_RE overleaf-tp3
call :traer TP4_OE4_Calibracion_RS overleaf-tp4
call :traer TP5_OE5_Paper_v1 overleaf-tp5
call :traer TP6_OE7_Punta_de_Corriente overleaf-tp6
call :traer TP7_Integrador_EMC_Europe overleaf-tp7

echo.
if %FALLAS%==0 (
    echo Listo: los siete TPs quedaron al día con Overleaf.
) else (
    echo Hubo %FALLAS% fallas: revisar los mensajes de arriba.
)
if not defined SIN_PAUSA pause
exit /b

rem --------------------------------------------------------------------------
rem Trae un TP. %1 es la carpeta dentro de TPs y %2 el remoto de Overleaf.
:traer
echo.
echo === %1 (%2)
git subtree pull -q --prefix=TPs/%1 %2 main --squash -m "Trabajos prácticos del proyecto"
if errorlevel 1 set /a FALLAS+=1
exit /b

rem --------------------------------------------------------------------------
:sin_commitear
echo Hay cambios sin commitear en el repo. Hacé el commit (o descartalos) y volvé a correr este archivo:
git status --short
if not defined SIN_PAUSA pause
exit /b 1
