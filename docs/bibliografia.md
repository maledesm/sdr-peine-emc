# Bibliografía

Trabajos encontrados para el estado del arte (punto 1 del [roadmap](roadmap.md), P2 de los acuerdos). Los PDF están en [`bibliografia/`](../bibliografia/); la columna **PDF** indica si ya está ahí o si hay que bajarlo a mano.

**Resultado de las búsquedas (17-09 y 16-10-2026, web abierta, sin IEEE Xplore):** no apareció ningún trabajo que use una SDR como generador peine o fuente de referencia para verificar la cadena de emisiones radiadas. Lo más cercano: un peine digital ecualizado línea por línea del AIST (9 kHz a 30 MHz), SDR como generador de pulsos de EMC (Perotoni) y peines sintonizables con PLL (Stellini, MIT LL). Falta confirmarlo en IEEE Xplore.

## A. SDR en EMC

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Spindelberger y Arthaber, "Out-of-the-Box Performance of popular SDRs for EMC pre-compliance Measurements", EMC Europe 2022, DOI 10.1109/EMCEurope51680.2022.9901003 | a mano (IEEE) | Compara HackRF, LimeSDR y USRP como receptores EMI contra CISPR 16-1-1; problemas de la conversión directa. |
| Spindelberger y Arthaber, "Improving the Performance of Direct-Conversion SDRs for Radiated Pre-Compliance Measurements", IEEE LEMCPA 2022, DOI 10.1109/LEMCPA.2022.3227409 | [sí](../bibliografia/2022_Spindelberger_direct-conversion-sdr-re-precompliance.pdf) | Cómo atacar las espurias de una SDR de conversión directa (P3). |
| Spindelberger y Arthaber, "Investigating the Potential of the Low-Cost SDR USRP B200mini as an EMI Receiver", IEEE TEMC 66(2), 2024, DOI 10.1109/TEMC.2023.3317731 | [sí](../bibliografia/2024_Spindelberger_usrp-b200mini-emi-receiver.pdf) | La B200mini usa el AD9364, primo del AD9361 de la xA9. Ensayada con las señales de CISPR 16-1-1. |
| Spindelberger, "Low-cost receivers for EMC measurements", tesis doctoral, TU Wien 2024, DOI 10.34726/hss.2024.74644 | a mano (abierta) | Montaje de unos 1,9 k€ comparado con laboratorios profesionales. |
| Perotoni, Vieira, Santos, "Generation of double-exponential EMC pulses with Software-Defined Radios", Advanced Electromagnetics 11(3), 2022, DOI 10.7716/aem.v11i3.1970 | [sí](../bibliografia/2022_Perotoni_double-exponential-emc-pulses-sdr.pdf) | **SDR como generador de señales de ensayo de EMC.** Antecedente directo. |
| Perotoni et al., "Software-Defined Radio Applied to a Shielding Effectiveness Measurement", JMOEA 22(3), 2023 | [sí](../bibliografia/2023_Perotoni_sdr-shielding-effectiveness.pdf) | SDR emitiendo y recibiendo por aire en una medición de EMC. |
| Stevers, "Suitability of the RSP2pro Software-Defined Radio for Precompliance Radiated Emissions Testing", tesis de maestría, Michigan State Univ., 2020 | [a mano](https://d.lib.msu.edu/etd/48572) | RE con SDR contra un analizador de EMC. |
| Erdősy, Bodolai, Bodnár, "Precompliance Testing Using Software Defined Radio", ICCC 2022, DOI 10.1109/ICCC54292.2022.9805858 | a mano (IEEE) | SDR contra receptor de EMC profesional. |
| Tena Sánchez, Sierra Castañer, Foged, Gray, "EMC Measurement System Based on Software Defined Radio and Diagnostic Techniques" | [sí](../bibliografia/s-f_TenaSanchez_emc-measurement-system-sdr.pdf) | SDR como receptor, validado contra un laboratorio a 3 m. |

## B. Generadores peine

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Müllner, Kriz, Haider, Kolb, "Conducted and Radiated Comb Generator Measurement Techniques", 7th Int. Symp. on EMC and Electromagnetic Ecology, 2007 | [sí](../bibliografia/2007_Mullner_conducted-radiated-comb-generator-techniques.pdf) | **Base metodológica:** *system check* (referencia, diferencia, umbral); peine a batería más repetible que con cable; RBW entre ancho de línea y separación. |
| Romero Espinoza, Marino Belcaguy, Fano, Cribari (FIUBA), "Interlaboratory Evaluation of Radiated and Conducted EMC Measurements Using Portable Calibrated Comb Generators", borrador | [sí](../bibliografia/borrador_RomeroEspinoza_interlaboratory-emc-comb-generators.pdf) | Comparación entre dos laboratorios con peines: RE de 30 MHz a 1 GHz a 3 m. |
| Anónimo, "Design and Experimental Validation of a Portable RF Comb Generator for EMC Laboratory Applications", borrador | [sí](../bibliografia/borrador_Anonimo_portable-rf-comb-generator-emc.pdf) | Peine a batería con flancos de 244 ps. |
| AIST/NMIJ, peine en escala logarítmica con generador arbitrario sobre FPGA, IEICE PEM 2015 (resumen) | [a mano](https://www.ieice.org/cs/emcj/jpn/pem/Term2/2_6thTechnicalMeeting(PEM2015)/Abstract/FCB-1.pdf) | **El más parecido:** peine digital con nivel ajustado por línea a ±0,01 dB para el chequeo diario (P5). |
| Stellini, Bertocco, Rossetto, "A low-cost Comb Generator for the Characterization of Test Sites", 2011 (sin DOI en Crossref) | [a mano](https://research.unipd.it/handle/11577/2478964) | Peine con PLL sintonizable de 600 MHz a 12 GHz; estabilidad de largo plazo (P11). |
| Reader, Williams, Hale, Clement, "Comb-Generator Characterization", IEEE T-MTT 56(2), 2008 | [sí](../bibliografia/2008_Reader_comb-generator-characterization.pdf) | Efecto de la temperatura y del nivel de excitación; 0,1 dB de incertidumbre (P11, P20). |
| Kolodziej (MIT Lincoln Lab), "Comb generator design for SWaP-constrained applications", IEEE RWS 2016, DOI 10.1109/RWS.2016.7444404 | [a mano (DTIC, abierto)](https://apps.dtic.mil/sti/pdfs/AD1034739.pdf) | Ecuaciones de diseño de un peine con diodo SRD. |
| Kolodziej (MIT Lincoln Lab), "Multi-channel agile comb generator for antenna radiation pattern measurements", IEEE APS-URSI 2016, DOI 10.1109/APS.2016.7695931 | [a mano](https://www.ll.mit.edu/r-d/publications/multi-channel-agile-comb-generator-antenna-radiation-pattern-measurements) | Peine sintonizable más un receptor barato para medir antenas (P15). |
| "Characterization of EM Fields in a GTEM Cell Using a KSQ1000 Comb Generator and Analysis of Comb Generator Technologies", CPEE 2024 | [a mano](https://indico.global/event/10041/contributions/96172) | Compara peines con diodo SRD y con línea no lineal (NLTL). |
| Rodwell et al., "GaAs Nonlinear Transmission Lines for Picosecond Pulse Generation and Millimeter-Wave Sampling", IEEE T-MTT 1991, DOI 10.1109/22.85387 | a mano (IEEE) | Base de los peines NLTL. |
| Osabe et al., "Correlation test among EMI measurement sites using a comb generator", IEEE ISEMC 2000, DOI 10.1109/ISEMC.2000.874750 | a mano (IEEE) | Comparación entre sitios con un peine. |
| Prapuchanay et al., "Design and implementation of a low cost BJTs comb generator", ISPACS 2011, DOI 10.1109/ISPACS.2011.6146072 | a mano (IEEE) | Peine de bajo costo con transistores. |

## C. Fuentes de referencia, comparaciones entre laboratorios e incertidumbre

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Bonci, Boni, Carobbi, "A Compact, Broadband, and Calculable Electromagnetic Field Source for Quality Assurance in EMC Testing", IEEE TEMC 63(2), 2021, DOI 10.1109/TEMC.2020.3010578 | [a mano](https://flore.unifi.it/handle/2158/1235795) | Fuente calculable que viaja entre laboratorios; más de 500 mediciones de 50 a 6000 MHz (P10, P20). Ojo: hay una versión de 2018 retractada (DOI 10.1109/TEMC.2018.2803449); citar la de 2021. |
| Carobbi y Guadagnoli, "Low-Uncertainty Characterization of a Predictable Active and Broadband Antenna", EuCAP 2019 (sin DOI en Crossref) | [a mano](https://flore.unifi.it/handle/2158/1161979) | Simulación de la antena más potencia medida da el campo, con incertidumbre. **Modelo para CST (P10).** |
| Carobbi et al., "The Combined use of Measurements and Simulations for the Low-Uncertainty Characterization…", IEEE M&N 2019, DOI 10.1109/IWMN.2019.8805032 | a mano (IEEE) | Variante del trabajo anterior: la mayor incertidumbre es el desacople entre la fuente interna y la antena. |
| Carobbi et al., "Site Validation Based on the Use of Broadband Calculable Antennas and Numerical Simulation", EuCAP 2020, DOI 10.23919/EuCAP48036.2020.9135958 | a mano (IEEE) | **Validar el sitio con antenas calculables y simulación:** muy cerca de P10 y P14. |
| Carobbi et al., "Generation and measurement of a reference field for round-robin comparison purposes", IEEE ISEMC 2008, DOI 10.1109/ISEMC.2008.4652092 | a mano (IEEE) | Campo de referencia para comparaciones entre laboratorios. |
| Carobbi, Cati, Panconi, peine de 20 MHz a 3 GHz como fuente de campo de referencia, Tutto Misure 2010 (sin DOI) | [a mano](https://flore.unifi.it/handle/2158/385923) | Sacar la ganancia o el factor de antena con un peine (P15). |
| Carobbi, "Proficiency test through interlaboratory comparison – Radiated emissions 30-1000 MHz – Scheme", Univ. de Florencia | [sí](../bibliografia/s-f_Carobbi_proficiency-test-re-30-1000-mhz.pdf) | Protocolo real con radiador de referencia: modelo para el procedimiento (P4, P18). |
| Carobbi, "Campioni elettromagnetici di riferimento costruiti a Firenze viaggiano in Europa", Firenze University Press | a mano: [parte A](https://books.fupress.com/chapter/campioni-elettromagnetici-di-riferimento-costruiti-a-firenze-viaggiano-in-europa--parte-a/17037), [parte B](https://books.fupress.com/chapter/campioni-elettromagnetici-di-riferimento-costruiti-a-firenze-viaggiano-in-europa--parte-b/17038) | En italiano. Comparación entre 14 sitios con un peine. |
| Kovačević, Munić, Brkljač, Stanković, "Interlaboratory comparison of radiated emission measurements using a tubular dipole", NT&RP 37(3), 2022, DOI 10.2298/NTRP2203207K | [a mano](https://ntrp.vinca.rs/2022_3/Kovacevic2022_3.pdf) | Valor de referencia sacado de simulación más medición; puntajes z y ζ (P20). |
| Kang, Chung, Won, Kim, "Interlaboratory comparison of radiated emission measurements using a spherical dipole radiator", IEE Proc. SMT 148(1), 2001, DOI 10.1049/ip-smt:20010184 | [a mano](https://remotecenter.postech.ac.kr/handle/2014.oak/19656) | Presupuesto de incertidumbre de unos ±5 dB, dominado por el factor de antena (P14, P20). |
| Kang y Kim, "A proficiency testing of electromagnetic radiated emission measurements", Meas. Sci. Technol. 13(9), 2002, DOI 10.1088/0957-0233/13/9/314 | [a mano](https://remotecenter.postech.ac.kr/handle/2014.oak/18886) | Puntaje z robusto y En en 12 sitios abiertos. |
| Kang et al., "Reproducibility and uncertainty in radiated emission measurements at open area test sites…", IEEE TEMC 2001, DOI 10.1109/15.974650 | a mano (IEEE) | Reproducibilidad de 7,3 dB en cámaras semianecoicas y 6,0 dB en sitios abiertos. |
| Koepke y Randa, "Screened-Room Measurements on the NIST Spherical-Dipole Standard Radiator", J. Res. NIST 99(6), 1994, DOI 10.6028/jres.099.066 | [a mano](https://pmc.ncbi.nlm.nih.gov/articles/PMC8345243/) | Diferencias grandes entre laboratorios y entre días en un mismo laboratorio (P11). |
| Aipu et al., "Interlaboratory Comparison of Radiated Emissions in Automotive EMC", EMC Europe 2018, DOI 10.1109/EMCEurope.2018.8485018 | a mano (IEEE) | Comparación entre laboratorios (Timișoara y Craiova). |
| Tas et al., "An Improved Reference Device for Radiated Immunity Interlaboratory Comparison", EMC Europe 2020, DOI 10.1109/EMCEurope48519.2020.9245638 | a mano (IEEE) | Para la etapa de susceptibilidad radiada. |
| METAS, informe 2007-218-630, peine con monopolo vertical y distintas conexiones al plano de tierra | [a mano](https://www.sem.admin.ch/dam/metas/en/data/fachbereiche/emv/metas_report_nr._2007-218-630-e.pdf.download.pdf/metas_report_nr._2007-218-630-e.pdf) | **Directo para P9.** |
| Seibersdorf, "Analysis of the CISPR 25 Component Test Setup", 2003 | el enlace da error 404 | Peine con monopolo: milímetros de diferencia en el cableado arruinan la repetibilidad. |

## D. Lazos cerrados y autocalibración con SDR

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Kim, Dhananjay, Rangan et al., "A Self-Calibrating SDR for High Fidelity Beam- and Null-forming Arrays", arXiv 2604.02498 | [sí](../bibliografia/2026_Kim_self-calibrating-sdr-arrays.pdf) | **El mejor para el lazo cerrado:** la SDR estima y compensa su propia respuesta con un lazo interno y filtros FIR (P5, P6). |
| Benzin y Caire, "Internal Self-Calibration Methods for Large Scale Array Transceiver Software-Defined Radios", WSA 2017 (actas VDE, sin DOI en Crossref) | [a mano](https://vde-verlag.de/proceedings-en/454394010.html) | Red de calibración interna. |
| Jovanović y Milenković, "IQ Imbalance Correction in Wideband Software Defined Radio Transceivers", Radioengineering 32(4), 2023 | [sí](../bibliografia/2023_Jovanovic_iq-imbalance-wideband-sdr.pdf) | Corrección digital de imagen y fuga en TX y RX (P3). |
| Li, Zhang, Huang et al., "Self-IQ-Demodulation Based Compensation Scheme of Frequency-Dependent IQ Imbalance for Wideband Direct-Conversion Transmitters", IEEE Trans. Broadcasting 2015 | [sí](../bibliografia/2015_Li_self-iq-demodulation-iq-imbalance-tx.pdf) | Lazo con el oscilador del TX y un detector de potencia. |
| Xiong, Tian, Chen et al., "An Adaptive software defined radio design based on a standard space telecommunication radio system API", arXiv 1711.09311 | [sí](../bibliografia/2017_Xiong_adaptive-sdr-strs-power-feedback.pdf) | Lazo cerrado de potencia de TX en GNU Radio. |
| Tesis de Oulu, "Design and demonstration of digital pre-distortion using software defined radio" | [a mano](https://oulurepo.oulu.fi/handle/10024/13639) | Una USRP X300 que transmite y se recibe a sí misma, como el EXP-18. |
| Maršálek y Pospíšil, predistorsión con tabla en una USRP N200, NORCHIP 2014, DOI 10.1109/NORCHIP.2014.7004715 | a mano (IEEE) | Lazo TX→RX con poca FPGA. |
| Dixe et al., "Metrological Evaluation of Software-Defined Radios (Adalm-Pluto and LimeSDR usb) in Radio Frequency Signal Generation", Procedia Computer Science 232, 2024, pp. 1248–1258, DOI 10.1016/j.procs.2024.01.123 | a mano (abierto en ScienceDirect); [datos](https://data.mendeley.com/datasets/49c6k4v3sv) | **SDR caracterizada como generador:** 0,5 dB de incertidumbre (P20). |

## E. Medición de antenas con SDR

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Kana-Chuctaya y Hilario-Tacuri, "Development of a prototype antenna radiation pattern measurement system using Software-Defined Radio", HardwareX 24, 2025, DOI 10.1016/j.ohx.2025.e00695 | [a mano](https://pmc.ncbi.nlm.nih.gov/articles/PMC12481085/) | Error medio de 2,6 dB sin cámara anecoica. |
| Hearn, "Open-Source Antenna Pattern Validation using FEKO", ACES Journal 35(11), 2020 | [sí](../bibliografia/2020_Hearn_open-source-antenna-pattern-feko-aces.pdf) | Medición con SDR comparada con simulación (P10). |
| Hearn, "Open-Source Antenna Pattern Measurement System", GRCon | [sí](../bibliografia/s-f_Hearn_open-source-antenna-pattern-sdr-grcon.pdf) | Lo mismo, hecho con GNU Radio. |
| Makhija, "The Precision Radio Instrument for Antenna Measurements" (PRIAM), tesis doctoral, Univ. of Virginia, 2024, DOI 10.18130/m9x2-da20 | [a mano](https://doi.org/10.18130/m9x2-da20) (95 MB, no se sube) | SDR como calibrador autónomo de antenas, montado en un dron. |

## F. Calibradores sincronizados (radioastronomía)

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Tyndall et al., "Beam Maps of CHIME Measured with a Drone", IEEE OJAP 2025, DOI 10.1109/OJAP.2025.3554457 | [sí](../bibliografia/2025_Tyndall_chime-beam-maps-drone.pdf) | Fuente sobre dron con pulsos sincronizados por GPS. |
| Bhopi et al., "PEACC – Precision Emitter for 21 cm Array Coherent Calibration", arXiv 2604.09859 | [sí](../bibliografia/2026_Bhopi_peacc-coherent-calibration-emitter.pdf) | Fuente sintetizada digitalmente con referencia en el receptor: la idea del canal de control. |
| Jacobs et al., "The External Calibrator for Hydrogen Observatories" (ECHO), arXiv 1610.02607 | [sí](../bibliografia/2016_Jacobs_echo-external-calibrator.pdf) | Calibrador externo sobre dron. |
| Chang, Monstein, Refregier, Amara, "Beam Calibration of Radio Telescopes with Drones", arXiv 1505.05885 | [sí](../bibliografia/2015_Chang_beam-calibration-radio-telescopes-drones.pdf) | Primer antecedente con dron. |

## G. Otros

- AR, Application Note 71, "Multi-Tone: Testing, Theory and Practice", y "Benefits of multitone EMC immunity testing" (ResearchGate): para la etapa de susceptibilidad radiada.
- Braun y Russer, sistema de medición EMI en el dominio del tiempo, IEEE T-MTT 53, 2005.
- Fuentes comerciales: Com-Power (CGO, CGC), York EMC (CGE01), Seibersdorf (RefRad), Schwarzbeck (SG 9302), AET (dipolo esférico USDS), TekBox (TBCG). Com-Power desaconseja acostar el peine para medir en vertical, por el efecto del plano de tierra: tenerlo en cuenta para P16.
- El INTI tiene servicio de EMC y la red SAC de calibración: verificar su alcance antes de afirmar que nadie calibra en Argentina.

## Normas (copias locales, no se suben)

- CISPR 11 (2024).
- MIL-STD-461E.
- CISPR 16-1-6 (calibración de antenas: método de las tres antenas, de la antena patrón y del sitio patrón) y ANSI C63.5: no las tenemos.
