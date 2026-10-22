# Conocimiento técnico

Lo verificado midiendo o leyendo código fuente. El detalle de cada medición está en [`SDR/Historial_Proyecto_SDR.txt`](../SDR/Historial_Proyecto_SDR.txt).

## Equipos

| Equipo | Datos clave |
|---|---|
| bladeRF 2.0 micro xA9 (del profesor) | Serie `321e0fa5875945d99b11070bb0a76d31`. TX de 47 MHz a 6 GHz, RX desde 70 MHz, hasta 56 MHz de ancho de banda y ganancia de TX de −23,75 a 66 dB. Solo USB 3. Firmware 2.4.0 y FPGA 0.14.0, que no se actualizan. Bias tee apagado. |
| bladeRF x40 (prestada) | Serie `96c4c15c9fc517a47ad39c98ae127a31`. De 237,5 MHz a 3,8 GHz, 28 MHz de ancho de banda y hasta +6 dBm. Nunca habilitar la XB-200 (no la tiene). |
| tinySA Ultra+ ZS-406 | De 100 kHz a 5,4 GHz. Máximo +6 dBm con atenuación en 0 dB, y +20 dBm de pico con 30 dB manual. CSV `MHz,dBm` de 450 puntos, CRLF. Barrer de 45 a 1005 MHz con RBW de 300 kHz tarda 2,8 s. |
| PC | Radioconda 2025.03.14 (GNU Radio 3.10.12, gr-osmosdr) en `C:\Users\tinch\radioconda`, y bladeRF-cli en `C:\Program Files\bladeRF\x64\`. |
| Accesorios | Cables SMA y una carga de 50 Ω, sin atenuador ni divisor. La antena de la SDR es la telescópica de 30 cm, totalmente extendida. |

## Peine medido (EXP-25 y EXP-26)

- 24 líneas de 60 a 980 MHz, una cada 40 MHz, emitidas de a una. El receptor las junta con MAX HOLD.
- Un tono por portadora, con la portadora S = 10 MHz arriba de la línea. 40 MSPS con bloques USB de 16384 × 128 (`buffers=128,buflen=16384`).
- 6 s por línea. Con silencio (6 s encendida, 6 s apagada y salto en el silencio) la pasada dura 4 min 48 s, y sin silencio 2 min 24 s.
- La calibración por cable lee el .csv del analizador ("Generar calibración"), toma el máximo a ±4 MHz de cada línea y la lleva a 0 dBm. Se guarda en un archivo, se importa en la cámara y admite retoque manual.
- Por cable, planitud de 1,1 dB (de −0,8 a +0,3 dBm) y desvío de 0,28 dB.
- El EXP-26 suma selector de ganancia, línea fija, botón "Congelar" y casilla de silencio.
- El peine actual (EXP-28) va con una línea cada 10 MHz, de 50 MHz a 1 GHz, 7 s por línea y 0,5 s de corte, objetivo conducido plano y una calibración irradiada con una sola traza contra CISPR 11 grupo 1 clase A (ver el [plan](plan.md)).

## Hallazgos de la xA9

- La salida no tiene filtro, así que cada línea se repite alrededor de los armónicos impares de su portadora C: 3C + S (−9 a −10 dBc), 5C − S (−12 a −17 dBc) y así hasta el orden 17 (−28 dBc). Solo un filtro los saca.
- Esas repeticiones caen sobre el propio peine si la separación D divide a 4S y la primera línea es múltiplo de D/2. Con D = 40 MHz pide S = 10 desde 60 MHz, y con D = 10 MHz cualquier línea múltiplo de 10 MHz sirve.
- La fuga de portadora queda de −37 a −51 dBc según la ganancia y no baja con la amplitud digital. La imagen de IQ queda en unos −40 dBc. El AD9361 se recalibra solo cuando el oscilador se mueve más de 100 MHz.
- La suma de amplitudes digitales nunca llega a 1,0 (tope 0,95).
- Con ganancia 65 y amplitud 0,25 las líneas salen en unos −3 dBm, y la salida cae 4,5 dB entre 420 MHz y 1 GHz. A +3 dBm comprime 0,4 dB.
- Sin bloques USB grandes, a más de 30 MSPS se cortan muestras. Hubo un corte de USB a los 15 min, y después de un corte hay que desenchufar y volver a enchufar.
- En MAX HOLD aparecían picos por el tono emitido durante el salto, y el silencio los saca. Queda uno recurrente en 750 MHz, sin causa confirmada.
- El lazo TX→RX quedó descartado (EXP-18), porque los armónicos del TX entran por las respuestas armónicas del RX y la lectura cambia en cada sintonía.

## GNU Radio con bladeRF

- En el osmocom Sink solo actúa RF Gain, de a 1 dB. En el osmocom Source, Gain Mode va en False.
- `set_center_freq` resintoniza aunque el valor no cambie, por eso los flujos tienen una guarda en el Python Snippet.
- La amplitud digital sale con el retardo del buffer, mientras que frecuencia y ganancia son inmediatas.
- Si el cierre del flujo se cuelga, el TX puede quedar habilitado. Verificar que no quede un proceso de Python con la placa tomada.
- El barrido no usa Python: un Function Probe recorre una lista y una cascada de bloques Variable.
- Los QT GUI Label y Chooser van dentro de una barra de herramientas que esconde detrás de un >> el texto que no entra. El EXP-28 los pasa a un renglón común desde el snippet.
- Para medir la ventana sin mostrarla, la plataforma offscreen de Qt no sirve (la letra sale rota y agranda todo). Con la de Windows y `WA_DontShowOnScreen` la ventana se arma de verdad.

## CETEM (13-10-2026)

Ver el [historial](historial.md) y el dashboard [`CETEM/Visita CETEM.html`](../CETEM/Visita%20CETEM.html).
- El ESR-7 barre de 30 MHz a 1 GHz en unos 3 s, en el dominio del tiempo: los 50 ms de "Meas Time" del encabezado son por bloque, no por punto.
- Los .DAT del R&S ESR-7 traen un encabezado de pares clave y valor, la cantidad de puntos y una fila por punto con la frecuencia en Hz y el nivel en dBµV/m (cable y bilog incluidos), separados por punto y coma. Se midió con MAX PEAK, MAX HOLD, RBW de 120 kHz, paso de 30 kHz, 50 ms por punto y preamplificador de 20 dB.
- El atenuador del receptor está compensado en los niveles mostrados, pero sube el piso. Con 20 dB el piso quedó entre 37 y 39 dBµV/m, unos 10 dB más alto que con 10 dB. En el dashboard todo está llevado a 20 dB.
- Con 0 dBm por cable, el máximo de las tres alturas en vertical quedó entre 36 y 49 dB por encima del límite de CISPR 11.

## Límites de CISPR 11 (grupo 1, clase B)

En cámara semianecoica y con cuasi-pico ([`normas/CISPR_11_2024.pdf`](../normas/CISPR_11_2024.pdf), Tabla 9), a 3 m son 40 dBµV/m de 30 a 230 MHz y 47 dBµV/m de 230 a 1000 MHz, y a 10 m, 30 y 37 dBµV/m.
