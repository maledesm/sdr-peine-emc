# Bibliografía

Trabajos encontrados para el estado del arte (punto 1 del [roadmap](roadmap.md), P2 de los acuerdos). Los PDF están en [`bibliografia/`](../bibliografia/); la columna **PDF** indica si ya está ahí o si hay que bajarlo a mano. Nombre de cada archivo: `AAAA_Apellido_Palabras_Clave.pdf`.

**Resultado de las búsquedas (17-09 y 16-10-2026, web abierta, sin IEEE Xplore):** no apareció ningún trabajo que use una SDR como generador peine o fuente de referencia para verificar la cadena de emisiones radiadas. Lo más cercano: un peine digital ecualizado línea por línea del AIST (9 kHz a 30 MHz), SDR como generador de pulsos de EMC (Perotoni) y peines sintonizables con PLL (Stellini, MIT LL). Falta confirmarlo en IEEE Xplore.

## Para leer primero

Los 20 principales, en las carpetas numeradas de [`bibliografia/`](../bibliografia/). Todo lo demás está en `6_Extra/`.

**SDR aplicada a EMC.** [2022_Perotoni_Double_Exponential_EMC_Pulses_SDR](../bibliografia/1_SDR_en_EMC/2022_Perotoni_Double_Exponential_EMC_Pulses_SDR.pdf), [2023_Perotoni_SDR_Shielding_Effectiveness](../bibliografia/1_SDR_en_EMC/2023_Perotoni_SDR_Shielding_Effectiveness.pdf), [2024_Spindelberger_USRP_B200mini_EMI_Receiver](../bibliografia/1_SDR_en_EMC/2024_Spindelberger_USRP_B200mini_EMI_Receiver.pdf), [2022_Spindelberger_Direct_Conversion_SDR_RE_Precompliance](../bibliografia/1_SDR_en_EMC/2022_Spindelberger_Direct_Conversion_SDR_RE_Precompliance.pdf), [2024_Dixe_Metrological_Evaluation_SDR_RF_Signal_Generation](../bibliografia/1_SDR_en_EMC/2024_Dixe_Metrological_Evaluation_SDR_RF_Signal_Generation.pdf).

**Generadores peine.** [2007_Mullner_Conducted_Radiated_Comb_Generator_Techniques](../bibliografia/2_Generadores_Peine/2007_Mullner_Conducted_Radiated_Comb_Generator_Techniques.pdf), [2026_RomeroEspinoza_Interlaboratory_EMC_Portable_Comb_Generators_Borrador](../bibliografia/2_Generadores_Peine/2026_RomeroEspinoza_Interlaboratory_EMC_Portable_Comb_Generators_Borrador.pdf), [2026_Anonimo_Portable_RF_Comb_Generator_EMC_Borrador](../bibliografia/2_Generadores_Peine/2026_Anonimo_Portable_RF_Comb_Generator_EMC_Borrador.pdf), [2015_Ameya_Log_Scale_Comb_Generator_FPGA_AWG](../bibliografia/2_Generadores_Peine/2015_Ameya_Log_Scale_Comb_Generator_FPGA_AWG.pdf), [2008_Reader_Comb_Generator_Characterization](../bibliografia/2_Generadores_Peine/2008_Reader_Comb_Generator_Characterization.pdf), [2000_Osabe_Correlation_Test_EMI_Sites_Comb_Generator](../bibliografia/2_Generadores_Peine/2000_Osabe_Correlation_Test_EMI_Sites_Comb_Generator.pdf), [2016_Kolodziej_Multichannel_Agile_Comb_Generator_Antenna_Patterns](../bibliografia/2_Generadores_Peine/2016_Kolodziej_Multichannel_Agile_Comb_Generator_Antenna_Patterns.pdf).

