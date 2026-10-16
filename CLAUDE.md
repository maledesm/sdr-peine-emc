# Instrucciones para Claude

Proyecto de Martín Ledesma (FIUBA, Compatibilidad Electromagnética): generador peine con una bladeRF 2.0 micro xA9 para verificar la cadena de emisiones radiadas del CETEM. Todo en español.

## Leer primero

1. [README.md](README.md): qué es el proyecto y mapa del repositorio.
2. [docs/roadmap.md](docs/roadmap.md) y [docs/acuerdos_2026-10-16.md](docs/acuerdos_2026-10-16.md): qué toca hacer ahora.
3. [docs/conocimiento_tecnico.md](docs/conocimiento_tecnico.md): equipos, límites y hallazgos ya verificados. No redescubrirlos.
4. [docs/historial.md](docs/historial.md): cronología. El detalle de cada experimento está en [SDR/Historial_Proyecto_SDR.txt](SDR/Historial_Proyecto_SDR.txt).

## Seguridad de los equipos (no negociable)

- La xA9 es del profesor y es carísima. Avanzar solo si es ultra seguro: ni la más mínima chance de dañarla.
- **Nunca escribir en la flash** (firmware, FPGA, `flash_init_cal`) sin autorización explícita. El profesor dijo que por ahora no se actualiza el firmware.
- Bias tee siempre apagado. En la x40, nunca habilitar la XB-200.
- TX1→RX1 solo por cable y con tope de ganancia de TX (30 dB).
- Un flujo que emite líneas de 0 dBm nunca va por cable al RX1. Con cable a la tinySA y nivel alto, su atenuación va en 30 dB manual.
- Suma de amplitudes digitales por debajo de 1,0 (tope 0,95).
- No tocar instalaciones ni nada fuera de esta carpeta.

## Forma de trabajo

- **Paso a paso.** Pedir el visto bueno antes de crear archivos, instalar algo o transmitir. Si Martín comparte un archivo o describe algo, analizar y parar; no implementar sin que lo pida.
- **Pedidos de trabajo con la SDR:** responder en tres partes y en este orden: riesgos y precauciones (con números concretos), análisis corto, instructivo para GNU Radio Companion bloque por bloque.
- **Charlas de estrategia:** respuestas cortas, de ida y vuelta, que cierran con una pregunta.
- **Python lo mínimo.** Primero resolver con bloques y expresiones de bloques Variable. Si hace falta, un solo Python Snippet con funciones cortas, sin clases, nombres en castellano, como lo escribiría alguien que programa hace dos meses.
- **Lienzos de GRC prolijos:** sin bloques superpuestos.
- **Carpetas de experimentos:** `A9_` o `X40_` + número de orden + nombre del EXP (por ejemplo `A9_20_EXP26_Peine_radiado`).
- **Capturas:** renombrarlas por experimento y anotar el nombre original en la sección 11 del historial.
- **`SDR/Historial_Proyecto_SDR.txt`:** ASCII puro (sin acentos) y fin de línea CRLF. Agregar una entrada por cada diseño, resultado o decisión. No editarlo con `sed -i` de Git Bash: le saca el CRLF.
- **LaTeX** (se edita en Overleaf): un solo `.tex`, cada párrafo en un solo renglón, figuras con `[H]` y el paquete `float`.
- Al cerrar un tema, actualizar `docs/historial.md` y, si cambia el plan, el estado en `docs/roadmap.md` y `docs/acuerdos_2026-10-16.md`.

## Repositorio

- GitHub privado `maledesm/sdr-peine-emc`. Lo que se sube se elige en `.gitignore` (lista blanca).
- No se sube: la carpeta `CONAE/`, nada de la tesis de radar ni de las tesis que pasó el profesor, normas pagas (CISPR 11) ni el `.rar` de CombGenerators.
- Antes de hacer `git push`, confirmar con Martín.
- Antes de borrar un archivo, verificar qué es (el dashboard del CETEM se llama `CETEM/Visita CETEM.html`).
