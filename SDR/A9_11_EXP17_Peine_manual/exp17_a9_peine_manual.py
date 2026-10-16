#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-17 xA9: peine por tandas con calibracion manual
# Description: bladeRF 2.0 micro xA9: peine de 70 a 420 MHz, lineas cada 10 MHz. Dos tonos en +/-5 MHz por portadora. Calibracion manual: una correccion de ganancia por portadora. Sin codigo Python
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
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
import math
import osmosdr
import time
import sip
import threading



class exp17_a9_peine_manual(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-17 xA9: peine por tandas con calibracion manual", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-17 xA9: peine por tandas con calibracion manual")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp17_a9_peine_manual")

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
        self.tabla_inicial = tabla_inicial = [0] * 18
        self.paso = paso = -1
        self.n_port = n_port = 18
        self.c_95 = c_95 = tabla_inicial[1]
        self.c_75 = c_75 = tabla_inicial[0]
        self.c_415 = c_415 = tabla_inicial[17]
        self.c_395 = c_395 = tabla_inicial[16]
        self.c_375 = c_375 = tabla_inicial[15]
        self.c_355 = c_355 = tabla_inicial[14]
        self.c_335 = c_335 = tabla_inicial[13]
        self.c_315 = c_315 = tabla_inicial[12]
        self.c_295 = c_295 = tabla_inicial[11]
        self.c_275 = c_275 = tabla_inicial[10]
        self.c_255 = c_255 = tabla_inicial[9]
        self.c_235 = c_235 = tabla_inicial[8]
        self.c_215 = c_215 = tabla_inicial[7]
        self.c_195 = c_195 = tabla_inicial[6]
        self.c_175 = c_175 = tabla_inicial[5]
        self.c_155 = c_155 = tabla_inicial[4]
        self.c_135 = c_135 = tabla_inicial[3]
        self.c_115 = c_115 = tabla_inicial[2]
        self.tabla = tabla = [c_75, c_95, c_115, c_135, c_155, c_175, c_195, c_215, c_235, c_255, c_275, c_295, c_315, c_335, c_355, c_375, c_395, c_415]
        self.indice = indice = max(paso, 0) % n_port
        self.tope = tope = 40
        self.ganancia_base = ganancia_base = 30
        self.correccion = correccion = tabla[indice]
        self.tx_gain = tx_gain = min(ganancia_base + correccion, tope)
        self.paso_port = paso_port = 20e6
        self.pasada = pasada = max(paso, 0) // n_port + 1
        self.f_primera = f_primera = 75e6
        self.emitir = emitir = 1
        self.amp = amp = 0.45
        self.permanencia = permanencia = 1.0
        self.nivel_estimado = nivel_estimado = tx_gain - 60 + 20 * math.log10(amp)
        self.linea_de_punto = linea_de_punto = [min(j // 7, 2 * n_port - 1) for j in range(256)]
        self.freq = freq = f_primera + paso_port * indice
        self.f_tono = f_tono = 5e6
        self.etapa = etapa = 'SILENCIO' if emitir == 0 else ('INICIACION' if paso < 0 else 'TRANSMISION, pasada %d' % pasada)
        self.samp_rate = samp_rate = 20e6
        self.lista_de_pasos = lista_de_pasos = list(range(100000))
        self.et_titulo = et_titulo = ''
        self.et_tiempos = et_tiempos = '%.0f s (%.1f s por portadora)' % (permanencia * n_port, permanencia)
        self.et_tabla = et_tabla = str(tabla)
        self.et_portadora = et_portadora = '%d de %d, en %.0f MHz' % (indice + 1, n_port, freq / 1e6)
        self.et_nivel = et_nivel = ('%.0f dBm' % nivel_estimado) if emitir == 1 else 'sin emision'
        self.et_lineas = et_lineas = '%.0f y %.0f MHz' % ((freq - f_tono) / 1e6, (freq + f_tono) / 1e6)
        self.et_ganancia = et_ganancia = '%d dB (base %d, correccion %d)' % (tx_gain, ganancia_base, correccion)
        self.et_etapa = et_etapa = etapa
        self.curva_tabla = curva_tabla = [tabla[k // 2] for k in linea_de_punto]
        self.curva_actual = curva_actual = [(tabla[k // 2] if (k // 2 == indice and emitir == 1) else -13) for k in linea_de_punto]
        self.ancho_banda = ancho_banda = 18e6
        self.amp_tx = amp_tx = amp if emitir == 1 else 0

        ##################################################
        # Blocks
        ##################################################

        self.tono_superior = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, amp_tx, 0, 0)
        self.tono_inferior = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-f_tono), amp_tx, 0, 0)
        self.suma = blocks.add_vcc(1)
        self.ritmo_grafico = blocks.throttle( gr.sizeof_float*256, 2000, True, 0 if "time" == "auto" else max( int(float(0.01) * 2000) if "time" == "time" else int(0.01), 1) )
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
        self.grafico = qtgui.vector_sink_f(
            256,
            ((f_primera - f_tono) / 1e6 - 5),
            (10.0 / 7),
            "Frecuencia de la linea",
            "Correccion",
            "Correccion aplicada a cada linea",
            2, # Number of inputs
            None # parent
        )
        self.grafico.set_update_time(0.10)
        self.grafico.set_y_axis((-13), 1)
        self.grafico.enable_autoscale(False)
        self.grafico.enable_grid(True)
        self.grafico.set_x_axis_units("MHz")
        self.grafico.set_y_axis_units("dB")
        self.grafico.set_ref_level(0)


        labels = ["Correccion de cada linea", "Lineas que salen ahora", '', '', '',
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
        self.top_grid_layout.addWidget(self._grafico_win, 6, 0, 1, 9)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._ganancia_base_options = [0, 10, 20, 30, 40]
        # Create the labels list
        self._ganancia_base_labels = ['0 dB', '10 dB', '20 dB', '30 dB', '40 dB']
        # Create the combo box
        self._ganancia_base_tool_bar = Qt.QToolBar(self)
        self._ganancia_base_tool_bar.addWidget(Qt.QLabel("Ganancia de transmision antes de corregir" + ": "))
        self._ganancia_base_combo_box = Qt.QComboBox()
        self._ganancia_base_tool_bar.addWidget(self._ganancia_base_combo_box)
        for _label in self._ganancia_base_labels: self._ganancia_base_combo_box.addItem(_label)
        self._ganancia_base_callback = lambda i: Qt.QMetaObject.invokeMethod(self._ganancia_base_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._ganancia_base_options.index(i)))
        self._ganancia_base_callback(self.ganancia_base)
        self._ganancia_base_combo_box.currentIndexChanged.connect(
            lambda i: self.set_ganancia_base(self._ganancia_base_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._ganancia_base_tool_bar, 2, 3, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_titulo_tool_bar = Qt.QToolBar(self)

        if None:
            self._et_titulo_formatter = None
        else:
            self._et_titulo_formatter = lambda x: str(x)

        self._et_titulo_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'><b>Correccion por portadora, en dB.</b> Cada selector baja las dos lineas de su portadora</span>"))
        self._et_titulo_label = Qt.QLabel(str(self._et_titulo_formatter(self.et_titulo)))
        self._et_titulo_tool_bar.addWidget(self._et_titulo_label)
        self.top_grid_layout.addWidget(self._et_titulo_tool_bar, 3, 0, 1, 9)
        for r in range(3, 4):
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
        self._et_tabla_tool_bar = Qt.QToolBar(self)

        if None:
            self._et_tabla_formatter = None
        else:
            self._et_tabla_formatter = lambda x: str(x)

        self._et_tabla_tool_bar.addWidget(Qt.QLabel("Tabla actual (para copiar en tabla_inicial): "))
        self._et_tabla_label = Qt.QLabel(str(self._et_tabla_formatter(self.et_tabla)))
        self._et_tabla_tool_bar.addWidget(self._et_tabla_label)
        self.top_grid_layout.addWidget(self._et_tabla_tool_bar, 7, 0, 1, 9)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 9):
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

        self._et_nivel_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Nivel estimado por linea: </span>"))
        self._et_nivel_label = Qt.QLabel(str(self._et_nivel_formatter(self.et_nivel)))
        self._et_nivel_tool_bar.addWidget(self._et_nivel_label)
        self.top_grid_layout.addWidget(self._et_nivel_tool_bar, 1, 5, 1, 4)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 9):
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
        self._et_ganancia_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_ganancia_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_ganancia_formatter = lambda x: str(x)

        self._et_ganancia_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Ganancia aplicada: </span>"))
        self._et_ganancia_label = Qt.QLabel(str(self._et_ganancia_formatter(self.et_ganancia)))
        self._et_ganancia_tool_bar.addWidget(self._et_ganancia_label)
        self.top_grid_layout.addWidget(self._et_ganancia_tool_bar, 1, 0, 1, 5)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 5):
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
        _emitir_check_box = Qt.QCheckBox("Emitir (destildar para dejar la salida en silencio)")
        self._emitir_choices = {True: 1, False: 0}
        self._emitir_choices_inv = dict((v,k) for k,v in self._emitir_choices.items())
        self._emitir_callback = lambda i: Qt.QMetaObject.invokeMethod(_emitir_check_box, "setChecked", Qt.Q_ARG("bool", self._emitir_choices_inv[i]))
        self._emitir_callback(self.emitir)
        _emitir_check_box.stateChanged.connect(lambda i: self.set_emitir(self._emitir_choices[bool(i)]))
        self.top_grid_layout.addWidget(_emitir_check_box, 2, 0, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.datos_tabla = blocks.vector_source_f(curva_tabla, True, 256, [])
        self.datos_actual = blocks.vector_source_f(curva_actual, True, 256, [])
        # Create the options list
        self._c_95_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_95_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_95_tool_bar = Qt.QToolBar(self)
        self._c_95_tool_bar.addWidget(Qt.QLabel("90-100" + ": "))
        self._c_95_combo_box = Qt.QComboBox()
        self._c_95_tool_bar.addWidget(self._c_95_combo_box)
        for _label in self._c_95_labels: self._c_95_combo_box.addItem(_label)
        self._c_95_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_95_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_95_options.index(i)))
        self._c_95_callback(self.c_95)
        self._c_95_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_95(self._c_95_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_95_tool_bar, 4, 1, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_75_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_75_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_75_tool_bar = Qt.QToolBar(self)
        self._c_75_tool_bar.addWidget(Qt.QLabel("70-80" + ": "))
        self._c_75_combo_box = Qt.QComboBox()
        self._c_75_tool_bar.addWidget(self._c_75_combo_box)
        for _label in self._c_75_labels: self._c_75_combo_box.addItem(_label)
        self._c_75_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_75_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_75_options.index(i)))
        self._c_75_callback(self.c_75)
        self._c_75_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_75(self._c_75_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_75_tool_bar, 4, 0, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_415_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_415_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_415_tool_bar = Qt.QToolBar(self)
        self._c_415_tool_bar.addWidget(Qt.QLabel("410-420" + ": "))
        self._c_415_combo_box = Qt.QComboBox()
        self._c_415_tool_bar.addWidget(self._c_415_combo_box)
        for _label in self._c_415_labels: self._c_415_combo_box.addItem(_label)
        self._c_415_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_415_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_415_options.index(i)))
        self._c_415_callback(self.c_415)
        self._c_415_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_415(self._c_415_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_415_tool_bar, 5, 8, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_395_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_395_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_395_tool_bar = Qt.QToolBar(self)
        self._c_395_tool_bar.addWidget(Qt.QLabel("390-400" + ": "))
        self._c_395_combo_box = Qt.QComboBox()
        self._c_395_tool_bar.addWidget(self._c_395_combo_box)
        for _label in self._c_395_labels: self._c_395_combo_box.addItem(_label)
        self._c_395_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_395_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_395_options.index(i)))
        self._c_395_callback(self.c_395)
        self._c_395_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_395(self._c_395_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_395_tool_bar, 5, 7, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_375_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_375_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_375_tool_bar = Qt.QToolBar(self)
        self._c_375_tool_bar.addWidget(Qt.QLabel("370-380" + ": "))
        self._c_375_combo_box = Qt.QComboBox()
        self._c_375_tool_bar.addWidget(self._c_375_combo_box)
        for _label in self._c_375_labels: self._c_375_combo_box.addItem(_label)
        self._c_375_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_375_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_375_options.index(i)))
        self._c_375_callback(self.c_375)
        self._c_375_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_375(self._c_375_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_375_tool_bar, 5, 6, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_355_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_355_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_355_tool_bar = Qt.QToolBar(self)
        self._c_355_tool_bar.addWidget(Qt.QLabel("350-360" + ": "))
        self._c_355_combo_box = Qt.QComboBox()
        self._c_355_tool_bar.addWidget(self._c_355_combo_box)
        for _label in self._c_355_labels: self._c_355_combo_box.addItem(_label)
        self._c_355_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_355_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_355_options.index(i)))
        self._c_355_callback(self.c_355)
        self._c_355_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_355(self._c_355_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_355_tool_bar, 5, 5, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_335_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_335_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_335_tool_bar = Qt.QToolBar(self)
        self._c_335_tool_bar.addWidget(Qt.QLabel("330-340" + ": "))
        self._c_335_combo_box = Qt.QComboBox()
        self._c_335_tool_bar.addWidget(self._c_335_combo_box)
        for _label in self._c_335_labels: self._c_335_combo_box.addItem(_label)
        self._c_335_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_335_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_335_options.index(i)))
        self._c_335_callback(self.c_335)
        self._c_335_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_335(self._c_335_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_335_tool_bar, 5, 4, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_315_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_315_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_315_tool_bar = Qt.QToolBar(self)
        self._c_315_tool_bar.addWidget(Qt.QLabel("310-320" + ": "))
        self._c_315_combo_box = Qt.QComboBox()
        self._c_315_tool_bar.addWidget(self._c_315_combo_box)
        for _label in self._c_315_labels: self._c_315_combo_box.addItem(_label)
        self._c_315_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_315_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_315_options.index(i)))
        self._c_315_callback(self.c_315)
        self._c_315_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_315(self._c_315_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_315_tool_bar, 5, 3, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_295_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_295_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_295_tool_bar = Qt.QToolBar(self)
        self._c_295_tool_bar.addWidget(Qt.QLabel("290-300" + ": "))
        self._c_295_combo_box = Qt.QComboBox()
        self._c_295_tool_bar.addWidget(self._c_295_combo_box)
        for _label in self._c_295_labels: self._c_295_combo_box.addItem(_label)
        self._c_295_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_295_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_295_options.index(i)))
        self._c_295_callback(self.c_295)
        self._c_295_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_295(self._c_295_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_295_tool_bar, 5, 2, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_275_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_275_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_275_tool_bar = Qt.QToolBar(self)
        self._c_275_tool_bar.addWidget(Qt.QLabel("270-280" + ": "))
        self._c_275_combo_box = Qt.QComboBox()
        self._c_275_tool_bar.addWidget(self._c_275_combo_box)
        for _label in self._c_275_labels: self._c_275_combo_box.addItem(_label)
        self._c_275_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_275_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_275_options.index(i)))
        self._c_275_callback(self.c_275)
        self._c_275_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_275(self._c_275_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_275_tool_bar, 5, 1, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_255_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_255_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_255_tool_bar = Qt.QToolBar(self)
        self._c_255_tool_bar.addWidget(Qt.QLabel("250-260" + ": "))
        self._c_255_combo_box = Qt.QComboBox()
        self._c_255_tool_bar.addWidget(self._c_255_combo_box)
        for _label in self._c_255_labels: self._c_255_combo_box.addItem(_label)
        self._c_255_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_255_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_255_options.index(i)))
        self._c_255_callback(self.c_255)
        self._c_255_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_255(self._c_255_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_255_tool_bar, 5, 0, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_235_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_235_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_235_tool_bar = Qt.QToolBar(self)
        self._c_235_tool_bar.addWidget(Qt.QLabel("230-240" + ": "))
        self._c_235_combo_box = Qt.QComboBox()
        self._c_235_tool_bar.addWidget(self._c_235_combo_box)
        for _label in self._c_235_labels: self._c_235_combo_box.addItem(_label)
        self._c_235_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_235_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_235_options.index(i)))
        self._c_235_callback(self.c_235)
        self._c_235_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_235(self._c_235_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_235_tool_bar, 4, 8, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_215_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_215_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_215_tool_bar = Qt.QToolBar(self)
        self._c_215_tool_bar.addWidget(Qt.QLabel("210-220" + ": "))
        self._c_215_combo_box = Qt.QComboBox()
        self._c_215_tool_bar.addWidget(self._c_215_combo_box)
        for _label in self._c_215_labels: self._c_215_combo_box.addItem(_label)
        self._c_215_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_215_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_215_options.index(i)))
        self._c_215_callback(self.c_215)
        self._c_215_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_215(self._c_215_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_215_tool_bar, 4, 7, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_195_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_195_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_195_tool_bar = Qt.QToolBar(self)
        self._c_195_tool_bar.addWidget(Qt.QLabel("190-200" + ": "))
        self._c_195_combo_box = Qt.QComboBox()
        self._c_195_tool_bar.addWidget(self._c_195_combo_box)
        for _label in self._c_195_labels: self._c_195_combo_box.addItem(_label)
        self._c_195_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_195_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_195_options.index(i)))
        self._c_195_callback(self.c_195)
        self._c_195_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_195(self._c_195_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_195_tool_bar, 4, 6, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_175_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_175_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_175_tool_bar = Qt.QToolBar(self)
        self._c_175_tool_bar.addWidget(Qt.QLabel("170-180" + ": "))
        self._c_175_combo_box = Qt.QComboBox()
        self._c_175_tool_bar.addWidget(self._c_175_combo_box)
        for _label in self._c_175_labels: self._c_175_combo_box.addItem(_label)
        self._c_175_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_175_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_175_options.index(i)))
        self._c_175_callback(self.c_175)
        self._c_175_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_175(self._c_175_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_175_tool_bar, 4, 5, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_155_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_155_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_155_tool_bar = Qt.QToolBar(self)
        self._c_155_tool_bar.addWidget(Qt.QLabel("150-160" + ": "))
        self._c_155_combo_box = Qt.QComboBox()
        self._c_155_tool_bar.addWidget(self._c_155_combo_box)
        for _label in self._c_155_labels: self._c_155_combo_box.addItem(_label)
        self._c_155_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_155_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_155_options.index(i)))
        self._c_155_callback(self.c_155)
        self._c_155_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_155(self._c_155_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_155_tool_bar, 4, 4, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_135_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_135_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_135_tool_bar = Qt.QToolBar(self)
        self._c_135_tool_bar.addWidget(Qt.QLabel("130-140" + ": "))
        self._c_135_combo_box = Qt.QComboBox()
        self._c_135_tool_bar.addWidget(self._c_135_combo_box)
        for _label in self._c_135_labels: self._c_135_combo_box.addItem(_label)
        self._c_135_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_135_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_135_options.index(i)))
        self._c_135_callback(self.c_135)
        self._c_135_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_135(self._c_135_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_135_tool_bar, 4, 3, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._c_115_options = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12]
        # Create the labels list
        self._c_115_labels = ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12']
        # Create the combo box
        self._c_115_tool_bar = Qt.QToolBar(self)
        self._c_115_tool_bar.addWidget(Qt.QLabel("110-120" + ": "))
        self._c_115_combo_box = Qt.QComboBox()
        self._c_115_tool_bar.addWidget(self._c_115_combo_box)
        for _label in self._c_115_labels: self._c_115_combo_box.addItem(_label)
        self._c_115_callback = lambda i: Qt.QMetaObject.invokeMethod(self._c_115_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._c_115_options.index(i)))
        self._c_115_callback(self.c_115)
        self._c_115_combo_box.currentIndexChanged.connect(
            lambda i: self.set_c_115(self._c_115_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._c_115_tool_bar, 4, 2, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.datos_actual, 0), (self.grafico, 1))
        self.connect((self.datos_tabla, 0), (self.ritmo_grafico, 0))
        self.connect((self.ritmo_grafico, 0), (self.grafico, 0))
        self.connect((self.suma, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.tono_inferior, 0), (self.suma, 1))
        self.connect((self.tono_superior, 0), (self.suma, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp17_a9_peine_manual")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_tabla_inicial(self):
        return self.tabla_inicial

    def set_tabla_inicial(self, tabla_inicial):
        self.tabla_inicial = tabla_inicial
        self.set_c_75(self.tabla_inicial[0])
        self.set_c_95(self.tabla_inicial[1])
        self.set_c_115(self.tabla_inicial[2])
        self.set_c_135(self.tabla_inicial[3])
        self.set_c_155(self.tabla_inicial[4])
        self.set_c_175(self.tabla_inicial[5])
        self.set_c_195(self.tabla_inicial[6])
        self.set_c_215(self.tabla_inicial[7])
        self.set_c_235(self.tabla_inicial[8])
        self.set_c_255(self.tabla_inicial[9])
        self.set_c_275(self.tabla_inicial[10])
        self.set_c_295(self.tabla_inicial[11])
        self.set_c_315(self.tabla_inicial[12])
        self.set_c_335(self.tabla_inicial[13])
        self.set_c_355(self.tabla_inicial[14])
        self.set_c_375(self.tabla_inicial[15])
        self.set_c_395(self.tabla_inicial[16])
        self.set_c_415(self.tabla_inicial[17])

    def get_paso(self):
        return self.paso

    def set_paso(self, paso):
        self.paso = paso
        self.set_indice(max(self.paso, 0) % self.n_port)
        self.set_pasada(max(self.paso, 0) // self.n_port + 1)
        self.set_etapa('SILENCIO' if self.emitir == 0 else ('INICIACION' if self.paso < 0 else 'TRANSMISION, pasada %d' % self.pasada))

    def get_n_port(self):
        return self.n_port

    def set_n_port(self, n_port):
        self.n_port = n_port
        self.set_indice(max(self.paso, 0) % self.n_port)
        self.set_pasada(max(self.paso, 0) // self.n_port + 1)
        self.set_et_portadora('%d de %d, en %.0f MHz' % (self.indice + 1, self.n_port, self.freq / 1e6))
        self.set_et_tiempos('%.0f s (%.1f s por portadora)' % (self.permanencia * self.n_port, self.permanencia))
        self.set_linea_de_punto([min(j // 7, 2 * self.n_port - 1) for j in range(256)])

    def get_c_95(self):
        return self.c_95

    def set_c_95(self, c_95):
        self.c_95 = c_95
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_95_callback(self.c_95)

    def get_c_75(self):
        return self.c_75

    def set_c_75(self, c_75):
        self.c_75 = c_75
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_75_callback(self.c_75)

    def get_c_415(self):
        return self.c_415

    def set_c_415(self, c_415):
        self.c_415 = c_415
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_415_callback(self.c_415)

    def get_c_395(self):
        return self.c_395

    def set_c_395(self, c_395):
        self.c_395 = c_395
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_395_callback(self.c_395)

    def get_c_375(self):
        return self.c_375

    def set_c_375(self, c_375):
        self.c_375 = c_375
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_375_callback(self.c_375)

    def get_c_355(self):
        return self.c_355

    def set_c_355(self, c_355):
        self.c_355 = c_355
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_355_callback(self.c_355)

    def get_c_335(self):
        return self.c_335

    def set_c_335(self, c_335):
        self.c_335 = c_335
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_335_callback(self.c_335)

    def get_c_315(self):
        return self.c_315

    def set_c_315(self, c_315):
        self.c_315 = c_315
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_315_callback(self.c_315)

    def get_c_295(self):
        return self.c_295

    def set_c_295(self, c_295):
        self.c_295 = c_295
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_295_callback(self.c_295)

    def get_c_275(self):
        return self.c_275

    def set_c_275(self, c_275):
        self.c_275 = c_275
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_275_callback(self.c_275)

    def get_c_255(self):
        return self.c_255

    def set_c_255(self, c_255):
        self.c_255 = c_255
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_255_callback(self.c_255)

    def get_c_235(self):
        return self.c_235

    def set_c_235(self, c_235):
        self.c_235 = c_235
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_235_callback(self.c_235)

    def get_c_215(self):
        return self.c_215

    def set_c_215(self, c_215):
        self.c_215 = c_215
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_215_callback(self.c_215)

    def get_c_195(self):
        return self.c_195

    def set_c_195(self, c_195):
        self.c_195 = c_195
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_195_callback(self.c_195)

    def get_c_175(self):
        return self.c_175

    def set_c_175(self, c_175):
        self.c_175 = c_175
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_175_callback(self.c_175)

    def get_c_155(self):
        return self.c_155

    def set_c_155(self, c_155):
        self.c_155 = c_155
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_155_callback(self.c_155)

    def get_c_135(self):
        return self.c_135

    def set_c_135(self, c_135):
        self.c_135 = c_135
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_135_callback(self.c_135)

    def get_c_115(self):
        return self.c_115

    def set_c_115(self, c_115):
        self.c_115 = c_115
        self.set_tabla([self.c_75, self.c_95, self.c_115, self.c_135, self.c_155, self.c_175, self.c_195, self.c_215, self.c_235, self.c_255, self.c_275, self.c_295, self.c_315, self.c_335, self.c_355, self.c_375, self.c_395, self.c_415])
        self._c_115_callback(self.c_115)

    def get_tabla(self):
        return self.tabla

    def set_tabla(self, tabla):
        self.tabla = tabla
        self.set_correccion(self.tabla[self.indice])
        self.set_et_tabla(str(self.tabla))
        self.set_curva_tabla([self.tabla[k // 2] for k in self.linea_de_punto])
        self.set_curva_actual([(self.tabla[k // 2] if (k // 2 == self.indice and self.emitir == 1) else -13) for k in self.linea_de_punto])

    def get_indice(self):
        return self.indice

    def set_indice(self, indice):
        self.indice = indice
        self.set_freq(self.f_primera + self.paso_port * self.indice)
        self.set_correccion(self.tabla[self.indice])
        self.set_et_portadora('%d de %d, en %.0f MHz' % (self.indice + 1, self.n_port, self.freq / 1e6))
        self.set_curva_actual([(self.tabla[k // 2] if (k // 2 == self.indice and self.emitir == 1) else -13) for k in self.linea_de_punto])

    def get_tope(self):
        return self.tope

    def set_tope(self, tope):
        self.tope = tope
        self.set_tx_gain(min(self.ganancia_base + self.correccion, self.tope))

    def get_ganancia_base(self):
        return self.ganancia_base

    def set_ganancia_base(self, ganancia_base):
        self.ganancia_base = ganancia_base
        self._ganancia_base_callback(self.ganancia_base)
        self.set_tx_gain(min(self.ganancia_base + self.correccion, self.tope))
        self.set_et_ganancia('%d dB (base %d, correccion %d)' % (self.tx_gain, self.ganancia_base, self.correccion))

    def get_correccion(self):
        return self.correccion

    def set_correccion(self, correccion):
        self.correccion = correccion
        self.set_tx_gain(min(self.ganancia_base + self.correccion, self.tope))
        self.set_et_ganancia('%d dB (base %d, correccion %d)' % (self.tx_gain, self.ganancia_base, self.correccion))

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.set_nivel_estimado(self.tx_gain - 60 + 20 * math.log10(self.amp))
        self.set_et_ganancia('%d dB (base %d, correccion %d)' % (self.tx_gain, self.ganancia_base, self.correccion))
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)

    def get_paso_port(self):
        return self.paso_port

    def set_paso_port(self, paso_port):
        self.paso_port = paso_port
        self.set_freq(self.f_primera + self.paso_port * self.indice)

    def get_pasada(self):
        return self.pasada

    def set_pasada(self, pasada):
        self.pasada = pasada
        self.set_etapa('SILENCIO' if self.emitir == 0 else ('INICIACION' if self.paso < 0 else 'TRANSMISION, pasada %d' % self.pasada))

    def get_f_primera(self):
        return self.f_primera

    def set_f_primera(self, f_primera):
        self.f_primera = f_primera
        self.set_freq(self.f_primera + self.paso_port * self.indice)
        self.grafico.set_x_axis(((self.f_primera - self.f_tono) / 1e6 - 5), (10.0 / 7))

    def get_emitir(self):
        return self.emitir

    def set_emitir(self, emitir):
        self.emitir = emitir
        self._emitir_callback(self.emitir)
        self.set_amp_tx(self.amp if self.emitir == 1 else 0)
        self.set_etapa('SILENCIO' if self.emitir == 0 else ('INICIACION' if self.paso < 0 else 'TRANSMISION, pasada %d' % self.pasada))
        self.set_et_nivel(('%.0f dBm' % self.nivel_estimado) if self.emitir == 1 else 'sin emision')
        self.set_curva_actual([(self.tabla[k // 2] if (k // 2 == self.indice and self.emitir == 1) else -13) for k in self.linea_de_punto])

    def get_amp(self):
        return self.amp

    def set_amp(self, amp):
        self.amp = amp
        self.set_amp_tx(self.amp if self.emitir == 1 else 0)
        self.set_nivel_estimado(self.tx_gain - 60 + 20 * math.log10(self.amp))

    def get_permanencia(self):
        return self.permanencia

    def set_permanencia(self, permanencia):
        self.permanencia = permanencia
        self.set_et_tiempos('%.0f s (%.1f s por portadora)' % (self.permanencia * self.n_port, self.permanencia))

    def get_nivel_estimado(self):
        return self.nivel_estimado

    def set_nivel_estimado(self, nivel_estimado):
        self.nivel_estimado = nivel_estimado
        self.set_et_nivel(('%.0f dBm' % self.nivel_estimado) if self.emitir == 1 else 'sin emision')

    def get_linea_de_punto(self):
        return self.linea_de_punto

    def set_linea_de_punto(self, linea_de_punto):
        self.linea_de_punto = linea_de_punto
        self.set_curva_tabla([self.tabla[k // 2] for k in self.linea_de_punto])
        self.set_curva_actual([(self.tabla[k // 2] if (k // 2 == self.indice and self.emitir == 1) else -13) for k in self.linea_de_punto])

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_et_portadora('%d de %d, en %.0f MHz' % (self.indice + 1, self.n_port, self.freq / 1e6))
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

    def get_et_tabla(self):
        return self.et_tabla

    def set_et_tabla(self, et_tabla):
        self.et_tabla = et_tabla
        Qt.QMetaObject.invokeMethod(self._et_tabla_label, "setText", Qt.Q_ARG("QString", str(self._et_tabla_formatter(self.et_tabla))))

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

    def get_et_lineas(self):
        return self.et_lineas

    def set_et_lineas(self, et_lineas):
        self.et_lineas = et_lineas
        Qt.QMetaObject.invokeMethod(self._et_lineas_label, "setText", Qt.Q_ARG("QString", str(self._et_lineas_formatter(self.et_lineas))))

    def get_et_ganancia(self):
        return self.et_ganancia

    def set_et_ganancia(self, et_ganancia):
        self.et_ganancia = et_ganancia
        Qt.QMetaObject.invokeMethod(self._et_ganancia_label, "setText", Qt.Q_ARG("QString", str(self._et_ganancia_formatter(self.et_ganancia))))

    def get_et_etapa(self):
        return self.et_etapa

    def set_et_etapa(self, et_etapa):
        self.et_etapa = et_etapa
        Qt.QMetaObject.invokeMethod(self._et_etapa_label, "setText", Qt.Q_ARG("QString", str(self._et_etapa_formatter(self.et_etapa))))

    def get_curva_tabla(self):
        return self.curva_tabla

    def set_curva_tabla(self, curva_tabla):
        self.curva_tabla = curva_tabla
        self.datos_tabla.set_data(self.curva_tabla, [])

    def get_curva_actual(self):
        return self.curva_actual

    def set_curva_actual(self, curva_actual):
        self.curva_actual = curva_actual
        self.datos_actual.set_data(self.curva_actual, [])

    def get_ancho_banda(self):
        return self.ancho_banda

    def set_ancho_banda(self, ancho_banda):
        self.ancho_banda = ancho_banda
        self.osmosdr_sink_0.set_bandwidth(self.ancho_banda, 0)

    def get_amp_tx(self):
        return self.amp_tx

    def set_amp_tx(self, amp_tx):
        self.amp_tx = amp_tx
        self.tono_superior.set_amplitude(self.amp_tx)
        self.tono_inferior.set_amplitude(self.amp_tx)




def main(top_block_cls=exp17_a9_peine_manual, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

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
