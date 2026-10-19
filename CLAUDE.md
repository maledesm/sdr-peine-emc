# Instrucciones para Claude

Proyecto de Martín Ledesma (FIUBA, Compatibilidad Electromagnética): generador peine con una bladeRF 2.0 micro xA9 para preverificar la cadena de emisiones radiadas del CETEM. Todo en español, salvo el paper.

## Leer primero

1. [docs/plan.md](docs/plan.md): objetivos, tareas y fechas. Es el único lugar del plan.
2. [docs/conocimiento_tecnico.md](docs/conocimiento_tecnico.md): equipos, límites y hallazgos ya verificados. No redescubrirlos.
3. [docs/historial.md](docs/historial.md): cronología. Detalle de cada experimento en [SDR/Historial_Proyecto_SDR.txt](SDR/Historial_Proyecto_SDR.txt).

## Seguridad de los equipos (no negociable)

- La xA9 es del profesor y es carísima. Avanzar solo si es ultra seguro: ni la más mínima chance de dañarla.
- **Nunca escribir en la flash** (firmware, FPGA, `flash_init_cal`) sin autorización explícita. Por ahora no se actualiza el firmware.
- Bias tee siempre apagado. En la x40, nunca habilitar la XB-200.
- TX1→RX1 solo por cable y con tope de ganancia de TX (30 dB).
- Un flujo que emite líneas de 0 dBm nunca va por cable al RX1. Con cable a la tinySA y nivel alto, su atenuación va en 30 dB manual.
- Suma de amplitudes digitales por debajo de 1,0 (tope 0,95).
- No tocar instalaciones ni nada fuera de esta carpeta.

## Forma de trabajo

- **Paso a paso.** Pedir el visto bueno antes de crear archivos, instalar algo o transmitir. Si Martín comparte un archivo o describe algo, analizar y parar. Ante dudas importantes, preguntar en vez de decidir.
- **Pedidos de trabajo con la SDR:** riesgos y precauciones (con números), análisis corto e instructivo para GNU Radio Companion bloque por bloque, en ese orden.
- **Charlas de estrategia:** respuestas cortas que cierran con una pregunta.
- **Python lo mínimo.** Primero bloques y expresiones de bloques Variable. Si hace falta, un solo Python Snippet con funciones cortas, sin clases y con nombres en castellano, como lo escribiría alguien que programa hace dos meses.
- **Lienzos de GRC** sin bloques superpuestos.
- **Experimentos:** carpeta `SDR/A9_` o `X40_` + número de orden + nombre del EXP. Capturas renombradas por experimento, con el nombre original anotado en la sección 11 de la bitácora.
- **Bitácora `SDR/Historial_Proyecto_SDR.txt`:** ASCII puro y CRLF; una entrada por diseño, resultado o decisión. No editarla con `sed -i` de Git Bash (saca el CRLF) y, en Python, cuidar las barras invertidas (`\a`, `\r`).
- **TPs:** un proyecto de Overleaf por TP en `TPs/`, con un solo `.tex`, cada párrafo en un renglón, figuras con `[H]` y el paquete `float`. TP1 a TP4 en español; TP5 y TP7 en inglés.
- **Documentos `.md`:** cortos. Al cerrar un tema, actualizar `docs/historial.md` y tildar la tarea en `docs/plan.md`.

## Repositorio

- GitHub privado `maledesm/sdr-peine-emc`, todo directo en `main`. Lo que se sube se elige en `.gitignore` (lista blanca).
- No se suben `privado/` (material del profesor) ni `CONAE/` (otro proyecto).
- Antes de hacer `git push`, confirmar con Martín. Antes de borrar algo, verificar qué es y consultarlo.
