# Plan de trabajo

Único lugar con los objetivos, las tareas y las fechas del proyecto (reemplaza al Trello de la consigna original).

El proyecto es un generador peine con una SDR (bladeRF 2.0 micro xA9) para preverificar la cadena de medición de emisiones radiadas (RE) de un laboratorio de EMC y seguir su continuidad en el tiempo.

La metodología es el Aprendizaje Basado en Proyectos (ABP): el alumno aprende investigando y resolviendo un problema real mediante un proyecto, y el docente marca el camino, supervisa y corrige. Va descripta en el paper.

## Fechas

| Qué | Cuándo |
|---|---|
| Fase 1: los cinco TPs, entregados juntos (valen como primer parcial) | semana del 26-10-2026 |
| Visita al CETEM | principios de diciembre de 2026, a coordinar |
| TP7: paper a EMC Europe 2027 | 22-02-2027 |

Plan de TPs pendiente de la confirmación de Walter Gustavo Fano. Supervisa Pablo Marino Belcaguy.

## Fase 1

Cada TP es un proyecto de Overleaf (un solo `.tex`) en su carpeta de [`TPs/`](../TPs/), y se sube al Campus Virtual con su código. TP1 a TP4 van en español y TP5 en inglés.

- [ ] Invitar a los docentes al repositorio y pasarles el enlace de Overleaf de cada TP.

### TP1 · OE1 · Procedimiento de ensayo de RE
Procedimiento normativo formal, paso a paso, para el ensayo de RE en laboratorio, con la SDR como EUT en su papel de calibrador.
- [x] Versión 2.0 del RE-TP-001 (19-10). Dos calibraciones, una conducida a bajo nivel y otra irradiada que deja cada línea sobre el límite de CISPR 11 grupo 1 clase B, peine con una línea cada 10 MHz, tres alturas de antena, solo antena Bilog Hybrid, planilla y tablas con la medición del 13-10 e incertidumbre simplificada.
- [x] Geometría de calibración en vertical, con el mayor nivel de las tres alturas. La horizontal se mide con la antena transmisora acostada, para comprobar que esa polarización funciona, sin compararla con el límite.
- [x] Sin pendientes en rojo (19-10). Distancia del 13-10 confirmada en 3 m, 7 s por línea con un barrido de unos 3 s, e incertidumbre con fórmulas y una tabla para completar.
- [x] El receptor barre de 30 MHz a 1 GHz en unos 3 s (lo verificó Martín en el CETEM, barrido en el dominio del tiempo).
- [x] Versión 2.2 (22-10): software del EXP-28, objetivo inicial plano, una sola traza en la irradiada y patrón.
- [x] Versión 2.3 (26-10): incertidumbre simplificada en dB, relativa al día de referencia (U = 3,3 dB con k = 2), verificación irradiada en ±2 dB y criterio de ±3,5 dB. Ya no hacen falta los certificados del CETEM.
- [ ] Reemplazar la reposición del montaje estimada (1,5 dB) con el resultado de la prueba de repetibilidad.
- [x] Repeticiones recortadas (22-10): de 16 a 12 páginas, con una planilla de niveles en una página. La separación de la portadora pasó al TP2.
- [ ] Revisión de los docentes.

### TP2 · OE2 · Manual y procedimiento funcional de la SDR
- [ ] Parte general: programas, configuración, modos de TX y RX, cuidados del equipo.
- [ ] El peine en detalle, con el flujo nuevo de líneas cada 10 MHz: parámetros y las dos calibraciones. Base en `desde_TP1_software_y_calibracion.tex`.
- [ ] Recepción, para RS. La autocalibración por lazo TX→RX quedó descartada (EXP-18).

### TP3 · OR3 · Reporte de mediciones de RE
Con los datos del CETEM del 13-10 y las mediciones que se hagan en casa o en la facultad.
- [ ] Análisis de los espectros, con la repetibilidad como eje. Explicar las portadoras casi al nivel de su línea con la antena a 1 y 2 m y los picos sueltos (265, 885 y 944 MHz en el CETEM, y el recurrente de 750 MHz en casa).
- [ ] Comparación con CISPR 11 grupo 1 clase B a 3 m, 40 dBµV/m hasta 230 MHz y 47 dBµV/m de 230 a 1000 MHz (cuasi-pico, nosotros medimos con pico).
- [ ] Fotos de las campañas.

### TP4 · OE4 · Procedimiento de calibración de RS
Procedimiento escrito, por ahora sin mediciones, con la SDR como instrumento o generador de referencia.
- [ ] Metodología, instrumental y secuencia: campo contra distancia (433 MHz), campo contra potencia y ensayo simplificado sobre un DUT, como en la consigna original.
- [ ] Sensores de campo cercano de la facultad: modelos, niveles de salida y frecuencias.
- [ ] Blindaje de la SDR para irradiarla con campo fuerte (idea: cubo de ferritas del CETEM, a definir).

