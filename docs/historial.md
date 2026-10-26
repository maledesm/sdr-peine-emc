# Historial del proyecto

Resumen cronológico de lo hecho: visitas, reuniones, experimentos y decisiones. La bitácora completa, con cada medición, está en [`SDR/Historial_Proyecto_SDR.txt`](../SDR/Historial_Proyecto_SDR.txt).

## Línea de tiempo

| Fecha | Hito |
|---|---|
| 10-09-2026 | Puesta en marcha de la bladeRF x40 (EXP-01). Firmware 2.6.0 y FPGA 0.16.0 grabados en la x40. |
| 12-09-2026 | Lazo TX→RX dentro de la x40 (EXP-02) y primeras espurias propias de la placa (EXP-03). |
| 14-09-2026 | Clase de técnicas de control de EMC ([notas](../materia/Notas%20clase%20EC%2014092026..md)). |
| 16-09-2026 | Primera visita al CETEM (Florencio Varela). El personal cuenta que en Argentina nadie les calibra todos los equipos de EMC ni siguen un estándar de calibración, así que no saben cuándo algo está descalibrado. De ahí sale el objetivo del proyecto. |
| 17-09-2026 | Primera búsqueda bibliográfica. No aparece ningún trabajo que use una SDR como generador peine para verificar sistemas EMC. |
| 26-09-2026 | Medición conducida de la x40 con la tinySA (EXP-04 a EXP-07). Matriz portadora, tono y amplitud (EXP-08) y cancelación de imagen por precorrección IQ (EXP-09). |
| 28-09-2026 | EXP-10, cancelación de la espuria del oscilador local de la x40. Queda en pausa porque la tinySA no alcanza. |
| 01-10-2026 | Primer peine por tandas con la x40 (EXP-12, 22 líneas de 300 a 510 MHz). En el EXP-13 la tabla de calibración de continua baja la fuga más de 20 dB, y el EXP-14 suma un ecualizador. |
| 02-10-2026 | El profesor aprueba pasar a la bladeRF 2.0 micro xA9 (suya). En el EXP-15, ganancia y amplitud, aparece el desborde con amplitud 1,0. El EXP-16 encuentra el límite de 30 MSPS por USB en esta PC. |
| 04-10-2026 | EXP-17, peine manual de 70 a 420 MHz, plano en 2,2 dB sin corregir y con líneas a 0 dBm. EXP-18, lazo TX1→RX1, que se deja de lado. EXP-19 (calibración automática) suspendido. EXP-20, calibración manual por valor medido. El profesor aprueba usar MAX HOLD. |
| 05-10-2026 | EXP-20 medido. EXP-21 (50 MHz a 1 GHz, botón "Generar calibración") y un corte de USB. EXP-22 a 40 MSPS con bloques USB grandes. En el EXP-23, con un tono por portadora, los armónicos del oscilador explican las líneas de más. En el EXP-24, con líneas cada 40 MHz y S = 10 MHz, los armónicos caen sobre el peine. El EXP-25 suma silencio en cada salto y el peine queda plano en 1,1 dB. Se escribe el Test Procedure RE-TP-001. El profesor indica no actualizar el firmware de la xA9. |
| 11-10-2026 | Diseño del EXP-26, ensayo radiado en casa. |
| 12-10-2026 | Ensayo radiado en casa a 2 m (EXP-26), con 20 de 24 líneas 10 dB o más sobre el ruido. Reunión con el profesor previa al CETEM ([resumen](../materia/reuniones/2026-10-12/resumen_reunion.pdf)). |
| 13-10-2026 | Segunda visita al CETEM y primera medición en la cámara semianecoica, con ayuda de Federico Martinez. Se mide el peine de la SDR y el Comb generator de la tesis de otro alumno ([datos](../CETEM/Mediciones), [fotos](../CETEM/Fotos)). |
| 15-10-2026 | Dashboard de las mediciones del CETEM ([`CETEM/Visita CETEM.html`](../CETEM/Visita%20CETEM.html)). |
| 16-10-2026 | Reunión con el profesor. Le gusta el trabajo y se acuerdan mejoras técnicas, tres ejercicios y una hoja de ruta hacia el paper (hoy en [plan.md](plan.md)). Se crea este repositorio y se hace la búsqueda bibliográfica (47 papers). |
| 18-10-2026 | Se redefine el plan con los docentes. La primera parte son cinco TPs (procedimiento de RE, manual de la SDR, reporte de RE, procedimiento de calibración de RS y paper v1), entregados juntos como primer parcial. La segunda son la punta de corriente y el integrador, un paper para EMC Europe 2027 (entrega 22-02-2027). Se adopta el Aprendizaje Basado en Proyectos. Ver [plan.md](plan.md). |
| 19-10-2026 | Repositorio reorganizado por TPs, con las normas y el material de la materia en sus carpetas. Versión 2.0 del procedimiento RE-TP-001 (TP1), con una calibración conducida y otra irradiada contra el límite de CISPR 11 y un peine cada 10 MHz. |
| 20-10-2026 | Diseño del EXP-27, peine cada 10 MHz con calibración conducida, irradiada y perfil de referencia. Versión 2.1 del TP1, con CISPR 11 grupo 1 clase A. |
| 21-10-2026 | Los siete TPs quedan vinculados con sus proyectos de Overleaf. |
| 22-10-2026 | EXP-28: el flujo del EXP-27 con objetivo plano, botones Reiniciar, conducida, irradiada con una sola traza y patrón, más versiones de casa y demo, probadas sin la placa. Martín confirma que el receptor del CETEM barra la banda en unos 3 s. Versión 2.2 del TP1, sin repeticiones (de 16 a 12 páginas). |
| 26-10-2026 | Versión 2.3 del TP1: incertidumbre simplificada en dB, relativa al día de referencia (U = 3,3 dB), verificación irradiada en ±2 dB y criterio de conformidad en ±3,5 dB. TP2 rehecho como manual de la xA9 como instrumento de RF (versión 2.0), sin repetir el TP1 y con gráficos de mediciones propias. Versión 1.0 del TP3, el reporte de las mediciones de casa y del CETEM, con la comparación contra CISPR 11 pendiente de diciembre. |

