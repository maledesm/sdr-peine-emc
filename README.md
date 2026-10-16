# Calibrador de emisiones radiadas con SDR

Generador peine hecho con una **bladeRF 2.0 micro xA9** y GNU Radio, para verificar la cadena de medición de emisiones radiadas (RE) de un laboratorio de EMC y seguir su continuidad en el tiempo. Trabajo Práctico Integrador de Compatibilidad Electromagnética (8664 y TB074), FIUBA, 2.º cuatrimestre de 2026.

**Motivación.** En la visita al CETEM (Florencio Varela) del 16-09-2026, el personal contó que en Argentina nadie les calibra todos los equipos de EMC ni siguen un estándar de calibración, así que no saben cuándo algo está descalibrado. La idea es una herramienta barata que el laboratorio pueda usar seguido para comprobar que su cadena de medición sigue igual.

## Personas

- **Martín Ledesma**, alumno (autor).
- **Pablo Marino Belcaguy**, JTP de la materia.
- **Walter Gustavo Fano**, docente de la materia.
- **Federico Martinez**, CETEM: ayuda con las mediciones en la cámara.

## Estado (16-10-2026)

- El peine funciona: 24 líneas de 60 a 980 MHz, calibradas por cable a 0 dBm ± 0,5 dB.
- Primera medición en la cámara semianecoica del CETEM hecha el 13-10-2026, junto con el Comb generator de la tesis de otro alumno.
- Siguiente etapa acordada con el profesor el 16-10-2026: [acuerdos](docs/acuerdos_2026-10-16.md) y [hoja de ruta](docs/roadmap.md).

## Documentación

| Documento | Para qué |
|---|---|
| [docs/acuerdos_2026-10-16.md](docs/acuerdos_2026-10-16.md) | Los 20 puntos acordados con el profesor, por tema. |
| [docs/roadmap.md](docs/roadmap.md) | Hoja de ruta hacia el informe final y el paper. |
| [docs/historial.md](docs/historial.md) | Línea de tiempo: visitas, reuniones, experimentos y decisiones. |
| [docs/conocimiento_tecnico.md](docs/conocimiento_tecnico.md) | Equipos, límites, configuración actual del peine y hallazgos técnicos. |
| [docs/bibliografia.md](docs/bibliografia.md) | Trabajos relacionados encontrados. |
| [SDR/Historial_Proyecto_SDR.txt](SDR/Historial_Proyecto_SDR.txt) | Bitácora detallada de cada experimento (EXP-01 a EXP-26) y mapa de archivos. |

## Carpetas

| Carpeta | Contenido |
|---|---|
| `SDR/` | Un subdirectorio por experimento: `X40_` o `A9_` (placa usada) + número de orden + experimento. Cada uno tiene su flujo `.grc` y sus capturas. También el procedimiento RE-TP-001 (`Test_Procedure_RE/`, LaTeX para Overleaf) y el material de la reunión del 12-10 (`Reunion_2026-10-12/`). |
| `CETEM/` | Medición del 13-10-2026: trazas del receptor (`Mediciones/`), fotos del laboratorio (`Fotos/`) y propias (`Fotos mias/`), y el dashboard `Visita CETEM.html` (se abre sin internet). |
| `bibliografia/` | PDF de los papers. |
| `docs/` | Documentación del proyecto. |
| raíz | Consigna del TP, Test Procedure de RE del profesor, notas de clase. |

## Herramientas

GNU Radio 3.10 (Radioconda) con gr-osmosdr; bladeRF-cli; tinySA Ultra+ como analizador de banco. Los flujos se abren con GNU Radio Companion.
