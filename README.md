# Calibrador de emisiones radiadas con SDR

Generador peine con una bladeRF 2.0 micro xA9 y GNU Radio para preverificar la cadena de medición de emisiones radiadas (RE) de un laboratorio de EMC y seguir su continuidad en el tiempo. Compatibilidad Electromagnética (8664 y TB074), FIUBA, 2C2026. Metodología: Aprendizaje Basado en Proyectos (ABP).

En el CETEM nadie les calibra todos los equipos de EMC ni siguen un estándar de calibración, así que no saben cuándo algo se descalibró. Este proyecto busca una referencia barata para comprobarlo seguido.

Trabajan en el proyecto Martín Ledesma (alumno), Pablo Marino Belcaguy y Walter Gustavo Fano (docentes) y Federico Martinez (CETEM).

## Cómo funciona

La SDR emite una línea por vez y el receptor las junta con MAX HOLD. El peine nuevo (EXP-27, en preparación) tiene 96 líneas de 50 MHz a 1 GHz, una cada 10 MHz, con 7 s por línea y 7 s de silencio entre saltos, así que una pasada dura 22 min 24 s. Se calibra dos veces:

1. Por conducción, contra un analizador por cable y a bajo nivel, para que todas las líneas salgan con el mismo nivel.
2. En forma irradiada, en la cámara, para que cada línea llegue a la antena de medición justo sobre el límite de CISPR 11 grupo 1 clase B (a 3 m, 40 dBµV/m hasta 230 MHz y 47 dBµV/m de 230 MHz a 1 GHz).

La antena de medición se pone en tres alturas (1, 2 y 3 m, o las que permita la cámara). La calibración usa la polarización vertical y el mayor nivel de las tres alturas. La horizontal se mide con la antena transmisora acostada, solo para comprobar que esa polarización funciona, sin compararla con el límite.

Después, cada verificación se compara contra el límite. Si el mismo peine, montado igual, se recibe distinto, lo que cambió es la cadena de medición.

## Estado (19-10-2026)

- El peine anterior (24 líneas de 60 a 980 MHz, calibradas por cable a 0 dBm, de −0,8 a +0,3 dBm) se midió en el CETEM el 13-10-2026. En vertical, el mayor nivel de las tres alturas quedó entre 36 y 49 dB por encima del límite.
- El TP1, procedimiento de ensayo de RE (RE-TP-001 versión 2.0), está listo para la revisión de los docentes, con su [PDF](TPs/TP1_OE1_Procedimiento_RE/TP1_OE1_Procedimiento_RE.pdf).
- Siguen el EXP-27 y los TP2 a TP5.

| Entrega | Fecha |
|---|---|
| Fase 1: TP1 a TP5, juntos, como primer parcial | semana del 26-10-2026 |
| Visita al CETEM | principios de diciembre de 2026, a coordinar |
| TP7: paper para EMC Europe 2027 | 22-02-2027 |

El plan de TPs está pendiente de la confirmación de Walter Gustavo Fano. El detalle de cada tarea está en el [plan](docs/plan.md).

## TPs

Los TP1 a TP5 forman la fase 1 y los TP6 y TP7, la fase 2. TP1 a TP4 van en español, TP5 y TP7 en inglés.

| TP | Código | Tema |
|---|---|---|
| [TP1](TPs/TP1_OE1_Procedimiento_RE/) | OE1 | Procedimiento de ensayo de RE |
| [TP2](TPs/TP2_OE2_Manual_SDR/) | OE2 | Manual y procedimiento funcional de la SDR |
| [TP3](TPs/TP3_OR3_Reporte_RE/) | OR3 | Reporte de mediciones de RE |
| [TP4](TPs/TP4_OE4_Calibracion_RS/) | OE4 | Procedimiento de calibración de RS |
| [TP5](TPs/TP5_OE5_Paper_v1/) | OE5 | Paper, versión 1 |
| [TP6](TPs/TP6_OE7_Punta_de_Corriente/) | OE7 | Medición con punta de corriente (en pausa) |
| [TP7](TPs/TP7_Integrador_EMC_Europe/) | - | Integrador, el paper para EMC Europe 2027 |

## Carpetas

| Carpeta | Contenido |
|---|---|
| [`docs/`](docs/) | [plan.md](docs/plan.md) (objetivos, tareas y fechas), [historial.md](docs/historial.md), [conocimiento_tecnico.md](docs/conocimiento_tecnico.md) y [bibliografia.md](docs/bibliografia.md). |
| [`TPs/`](TPs/) | Un proyecto de Overleaf por TP, con el PDF compilado junto al `.tex`. |
| [`SDR/`](SDR/) | Un subdirectorio por experimento (`X40_` o `A9_` + orden + EXP) con su flujo `.grc` y sus capturas, y la bitácora [`Historial_Proyecto_SDR.txt`](SDR/Historial_Proyecto_SDR.txt). |
| [`CETEM/`](CETEM/) | Medición del 13-10-2026: trazas, fotos y el dashboard `Visita CETEM.html`. |
| [`bibliografia/`](bibliografia/) | 47 papers, los 20 principales en cinco carpetas por tema y el resto en `6_Extra`. |
| [`materia/`](materia/) | Consigna original, notas de clase, guía de medición de cables y reuniones. |
| [`normas/`](normas/) | CISPR 11:2024 y MIL-STD-461E. |

Las reglas para trabajar en el proyecto (seguridad de los equipos, forma de trabajo y estilo) están en [context.md](context.md).

Herramientas: GNU Radio 3.10 (Radioconda) con gr-osmosdr, bladeRF-cli, tinySA Ultra+ como analizador de banco, pdfLaTeX (MiKTeX) y Overleaf.