## Etapas

### 1. bladeRF x40 (10-09 a 01-10)
Aprender la placa y sus defectos con la tinySA por cable. Se catalogaron la fuga de portadora, la imagen, los armónicos del reloj de 38,4 MHz y una réplica fija a −937,2 kHz del oscilador. De ahí salieron las reglas de diseño del peine: ninguna línea sobre el oscilador, todas de un solo lado y calibración de continua al arrancar. El peine por tandas (una portadora por vez con varios tonos) funcionó el 01-10.

### 2. bladeRF xA9 por cable (02-10 a 05-10)
Con la xA9 el peine sale mucho más limpio. Se pasó a un tono por portadora, líneas cada 40 MHz de 60 a 980 MHz, portadora 10 MHz arriba de cada línea y 40 MSPS. Con eso, los armónicos impares del oscilador caen sobre otras líneas del peine. La calibración es manual contra un analizador (una captura .csv da el archivo de calibración) y deja todas las líneas en 0 dBm, de −0,8 a +0,3 dBm. Un silencio en cada salto saca los picos momentáneos del tono mientras el oscilador se mueve.

### 3. Procedimiento y ensayo radiado (05-10 a 12-10)
Test Procedure RE-TP-001 en LaTeX ([`TPs/TP1_OE1_Procedimiento_RE/main.tex`](../TPs/TP1_OE1_Procedimiento_RE/main.tex)), sobre la base del esquema del profesor. El objetivo era verificar la cadena de medición del CETEM y su continuidad en el tiempo, sin comparar contra límites (desde el 18-10 se compara con CISPR 11). Ensayo radiado en casa con la antena telescópica de 30 cm de la SDR.

### 4. Primera medición en el CETEM (13-10)
Receptor R&S ESR-7, antena bilog en el mástil, RBW de 120 kHz y MAX HOLD.
- Las 24 líneas de la SDR se vieron a 1, 2 y 3 m de altura, entre 69 y 96 dBµV/m y de 30 a 46 dB sobre la SDR en pausa.
- Del Comb generator se vieron 75 de 98 líneas a 1 m. La SDR emite unos 33 dB más.
- Con la antena a 1 y 2 m, varias frecuencias de portadora aparecieron casi al nivel de su línea, y hubo picos sueltos fuertes (265, 885 y 944 MHz). La altura cambia cada línea una mediana de 7,9 dB, por el reflejo en el piso. En horizontal el Comb generator no se ve. La notebook quedó dentro de la cámara, sobre la mesa.
- El Comb generator y la SDR en pausa se midieron con 10 dB de atenuación en el receptor y la SDR emitiendo con 20 dB. En el dashboard todo está llevado a 20 dB.

### 5. Plan por TPs (desde 18-10)
Cinco TPs antes del primer parcial y el paper para EMC Europe 2027 como integrador. Ver [plan.md](plan.md).

## Preguntas abiertas
- Si el silencio entre saltos estaba activado en el CETEM. Con silencio la pasada dura 4,8 min y sin silencio 2,4 min, así que si duró unos 2,5 min estaba desactivado.
- La causa de los picos en frecuencias de portadora, de los picos sueltos y del pico recurrente en 750 MHz.
- El significado de "1 M, 2 M, 3 M" (se asumió altura de antena) y "cara" (posición de la mesa) en los nombres de archivo.
- La robustez del USB, porque hubo un corte a los 15 min con el cable original.
