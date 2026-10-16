# Bibliografía

Lista de trabajos encontrados hasta ahora. La búsqueda completa del estado del arte es el punto 1 del [roadmap](roadmap.md) (P2 de los acuerdos). Los PDF van en [`bibliografia/`](../bibliografia/).

Búsqueda del 17-09-2026, en web abierta y sin acceso completo a IEEE Xplore: no apareció ningún trabajo que use una SDR como sustituto de un generador peine para verificar sistemas EMC. Hay que repetirla en IEEE Xplore antes de afirmar que es novedoso.

## Generadores peine y verificación de sistemas

- Müllner, Kriz, Haider, Kolb (ARC Seibersdorf), "Conducted and Radiated Comb Generator Measurement Techniques", 7th Int. Symp. on EMC and Electromagnetic Ecology, San Petersburgo, 2007. IEEE Xplore 4371688. [PDF del autor](https://www.seibersdorf-laboratories.at/fileadmin/user_upload/docs/le/rf/publ/2007_conducted_and_radiated_comb.pdf).
  - Base metodológica: procedimiento de *system check* (medición de referencia, diferencia contra la actual y umbral de aceptación).
  - Un peine a batería es más repetible que un generador con cable, porque el cable altera los modos de la cámara. Una antena acopladora es más repetible que un monopolo.
  - El RBW tiene que estar entre el ancho de línea y la separación del peine. La potencia total del peine puede saturar al analizador.
- "Interlaboratory Comparison of Radiated Emissions in Automotive EMC", IEEE Xplore 8485018. Peine como artefacto viajero; métricas z-score y En.
- Romero Espinoza, Marino Belcaguy, Fano, Cribari (FIUBA), "Interlaboratory Evaluation of Radiated and Conducted EMC Measurements Using Portable Calibrated Comb Generators". Borrador. Comparación entre dos laboratorios con peines portátiles calibrados: RE de 30 MHz a 1 GHz a 3 m y CE de 150 kHz a 30 MHz. [PDF](../bibliografia/borrador_RomeroEspinoza_interlaboratory-emc-comb-generators.pdf).
- Anónimo (envío a revisión doble ciego), "Design and Experimental Validation of a Portable RF Comb Generator for EMC Laboratory Applications". Borrador. Peine portátil a batería con flancos de 244 ps y control embebido, proyecto de grado de Ingeniería Electrónica. [PDF](../bibliografia/borrador_Anonimo_portable-rf-comb-generator-emc.pdf).

## SDR en EMC

- Tena Sánchez, Sierra Castañer (UPM), Foged, Gray (MVG), "EMC Measurement System Based on Software Defined Radio and Diagnostic Techniques". [Caso de estudio MVG](https://www.mvg-world.com/upload/media/case_study_document/0001/01/dd314ef9c939934246263a1fa951389d11ad789d.pdf). SDR como receptor de bajo costo, validado contra un laboratorio a 3 m.

## Calibradores sincronizados (radioastronomía)

Lo más parecido a la idea de una fuente que anuncia su propio paso:
- CHIME con dron y fuente pulsada sincronizada por GPS: arXiv 2407.04848.
- PEACC, fuente sintetizada digitalmente con dos unidades y PPS de GPS: arXiv 2604.09859.
- ECHO: arXiv 1610.02607.
- Chang et al., "Beam Calibration of Radio Telescopes with Drones": arXiv 1505.05885.

## Susceptibilidad radiada (etapa posterior)

- AR, Application Note 71, "Multi-Tone: Testing, Theory and Practice".
- "Benefits of multitone EMC immunity testing" (ResearchGate).

## Contexto

- Braun y Russer, sistema EMI en el dominio del tiempo, IEEE T-MTT vol. 53, 2005.
- Fuentes comerciales: York CNE, Com-Power CGO.
- El INTI tiene servicio de EMC y la red SAC de calibración: verificar su alcance antes de afirmar que nadie calibra en Argentina.

## Normas

- CISPR 11 (2024). Copia local, no se sube (norma paga).
- MIL-STD-461E. Copia local.