**Fuentes calculables y simulación.** [2021_Bonci_Compact_Broadband_Calculable_Field_Source](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2021_Bonci_Compact_Broadband_Calculable_Field_Source.pdf), [2019_Carobbi_Measurements_Simulations_Low_Uncertainty_Antenna](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2019_Carobbi_Measurements_Simulations_Low_Uncertainty_Antenna.pdf), [2020_Carobbi_Site_Validation_Calculable_Antennas_Simulation](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2020_Carobbi_Site_Validation_Calculable_Antennas_Simulation.pdf).

**Comparaciones entre laboratorios e incertidumbre.** [2014_Carobbi_Proficiency_Test_Scheme_RE_30_1000_MHz](../bibliografia/4_Comparaciones_e_Incertidumbre/2014_Carobbi_Proficiency_Test_Scheme_RE_30_1000_MHz.pdf), [2022_Kovacevic_Interlaboratory_Comparison_RE_Tubular_Dipole](../bibliografia/4_Comparaciones_e_Incertidumbre/2022_Kovacevic_Interlaboratory_Comparison_RE_Tubular_Dipole.pdf), [2001_Kang_Reproducibility_Uncertainty_RE_OATS_SAC](../bibliografia/4_Comparaciones_e_Incertidumbre/2001_Kang_Reproducibility_Uncertainty_RE_OATS_SAC.pdf).

**Lazo cerrado y autocalibración de SDR.** [2026_Kim_Self_Calibrating_SDR_Arrays](../bibliografia/5_Lazo_Cerrado_y_Autocalibracion/2026_Kim_Self_Calibrating_SDR_Arrays.pdf), [2023_Jovanovic_IQ_Imbalance_Wideband_SDR](../bibliografia/5_Lazo_Cerrado_y_Autocalibracion/2023_Jovanovic_IQ_Imbalance_Wideband_SDR.pdf).

## A. SDR en EMC

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Spindelberger y Arthaber, "Out-of-the-Box Performance of popular SDRs for EMC pre-compliance Measurements", EMC Europe 2022, DOI 10.1109/EMCEurope51680.2022.9901003 | [sí](../bibliografia/6_Extra/2022_Spindelberger_Out_Of_The_Box_SDR_EMC_Precompliance.pdf) | Compara HackRF, LimeSDR y USRP como receptores EMI contra CISPR 16-1-1; problemas de la conversión directa. |
| Spindelberger y Arthaber, "Improving the Performance of Direct-Conversion SDRs for Radiated Pre-Compliance Measurements", IEEE LEMCPA 2022, DOI 10.1109/LEMCPA.2022.3227409 | [sí](../bibliografia/1_SDR_en_EMC/2022_Spindelberger_Direct_Conversion_SDR_RE_Precompliance.pdf) | Cómo atacar las espurias de una SDR de conversión directa (P3). |
| Spindelberger y Arthaber, "Investigating the Potential of the Low-Cost SDR USRP B200mini as an EMI Receiver", IEEE TEMC 66(2), 2024, DOI 10.1109/TEMC.2023.3317731 | [sí](../bibliografia/1_SDR_en_EMC/2024_Spindelberger_USRP_B200mini_EMI_Receiver.pdf) | La B200mini usa el AD9364, primo del AD9361 de la xA9. Ensayada con las señales de CISPR 16-1-1. |
| Spindelberger, "Low-cost receivers for EMC measurements", tesis doctoral, TU Wien 2024, DOI 10.34726/hss.2024.74644 | [sí](../bibliografia/6_Extra/2024_Spindelberger_Low_Cost_Receivers_EMC_Tesis.pdf) | Montaje de unos 1,9 k€ comparado con laboratorios profesionales. |
| Perotoni, Vieira, Santos, "Generation of double-exponential EMC pulses with Software-Defined Radios", Advanced Electromagnetics 11(3), 2022, DOI 10.7716/aem.v11i3.1970 | [sí](../bibliografia/1_SDR_en_EMC/2022_Perotoni_Double_Exponential_EMC_Pulses_SDR.pdf) | **SDR como generador de señales de ensayo de EMC.** Antecedente directo. |
| Perotoni et al., "Software-Defined Radio Applied to a Shielding Effectiveness Measurement", JMOEA 22(3), 2023 | [sí](../bibliografia/1_SDR_en_EMC/2023_Perotoni_SDR_Shielding_Effectiveness.pdf) | SDR emitiendo y recibiendo por aire en una medición de EMC. |
| Stevers, "Suitability of the RSP2pro Software-Defined Radio for Precompliance Radiated Emissions Testing", tesis de maestría, Michigan State Univ., 2020 | [sí](../bibliografia/6_Extra/2020_Stevers_RSP2pro_SDR_Precompliance_Radiated_Emissions_Tesis.pdf) | RE con SDR contra un analizador de EMC. |
| Erdősy, Bodolai, Bodnár, "Precompliance Testing Using Software Defined Radio", ICCC 2022, DOI 10.1109/ICCC54292.2022.9805858 | [sí](../bibliografia/6_Extra/2022_Erdosy_Precompliance_Testing_SDR.pdf) | SDR contra receptor de EMC profesional. |
| Tena Sánchez, Sierra Castañer, Foged, Gray, "EMC Measurement System Based on Software Defined Radio and Diagnostic Techniques" | [sí](../bibliografia/6_Extra/2019_TenaSanchez_EMC_Measurement_System_SDR.pdf) | SDR como receptor, validado contra un laboratorio a 3 m. |

