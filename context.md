# Contexto del proyecto

Proyecto de Martín Ledesma (FIUBA, Compatibilidad Electromagnética): generador peine con una bladeRF 2.0 micro xA9 para preverificar la cadena de emisiones radiadas del CETEM. Todo va en español, salvo el paper.

Este archivo reúne las reglas para trabajar en el proyecto. Conviene leerlo antes de empezar cualquier tarea.

## Leer primero

1. [docs/plan.md](docs/plan.md), con los objetivos, las tareas y las fechas. Es el único lugar del plan.
2. [docs/conocimiento_tecnico.md](docs/conocimiento_tecnico.md), con los equipos, los límites y los hallazgos ya verificados. No hace falta volver a descubrirlos.
3. [docs/historial.md](docs/historial.md), con la cronología. El detalle de cada experimento está en [SDR/Historial_Proyecto_SDR.txt](SDR/Historial_Proyecto_SDR.txt).
4. La sección Overleaf de este archivo, antes de tocar un TP o hacer cualquier operación de Git.

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
- Cada TP es un proyecto de Overleaf en `TPs/`, con un solo `.tex`, cada párrafo en un renglón y figuras con `[H]` y el paquete `float`. TP1 a TP4 van en español, TP5 y TP7 en inglés. La carpeta de cada TP tiene solo lo que va a Overleaf. El PDF compilado va en `TPs/PDFs/`, con el nombre de la carpeta del TP, y se recompila cada vez que cambia el `.tex` (compilar en otra carpeta para no subir los archivos auxiliares).
- Los `.md` van cortos. Al cerrar un tema, actualizar `docs/historial.md` y tildar la tarea en `docs/plan.md`.

## Estilo de escritura

- Nunca usar punto y coma, en ningún texto.
- Nada de negritas de entrada del tipo "Texto en negrita. Texto...". Usar secciones o subsecciones, o escribirlo seguido.
- Sin cursivas dentro del texto, salvo que sea estrictamente necesario.
- En LaTeX, letra Source Sans Pro (`\usepackage[default]{sourcesanspro}`).

## Repositorio

- GitHub privado `maledesm/sdr-peine-emc`, todo directo en `main`. Lo que se sube se elige en `.gitignore` (lista blanca).
- No se suben `privado/` (material del profesor) ni `CONAE/` (otro proyecto).
- Cada commit lleva como título la descripción de la carpeta que toca, para que GitHub la siga mostrando en la lista de carpetas. Si toca varias carpetas, un commit por carpeta. El detalle va en el cuerpo del mensaje.

## Overleaf (sincronización de los TPs)

Los TPs se editan en Overleaf. Cada carpeta de `TPs/` vinculada es un `git subtree` de su proyecto de Overleaf, y la versión de Overleaf manda. Toda operación de Git sobre el repo (commit, pull, push) tiene que tener en cuenta también los proyectos de Overleaf.

| TP | Carpeta | Remoto | Dirección |
|---|---|---|---|
| TP1 | `TPs/TP1_OE1_Procedimiento_RE` | `overleaf-tp1` | `https://git@git.overleaf.com/6ad8258ac639ee8038bd9fc0` |
| TP2 | `TPs/TP2_OE2_Manual_SDR` | `overleaf-tp2` | `https://git@git.overleaf.com/6ad82e4108e3de47cf251656` |
| TP3 | `TPs/TP3_OR3_Reporte_RE` | `overleaf-tp3` | `https://git@git.overleaf.com/6ad82ea02324e25380499180` |
| TP4 | `TPs/TP4_OE4_Calibracion_RS` | `overleaf-tp4` | `https://git@git.overleaf.com/6ad82eaef67a96b728317bb5` |
| TP5 | `TPs/TP5_OE5_Paper_v1` | `overleaf-tp5` | `https://git@git.overleaf.com/6ad82ecbf4f2b91a61df4dc7` |
| TP6 | `TPs/TP6_OE7_Punta_de_Corriente` | `overleaf-tp6` | `https://git@git.overleaf.com/6ad82efceeda62b7c26baaa3` |
| TP7 | `TPs/TP7_Integrador_EMC_Europe` | `overleaf-tp7` | `https://git@git.overleaf.com/6ad82f156fc9e5d486be2f91` |

Rutina:
1. Antes de tocar un TP, y antes de cualquier commit o `git push`, traer lo de Overleaf de cada proyecto vinculado: `git subtree pull --prefix=<carpeta> <remoto> main --squash`.
2. Después de hacer el commit de un cambio en la carpeta de un TP, subirlo a Overleaf: `git subtree push --prefix=<carpeta> <remoto> main`.
3. Antes de `git push` a GitHub, confirmar que todos los proyectos de Overleaf quedaron al día en los dos sentidos.

Los pasos 1 y 2 para los siete TPs juntos los hacen `traer_de_overleaf.bat` y `subir_a_overleaf.bat`, en la raíz del repo. Si se agrega un proyecto, sumarlo también en los dos .bat.

Detalles:
- Todos los TPs están vinculados. Las plantillas con que se crearon los proyectos están en `TPs/Plantillas/` (TP5 y TP7 en formato IEEE de congreso, con su letra Times).
- El primer pull después de un push crea un commit de unión sin cambios de archivos. Es normal.
- Al titular los commits de pull, usar `-m "Trabajos prácticos del proyecto"`, la descripción de la carpeta `TPs`.
- La rama de Overleaf es `main`. El token de Overleaf lo escribe Martín, nunca quien asiste, y queda guardado en el administrador de credenciales de Windows.
- La carpeta de un TP tiene solo lo que va a Overleaf. El PDF compilado va en `TPs/PDFs/`.
- En un clon nuevo del repo faltan los remotos: `git remote add <remoto> <dirección>` para cada fila de la tabla.
- No usar la sincronización con GitHub de Overleaf: vincula un repositorio entero por proyecto.
- Vincular un proyecto nuevo:
  1. crear el proyecto en Overleaf (por ejemplo, subiendo el .zip de la plantilla),
  2. `git remote add overleaf-tpN <dirección>` y `git fetch overleaf-tpN`, este último lo corre Martín con su token,
  3. sacar la carpeta del TP del repo con un commit (lo que no va a Overleaf se mueve antes a otro lado),
  4. `git subtree add --prefix=<carpeta> overleaf-tpN main --squash`,
  5. agregar la fila a la tabla de arriba.
- Si Windows no deja borrar una carpeta vacía ("busy"), suele ser una terminal o una ventana abierta en ella.
- Antes de hacer `git push`, confirmar con Martín. Antes de borrar algo, verificar qué es y consultarlo.
