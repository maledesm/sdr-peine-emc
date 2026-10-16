# Historial del proyecto

Resumen cronológico de lo hecho: visitas, reuniones, experimentos y decisiones. La bitácora completa, con cada medición, está en [`SDR/Historial_Proyecto_SDR.txt`](../SDR/Historial_Proyecto_SDR.txt).

## Línea de tiempo

| Fecha | Hito |
|---|---|
| 10-09-2026 | Puesta en marcha de la bladeRF x40 (EXP-01). Firmware 2.6.0 y FPGA 0.16.0 grabados en la x40. |
| 12-09-2026 | Lazo TX→RX dentro de la x40 (EXP-02) y primeras espurias propias de la placa (EXP-03). |
| 14-09-2026 | Clase de técnicas de control de EMC ([notas](../Notas%20clase%20EC%2014092026..md)). |
| **16-09-2026** | **Primera visita al CETEM (Florencio Varela).** El personal cuenta que en Argentina nadie les calibra todos los equipos de EMC ni siguen un estándar de calibración: no saben cuándo algo está descalibrado. De ahí sale el objetivo del proyecto. |
| 17-09-2026 | Primera búsqueda bibliográfica: no aparece ningún trabajo que use una SDR como generador peine para verificar sistemas EMC. |
| 26-09-2026 | Medición conducida de la x40 con la tinySA (EXP-04 a EXP-07). Matriz portadora/tono/amplitud (EXP-08) y cancelación de imagen por precorrección IQ (EXP-09). |
| 28-09-2026 | EXP-10, cancelación de la espuria del oscilador local de la x40: queda en pausa (la tinySA no alcanza). |
| 01-10-2026 | Primer peine por tandas con la x40 (EXP-12, 22 líneas de 300 a 510 MHz). EXP-13: la tabla de calibración de continua baja la fuga más de 20 dB. EXP-14: peine con ecualizador. |
| 02-10-2026 | El profesor aprueba pasar a la **bladeRF 2.0 micro xA9** (suya). EXP-15: ganancia y amplitud; se descubre el desborde con amplitud 1,0. EXP-16: límite de 30 MSPS por USB en esta PC. |
| 04-10-2026 | EXP-17: peine manual de 70 a 420 MHz, plano en 2,2 dB sin corregir; líneas a 0 dBm. EXP-18: lazo TX1→RX1 (se deja de lado). EXP-19 (calibración automática) suspendido. EXP-20: calibración manual por valor medido. El profesor aprueba usar MAX HOLD. |
| 05-10-2026 | EXP-20 medido. EXP-21 (50 MHz a 1 GHz, botón "Generar calibración") y un corte de USB. EXP-22 a 40 MSPS con bloques USB grandes. EXP-23 con un tono por portadora: los armónicos del oscilador explican las líneas de más. EXP-24: líneas cada 40 MHz con S = 10 MHz, los armónicos caen sobre el peine. EXP-25: silencio en cada salto, peine plano en 1,1 dB. Se escribe el Test Procedure RE-TP-001. El profesor indica no actualizar el firmware de la xA9. |
| 11-10-2026 | Diseño del EXP-26, ensayo radiado en casa. |
| 12-10-2026 | Ensayo radiado en casa a 2 m (EXP-26): 20 de 24 líneas con 10 dB o más sobre el ruido. **Reunión con el profesor** previa al CETEM ([resumen](../SDR/Reunion_2026-10-12/resumen_reunion.pdf)). |
| **13-10-2026** | **Segunda visita al CETEM: primera medición en la cámara semianecoica**, con ayuda de Federico Martinez. Se mide el peine de la SDR y el Comb generator de la tesis de otro alumno ([datos](../CETEM/Mediciones), [fotos](../CETEM/Fotos)). |
| 15-10-2026 | Dashboard de las mediciones del CETEM ([`CETEM/Visita CETEM.html`](../CETEM/Visita%20CETEM.html)). |
| **16-10-2026** | **Reunión con el profesor:** le gusta el trabajo; se acuerdan 20 puntos y una hoja de ruta ([acuerdos](acuerdos_2026-10-16.md), [roadmap](roadmap.md)). Se crea este repositorio. |

## Etapas

### 1. bladeRF x40 (10-09 a 01-10)
Aprender la placa y sus defectos con la tinySA por cable. Se catalogaron la fuga de portadora, la imagen, los armónicos del reloj de 38,4 MHz y una réplica fija a −937,2 kHz del oscilador. De ahí salieron las reglas de diseño del peine: ninguna línea sobre el oscilador, todas de un solo lado y calibración de continua al arrancar. El peine por tandas (una portadora por vez con varios tonos) funcionó el 01-10.

### 2. bladeRF xA9 por cable (02-10 a 05-10)
Con la xA9 el peine sale mucho más limpio. Se pasó a un tono por portadora, líneas cada 40 MHz de 60 a 980 MHz, portadora 10 MHz arriba de cada línea y 40 MSPS. Con eso, los armónicos impares del oscilador caen sobre otras líneas del peine. La calibración es manual contra un analizador (una captura .csv → archivo de calibración) y deja todas las líneas en 0 dBm ± 0,5 dB. Un silencio en cada salto saca los picos momentáneos del tono mientras el oscilador se mueve.

### 3. Procedimiento y ensayo radiado (05-10 a 12-10)
Test Procedure RE-TP-001 en LaTeX ([`SDR/Test_Procedure_RE/main.tex`](../SDR/Test_Procedure_RE/main.tex)), sobre la base del esquema del profesor. Objetivo: verificar la cadena de medición del CETEM y su continuidad en el tiempo, no comparar contra límites. Ensayo radiado en casa con la antena telescópica de 30 cm de la SDR.

### 4. Primera medición en el CETEM (13-10)
Receptor R&S ESR-7, antena bilog en el mástil, RBW 120 kHz, MAX HOLD.
- **SDR:** las 24 líneas se vieron a 1, 2 y 3 m de altura, entre 69 y 96 dBµV/m, de 30 a 46 dB sobre la SDR en pausa.
- **Comb generator:** 75 de 98 líneas a 1 m. La SDR emite unos 33 dB más que el Comb generator.
- **Problemas:** con la antena a 1 y 2 m, varias frecuencias de portadora aparecieron casi al nivel de su línea, y hubo picos sueltos fuertes (265, 885 y 944 MHz). La altura cambia cada línea una mediana de 7,9 dB (reflejo en el piso). En horizontal el Comb generator no se ve. La notebook quedó dentro de la cámara, sobre la mesa.
- **Atenuación:** el Comb generator y la SDR en pausa se midieron con 10 dB en el receptor y la SDR emitiendo con 20 dB; en el dashboard todo está llevado a 20 dB.

### 5. Segunda etapa (desde 16-10)
Ver [roadmap.md](roadmap.md).

## Preguntas abiertas
- Si el silencio entre saltos estaba activado en el CETEM (ver la nota de P13 en los acuerdos).
- Causa de los picos en frecuencias de portadora y de los picos sueltos; el pico recurrente en 750 MHz.
- Cómo tomó el receptor cada traza: con paso de 30 kHz y 50 ms por punto, un barrido tardaría unos 27 min.
- El significado de "1 M, 2 M, 3 M" (se asumió altura de antena) y "cara" (posición de la mesa) en los nombres de archivo.
- Robustez del USB: hubo un corte a los 15 min con el cable original.
