# Conocimiento técnico acumulado

Lo que se sabe de los equipos y del peine, verificado midiendo o leyendo el código fuente. El detalle de cada medición está en [`SDR/Historial_Proyecto_SDR.txt`](../SDR/Historial_Proyecto_SDR.txt).

## Equipos

| Equipo | Datos clave |
|---|---|
| **bladeRF 2.0 micro xA9** (del profesor, muy cara) | Serie `321e0fa5875945d99b11070bb0a76d31`. TX de 47 MHz a 6 GHz, RX desde 70 MHz, ancho de banda hasta 56 MHz, ganancia de TX de −23,75 a 66 dB. Solo USB 3. Firmware 2.4.0 y FPGA 0.14.0: **no actualizar** (indicación del profesor). Bias tee apagado en los cuatro puertos. |
| bladeRF x40 (prestada) | Serie `96c4c15c9fc517a47ad39c98ae127a31`. 237,5 MHz a 3,8 GHz, 28 MHz de ancho de banda, hasta +6 dBm. Sin placa XB-200: **nunca habilitarla por software**. Firmware 2.6.0, FPGA 0.16.0. |
| tinySA Ultra+ ZS-406 | 100 kHz a 5,4 GHz. Entrada máxima +6 dBm con atenuación en 0 dB; con atenuación manual de 30 dB tolera +20 dBm de pico. Las capturas .csv son `MHz,dBm`, 450 puntos, CRLF, sin encabezado. Barrer 45 a 1005 MHz con RBW 300 kHz tarda 2,8 s. |
| PC | Radioconda 2025.03.14 (GNU Radio 3.10.12, gr-osmosdr) en `C:\Users\tinch\radioconda`; bladeRF-cli en `C:\Program Files\bladeRF\x64\`. |
| Accesorios | Cables SMA y una carga de 50 Ω. Sin atenuador ni divisor. Antenas: telescópica de 30 cm (la que se usa en la SDR, totalmente extendida) y una de 10 cm. |

## Peine actual (EXP-25 / EXP-26)

- 24 líneas de 60 a 980 MHz, una cada 40 MHz, una por vez; el receptor las acumula con MAX HOLD.
- Un tono por portadora, con la portadora S = 10 MHz por encima de la línea. Tasa de 40 MSPS con bloques USB de 16384 × 128 (`buffers=128,buflen=16384` en los argumentos del dispositivo).
- 6 s por línea. Con silencio activado: 6 s encendida y 6 s apagada, salto durante el silencio; la pasada dura 4 min 48 s (sin silencio, 2 min 24 s).
- Calibración por cable contra un analizador: el botón "Generar calibración" lee la captura .csv, toma el máximo a menos de 4 MHz de cada línea y la lleva a 0 dBm. Se guarda en un archivo y se importa en la cámara. Admite retoque manual por línea.
- Resultado por cable: planitud de 1,1 dB (de −0,8 a +0,3 dBm), desvío de 0,28 dB.
- El EXP-26 agrega: selector de ganancia, modo de línea fija, botón "Congelar" (deja fija la portadora actual transmitiendo) y casilla de silencio.

## Hallazgos de la xA9

- **Armónicos del oscilador:** la salida no tiene filtro. Cada línea se repite alrededor de los armónicos impares de su portadora C: 3C + S (−9 a −10 dBc), 5C − S (−12 a −17 dBc), y así hasta el orden 17 (−28 dBc). El triple de la portadora queda a −33 a −46 dBc. Ninguna calibración las saca; solo un filtro.
- **Regla de diseño:** los armónicos caen sobre el propio peine si la separación entre líneas D divide a 4S y la primera línea es múltiplo de D/2. Cada 40 MHz pide S = 10 arrancando en 60 (no en 50); cada 50 MHz pediría S = 12,5; cada 100 MHz, S = 25 (inalcanzable por USB).
- **Fuga de portadora:** −37 a −51 dBc según la ganancia. Imagen de IQ: unos −40 dBc. Imagen del muestreo en L + tasa. El AD9361 se calibra solo: al arrancar y cada vez que el oscilador se mueve más de 100 MHz de la última calibración (pasa a ALERT un instante). `calibrate` de bladeRF-cli es solo para la primera generación.
- **Desborde digital:** la suma de amplitudes nunca debe llegar a 1,0 (da la vuelta en 12 bits). Tope práctico 0,95 con un tono.
- **Nivel:** con ganancia 65 y amplitud 0,25 las líneas salen en unos −3 dBm; la salida cae de −3 a −7,5 dBm entre 420 MHz y 1 GHz. Con +3 dB sobre 0 dBm empieza a comprimir (0,4 dB).
- **USB:** sin bloques grandes, a más de 30 MSPS hay cortes de muestras (el LED titila). Una vez se cortó la comunicación USB a los 15 min de uso (`Hit stall for buffer`); tras un corte, desenchufar y volver a enchufar la placa.
- **Picos momentáneos en MAX HOLD:** el tono emitido mientras el oscilador salta; el silencio en cada salto los saca. Queda un pico recurrente en 750 MHz (frecuencia de portadora), sin causa confirmada.

## Particularidades de GNU Radio con bladeRF

- En osmocom Sink solo actúa RF Gain, como ganancia total y de a 1 dB. En osmocom Source, Gain Mode en False.
- `set_center_freq` resintoniza siempre, aunque el valor no cambie: en los flujos del barrido hay una guarda en el Python Snippet que solo manda la frecuencia si cambió.
- Un cambio de amplitud digital sale con el retardo del buffer del sumidero (bloques × largo / tasa); frecuencia y ganancia son inmediatas.
- Si el cierre del flujo se cuelga, el transmisor puede quedar habilitado: verificar que no quede otro proceso de Python con la placa tomada.
- El barrido se hace sin Python: un Function Probe que saca valores de una lista y una cascada de bloques Variable.

## Medición en el CETEM (13-10-2026)

Ver [historial.md](historial.md#4-primera-medición-en-el-cetem-13-10) y el dashboard [`CETEM/Dashboard_CETEM_13-10.html`](../CETEM/Dashboard_CETEM_13-10.html).
- Archivos .DAT del R&S ESR-7: encabezado `Clave;valor;`, después `Values;N;` y filas `frecuencia_Hz;nivel;` en dBµV/m. Transductor "08- (ER) 2 CBL;10- BL 01" (cable y bilog ya incluidos). Detector MAX PEAK, traza MAX HOLD, RBW 120 kHz, paso 30 kHz, 50 ms por punto, preamplificador 20 dB.
- El atenuador interno del receptor está compensado en los niveles mostrados: con 20 dB el piso sale unos 10 dB más alto que con 10 dB. Para comparar mediciones tomadas con distinta atenuación, en el dashboard todo se llevó a 20 dB.
