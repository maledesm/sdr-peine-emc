# Bibliografía

PDF en [`bibliografia/`](../bibliografia/): las carpetas 1 a 5 tienen los 20 principales; `6_Extra/` el resto. Búsqueda del 17-09 y el 16-10-2026 en web abierta: ningún trabajo usa una SDR como peine para verificar la cadena de RE (falta confirmarlo en IEEE Xplore).

## 1. SDR aplicada a EMC
- [Perotoni et al., 2022](../bibliografia/1_SDR_en_EMC/2022_Perotoni_Double_Exponential_EMC_Pulses_SDR.pdf). Double-exponential EMC pulses with SDRs. Adv. Electromagnetics. DOI 10.7716/aem.v11i3.1970. SDR como generador de ensayo.
- [Perotoni et al., 2023](../bibliografia/1_SDR_en_EMC/2023_Perotoni_SDR_Shielding_Effectiveness.pdf). SDR applied to a shielding effectiveness measurement. JMOEA. DOI 10.1590/2179-10742023v22i3274047. SDR que emite y recibe.
- [Spindelberger y Arthaber, 2024](../bibliografia/1_SDR_en_EMC/2024_Spindelberger_USRP_B200mini_EMI_Receiver.pdf). USRP B200mini as an EMI receiver. IEEE TEMC. DOI 10.1109/TEMC.2023.3317731. Chip AD9364, primo del de la xA9.
- [Spindelberger y Arthaber, 2022](../bibliografia/1_SDR_en_EMC/2022_Spindelberger_Direct_Conversion_SDR_RE_Precompliance.pdf). Improving direct-conversion SDRs for RE pre-compliance. IEEE LEMCPA. DOI 10.1109/LEMCPA.2022.3227409. Espurias de la conversión directa.
- [Dixe et al., 2024](../bibliografia/1_SDR_en_EMC/2024_Dixe_Metrological_Evaluation_SDR_RF_Signal_Generation.pdf). Metrological evaluation of SDRs in RF signal generation. Procedia CS. DOI 10.1016/j.procs.2024.01.123. SDR como generador: 0,5 dB de incertidumbre.

## 2. Generadores peine
- [Müllner et al., 2007](../bibliografia/2_Generadores_Peine/2007_Mullner_Conducted_Radiated_Comb_Generator_Techniques.pdf). Conducted and radiated comb generator measurement techniques. EMC & EM Ecology. DOI 10.1109/EMCECO.2007.4371688. Base del método: referencia, diferencia y umbral.
- [Romero Espinoza et al., borrador](../bibliografia/2_Generadores_Peine/2026_RomeroEspinoza_Interlaboratory_EMC_Portable_Comb_Generators_Borrador.pdf). Interlaboratory evaluation with portable comb generators (FIUBA). Modelo para el TP5.
- [Anónimo, borrador](../bibliografia/2_Generadores_Peine/2026_Anonimo_Portable_RF_Comb_Generator_EMC_Borrador.pdf). Portable RF comb generator for EMC laboratories. Peine a batería, flancos de 244 ps.
- [Ameya y Kurokawa, 2015](../bibliografia/2_Generadores_Peine/2015_Ameya_Log_Scale_Comb_Generator_FPGA_AWG.pdf). Log-scale comb generator with an FPGA-based AWG. IEICE PEM. Peine digital ecualizado por línea: el más parecido al nuestro.
- [Reader et al., 2008](../bibliografia/2_Generadores_Peine/2008_Reader_Comb_Generator_Characterization.pdf). Comb-generator characterization. IEEE T-MTT. DOI 10.1109/TMTT.2007.914630. Temperatura y nivel de excitación.
- [Osabe et al., 2000](../bibliografia/2_Generadores_Peine/2000_Osabe_Correlation_Test_EMI_Sites_Comb_Generator.pdf). Correlation test among EMI sites using a comb generator. IEEE ISEMC. DOI 10.1109/ISEMC.2000.874750. Nuestro caso de uso.
- [Kolodziej y Hurst, 2016](../bibliografia/2_Generadores_Peine/2016_Kolodziej_Multichannel_Agile_Comb_Generator_Antenna_Patterns.pdf). Agile comb generator for antenna pattern measurements. IEEE APS-URSI. DOI 10.1109/APS.2016.7695931. Peine sintonizable para medir antenas.

## 3. Fuentes calculables y simulación
- [Bonci, Boni, Carobbi, 2021](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2021_Bonci_Compact_Broadband_Calculable_Field_Source.pdf). Compact, broadband, calculable field source. IEEE TEMC. DOI 10.1109/TEMC.2020.3010578. Fuente de referencia calculable. No citar la versión de 2018, retractada.
- [Carobbi et al., 2019](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2019_Carobbi_Measurements_Simulations_Low_Uncertainty_Antenna.pdf). Measurements and simulations for low-uncertainty characterization. IEEE M&N. DOI 10.1109/IWMN.2019.8805032. Medición más simulación: modelo para CST.
- [Carobbi y Bonci, 2020](../bibliografia/3_Fuentes_Calculables_y_Simulacion/2020_Carobbi_Site_Validation_Calculable_Antennas_Simulation.pdf). Site validation with calculable antennas and simulation. EuCAP. DOI 10.23919/EuCAP48036.2020.9135958. Validar el sitio simulando.

