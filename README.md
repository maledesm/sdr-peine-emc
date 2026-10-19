# Calibrador de emisiones radiadas con SDR

Generador peine con una bladeRF 2.0 micro xA9 y GNU Radio para preverificar la cadena de medición de emisiones radiadas (RE) de un laboratorio de EMC y seguir su continuidad en el tiempo. Compatibilidad Electromagnética (8664 y TB074), FIUBA, 2C2026. Metodología: Aprendizaje Basado en Proyectos (ABP).

En el CETEM nadie les calibra todos los equipos de EMC ni siguen un estándar de calibración, así que no saben cuándo algo se descalibró. Este proyecto busca una referencia barata para comprobarlo seguido.

Trabajan en el proyecto Martín Ledesma (alumno), Pablo Marino Belcaguy y Walter Gustavo Fano (docentes) y Federico Martinez (CETEM).

El peine funciona: 24 líneas de 60 a 980 MHz, calibradas por cable a 0 dBm ± 0,5 dB y medidas en el CETEM el 13-10-2026. Ahora se trabaja en los cinco TPs de la fase 1 ([plan](docs/plan.md)).

## Carpetas

| Carpeta | Contenido |
|---|---|
| [`docs/`](docs/) | [plan.md](docs/plan.md) (objetivos, tareas y fechas), [historial.md](docs/historial.md), [conocimiento_tecnico.md](docs/conocimiento_tecnico.md) y [bibliografia.md](docs/bibliografia.md). |
| [`TPs/`](TPs/) | Un proyecto de Overleaf por TP (TP1 a TP7). |
| [`SDR/`](SDR/) | Un subdirectorio por experimento (`X40_` o `A9_` + orden + EXP) con su flujo `.grc` y sus capturas, y la bitácora [`Historial_Proyecto_SDR.txt`](SDR/Historial_Proyecto_SDR.txt). |
| [`CETEM/`](CETEM/) | Medición del 13-10-2026: trazas, fotos y el dashboard `Visita CETEM.html`. |
| [`bibliografia/`](bibliografia/) | Papers, por tema. |
| [`materia/`](materia/) | Consigna original, notas de clase, guía de medición de cables y reuniones. |
| [`normas/`](normas/) | CISPR 11:2024 y MIL-STD-461E. |

Herramientas: GNU Radio 3.10 (Radioconda) con gr-osmosdr, bladeRF-cli, tinySA Ultra+ como analizador de banco y Overleaf.
