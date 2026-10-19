# Plan de trabajo

Único lugar con los objetivos, las tareas y las fechas del proyecto (reemplaza al Trello de la consigna original).

**Proyecto.** Generador peine con una SDR (bladeRF 2.0 micro xA9) para preverificar la cadena de medición de emisiones radiadas (RE) de un laboratorio de EMC y seguir su continuidad en el tiempo.

**Metodología: Aprendizaje Basado en Proyectos (ABP).** El alumno aprende investigando y resolviendo un problema real mediante un proyecto; el docente marca el camino, supervisa y corrige. Va descripta en el paper.

## Fechas

| Qué | Cuándo |
|---|---|
| Fase 1: los cinco TPs, entregados juntos (valen como primer parcial) | semana del 26-10-2026 |
| Visita al CETEM | principios de diciembre de 2026, a coordinar |
| TP7: paper a EMC Europe 2027 | 22-02-2027 |

Plan de TPs pendiente de la confirmación de Walter Gustavo Fano. Supervisa Pablo Marino Belcaguy.

## Fase 1

Cada TP es un proyecto de Overleaf (un solo `.tex`) en su carpeta de [`TPs/`](../TPs/), y se sube al Campus Virtual con su código. TP1 a TP4 en español; TP5 en inglés.

- [ ] Invitar a los docentes al repositorio y pasarles el enlace de Overleaf de cada TP.

### TP1 · OE1 · Procedimiento de ensayo de RE
Procedimiento normativo formal, paso a paso, para el ensayo de RE en laboratorio. La SDR es el EUT, en su papel de calibrador. Base: RE-TP-001 y la guía del profesor, ya en la carpeta.
- [ ] Entorno de medición, instrumental y criterios de aceptación.
- [ ] Tiempo por línea (6 s) y duración de la pasada: 2,4 min sin silencio, 4,8 min con silencio.
- [ ] Alturas de antena adaptables a cada cámara (por ejemplo 1, 1,5 y 2 m en una de 2 m).
- [ ] Incertidumbres y errores sistemáticos a registrar.

### TP2 · OE2 · Manual y procedimiento funcional de la SDR
- [ ] Parte general: programas, configuración, modos de TX y RX, cuidados del equipo.
- [ ] El peine en detalle (EXP-25 y EXP-26, después el EXP-27): parámetros, calibración e importación.
- [ ] Recepción, para RS. La autocalibración por lazo TX→RX quedó descartada (EXP-18).

### TP3 · OR3 · Reporte de mediciones de RE
Con los datos del CETEM del 13-10 y las mediciones que se hagan en casa o en la facultad.
- [ ] Análisis de los espectros, con la repetibilidad como eje. Explicar las portadoras casi al nivel de su línea con la antena a 1 y 2 m y los picos sueltos (265, 885 y 944 MHz en el CETEM; el recurrente de 750 MHz en casa).
- [ ] Comparación con CISPR 11, grupo 1, clase B, a 3 m: 40 dBµV/m hasta 230 MHz y 47 dBµV/m de 230 a 1000 MHz (cuasi-pico; nosotros medimos con pico).
- [ ] Fotos de las campañas.

### TP4 · OE4 · Procedimiento de calibración de RS
Procedimiento escrito, por ahora sin mediciones, con la SDR como instrumento o generador de referencia.
- [ ] Metodología, instrumental y secuencia: campo contra distancia (433 MHz), campo contra potencia y ensayo simplificado sobre un DUT, como en la consigna original.
- [ ] Sensores de campo cercano de la facultad: modelos, niveles de salida y frecuencias.
- [ ] Blindaje de la SDR para irradiarla con campo fuerte (idea: cubo de ferritas del CETEM; a definir).

### TP5 · OE5 · Paper, versión 1
Título tentativo: "Preverificaciones de RE con comb generator a base de SDR". En inglés, formato IEEE, 8 carillas. Modelo: Romero Espinoza et al., en [`bibliografia/2_Generadores_Peine/`](../bibliografia/2_Generadores_Peine/).
- [ ] Integrar todo lo hecho: propuesta, teoría, metodología, cuidados e innovación (los tres ejercicios de la fase 2 como trabajo en curso), con la metodología ABP.
- [ ] Al menos 20 referencias de valor ([bibliografia.md](bibliografia.md)): normas (CISPR 11, CISPR 16, IEC 61000-4-3, MIL-STD-461, ECSS-E-ST-20), artículos, datasheets (bladeRF 2.0 micro, AD9361) y manuales (tinySA, receptor R&S).
- [ ] Confirmar en IEEE Xplore que no hay trabajos iguales y consultar al INTI el alcance de su calibración en EMC.

### EXP-27 · Nivel y ecualización del peine
- [ ] Bajar el peine unos 15 dB con la ganancia de RF (no con la amplitud digital) para tener margen de ecualización hacia arriba y hacia abajo, en un punto repetible.
- [ ] Medir por cable las espurias a varios niveles: la fuga de portadora y sus armónicos son lo que más mete. Ver si la corrección manual de continua del AD9361 baja la fuga.
- [ ] Evaluar una calibración que deje las líneas sobre el límite de CISPR 11, con su salto de 7 dB en 230 MHz. Con los niveles del 13-10 (69 a 96 dBµV/m) hay que bajar bastante más de 15 dB.

## Fase 2

### TP6 · OE7 · Medición con punta de corriente
Con Alejandro Catonar. Armar antes un JIG que le dé repetibilidad. En pausa.

### TP7 · Integrador: paper para EMC Europe 2027
Evolución del TP5 para revisión de pares: resultados, pros y contras, simulación contra medición y conclusiones.

**Antes de la visita al CETEM**
- [ ] Estabilidad del peine: calentamiento, deriva, efecto de la alimentación o la batería.
- [ ] Antena y plano de tierra, para que el ensayo sea repetible (el monopolo del Comb generator no tiene plano de tierra).
- [ ] CST: la antena, el peine con la antena, y los niveles de campo para RS.
- [ ] Conseguir un atenuador y un divisor.

**En la visita**
- [ ] Primero un peine hasta 1 GHz con las mejoras; si anda bien, más ancho de banda; si no, volver a 1 GHz.
- [ ] Un RBW menor que 120 kHz, más acorde a CISPR 11, aunque la medición tarde más.
- [ ] Piso de ruido en horizontal y polarización horizontal con el monopolo de costado (el fabricante desaconseja acostar el peine).
- [ ] Mediciones estandarizadas de la variación con la altura y la frecuencia.
- [ ] Confirmar si el silencio estaba activado el 13-10 y cómo toma las trazas el receptor.

**Ejercicios para el paper**
- [ ] Calibración in situ minimizando el error cuadrático medio, guardada para seguir su variación; repetibilidad en la misma instalación, con el canal de control.
- [ ] "Teletransportación": medir un comb físico y reproducir su firma con la SDR, para que sirva de patrón.
- [ ] Emitir con potencia constante para ver qué atenúa más en el camino.

**Factor de antena e incertidumbre**
- [ ] El procedimiento de RE verifica la cadena inyectando en el cable, sin la antena: el factor de antena tiene que estar bien medido y ser repetible. Explorar un método alternativo al de las tres antenas.
- [ ] Incertidumbres y errores sistemáticos del ensayo y de los factores de antena, y cómo entran en el perfil del analizador.

## Hecho
- Repositorio en GitHub y búsqueda bibliográfica: 47 papers en [`bibliografia/`](../bibliografia/) (16-10-2026).
- Repositorio reorganizado por TPs (19-10-2026).