### TP5 · OE5 · Paper, versión 1
Título tentativo: "Preverificaciones de RE con comb generator a base de SDR". En inglés, formato IEEE, 8 carillas. Modelo: Romero Espinoza et al., en [`bibliografia/2_Generadores_Peine/`](../bibliografia/2_Generadores_Peine/).
- [ ] Integrar todo lo hecho: propuesta, teoría, metodología, cuidados e innovación (los tres ejercicios de la fase 2 como trabajo en curso), con la metodología ABP.
- [ ] Al menos 20 referencias de valor ([bibliografia.md](bibliografia.md)): normas (CISPR 11, CISPR 16, IEC 61000-4-3, MIL-STD-461, ECSS-E-ST-20), artículos, datasheets (bladeRF 2.0 micro, AD9361) y manuales (tinySA, receptor R&S).
- [ ] Confirmar en IEEE Xplore que no hay trabajos iguales y consultar al INTI el alcance de su calibración en EMC.

### EXP-27 y EXP-28 · Peine cada 10 MHz calibrado hacia CISPR 11 clase A
- [x] Flujo con 96 líneas de 50 MHz a 1 GHz, una cada 10 MHz (EXP-27, 20-10). Rehecho en el EXP-28 (22-10) con Reiniciar, conducida, irradiada con una sola traza, guardar y cargar patrón, más una versión de casa (irradiada con la tinySA) y una demo sin placa.
- [x] Nivel conducido: objetivo plano de −33 dBm, que la irradiada corrige línea por línea. Se baja con la ganancia de TX (la mínima que muestra la ventana) y la amplitud digital corrige cada línea.
- [x] Tope de corrección irradiada en 15 dB (22-10). Con 10 dB, 1 o 2 de cada 24 líneas del 13-10 no se corregían.
- [ ] Calibración conducida real con la tinySA, irradiada y verificación en casa, y patrón para la prueba de repetibilidad.
- [ ] Calibración irradiada en el CETEM con el límite de CISPR 11 como objetivo.
- [ ] Verificar con el modo de línea fija que ninguna repetición de otra línea tape a una línea débil.

## Fase 2

### TP6 · OE7 · Medición con punta de corriente
Con Alejandro Catonar. Armar antes un JIG que le dé repetibilidad. En pausa.

### TP7 · Integrador: paper para EMC Europe 2027
Evolución del TP5 para revisión de pares: resultados, pros y contras, simulación contra medición y conclusiones.

#### Antes de la visita al CETEM
- [ ] Estabilidad del peine: calentamiento, deriva y efecto de la alimentación o la batería.
- [ ] Antena y plano de tierra, para que el ensayo sea repetible (el monopolo del Comb generator no tiene plano de tierra).
- [ ] CST: la antena, el peine con la antena y los niveles de campo para RS.
- [ ] Conexión entre la SDR y la PC. En el CETEM hay una sola conexión Ethernet hecha (podría usarse un conversor de USB a Ethernet, a analizar), y pasar el USB por debajo de la puerta deja unos 10 m entre el EUT y la PC.
- [ ] Conseguir un atenuador y un divisor.

#### En la visita
- [ ] Primero un peine hasta 1 GHz con las mejoras. Si anda bien, más ancho de banda, y si no, volver a 1 GHz.
- [ ] Un RBW menor que 120 kHz, más acorde a CISPR 11, aunque la medición tarde más.
- [ ] Piso de ruido en horizontal y polarización horizontal con el monopolo de costado (el fabricante desaconseja acostar el peine).
- [ ] Mediciones estandarizadas de la variación con la altura y la frecuencia.
- [ ] Confirmar si el silencio estaba activado el 13-10 y cómo toma las trazas el receptor.

#### Ejercicios para el paper
- [ ] Calibración in situ minimizando el error cuadrático medio, guardada para seguir su variación, y repetibilidad en la misma instalación con el canal de control.
- [ ] "Teletransportación": medir un comb físico y reproducir su firma con la SDR, para que sirva de patrón.
- [ ] Emitir con potencia constante para ver qué atenúa más en el camino.

#### Factor de antena e incertidumbre
- [ ] El procedimiento de RE verifica la cadena inyectando en el cable, sin la antena, así que el factor de antena tiene que estar bien medido y ser repetible. Explorar un método alternativo al de las tres antenas.
- [ ] Incertidumbres y errores sistemáticos del ensayo y de los factores de antena, y cómo entran en el perfil del analizador.

## Hecho
- Repositorio en GitHub y búsqueda bibliográfica, con 47 papers en [`bibliografia/`](../bibliografia/) (16-10-2026).
- Repositorio reorganizado por TPs (19-10-2026).
