# Contexto del proyecto

Proyecto de Martín Ledesma (FIUBA, Compatibilidad Electromagnética): generador peine con una bladeRF 2.0 micro xA9 para preverificar la cadena de emisiones radiadas del CETEM. Todo va en español, salvo el paper.

Este archivo reúne las reglas para trabajar en el proyecto. Conviene leerlo antes de empezar cualquier tarea.

## Leer primero

1. [docs/plan.md](docs/plan.md), con los objetivos, las tareas y las fechas. Es el único lugar del plan.
2. [docs/conocimiento_tecnico.md](docs/conocimiento_tecnico.md), con los equipos, los límites y los hallazgos ya verificados. No hace falta volver a descubrirlos.
3. [docs/historial.md](docs/historial.md), con la cronología. El detalle de cada experimento está en [SDR/Historial_Proyecto_SDR.txt](SDR/Historial_Proyecto_SDR.txt).

## Seguridad de los equipos (no negociable)

- La xA9 es del profesor y es carísima. Avanzar solo si es ultra seguro, sin la más mínima chance de dañarla.
- Nunca escribir en la flash (firmware, FPGA, `flash_init_cal`) sin autorización explícita de Martín. Por ahora no se actualiza el firmware.
- Bias tee siempre apagado. En la x40, nunca habilitar la XB-200.
- TX1→RX1 solo por cable y con tope de ganancia de TX (30 dB).
- Un flujo que emite líneas de 0 dBm nunca va por cable al RX1. Con cable a la tinySA y nivel alto, su atenuación va en 30 dB manual.
- Suma de amplitudes digitales por debajo de 1,0 (tope 0,95).
- No tocar instalaciones ni nada fuera de esta carpeta.

## Forma de trabajo

- Trabajar paso a paso. Pedirle el visto bueno a Martín antes de crear archivos, instalar algo o transmitir. Si comparte un archivo o describe algo, analizar y parar. Ante dudas importantes, preguntar en vez de decidir.
- En los pedidos de trabajo con la SDR, responder con riesgos y precauciones (con números), un análisis corto y un instructivo para GNU Radio Companion bloque por bloque, en ese orden.
- En las charlas de estrategia, respuestas cortas que cierran con una pregunta.
- Python lo mínimo. Primero bloques y expresiones de bloques Variable. Si hace falta, un solo Python Snippet con funciones cortas, sin clases y con nombres en castellano, como lo escribiría alguien que programa hace dos meses.
- Lienzos de GRC sin bloques superpuestos.
- Cada experimento va en una carpeta `SDR/A9_` o `X40_` + número de orden + nombre del EXP. Las capturas se renombran por experimento y el nombre original se anota en la sección 11 de la bitácora.
- La bitácora `SDR/Historial_Proyecto_SDR.txt` va en ASCII puro y CRLF, con una entrada por diseño, resultado o decisión. No editarla con `sed -i` de Git Bash (saca el CRLF) y, en Python, cuidar las barras invertidas (`\a`, `\r`).
- Cada TP es un proyecto de Overleaf en `TPs/`, con un solo `.tex`, cada párrafo en un renglón y figuras con `[H]` y el paquete `float`. TP1 a TP4 van en español, TP5 y TP7 en inglés. Junto al `.tex` va el PDF compilado, con el nombre de la carpeta del TP, y se recompila cada vez que cambia el `.tex` (compilar en otra carpeta para no subir los archivos auxiliares).
- Los `.md` van cortos. Al cerrar un tema, actualizar `docs/historial.md` y tildar la tarea en `docs/plan.md`.

## Estilo de escritura

- Nunca usar punto y coma, en ningún texto.
- Nada de negritas de entrada del tipo "Texto en negrita. Texto...". Usar secciones o subsecciones, o escribirlo seguido.
- Sin cursivas dentro del texto, salvo que sea estrictamente necesario.
- En LaTeX, letra Source Sans Pro (`\usepackage[default]{sourcesanspro}`).

## Repositorio

- GitHub privado `maledesm/sdr-peine-emc`, todo directo en `main`. Lo que se sube se elige en `.gitignore` (lista blanca).
- No se suben `privado/` (material del profesor) ni `CONAE/` (otro proyecto).
- Antes de hacer `git push`, confirmar con Martín. Antes de borrar algo, verificar qué es y consultarlo.
