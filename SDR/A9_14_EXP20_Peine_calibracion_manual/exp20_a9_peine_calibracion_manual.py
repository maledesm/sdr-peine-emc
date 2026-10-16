#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-20 xA9: peine con calibracion manual por valor medido
# Description: bladeRF 2.0 micro xA9: peine de 70 a 420 MHz. Sin calibrar, las lineas salen cerca de -3 dBm. En cada contador se carga el valor leido en el analizador y el flujo sube esa linea hasta 0 dBm. La calibracion se guarda en un archivo y se puede importar. SOLO para medir con el analizador: nunca con el cable en RX1
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
import os
import osmosdr
import time
import sip
import threading


def snipfcn_guardar_e_importar(self):
    # ============================================================================
    # GUARDAR E IMPORTAR LA CALIBRACION
    # Es el unico codigo Python del flujo. Hace falta porque los bloques no saben
    # escribir ni leer un archivo con valores.
    #   Boton "Guardar calibracion": escribe en un archivo de texto los 36 valores
    #   cargados en la ventana, uno por renglon, junto a su frecuencia.
    #   Boton "Importar calibracion previa": lee ese archivo y pone cada valor en
    #   su contador.
    # ============================================================================
    import os
    import time

    # Los 36 contadores de la ventana, en orden de frecuencia (70, 80, ... 420 MHz).
    # d_widget es la casilla con flechas que se ve en pantalla.
    contadores = [
        self._m_70_win.d_widget, self._m_80_win.d_widget, self._m_90_win.d_widget,
        self._m_100_win.d_widget, self._m_110_win.d_widget, self._m_120_win.d_widget,
        self._m_130_win.d_widget, self._m_140_win.d_widget, self._m_150_win.d_widget,
        self._m_160_win.d_widget, self._m_170_win.d_widget, self._m_180_win.d_widget,
        self._m_190_win.d_widget, self._m_200_win.d_widget, self._m_210_win.d_widget,
        self._m_220_win.d_widget, self._m_230_win.d_widget, self._m_240_win.d_widget,
        self._m_250_win.d_widget, self._m_260_win.d_widget, self._m_270_win.d_widget,
        self._m_280_win.d_widget, self._m_290_win.d_widget, self._m_300_win.d_widget,
        self._m_310_win.d_widget, self._m_320_win.d_widget, self._m_330_win.d_widget,
        self._m_340_win.d_widget, self._m_350_win.d_widget, self._m_360_win.d_widget,
        self._m_370_win.d_widget, self._m_380_win.d_widget, self._m_390_win.d_widget,
        self._m_400_win.d_widget, self._m_410_win.d_widget, self._m_420_win.d_widget,
    ]


    def guardar():
        valores = self.get_medidos()                 # los 36 valores de la ventana
        try:
            archivo = open(self.get_archivo(), 'w')
            # primer renglon: cuando se guardo y con que ganancia se leyeron los valores
            archivo.write('# guardada el ' + time.strftime('%d-%m-%Y %H:%M') +
                          ', valores leidos con ganancia %d dB\n' % self.get_ganancia_de_lectura())
            for k in range(len(valores)):
                frecuencia = 70 + 10 * k
                archivo.write('%d %.1f\n' % (frecuencia, valores[k]))
            archivo.close()
        except Exception:
            self.set_estado_archivo('NO se pudo guardar')
            return
        self.set_estado_archivo('guardada a las ' + time.strftime('%H:%M:%S'))


    def importar():
        if not os.path.exists(self.get_archivo()):
            self.set_estado_archivo('no hay ninguna calibracion guardada')
            return
        try:
            archivo = open(self.get_archivo())
            renglones = archivo.readlines()
            archivo.close()
            if renglones[0].startswith('#'):
                renglones = renglones[1:]            # se saltea el renglon de encabezado
            valores = []
            for k in range(len(contadores)):
                partes = renglones[k].split()        # cada renglon: frecuencia y valor
                valores.append(float(partes[1]))
        except Exception:
            self.set_estado_archivo('el archivo no se pudo leer: no se importo nada')
            return
        for k in range(len(contadores)):
            contadores[k].setValue(valores[k])       # al cambiar el contador, el flujo se actualiza solo
        self.set_estado_archivo('importada a las ' + time.strftime('%H:%M:%S'))


    # GNU Radio llama a set_boton_guardar(1) cuando se aprieta el boton y a
    # set_boton_guardar(0) cuando se suelta. Aca se define que hace esa llamada.
    def al_tocar_guardar(valor):
        if valor == 1:
            guardar()


    def al_tocar_importar(valor):
        if valor == 1:
            importar()


    self.set_boton_guardar = al_tocar_guardar
    self.set_boton_importar = al_tocar_importar


def snippets_main_after_init(tb):
    snipfcn_guardar_e_importar(tb)