## B. Generadores peine

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Müllner, Kriz, Haider, Kolb, "Conducted and Radiated Comb Generator Measurement Techniques", 7th Int. Symp. on EMC and Electromagnetic Ecology, 2007 | [sí](../bibliografia/2_Generadores_Peine/2007_Mullner_Conducted_Radiated_Comb_Generator_Techniques.pdf) | **Base metodológica:** *system check* (referencia, diferencia, umbral); peine a batería más repetible que con cable; RBW entre ancho de línea y separación. |
| Romero Espinoza, Marino Belcaguy, Fano, Cribari (FIUBA), "Interlaboratory Evaluation of Radiated and Conducted EMC Measurements Using Portable Calibrated Comb Generators", borrador | [sí](../bibliografia/2_Generadores_Peine/2026_RomeroEspinoza_Interlaboratory_EMC_Portable_Comb_Generators_Borrador.pdf) | Comparación entre dos laboratorios con peines: RE de 30 MHz a 1 GHz a 3 m. |
| Anónimo, "Design and Experimental Validation of a Portable RF Comb Generator for EMC Laboratory Applications", borrador | [sí](../bibliografia/2_Generadores_Peine/2026_Anonimo_Portable_RF_Comb_Generator_EMC_Borrador.pdf) | Peine a batería con flancos de 244 ps. |
| AIST/NMIJ, peine en escala logarítmica con generador arbitrario sobre FPGA, IEICE PEM 2015 (resumen) | [sí](../bibliografia/2_Generadores_Peine/2015_Ameya_Log_Scale_Comb_Generator_FPGA_AWG.pdf) | **El más parecido:** peine digital con nivel ajustado por línea a ±0,01 dB para el chequeo diario (P5). |
| Stellini, Bertocco, Rossetto, "A low-cost Comb Generator for the Characterization of Test Sites", 2011 (sin DOI en Crossref) | [a mano](https://research.unipd.it/handle/11577/2478964) | Peine con PLL sintonizable de 600 MHz a 12 GHz; estabilidad de largo plazo (P11). |
| Reader, Williams, Hale, Clement, "Comb-Generator Characterization", IEEE T-MTT 56(2), 2008 | [sí](../bibliografia/2_Generadores_Peine/2008_Reader_Comb_Generator_Characterization.pdf) | Efecto de la temperatura y del nivel de excitación; 0,1 dB de incertidumbre (P11, P20). |
| Kolodziej (MIT Lincoln Lab), "Comb generator design for SWaP-constrained applications", IEEE RWS 2016, DOI 10.1109/RWS.2016.7444404 | [sí](../bibliografia/6_Extra/2016_Kolodziej_Comb_Generator_SWaP_Constrained.pdf) | Ecuaciones de diseño de un peine con diodo SRD. |
| Kolodziej (MIT Lincoln Lab), "Multi-channel agile comb generator for antenna radiation pattern measurements", IEEE APS-URSI 2016, DOI 10.1109/APS.2016.7695931 | [sí](../bibliografia/2_Generadores_Peine/2016_Kolodziej_Multichannel_Agile_Comb_Generator_Antenna_Patterns.pdf) | Peine sintonizable más un receptor barato para medir antenas (P15). |
| Olczyk, Malecka, Sroka, "Characterization of EM Fields in a GTEM Cell Using a KSQ1000 Comb Generator and Analysis of Comb Generator Technologies", CPEE 2024 | [sí](../bibliografia/6_Extra/2024_Olczyk_KSQ1000_Comb_Generator_GTEM_Technologies.pdf) | Compara peines con diodo SRD y con línea no lineal (NLTL). |
| Rodwell et al., "GaAs Nonlinear Transmission Lines for Picosecond Pulse Generation and Millimeter-Wave Sampling", IEEE T-MTT 1991, DOI 10.1109/22.85387 | [sí](../bibliografia/6_Extra/1991_Rodwell_GaAs_NLTL_Picosecond_Pulse_Generation.pdf) | Base de los peines NLTL. |
| Osabe et al., "Correlation test among EMI measurement sites using a comb generator", IEEE ISEMC 2000, DOI 10.1109/ISEMC.2000.874750 | [sí](../bibliografia/2_Generadores_Peine/2000_Osabe_Correlation_Test_EMI_Sites_Comb_Generator.pdf) | Comparación entre sitios con un peine. |

## C. Fuentes de referencia, comparaciones entre laboratorios e incertidumbre

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Bonci, Boni, Carobbi, "A Compact, Broadband, and Calculable Electromagnetic Field Source for Quality Assurance in EMC Testing", IEEE TEMC 63(2), 2021, DOI 10.1109/TEMC.2020.3010578 | [sí](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2021_Bonci_Compact_Broadband_Calculable_Field_Source.pdf) | Fuente calculable que viaja entre laboratorios; más de 500 mediciones de 50 a 6000 MHz (P10, P20). Ojo: hay una versión de 2018 retractada (DOI 10.1109/TEMC.2018.2803449); citar la de 2021. |
| Carobbi y Guadagnoli, "Low-Uncertainty Characterization of a Predictable Active and Broadband Antenna", EuCAP 2019 (sin DOI en Crossref) | [a mano](https://flore.unifi.it/handle/2158/1161979) | Simulación de la antena más potencia medida da el campo, con incertidumbre. **Modelo para CST (P10).** |
| Carobbi et al., "The Combined use of Measurements and Simulations for the Low-Uncertainty Characterization…", IEEE M&N 2019, DOI 10.1109/IWMN.2019.8805032 | [sí](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2019_Carobbi_Measurements_Simulations_Low_Uncertainty_Antenna.pdf) | Variante del trabajo anterior: la mayor incertidumbre es el desacople entre la fuente interna y la antena. |
| Carobbi et al., "Site Validation Based on the Use of Broadband Calculable Antennas and Numerical Simulation", EuCAP 2020, DOI 10.23919/EuCAP48036.2020.9135958 | [sí](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2020_Carobbi_Site_Validation_Calculable_Antennas_Simulation.pdf) | **Validar el sitio con antenas calculables y simulación:** muy cerca de P10 y P14. |
| Carobbi et al., "Generation and measurement of a reference field for round-robin comparison purposes", IEEE ISEMC 2008, DOI 10.1109/ISEMC.2008.4652092 | [sí](../bibliografia/6_Extra/2008_Carobbi_Reference_Field_Round_Robin_Comparison.pdf) | Campo de referencia para comparaciones entre laboratorios. |
| Carobbi, Cati, Panconi, peine de 20 MHz a 3 GHz como fuente de campo de referencia, Tutto Misure 2010 (sin DOI) | [a mano](https://flore.unifi.it/handle/2158/385923) | Sacar la ganancia o el factor de antena con un peine (P15). |
| Carobbi, "Proficiency test through interlaboratory comparison – Radiated emissions 30-1000 MHz – Scheme", Univ. de Florencia | [sí](../bibliografia/4_Comparaciones_e_Incertidumbre/2014_Carobbi_Proficiency_Test_Scheme_RE_30_1000_MHz.pdf) | Protocolo real con radiador de referencia: modelo para el procedimiento (P4, P18). |
| Carobbi, "Campioni elettromagnetici di riferimento costruiti a Firenze viaggiano in Europa", Firenze University Press | sí: [parte A](../bibliografia/6_Extra/2026_Carobbi_Campioni_Riferimento_Firenze_Parte_A.pdf), [parte B](../bibliografia/6_Extra/2026_Carobbi_Campioni_Riferimento_Firenze_Parte_B.pdf) | En italiano. Comparación entre 14 sitios con un peine. |
| Kovačević, Munić, Brkljač, Stanković, "Interlaboratory comparison of radiated emission measurements using a tubular dipole", NT&RP 37(3), 2022, DOI 10.2298/NTRP2203207K | [sí](../bibliografia/4_Comparaciones_e_Incertidumbre/2022_Kovacevic_Interlaboratory_Comparison_RE_Tubular_Dipole.pdf) | Valor de referencia sacado de simulación más medición; puntajes z y ζ (P20). |
| Kang, Chung, Won, Kim, "Interlaboratory comparison of radiated emission measurements using a spherical dipole radiator", IEE Proc. SMT 148(1), 2001, DOI 10.1049/ip-smt:20010184 | [sí](../bibliografia/6_Extra/2001_Kang_Interlaboratory_RE_Spherical_Dipole.pdf) | Presupuesto de incertidumbre de unos ±5 dB, dominado por el factor de antena (P14, P20). |
| Kang y Kim, "A proficiency testing of electromagnetic radiated emission measurements", Meas. Sci. Technol. 13(9), 2002, DOI 10.1088/0957-0233/13/9/314 | [sí](../bibliografia/6_Extra/2002_Kang_Proficiency_Testing_Radiated_Emission.pdf) | Puntaje z robusto y En en 12 sitios abiertos. |
| Kang et al., "Reproducibility and uncertainty in radiated emission measurements at open area test sites…", IEEE TEMC 2001, DOI 10.1109/15.974650 | [sí](../bibliografia/4_Comparaciones_e_Incertidumbre/2001_Kang_Reproducibility_Uncertainty_RE_OATS_SAC.pdf) | Reproducibilidad de 7,3 dB en cámaras semianecoicas y 6,0 dB en sitios abiertos. |
| Koepke y Randa, "Screened-Room Measurements on the NIST Spherical-Dipole Standard Radiator", J. Res. NIST 99(6), 1994, DOI 10.6028/jres.099.066 | [sí](../bibliografia/6_Extra/1994_Koepke_NIST_Spherical_Dipole_Screened_Room.pdf) | Diferencias grandes entre laboratorios y entre días en un mismo laboratorio (P11). |
| Aipu et al., "Interlaboratory Comparison of Radiated Emissions in Automotive EMC", EMC Europe 2018, DOI 10.1109/EMCEurope.2018.8485018 | [sí](../bibliografia/6_Extra/2018_Aipu_Interlaboratory_Comparison_RE_Automotive_EMC.pdf) | Comparación entre laboratorios (Timișoara y Craiova). |
| Tas et al., "An Improved Reference Device for Radiated Immunity Interlaboratory Comparison", EMC Europe 2020, DOI 10.1109/EMCEurope48519.2020.9245638 | [sí](../bibliografia/6_Extra/2020_Tas_Reference_Device_Radiated_Immunity_Interlaboratory.pdf) | Para la etapa de susceptibilidad radiada. |
| METAS, informe 2007-218-630, peine con monopolo vertical y distintas conexiones al plano de tierra | [a mano](https://www.sem.admin.ch/dam/metas/en/data/fachbereiche/emv/metas_report_nr._2007-218-630-e.pdf.download.pdf/metas_report_nr._2007-218-630-e.pdf) (acceso bloqueado) | **Directo para P9.** |
| Seibersdorf, "Analysis of the CISPR 25 Component Test Setup", 2003 | el enlace da error 404 | Peine con monopolo: milímetros de diferencia en el cableado arruinan la repetibilidad. |

## D. Lazos cerrados y autocalibración con SDR

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Kim, Dhananjay, Rangan et al., "A Self-Calibrating SDR for High Fidelity Beam- and Null-forming Arrays", arXiv 2604.02498 | [sí](../bibliografia/5_Lazo_Cerrado_y_Autocalibracion/2026_Kim_Self_Calibrating_SDR_Arrays.pdf) | **El mejor para el lazo cerrado:** la SDR estima y compensa su propia respuesta con un lazo interno y filtros FIR (P5, P6). |
| Benzin y Caire, "Internal Self-Calibration Methods for Large Scale Array Transceiver Software-Defined Radios", WSA 2017 (actas VDE, sin DOI en Crossref) | [a mano](https://vde-verlag.de/proceedings-en/454394010.html) | Red de calibración interna. |
| Jovanović y Milenković, "IQ Imbalance Correction in Wideband Software Defined Radio Transceivers", Radioengineering 32(4), 2023 | [sí](../bibliografia/5_Lazo_Cerrado_y_Autocalibracion/2023_Jovanovic_IQ_Imbalance_Wideband_SDR.pdf) | Corrección digital de imagen y fuga en TX y RX (P3). |
| Li, Zhang, Huang et al., "Self-IQ-Demodulation Based Compensation Scheme of Frequency-Dependent IQ Imbalance for Wideband Direct-Conversion Transmitters", IEEE Trans. Broadcasting 2015 | [sí](../bibliografia/6_Extra/2015_Li_Self_IQ_Demodulation_IQ_Imbalance_TX.pdf) | Lazo con el oscilador del TX y un detector de potencia. |
| Xiong, Tian, Chen et al., "An Adaptive software defined radio design based on a standard space telecommunication radio system API", arXiv 1711.09311 | [sí](../bibliografia/6_Extra/2017_Xiong_Adaptive_SDR_STRS_Power_Feedback.pdf) | Lazo cerrado de potencia de TX en GNU Radio. |
| Tesis de Oulu, "Design and demonstration of digital pre-distortion using software defined radio" | [a mano](https://oulurepo.oulu.fi/handle/10024/13639) (acceso bloqueado) | Una USRP X300 que transmite y se recibe a sí misma, como el EXP-18. |
| Maršálek y Pospíšil, predistorsión con tabla en una USRP N200, NORCHIP 2014, DOI 10.1109/NORCHIP.2014.7004715 | [sí](../bibliografia/6_Extra/2014_Marsalek_Digital_Predistortion_USRP_N200.pdf) | Lazo TX→RX con poca FPGA. |
| Dixe et al., "Metrological Evaluation of Software-Defined Radios (Adalm-Pluto and LimeSDR usb) in Radio Frequency Signal Generation", Procedia Computer Science 232, 2024, pp. 1248–1258, DOI 10.1016/j.procs.2024.01.123 | [sí](../bibliografia/1_SDR_en_EMC/2024_Dixe_Metrological_Evaluation_SDR_RF_Signal_Generation.pdf) | **SDR caracterizada como generador:** 0,5 dB de incertidumbre (P20). |

## E. Medición de antenas con SDR

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Kana-Chuctaya y Hilario-Tacuri, "Development of a prototype antenna radiation pattern measurement system using Software-Defined Radio", HardwareX 24, 2025, DOI 10.1016/j.ohx.2025.e00695 | [sí](../bibliografia/6_Extra/2025_KanaChuctaya_Antenna_Pattern_Measurement_SDR_Prototype.pdf) | Error medio de 2,6 dB sin cámara anecoica. |
| Hearn, "Open-Source Antenna Pattern Validation using FEKO", ACES Journal 35(11), 2020 | [sí](../bibliografia/6_Extra/2020_Hearn_Open_Source_Antenna_Pattern_FEKO_ACES.pdf) | Medición con SDR comparada con simulación (P10). |
| Hearn, "Open-Source Antenna Pattern Measurement System", GRCon | [sí](../bibliografia/6_Extra/2022_Hearn_Open_Source_Antenna_Pattern_Measurement_SDR_GRCon.pdf) | Lo mismo, hecho con GNU Radio. |
| Makhija, "The Precision Radio Instrument for Antenna Measurements" (PRIAM), tesis doctoral, Univ. of Virginia, 2024, DOI 10.18130/m9x2-da20 | en la carpeta local, no se sube (95 MB): `6_Extra/2024_Makhija_PRIAM_Precision_Radio_Instrument_Antenna_Measurements_Tesis.pdf` | SDR como calibrador autónomo de antenas, montado en un dron. |

## F. Calibradores sincronizados (radioastronomía)

| Trabajo | PDF | Qué nos sirve |
|---|---|---|
| Tyndall et al., "Beam Maps of CHIME Measured with a Drone", IEEE OJAP 2025, DOI 10.1109/OJAP.2025.3554457 | [sí](../bibliografia/6_Extra/2025_Tyndall_CHIME_Beam_Maps_Drone.pdf) | Fuente sobre dron con pulsos sincronizados por GPS. |
| Bhopi et al., "PEACC – Precision Emitter for 21 cm Array Coherent Calibration", arXiv 2604.09859 | [sí](../bibliografia/6_Extra/2026_Bhopi_PEACC_Coherent_Calibration_Emitter.pdf) | Fuente sintetizada digitalmente con referencia en el receptor: la idea del canal de control. |
| Jacobs et al., "The External Calibrator for Hydrogen Observatories" (ECHO), arXiv 1610.02607 | [sí](../bibliografia/6_Extra/2016_Jacobs_ECHO_External_Calibrator.pdf) | Calibrador externo sobre dron. |
| Chang, Monstein, Refregier, Amara, "Beam Calibration of Radio Telescopes with Drones", arXiv 1505.05885 | [sí](../bibliografia/6_Extra/2015_Chang_Beam_Calibration_Radio_Telescopes_Drones.pdf) | Primer antecedente con dron. |

## G. Otros

- AR, Application Note 71, "Multi-Tone: Testing, Theory and Practice", y "Benefits of multitone EMC immunity testing" (ResearchGate): para la etapa de susceptibilidad radiada.
- Braun y Russer, "A low-noise multiresolution high-dynamic ultra-broad-band time-domain EMI measurement system", IEEE T-MTT 53(11), 2005, DOI 10.1109/TMTT.2005.855745. [PDF](../bibliografia/6_Extra/2005_Braun_Time_Domain_EMI_Measurement_System.pdf).
- Fuentes comerciales: Com-Power (CGO, CGC), York EMC (CGE01), Seibersdorf (RefRad), Schwarzbeck (SG 9302), AET (dipolo esférico USDS), TekBox (TBCG). Com-Power desaconseja acostar el peine para medir en vertical, por el efecto del plano de tierra: tenerlo en cuenta para P16.
- El INTI tiene servicio de EMC y la red SAC de calibración: verificar su alcance antes de afirmar que nadie calibra en Argentina.

## Normas (copias locales, no se suben)

- CISPR 11 (2024).
- MIL-STD-461E.
- CISPR 16-1-6 (calibración de antenas: método de las tres antenas, de la antena patrón y del sitio patrón) y ANSI C63.5: no las tenemos.