## 4. Comparaciones entre laboratorios e incertidumbre
- [Carobbi, 2014](../bibliografia/4_Comparaciones_e_Incertidumbre/2014_Carobbi_Proficiency_Test_Scheme_RE_30_1000_MHz.pdf). Proficiency test scheme, RE 30–1000 MHz (Univ. de Florencia). Protocolo real con radiador de referencia.
- [Kovačević et al., 2022](../bibliografia/4_Comparaciones_e_Incertidumbre/2022_Kovacevic_Interlaboratory_Comparison_RE_Tubular_Dipole.pdf). Interlaboratory comparison of RE with a tubular dipole. NT&RP. DOI 10.2298/NTRP2203207K. Referencia por simulación y medición.
- [Kang et al., 2001](../bibliografia/4_Comparaciones_e_Incertidumbre/2001_Kang_Reproducibility_Uncertainty_RE_OATS_SAC.pdf). Reproducibility and uncertainty of RE at OATS and SAC. IEEE TEMC. DOI 10.1109/15.974650. Reproducibilidad en cámaras semianecoicas.

## 5. Lazo cerrado y autocalibración de SDR
- [Kim et al., 2026](../bibliografia/5_Lazo_Cerrado_y_Autocalibracion/2026_Kim_Self_Calibrating_SDR_Arrays.pdf). A self-calibrating SDR for beam- and null-forming arrays. arXiv 2604.02498. La SDR mide y compensa su respuesta.
- [Jovanović y Milenković, 2023](../bibliografia/5_Lazo_Cerrado_y_Autocalibracion/2023_Jovanovic_IQ_Imbalance_Wideband_SDR.pdf). IQ imbalance correction in wideband SDR transceivers. Radioengineering. DOI 10.13164/re.2023.0479. Corrección de imagen y fuga.

## 6. Extra (de consulta)
- **SDR en EMC:** Spindelberger y Arthaber 2022, out-of-the-box SDRs for EMC (DOI 10.1109/EMCEurope51680.2022.9901003); Spindelberger 2024, tesis (DOI 10.34726/hss.2024.74644); Stevers 2020, tesis; Erdősy et al. 2022 (DOI 10.1109/ICCC54292.2022.9805858); Tena Sánchez et al. 2019 (DOI 10.23919/AMTAP.2019.8906444).
- **Peines:** Kolodziej 2016, peine SWaP (DOI 10.1109/RWS.2016.7444404); Olczyk et al. 2024, SRD frente a NLTL (DOI 10.1109/CPEE64152.2024.10720403); Rodwell et al. 1991, NLTL (DOI 10.1109/22.85387); Braun y Russer 2005, EMI en el tiempo (DOI 10.1109/TMTT.2005.855745).
- **Referencias e incertidumbre:** Carobbi et al. 2008 (DOI 10.1109/ISEMC.2008.4652092); Carobbi, capítulos A y B en italiano; Kang et al. 2001, IEE Proc. (DOI 10.1049/ip-smt:20010184); Kang y Kim 2002 (DOI 10.1088/0957-0233/13/9/314); Koepke y Randa 1994 (DOI 10.6028/jres.099.066); Aipu et al. 2018 (DOI 10.1109/EMCEurope.2018.8485018); Tas et al. 2020, RS (DOI 10.1109/EMCEurope48519.2020.9245638).
- **Lazo cerrado:** Li et al. 2015 (DOI 10.1109/TBC.2015.2465138); Xiong et al. 2017 (arXiv 1711.09311); Maršálek y Pospíšil 2014 (DOI 10.1109/NORCHIP.2014.7004715).
- **Antenas con SDR:** Hearn 2020, ACES (DOI 10.47037/2020.ACES.J.351149); Hearn 2022, GRCon; Kana-Chuctaya y Hilario-Tacuri 2025 (DOI 10.1016/j.ohx.2025.e00695); Makhija 2024, tesis PRIAM (DOI 10.18130/m9x2-da20; solo local, 95 MB).
- **Radioastronomía:** Tyndall et al. 2025, CHIME (DOI 10.1109/OJAP.2025.3554457); Bhopi et al. 2026, PEACC (arXiv 2604.09859); Jacobs et al. 2016, ECHO (arXiv 1610.02607); Chang et al. 2015 (arXiv 1505.05885).

## Sin conseguir
- Sin DOI: Stellini et al. 2011, peine con PLL ([Padua](https://research.unipd.it/handle/11577/2478964)); Carobbi y Guadagnoli, EuCAP 2019 ([Florencia](https://flore.unifi.it/handle/2158/1161979)); Carobbi et al., Tutto Misure 2010 ([Florencia](https://flore.unifi.it/handle/2158/385923)); Benzin y Caire, WSA 2017 ([VDE](https://vde-verlag.de/proceedings-en/454394010.html)).
- Acceso bloqueado: informe METAS 2007-218-630, peine con monopolo y plano de tierra ([enlace](https://www.sem.admin.ch/dam/metas/en/data/fachbereiche/emv/metas_report_nr._2007-218-630-e.pdf.download.pdf/metas_report_nr._2007-218-630-e.pdf)); tesis de Oulu sobre predistorsión con SDR ([enlace](https://oulurepo.oulu.fi/handle/10024/13639)). Enlace roto: Seibersdorf 2003, CISPR 25.
- A buscar: Tena Sánchez et al. 2020, medición de antenas sin referencia con SDR, IEEE AP Magazine (DOI 10.1109/MAP.2020.3012897).

## Normas
- En [`normas/`](../normas/): CISPR 11:2024 y MIL-STD-461E.
- No las tenemos: CISPR 16-1-1, 16-1-4 y 16-1-6, CISPR 32, ANSI C63.4 y C63.5, IEC 61000-4-3, ECSS-E-ST-20.
- Fuentes comerciales de referencia: Com-Power, York EMC, Seibersdorf (RefRad), Schwarzbeck, AET (dipolo esférico), TekBox; nota de aplicación 71 de AR sobre ensayos multitono.
