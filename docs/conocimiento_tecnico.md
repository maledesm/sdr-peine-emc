# Conocimiento técnico

Lo verificado midiendo o leyendo código fuente. Detalle de cada medición: [`SDR/Historial_Proyecto_SDR.txt`](../SDR/Historial_Proyecto_SDR.txt).

## Equipos

| Equipo | Datos clave |
|---|---|
| **bladeRF 2.0 micro xA9** (del profesor) | Serie `321e0fa5875945d99b11070bb0a76d31`. TX 47 MHz–6 GHz, RX desde 70 MHz, hasta 56 MHz de ancho de banda, ganancia de TX de −23,75 a 66 dB. Solo USB 3. Firmware 2.4.0 y FPGA 0.14.0: **no actualizar**. Bias tee apagado. |
| bladeRF x40 (prestada) | Serie `96c4c15c9fc517a47ad39c98ae127a31`. 237,5 MHz–3,8 GHz, 28 MHz, hasta +6 dBm. **Nunca habilitar la XB-200** (no la tiene). |
| tinySA Ultra+ ZS-406 | 100 kHz–5,4 GHz. Máximo +6 dBm con atenuación en 0 dB; +20 dBm de pico con 30 dB manual. CSV `MHz,dBm`, 450 puntos, CRLF. Barrer 45–1005 MHz con RBW 300 kHz: 2,8 s. |
| PC | Radioconda 2025.03.14 (GNU Radio 3.10.12, gr-osmosdr) en `C:\Users\tinch\radioconda`; bladeRF-cli en `C:\Program Files\bladeRF\x64\`. |
| Accesorios | Cables SMA y carga de 50 Ω; sin atenuador ni divisor. Antena de la SDR: telescópica de 30 cm, totalmente extendida. |

## Peine actual (EXP-25 / EXP-26)

- 24 líneas de 60 a 980 MHz, cada 40 MHz, una por vez; el receptor las junta con MAX HOLD.
- Un tono por portadora, portadora S = 10 MHz arriba de la línea. 40 MSPS con bloques USB de 16384 × 128 (`buffers=128,buflen=16384`).
- 6 s por línea. Con silencio (6 s encendida, 6 s apagada, salto en el silencio) la pasada dura 4 min 48 s; sin silencio, 2 min 24 s.
- Calibración por cable: "Generar calibración" lee el .csv del analizador, toma el máximo a ±4 MHz de cada línea y la lleva a 0 dBm; se guarda en un archivo y se importa en la cámara. Admite retoque manual.
- Por cable: planitud de 1,1 dB (−0,8 a +0,3 dBm), desvío de 0,28 dB.
- EXP-26: selector de ganancia, línea fija, botón "Congelar" y casilla de silencio.

## Hallazgos de la xA9

- **Armónicos del oscilador:** sin filtro de salida, cada línea se repite alrededor de los armónicos impares de su portadora C: 3C + S (−9 a −10 dBc), 5C − S (−12 a −17 dBc), hasta el orden 17 (−28 dBc). Solo un filtro los saca.
- **Regla de diseño:** caen sobre el propio peine si la separación D divide a 4S y la primera línea es múltiplo de D/2 (cada 40 MHz: S = 10 desde 60 MHz).
- **Fuga de portadora:** −37 a −51 dBc según la ganancia; no baja con la amplitud digital. Imagen de IQ: unos −40 dBc. El AD9361 se recalibra solo cuando el oscilador se mueve más de 100 MHz.
- **Desborde:** la suma de amplitudes digitales nunca llega a 1,0; tope 0,95.
- **Nivel:** ganancia 65 y amplitud 0,25 dan unos −3 dBm; la salida cae 4,5 dB entre 420 MHz y 1 GHz. A +3 dBm comprime 0,4 dB.
- **USB:** sin bloques grandes, a más de 30 MSPS se cortan muestras. Hubo un corte de USB a los 15 min; después de un corte, desenchufar y volver a enchufar.
- **Picos en MAX HOLD:** el tono durante el salto; el silencio los saca. Queda uno recurrente en 750 MHz, sin causa confirmada.
- **Lazo TX→RX:** descartado (EXP-18): los armónicos del TX entran por las respuestas armónicas del RX y la lectura cambia en cada sintonía.

## GNU Radio con bladeRF

- osmocom Sink: solo actúa RF Gain, de a 1 dB. osmocom Source: Gain Mode en False.
- `set_center_freq` resintoniza aunque el valor no cambie: los flujos tienen una guarda en el Python Snippet.
- La amplitud digital sale con el retardo del buffer; frecuencia y ganancia son inmediatas.
- Si el cierre del flujo se cuelga, el TX puede quedar habilitado: verificar que no quede un proceso de Python con la placa.
- El barrido no usa Python: un Function Probe recorre una lista y una cascada de bloques Variable.

## CETEM (13-10-2026)

Ver el [historial](historial.md) y el dashboard [`CETEM/Visita CETEM.html`](../CETEM/Visita%20CETEM.html).
- .DAT del R&S ESR-7: encabezado `Clave;valor;`, luego `Values;N;` y filas `frecuencia_Hz;nivel;` en dBµV/m, con cable y bilog incluidos. MAX PEAK, MAX HOLD, RBW 120 kHz, paso 30 kHz, 50 ms por punto, preamplificador 20 dB.
- El atenuador del receptor está compensado: con 20 dB el piso sale 10 dB más alto que con 10 dB. En el dashboard todo está llevado a 20 dB.

## Límites de CISPR 11 (grupo 1, clase B)

Cuasi-pico en cámara semianecoica ([`normas/CISPR_11_2024.pdf`](../normas/CISPR_11_2024.pdf), Tabla 9): a 3 m, 40 dBµV/m de 30 a 230 MHz y 47 dBµV/m de 230 a 1000 MHz; a 10 m, 30 y 37 dBµV/m.