class exp20_a9_peine_calibracion_manual(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-20 xA9: peine con calibracion manual por valor medido", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-20 xA9: peine con calibracion manual por valor medido")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp20_a9_peine_calibracion_manual")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.m_90 = m_90 = 0
        self.m_80 = m_80 = 0
        self.m_70 = m_70 = 0
        self.m_420 = m_420 = 0
        self.m_410 = m_410 = 0
        self.m_400 = m_400 = 0
        self.m_390 = m_390 = 0
        self.m_380 = m_380 = 0
        self.m_370 = m_370 = 0
        self.m_360 = m_360 = 0
        self.m_350 = m_350 = 0
        self.m_340 = m_340 = 0
        self.m_330 = m_330 = 0
        self.m_320 = m_320 = 0
        self.m_310 = m_310 = 0
        self.m_300 = m_300 = 0
        self.m_290 = m_290 = 0
        self.m_280 = m_280 = 0
        self.m_270 = m_270 = 0
        self.m_260 = m_260 = 0
        self.m_250 = m_250 = 0
        self.m_240 = m_240 = 0
        self.m_230 = m_230 = 0
        self.m_220 = m_220 = 0
        self.m_210 = m_210 = 0
        self.m_200 = m_200 = 0
        self.m_190 = m_190 = 0
        self.m_180 = m_180 = 0
        self.m_170 = m_170 = 0
        self.m_160 = m_160 = 0
        self.m_150 = m_150 = 0
        self.m_140 = m_140 = 0
        self.m_130 = m_130 = 0
        self.m_120 = m_120 = 0
        self.m_110 = m_110 = 0
        self.m_100 = m_100 = 0
        self.orden_recorrido = orden_recorrido = 0
        self.n_port = n_port = 18
        self.medidos = medidos = [m_70, m_80, m_90, m_100, m_110, m_120, m_130, m_140, m_150, m_160, m_170, m_180, m_190, m_200, m_210, m_220, m_230, m_240, m_250, m_260, m_270, m_280, m_290, m_300, m_310, m_320, m_330, m_340, m_350, m_360, m_370, m_380, m_390, m_400, m_410, m_420]
        self.ganancia_de_lectura = ganancia_de_lectura = 45
        self.pasos_por_pasada = pasos_por_pasada = n_port + 1 if orden_recorrido == 1 else n_port
        self.paso = paso = -1
        self.comp = comp = [(0.0 if leido == 0 else (ganancia_de_lectura - 65) - leido) for leido in medidos]
        self.posicion = posicion = max(paso, 0) % pasos_por_pasada
        self.orden = orden = sorted(range(n_port), key=lambda p: comp[2 * p] + comp[2 * p + 1]) if orden_recorrido == 1 else list(range(n_port))
        self.indice = indice = orden[posicion] if posicion < n_port else n_port
        self.pausa = pausa = 1
        self.paso_port = paso_port = 20e6
        self.pasada = pasada = max(paso, 0) // pasos_por_pasada + 1
        self.indice_freq = indice_freq = orden[n_port - 1] if indice >= n_port else indice
        self.f_primera = f_primera = 75e6
        self.entre_pasadas = entre_pasadas = 1 if indice >= n_port else 0
        self.archivo = archivo = 'calibracion_peine.txt'
        self.amp_max = amp_max = 0.47
        self.amp_base = amp_base = 0.25
        self.sin_margen = sin_margen = sum(1 for db in comp if amp_base * 10 ** (db / 20.0) > amp_max)
        self.permanencia = permanencia = 2.0
        self.linea_de_punto = linea_de_punto = [min(j // 7, 2 * n_port - 1) for j in range(256)]
        self.ganancia = ganancia = 45
        self.freq = freq = f_primera + paso_port * indice_freq
        self.f_tono = f_tono = 5e6
        self.etapa = etapa = 'PAUSA (sin emitir)' if pausa == 1 else ('INICIACION' if paso < 0 else ('SILENCIO ENTRE PASADAS' if entre_pasadas == 1 else 'TRANSMISION, pasada %d' % pasada))
        self.estado_archivo = estado_archivo = 'hay una guardada, sin importar' if os.path.exists(archivo) else 'todavia no hay ninguna guardada'
        self.emite = emite = 1 if (pausa == 0 and paso >= 0) else 0
        self.cargadas = cargadas = sum(1 for leido in medidos if leido != 0)
        self.amp_tabla = amp_tabla = [min(amp_base * 10 ** (db / 20.0), amp_max) for db in comp] + [0.0, 0.0]
        self.tx_gain = tx_gain = ganancia if pausa == 0 else 0
        self.samp_rate = samp_rate = 20e6
        self.lista_de_pasos = lista_de_pasos = list(range(100000))
        self.et_titulo = et_titulo = 'con MAX HOLD, con la ganancia de TX en %d dB y con ese contador en 0' % ganancia_de_lectura
        self.et_tiempos = et_tiempos = '%.0f s (%.1f s por portadora)' % (permanencia * pasos_por_pasada, permanencia)
        self.et_portadora = et_portadora = '%.0f MHz (paso %d de %d)' % (freq / 1e6, posicion + 1, pasos_por_pasada)
        self.et_nivel = et_nivel = 'sin calibrar unos %d dBm, calibradas %d dBm' % (ganancia - 68, ganancia - 65)
        self.et_margen = et_margen = sin_margen
        self.et_lineas = et_lineas = '%.0f y %.0f MHz' % ((freq - f_tono) / 1e6, (freq + f_tono) / 1e6)
        self.et_etapa = et_etapa = etapa
        self.et_comp = et_comp = '%+.1f y %+.1f dB' % (comp[2 * indice_freq], comp[2 * indice_freq + 1])
        self.et_cargadas = et_cargadas = '%d de %d' % (cargadas, 2 * n_port)
        self.et_archivo = et_archivo = estado_archivo
        self.curva_comp = curva_comp = [comp[k] for k in linea_de_punto]
        self.curva_actual = curva_actual = [(comp[k] if (k // 2 == indice and emite == 1) else -2) for k in linea_de_punto]
        self.boton_importar = boton_importar = 0
        self.boton_guardar = boton_guardar = 0
        self.ancho_banda = ancho_banda = 18e6
        self.amp_sup_tx = amp_sup_tx = amp_tabla[2 * indice + 1] if emite == 1 else 0
        self.amp_inf_tx = amp_inf_tx = amp_tabla[2 * indice] if emite == 1 else 0

        ##################################################
        # Blocks
        ##################################################

        self.tono_superior = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, amp_sup_tx, 0, 0)
        self.tono_inferior = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-f_tono), amp_inf_tx, 0, 0)
        self.suma = blocks.add_vcc(1)
        self.ritmo_grafico = blocks.throttle( gr.sizeof_float*256, 2000, True, 0 if "time" == "auto" else max( int(float(0.01) * 2000) if "time" == "time" else int(0.01), 1) )
        _pausa_check_box = Qt.QCheckBox("PAUSA: la salida queda en silencio. Destildar para transmitir")
        self._pausa_choices = {True: 1, False: 0}
        self._pausa_choices_inv = dict((v,k) for k,v in self._pausa_choices.items())
        self._pausa_callback = lambda i: Qt.QMetaObject.invokeMethod(_pausa_check_box, "setChecked", Qt.Q_ARG("bool", self._pausa_choices_inv[i]))
        self._pausa_callback(self.pausa)
        _pausa_check_box.stateChanged.connect(lambda i: self.set_pausa(self._pausa_choices[bool(i)]))
        self.top_grid_layout.addWidget(_pausa_check_box, 1, 0, 1, 3)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        def _paso_probe():
          self.flowgraph_started.wait()
          while True:

            val = self.lista_de_pasos.pop(0)
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_paso,val))
              except AttributeError:
                self.set_paso(val)
            except AttributeError:
              pass
            time.sleep(1.0 / ((1.0 / permanencia)))
        _paso_thread = threading.Thread(target=_paso_probe)
        _paso_thread.daemon = True
        _paso_thread.start()
        self.osmosdr_sink_0 = osmosdr.sink(
            args="numchan=" + str(1) + " " + 'bladerf=321e0fa5875945d99b11070bb0a76d31'
        )
        self.osmosdr_sink_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_sink_0.set_sample_rate(samp_rate)
        self.osmosdr_sink_0.set_center_freq(freq, 0)
        self.osmosdr_sink_0.set_freq_corr(0, 0)
        self.osmosdr_sink_0.set_gain(tx_gain, 0)
        self.osmosdr_sink_0.set_if_gain(0, 0)
        self.osmosdr_sink_0.set_bb_gain(0, 0)
        self.osmosdr_sink_0.set_antenna('', 0)
        self.osmosdr_sink_0.set_bandwidth(ancho_banda, 0)
        # Create the options list
        self._orden_recorrido_options = [0, 1]
        # Create the labels list
        self._orden_recorrido_labels = ['Por frecuencia', 'De menor a mayor nivel (evita el efecto del retardo)']
        # Create the combo box
        self._orden_recorrido_tool_bar = Qt.QToolBar(self)
        self._orden_recorrido_tool_bar.addWidget(Qt.QLabel("Orden de recorrido" + ": "))
        self._orden_recorrido_combo_box = Qt.QComboBox()
        self._orden_recorrido_tool_bar.addWidget(self._orden_recorrido_combo_box)
        for _label in self._orden_recorrido_labels: self._orden_recorrido_combo_box.addItem(_label)
        self._orden_recorrido_callback = lambda i: Qt.QMetaObject.invokeMethod(self._orden_recorrido_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._orden_recorrido_options.index(i)))
        self._orden_recorrido_callback(self.orden_recorrido)
        self._orden_recorrido_combo_box.currentIndexChanged.connect(
            lambda i: self.set_orden_recorrido(self._orden_recorrido_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._orden_recorrido_tool_bar, 1, 6, 1, 3)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_90_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_90_win = qtgui.RangeWidget(self._m_90_range, self.set_m_90, "<div align='right'>90:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_90_win, 6, 2, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_80_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_80_win = qtgui.RangeWidget(self._m_80_range, self.set_m_80, "<div align='right'>80:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_80_win, 6, 1, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_70_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_70_win = qtgui.RangeWidget(self._m_70_range, self.set_m_70, "<div align='right'>70:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_70_win, 6, 0, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_420_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_420_win = qtgui.RangeWidget(self._m_420_range, self.set_m_420, "<div align='right'>420:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_420_win, 9, 8, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_410_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_410_win = qtgui.RangeWidget(self._m_410_range, self.set_m_410, "<div align='right'>410:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_410_win, 9, 7, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_400_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_400_win = qtgui.RangeWidget(self._m_400_range, self.set_m_400, "<div align='right'>400:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_400_win, 9, 6, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_390_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_390_win = qtgui.RangeWidget(self._m_390_range, self.set_m_390, "<div align='right'>390:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_390_win, 9, 5, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_380_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_380_win = qtgui.RangeWidget(self._m_380_range, self.set_m_380, "<div align='right'>380:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_380_win, 9, 4, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_370_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_370_win = qtgui.RangeWidget(self._m_370_range, self.set_m_370, "<div align='right'>370:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_370_win, 9, 3, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_360_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_360_win = qtgui.RangeWidget(self._m_360_range, self.set_m_360, "<div align='right'>360:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_360_win, 9, 2, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_350_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_350_win = qtgui.RangeWidget(self._m_350_range, self.set_m_350, "<div align='right'>350:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_350_win, 9, 1, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_340_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_340_win = qtgui.RangeWidget(self._m_340_range, self.set_m_340, "<div align='right'>340:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_340_win, 9, 0, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_330_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_330_win = qtgui.RangeWidget(self._m_330_range, self.set_m_330, "<div align='right'>330:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_330_win, 8, 8, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_320_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_320_win = qtgui.RangeWidget(self._m_320_range, self.set_m_320, "<div align='right'>320:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_320_win, 8, 7, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_310_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_310_win = qtgui.RangeWidget(self._m_310_range, self.set_m_310, "<div align='right'>310:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_310_win, 8, 6, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_300_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_300_win = qtgui.RangeWidget(self._m_300_range, self.set_m_300, "<div align='right'>300:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_300_win, 8, 5, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_290_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_290_win = qtgui.RangeWidget(self._m_290_range, self.set_m_290, "<div align='right'>290:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_290_win, 8, 4, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_280_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_280_win = qtgui.RangeWidget(self._m_280_range, self.set_m_280, "<div align='right'>280:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_280_win, 8, 3, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_270_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_270_win = qtgui.RangeWidget(self._m_270_range, self.set_m_270, "<div align='right'>270:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_270_win, 8, 2, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_260_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_260_win = qtgui.RangeWidget(self._m_260_range, self.set_m_260, "<div align='right'>260:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_260_win, 8, 1, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_250_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_250_win = qtgui.RangeWidget(self._m_250_range, self.set_m_250, "<div align='right'>250:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_250_win, 8, 0, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_240_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_240_win = qtgui.RangeWidget(self._m_240_range, self.set_m_240, "<div align='right'>240:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_240_win, 7, 8, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_230_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_230_win = qtgui.RangeWidget(self._m_230_range, self.set_m_230, "<div align='right'>230:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_230_win, 7, 7, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_220_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_220_win = qtgui.RangeWidget(self._m_220_range, self.set_m_220, "<div align='right'>220:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_220_win, 7, 6, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_210_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_210_win = qtgui.RangeWidget(self._m_210_range, self.set_m_210, "<div align='right'>210:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_210_win, 7, 5, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_200_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_200_win = qtgui.RangeWidget(self._m_200_range, self.set_m_200, "<div align='right'>200:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_200_win, 7, 4, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_190_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_190_win = qtgui.RangeWidget(self._m_190_range, self.set_m_190, "<div align='right'>190:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_190_win, 7, 3, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_180_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_180_win = qtgui.RangeWidget(self._m_180_range, self.set_m_180, "<div align='right'>180:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_180_win, 7, 2, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_170_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_170_win = qtgui.RangeWidget(self._m_170_range, self.set_m_170, "<div align='right'>170:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_170_win, 7, 1, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_160_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_160_win = qtgui.RangeWidget(self._m_160_range, self.set_m_160, "<div align='right'>160:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_160_win, 7, 0, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_150_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_150_win = qtgui.RangeWidget(self._m_150_range, self.set_m_150, "<div align='right'>150:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_150_win, 6, 8, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_140_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_140_win = qtgui.RangeWidget(self._m_140_range, self.set_m_140, "<div align='right'>140:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_140_win, 6, 7, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_130_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_130_win = qtgui.RangeWidget(self._m_130_range, self.set_m_130, "<div align='right'>130:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_130_win, 6, 6, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_120_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_120_win = qtgui.RangeWidget(self._m_120_range, self.set_m_120, "<div align='right'>120:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_120_win, 6, 5, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_110_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_110_win = qtgui.RangeWidget(self._m_110_range, self.set_m_110, "<div align='right'>110:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_110_win, 6, 4, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_100_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_100_win = qtgui.RangeWidget(self._m_100_range, self.set_m_100, "<div align='right'>100:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_100_win, 6, 3, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.grafico = qtgui.vector_sink_f(
            256,
            ((f_primera - f_tono) / 1e6 - 5),
            (10.0 / 7),
            "Frecuencia de la linea",
            "Compensacion",
            "Compensacion aplicada a cada linea",
            2, # Number of inputs
            None # parent
        )
        self.grafico.set_update_time(0.10)
        self.grafico.set_y_axis((-2), 7)
        self.grafico.enable_autoscale(False)
        self.grafico.enable_grid(True)
        self.grafico.set_x_axis_units("MHz")
        self.grafico.set_y_axis_units("dB")
        self.grafico.set_ref_level(0)


        labels = ["Compensacion de cada linea", "Lineas que salen ahora", '', '', '',
            '', '', '', '', '']
        widths = [2, 3, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(2):
            if len(labels[i]) == 0:
                self.grafico.set_line_label(i, "Data {0}".format(i))
            else:
                self.grafico.set_line_label(i, labels[i])
            self.grafico.set_line_width(i, widths[i])
            self.grafico.set_line_color(i, colors[i])
            self.grafico.set_line_alpha(i, alphas[i])

        self._grafico_win = sip.wrapinstance(self.grafico.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._grafico_win, 10, 0, 1, 9)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._ganancia_options = [45, 55, 65]
        # Create the labels list
        self._ganancia_labels = ['45 dB: para leer y calibrar (lineas en -20 dBm)', '55 dB: lineas en -10 dBm', '65 dB: lineas en 0 dBm']
        # Create the combo box
        self._ganancia_tool_bar = Qt.QToolBar(self)
        self._ganancia_tool_bar.addWidget(Qt.QLabel("Ganancia de TX" + ": "))
        self._ganancia_combo_box = Qt.QComboBox()
        self._ganancia_tool_bar.addWidget(self._ganancia_combo_box)
        for _label in self._ganancia_labels: self._ganancia_combo_box.addItem(_label)
        self._ganancia_callback = lambda i: Qt.QMetaObject.invokeMethod(self._ganancia_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._ganancia_options.index(i)))
        self._ganancia_callback(self.ganancia)
        self._ganancia_combo_box.currentIndexChanged.connect(
            lambda i: self.set_ganancia(self._ganancia_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._ganancia_tool_bar, 1, 3, 1, 3)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_titulo_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'>" + str(x) + "</span>":
            self._et_titulo_formatter = lambda x: "<span style='font-size:11pt'>" + str(x) + "</span>"
        else:
            self._et_titulo_formatter = lambda x: str(x)

        self._et_titulo_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'><b>Valor leido en el analizador para cada linea (MHz), en dBm: </b></span>"))
        self._et_titulo_label = Qt.QLabel(str(self._et_titulo_formatter(self.et_titulo)))
        self._et_titulo_tool_bar.addWidget(self._et_titulo_label)
        self.top_grid_layout.addWidget(self._et_titulo_tool_bar, 5, 0, 1, 9)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_tiempos_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_tiempos_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_tiempos_formatter = lambda x: str(x)

        self._et_tiempos_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Pasada completa: </span>"))
        self._et_tiempos_label = Qt.QLabel(str(self._et_tiempos_formatter(self.et_tiempos)))
        self._et_tiempos_tool_bar.addWidget(self._et_tiempos_label)
        self.top_grid_layout.addWidget(self._et_tiempos_tool_bar, 2, 6, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_portadora_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>":
            self._et_portadora_formatter = lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_portadora_formatter = lambda x: str(x)

        self._et_portadora_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Portadora: </span>"))
        self._et_portadora_label = Qt.QLabel(str(self._et_portadora_formatter(self.et_portadora)))
        self._et_portadora_tool_bar.addWidget(self._et_portadora_label)
        self.top_grid_layout.addWidget(self._et_portadora_tool_bar, 0, 3, 1, 3)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_nivel_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_nivel_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_nivel_formatter = lambda x: str(x)

        self._et_nivel_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Con esta ganancia: </span>"))
        self._et_nivel_label = Qt.QLabel(str(self._et_nivel_formatter(self.et_nivel)))
        self._et_nivel_tool_bar.addWidget(self._et_nivel_label)
        self.top_grid_layout.addWidget(self._et_nivel_tool_bar, 2, 0, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_margen_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_margen_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_margen_formatter = lambda x: str(x)

        self._et_margen_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Lineas que piden mas de lo que hay: </span>"))
        self._et_margen_label = Qt.QLabel(str(self._et_margen_formatter(self.et_margen)))
        self._et_margen_tool_bar.addWidget(self._et_margen_label)
        self.top_grid_layout.addWidget(self._et_margen_tool_bar, 3, 3, 1, 3)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_lineas_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>":
            self._et_lineas_formatter = lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_lineas_formatter = lambda x: str(x)

        self._et_lineas_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Lineas: </span>"))
        self._et_lineas_label = Qt.QLabel(str(self._et_lineas_formatter(self.et_lineas)))
        self._et_lineas_tool_bar.addWidget(self._et_lineas_label)
        self.top_grid_layout.addWidget(self._et_lineas_tool_bar, 0, 6, 1, 3)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_etapa_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>":
            self._et_etapa_formatter = lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_etapa_formatter = lambda x: str(x)

        self._et_etapa_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Etapa: </span>"))
        self._et_etapa_label = Qt.QLabel(str(self._et_etapa_formatter(self.et_etapa)))
        self._et_etapa_tool_bar.addWidget(self._et_etapa_label)
        self.top_grid_layout.addWidget(self._et_etapa_tool_bar, 0, 0, 1, 3)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_comp_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_comp_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_comp_formatter = lambda x: str(x)

        self._et_comp_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Compensacion de estas dos lineas: </span>"))
        self._et_comp_label = Qt.QLabel(str(self._et_comp_formatter(self.et_comp)))
        self._et_comp_tool_bar.addWidget(self._et_comp_label)
        self.top_grid_layout.addWidget(self._et_comp_tool_bar, 2, 3, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_cargadas_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_cargadas_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_cargadas_formatter = lambda x: str(x)

        self._et_cargadas_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Lineas con valor cargado: </span>"))
        self._et_cargadas_label = Qt.QLabel(str(self._et_cargadas_formatter(self.et_cargadas)))
        self._et_cargadas_tool_bar.addWidget(self._et_cargadas_label)
        self.top_grid_layout.addWidget(self._et_cargadas_tool_bar, 3, 0, 1, 3)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_archivo_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_archivo_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_archivo_formatter = lambda x: str(x)

        self._et_archivo_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Calibracion en archivo: </span>"))
        self._et_archivo_label = Qt.QLabel(str(self._et_archivo_formatter(self.et_archivo)))
        self._et_archivo_tool_bar.addWidget(self._et_archivo_label)
        self.top_grid_layout.addWidget(self._et_archivo_tool_bar, 4, 4, 1, 5)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.datos_comp = blocks.vector_source_f(curva_comp, True, 256, [])
        self.datos_actual = blocks.vector_source_f(curva_actual, True, 256, [])
        _boton_importar_push_button = Qt.QPushButton('Importar calibracion previa')
        _boton_importar_push_button = Qt.QPushButton('Importar calibracion previa')
        self._boton_importar_choices = {'Pressed': 1, 'Released': 0}
        _boton_importar_push_button.pressed.connect(lambda: self.set_boton_importar(self._boton_importar_choices['Pressed']))
        _boton_importar_push_button.released.connect(lambda: self.set_boton_importar(self._boton_importar_choices['Released']))
        self.top_grid_layout.addWidget(_boton_importar_push_button, 4, 2, 1, 2)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_guardar_push_button = Qt.QPushButton('Guardar calibracion')
        _boton_guardar_push_button = Qt.QPushButton('Guardar calibracion')
        self._boton_guardar_choices = {'Pressed': 1, 'Released': 0}
        _boton_guardar_push_button.pressed.connect(lambda: self.set_boton_guardar(self._boton_guardar_choices['Pressed']))
        _boton_guardar_push_button.released.connect(lambda: self.set_boton_guardar(self._boton_guardar_choices['Released']))
        self.top_grid_layout.addWidget(_boton_guardar_push_button, 4, 0, 1, 2)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.datos_actual, 0), (self.grafico, 1))
        self.connect((self.datos_comp, 0), (self.ritmo_grafico, 0))
        self.connect((self.ritmo_grafico, 0), (self.grafico, 0))
        self.connect((self.suma, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.tono_inferior, 0), (self.suma, 1))
        self.connect((self.tono_superior, 0), (self.suma, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp20_a9_peine_calibracion_manual")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_m_90(self):
        return self.m_90

    def set_m_90(self, m_90):
        self.m_90 = m_90
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_80(self):
        return self.m_80

    def set_m_80(self, m_80):
        self.m_80 = m_80
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_70(self):
        return self.m_70

    def set_m_70(self, m_70):
        self.m_70 = m_70
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_420(self):
        return self.m_420

    def set_m_420(self, m_420):
        self.m_420 = m_420
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_410(self):
        return self.m_410

    def set_m_410(self, m_410):
        self.m_410 = m_410
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_400(self):
        return self.m_400

    def set_m_400(self, m_400):
        self.m_400 = m_400
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_390(self):
        return self.m_390

    def set_m_390(self, m_390):
        self.m_390 = m_390
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_380(self):
        return self.m_380

    def set_m_380(self, m_380):
        self.m_380 = m_380
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_370(self):
        return self.m_370

    def set_m_370(self, m_370):
        self.m_370 = m_370
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_360(self):
        return self.m_360

    def set_m_360(self, m_360):
        self.m_360 = m_360
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_350(self):
        return self.m_350

    def set_m_350(self, m_350):
        self.m_350 = m_350
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_340(self):
        return self.m_340

    def set_m_340(self, m_340):
        self.m_340 = m_340
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_330(self):
        return self.m_330

    def set_m_330(self, m_330):
        self.m_330 = m_330
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_320(self):
        return self.m_320

    def set_m_320(self, m_320):
        self.m_320 = m_320
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_310(self):
        return self.m_310

    def set_m_310(self, m_310):
        self.m_310 = m_310
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_300(self):
        return self.m_300

    def set_m_300(self, m_300):
        self.m_300 = m_300
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_290(self):
        return self.m_290

    def set_m_290(self, m_290):
        self.m_290 = m_290
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_280(self):
        return self.m_280

    def set_m_280(self, m_280):
        self.m_280 = m_280
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_270(self):
        return self.m_270

    def set_m_270(self, m_270):
        self.m_270 = m_270
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_260(self):
        return self.m_260

    def set_m_260(self, m_260):
        self.m_260 = m_260
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_250(self):
        return self.m_250

    def set_m_250(self, m_250):
        self.m_250 = m_250
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_240(self):
        return self.m_240

    def set_m_240(self, m_240):
        self.m_240 = m_240
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_230(self):
        return self.m_230

    def set_m_230(self, m_230):
        self.m_230 = m_230
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_220(self):
        return self.m_220

    def set_m_220(self, m_220):
        self.m_220 = m_220
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_210(self):
        return self.m_210

    def set_m_210(self, m_210):
        self.m_210 = m_210
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_200(self):
        return self.m_200

    def set_m_200(self, m_200):
        self.m_200 = m_200
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_190(self):
        return self.m_190

    def set_m_190(self, m_190):
        self.m_190 = m_190
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_180(self):
        return self.m_180

    def set_m_180(self, m_180):
        self.m_180 = m_180
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_170(self):
        return self.m_170

    def set_m_170(self, m_170):
        self.m_170 = m_170
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_160(self):
        return self.m_160

    def set_m_160(self, m_160):
        self.m_160 = m_160
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_150(self):
        return self.m_150

    def set_m_150(self, m_150):
        self.m_150 = m_150
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_140(self):
        return self.m_140

    def set_m_140(self, m_140):
        self.m_140 = m_140
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_130(self):
        return self.m_130

    def set_m_130(self, m_130):
        self.m_130 = m_130
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_120(self):
        return self.m_120

    def set_m_120(self, m_120):
        self.m_120 = m_120
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_110(self):
        return self.m_110

    def set_m_110(self, m_110):
        self.m_110 = m_110
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_m_100(self):
        return self.m_100

    def set_m_100(self, m_100):
        self.m_100 = m_100
        self.set_medidos([self.m_70, self.m_80, self.m_90, self.m_100, self.m_110, self.m_120, self.m_130, self.m_140, self.m_150, self.m_160, self.m_170, self.m_180, self.m_190, self.m_200, self.m_210, self.m_220, self.m_230, self.m_240, self.m_250, self.m_260, self.m_270, self.m_280, self.m_290, self.m_300, self.m_310, self.m_320, self.m_330, self.m_340, self.m_350, self.m_360, self.m_370, self.m_380, self.m_390, self.m_400, self.m_410, self.m_420])

    def get_orden_recorrido(self):
        return self.orden_recorrido

    def set_orden_recorrido(self, orden_recorrido):
        self.orden_recorrido = orden_recorrido
        self.set_pasos_por_pasada(self.n_port + 1 if self.orden_recorrido == 1 else self.n_port)
        self.set_orden(sorted(range(self.n_port), key=lambda p: self.comp[2 * p] + self.comp[2 * p + 1]) if self.orden_recorrido == 1 else list(range(self.n_port)))
        self._orden_recorrido_callback(self.orden_recorrido)

    def get_n_port(self):
        return self.n_port

    def set_n_port(self, n_port):
        self.n_port = n_port
        self.set_pasos_por_pasada(self.n_port + 1 if self.orden_recorrido == 1 else self.n_port)
        self.set_orden(sorted(range(self.n_port), key=lambda p: self.comp[2 * p] + self.comp[2 * p + 1]) if self.orden_recorrido == 1 else list(range(self.n_port)))
        self.set_indice(self.orden[self.posicion] if self.posicion < self.n_port else self.n_port)
        self.set_entre_pasadas(1 if self.indice >= self.n_port else 0)
        self.set_indice_freq(self.orden[self.n_port - 1] if self.indice >= self.n_port else self.indice)
        self.set_et_cargadas('%d de %d' % (self.cargadas, 2 * self.n_port))
        self.set_linea_de_punto([min(j // 7, 2 * self.n_port - 1) for j in range(256)])

    def get_medidos(self):
        return self.medidos

    def set_medidos(self, medidos):
        self.medidos = medidos
        self.set_comp([(0.0 if leido == 0 else (self.ganancia_de_lectura - 65) - leido) for leido in self.medidos])
        self.set_cargadas(sum(1 for leido in self.medidos if leido != 0))

    def get_ganancia_de_lectura(self):
        return self.ganancia_de_lectura

    def set_ganancia_de_lectura(self, ganancia_de_lectura):
        self.ganancia_de_lectura = ganancia_de_lectura
        self.set_comp([(0.0 if leido == 0 else (self.ganancia_de_lectura - 65) - leido) for leido in self.medidos])
        self.set_et_titulo('con MAX HOLD, con la ganancia de TX en %d dB y con ese contador en 0' % self.ganancia_de_lectura)

    def get_pasos_por_pasada(self):
        return self.pasos_por_pasada

    def set_pasos_por_pasada(self, pasos_por_pasada):
        self.pasos_por_pasada = pasos_por_pasada
        self.set_posicion(max(self.paso, 0) % self.pasos_por_pasada)
        self.set_pasada(max(self.paso, 0) // self.pasos_por_pasada + 1)
        self.set_et_portadora('%.0f MHz (paso %d de %d)' % (self.freq / 1e6, self.posicion + 1, self.pasos_por_pasada))
        self.set_et_tiempos('%.0f s (%.1f s por portadora)' % (self.permanencia * self.pasos_por_pasada, self.permanencia))

    def get_paso(self):
        return self.paso

    def set_paso(self, paso):
        self.paso = paso
        self.set_posicion(max(self.paso, 0) % self.pasos_por_pasada)
        self.set_pasada(max(self.paso, 0) // self.pasos_por_pasada + 1)
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0) else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO ENTRE PASADAS' if self.entre_pasadas == 1 else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_comp(self):
        return self.comp

    def set_comp(self, comp):
        self.comp = comp
        self.set_orden(sorted(range(self.n_port), key=lambda p: self.comp[2 * p] + self.comp[2 * p + 1]) if self.orden_recorrido == 1 else list(range(self.n_port)))
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.comp] + [0.0, 0.0])
        self.set_sin_margen(sum(1 for db in self.comp if self.amp_base * 10 ** (db / 20.0) > self.amp_max))
        self.set_et_comp('%+.1f y %+.1f dB' % (self.comp[2 * self.indice_freq], self.comp[2 * self.indice_freq + 1]))
        self.set_curva_comp([self.comp[k] for k in self.linea_de_punto])
        self.set_curva_actual([(self.comp[k] if (k // 2 == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

    def get_posicion(self):
        return self.posicion

    def set_posicion(self, posicion):
        self.posicion = posicion
        self.set_indice(self.orden[self.posicion] if self.posicion < self.n_port else self.n_port)
        self.set_et_portadora('%.0f MHz (paso %d de %d)' % (self.freq / 1e6, self.posicion + 1, self.pasos_por_pasada))

    def get_orden(self):
        return self.orden

    def set_orden(self, orden):
        self.orden = orden
        self.set_indice(self.orden[self.posicion] if self.posicion < self.n_port else self.n_port)
        self.set_indice_freq(self.orden[self.n_port - 1] if self.indice >= self.n_port else self.indice)

    def get_indice(self):
        return self.indice

    def set_indice(self, indice):
        self.indice = indice
        self.set_entre_pasadas(1 if self.indice >= self.n_port else 0)
        self.set_indice_freq(self.orden[self.n_port - 1] if self.indice >= self.n_port else self.indice)
        self.set_amp_inf_tx(self.amp_tabla[2 * self.indice] if self.emite == 1 else 0)
        self.set_amp_sup_tx(self.amp_tabla[2 * self.indice + 1] if self.emite == 1 else 0)
        self.set_curva_actual([(self.comp[k] if (k // 2 == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

    def get_pausa(self):
        return self.pausa

    def set_pausa(self, pausa):
        self.pausa = pausa
        self._pausa_callback(self.pausa)
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0) else 0)
        self.set_tx_gain(self.ganancia if self.pausa == 0 else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO ENTRE PASADAS' if self.entre_pasadas == 1 else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_paso_port(self):
        return self.paso_port

    def set_paso_port(self, paso_port):
        self.paso_port = paso_port
        self.set_freq(self.f_primera + self.paso_port * self.indice_freq)

    def get_pasada(self):
        return self.pasada

    def set_pasada(self, pasada):
        self.pasada = pasada
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO ENTRE PASADAS' if self.entre_pasadas == 1 else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_indice_freq(self):
        return self.indice_freq

    def set_indice_freq(self, indice_freq):
        self.indice_freq = indice_freq
        self.set_freq(self.f_primera + self.paso_port * self.indice_freq)
        self.set_et_comp('%+.1f y %+.1f dB' % (self.comp[2 * self.indice_freq], self.comp[2 * self.indice_freq + 1]))

    def get_f_primera(self):
        return self.f_primera

    def set_f_primera(self, f_primera):
        self.f_primera = f_primera
        self.set_freq(self.f_primera + self.paso_port * self.indice_freq)
        self.grafico.set_x_axis(((self.f_primera - self.f_tono) / 1e6 - 5), (10.0 / 7))

    def get_entre_pasadas(self):
        return self.entre_pasadas

    def set_entre_pasadas(self, entre_pasadas):
        self.entre_pasadas = entre_pasadas
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO ENTRE PASADAS' if self.entre_pasadas == 1 else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_archivo(self):
        return self.archivo

    def set_archivo(self, archivo):
        self.archivo = archivo
        self.set_estado_archivo('hay una guardada, sin importar' if os.path.exists(self.archivo) else 'todavia no hay ninguna guardada')

    def get_amp_max(self):
        return self.amp_max

    def set_amp_max(self, amp_max):
        self.amp_max = amp_max
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.comp] + [0.0, 0.0])
        self.set_sin_margen(sum(1 for db in self.comp if self.amp_base * 10 ** (db / 20.0) > self.amp_max))

    def get_amp_base(self):
        return self.amp_base

    def set_amp_base(self, amp_base):
        self.amp_base = amp_base
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.comp] + [0.0, 0.0])
        self.set_sin_margen(sum(1 for db in self.comp if self.amp_base * 10 ** (db / 20.0) > self.amp_max))

    def get_sin_margen(self):
        return self.sin_margen

    def set_sin_margen(self, sin_margen):
        self.sin_margen = sin_margen
        self.set_et_margen(self.sin_margen)

    def get_permanencia(self):
        return self.permanencia

    def set_permanencia(self, permanencia):
        self.permanencia = permanencia
        self.set_et_tiempos('%.0f s (%.1f s por portadora)' % (self.permanencia * self.pasos_por_pasada, self.permanencia))

    def get_linea_de_punto(self):
        return self.linea_de_punto

    def set_linea_de_punto(self, linea_de_punto):
        self.linea_de_punto = linea_de_punto
        self.set_curva_comp([self.comp[k] for k in self.linea_de_punto])
        self.set_curva_actual([(self.comp[k] if (k // 2 == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

    def get_ganancia(self):
        return self.ganancia

    def set_ganancia(self, ganancia):
        self.ganancia = ganancia
        self._ganancia_callback(self.ganancia)
        self.set_tx_gain(self.ganancia if self.pausa == 0 else 0)
        self.set_et_nivel('sin calibrar unos %d dBm, calibradas %d dBm' % (self.ganancia - 68, self.ganancia - 65))

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_et_portadora('%.0f MHz (paso %d de %d)' % (self.freq / 1e6, self.posicion + 1, self.pasos_por_pasada))
        self.set_et_lineas('%.0f y %.0f MHz' % ((self.freq - self.f_tono) / 1e6, (self.freq + self.f_tono) / 1e6))
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_f_tono(self):
        return self.f_tono

    def set_f_tono(self, f_tono):
        self.f_tono = f_tono
        self.set_et_lineas('%.0f y %.0f MHz' % ((self.freq - self.f_tono) / 1e6, (self.freq + self.f_tono) / 1e6))
        self.tono_superior.set_frequency(self.f_tono)
        self.tono_inferior.set_frequency((-self.f_tono))
        self.grafico.set_x_axis(((self.f_primera - self.f_tono) / 1e6 - 5), (10.0 / 7))

    def get_etapa(self):
        return self.etapa

    def set_etapa(self, etapa):
        self.etapa = etapa
        self.set_et_etapa(self.etapa)

    def get_estado_archivo(self):
        return self.estado_archivo

    def set_estado_archivo(self, estado_archivo):
        self.estado_archivo = estado_archivo
        self.set_et_archivo(self.estado_archivo)

    def get_emite(self):
        return self.emite

    def set_emite(self, emite):
        self.emite = emite
        self.set_amp_inf_tx(self.amp_tabla[2 * self.indice] if self.emite == 1 else 0)
        self.set_amp_sup_tx(self.amp_tabla[2 * self.indice + 1] if self.emite == 1 else 0)
        self.set_curva_actual([(self.comp[k] if (k // 2 == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

    def get_cargadas(self):
        return self.cargadas

    def set_cargadas(self, cargadas):
        self.cargadas = cargadas
        self.set_et_cargadas('%d de %d' % (self.cargadas, 2 * self.n_port))

    def get_amp_tabla(self):
        return self.amp_tabla

    def set_amp_tabla(self, amp_tabla):
        self.amp_tabla = amp_tabla
        self.set_amp_inf_tx(self.amp_tabla[2 * self.indice] if self.emite == 1 else 0)
        self.set_amp_sup_tx(self.amp_tabla[2 * self.indice + 1] if self.emite == 1 else 0)

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.tono_superior.set_sampling_freq(self.samp_rate)
        self.tono_inferior.set_sampling_freq(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)

    def get_lista_de_pasos(self):
        return self.lista_de_pasos

    def set_lista_de_pasos(self, lista_de_pasos):
        self.lista_de_pasos = lista_de_pasos

    def get_et_titulo(self):
        return self.et_titulo

    def set_et_titulo(self, et_titulo):
        self.et_titulo = et_titulo
        Qt.QMetaObject.invokeMethod(self._et_titulo_label, "setText", Qt.Q_ARG("QString", str(self._et_titulo_formatter(self.et_titulo))))

    def get_et_tiempos(self):
        return self.et_tiempos

    def set_et_tiempos(self, et_tiempos):
        self.et_tiempos = et_tiempos
        Qt.QMetaObject.invokeMethod(self._et_tiempos_label, "setText", Qt.Q_ARG("QString", str(self._et_tiempos_formatter(self.et_tiempos))))

    def get_et_portadora(self):
        return self.et_portadora

    def set_et_portadora(self, et_portadora):
        self.et_portadora = et_portadora
        Qt.QMetaObject.invokeMethod(self._et_portadora_label, "setText", Qt.Q_ARG("QString", str(self._et_portadora_formatter(self.et_portadora))))

    def get_et_nivel(self):
        return self.et_nivel

    def set_et_nivel(self, et_nivel):
        self.et_nivel = et_nivel
        Qt.QMetaObject.invokeMethod(self._et_nivel_label, "setText", Qt.Q_ARG("QString", str(self._et_nivel_formatter(self.et_nivel))))

    def get_et_margen(self):
        return self.et_margen

    def set_et_margen(self, et_margen):
        self.et_margen = et_margen
        Qt.QMetaObject.invokeMethod(self._et_margen_label, "setText", Qt.Q_ARG("QString", str(self._et_margen_formatter(self.et_margen))))

    def get_et_lineas(self):
        return self.et_lineas

    def set_et_lineas(self, et_lineas):
        self.et_lineas = et_lineas
        Qt.QMetaObject.invokeMethod(self._et_lineas_label, "setText", Qt.Q_ARG("QString", str(self._et_lineas_formatter(self.et_lineas))))

    def get_et_etapa(self):
        return self.et_etapa

    def set_et_etapa(self, et_etapa):
        self.et_etapa = et_etapa
        Qt.QMetaObject.invokeMethod(self._et_etapa_label, "setText", Qt.Q_ARG("QString", str(self._et_etapa_formatter(self.et_etapa))))

    def get_et_comp(self):
        return self.et_comp

    def set_et_comp(self, et_comp):
        self.et_comp = et_comp
        Qt.QMetaObject.invokeMethod(self._et_comp_label, "setText", Qt.Q_ARG("QString", str(self._et_comp_formatter(self.et_comp))))

    def get_et_cargadas(self):
        return self.et_cargadas

    def set_et_cargadas(self, et_cargadas):
        self.et_cargadas = et_cargadas
        Qt.QMetaObject.invokeMethod(self._et_cargadas_label, "setText", Qt.Q_ARG("QString", str(self._et_cargadas_formatter(self.et_cargadas))))

    def get_et_archivo(self):
        return self.et_archivo

    def set_et_archivo(self, et_archivo):
        self.et_archivo = et_archivo
        Qt.QMetaObject.invokeMethod(self._et_archivo_label, "setText", Qt.Q_ARG("QString", str(self._et_archivo_formatter(self.et_archivo))))

    def get_curva_comp(self):
        return self.curva_comp

    def set_curva_comp(self, curva_comp):
        self.curva_comp = curva_comp
        self.datos_comp.set_data(self.curva_comp, [])

    def get_curva_actual(self):
        return self.curva_actual

    def set_curva_actual(self, curva_actual):
        self.curva_actual = curva_actual
        self.datos_actual.set_data(self.curva_actual, [])

    def get_boton_importar(self):
        return self.boton_importar

    def set_boton_importar(self, boton_importar):
        self.boton_importar = boton_importar

    def get_boton_guardar(self):
        return self.boton_guardar

    def set_boton_guardar(self, boton_guardar):
        self.boton_guardar = boton_guardar

    def get_ancho_banda(self):
        return self.ancho_banda

    def set_ancho_banda(self, ancho_banda):
        self.ancho_banda = ancho_banda
        self.osmosdr_sink_0.set_bandwidth(self.ancho_banda, 0)

    def get_amp_sup_tx(self):
        return self.amp_sup_tx

    def set_amp_sup_tx(self, amp_sup_tx):
        self.amp_sup_tx = amp_sup_tx
        self.tono_superior.set_amplitude(self.amp_sup_tx)

    def get_amp_inf_tx(self):
        return self.amp_inf_tx

    def set_amp_inf_tx(self, amp_inf_tx):
        self.amp_inf_tx = amp_inf_tx
        self.tono_inferior.set_amplitude(self.amp_inf_tx)




def main(top_block_cls=exp20_a9_peine_calibracion_manual, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()
    snippets_main_after_init(tb)
    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
