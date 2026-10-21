@echo off
rem ==========================================================================
rem Sube a Overleaf lo que se commiteo en las carpetas de los siete TPs
rem (git subtree push). Usarlo despues de hacer el commit: lo que no esta
rem commiteado no se sube. Si Overleaf tiene cambios nuevos, rechaza la
rem subida de ese TP: correr antes traer_de_overleaf.bat.
rem No sube nada a GitHub. Para eso esta git push.
rem Los proyectos y sus remotos estan en la seccion Overleaf de context.md.
rem ==========================================================================
chcp 65001 >nul
cd /d "%~dp0"

git diff --quiet -- TPs
if errorlevel 1 echo Aviso: hay cambios sin commitear en TPs. No se suben hasta hacer el commit.

set FALLAS=0
call :subir TP1_OE1_Procedimiento_RE overleaf-tp1
call :subir TP2_OE2_Manual_SDR overleaf-tp2
call :subir TP3_OR3_Reporte_RE overleaf-tp3
call :subir TP4_OE4_Calibracion_RS overleaf-tp4
call :subir TP5_OE5_Paper_v1 overleaf-tp5
call :subir TP6_OE7_Punta_de_Corriente overleaf-tp6
call :subir TP7_Integrador_EMC_Europe overleaf-tp7

echo.
if %FALLAS%==0 (
    echo Listo: los siete TPs quedaron subidos a Overleaf.
) else (
    echo Hubo %FALLAS% fallas. Si dice "rejected", correr traer_de_overleaf.bat y volver a subir.
)
echo Esto no sube nada a GitHub. Para eso: git push.
if not defined SIN_PAUSA pause
exit /b

rem --------------------------------------------------------------------------
rem Sube un TP. %1 es la carpeta dentro de TPs y %2 el remoto de Overleaf.
:subir
echo.
echo === %1 (%2)
git subtree push -q --prefix=TPs/%1 %2 main
if errorlevel 1 set /a FALLAS+=1
exit /b
