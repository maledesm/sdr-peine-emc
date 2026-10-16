#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-18 xA9: lazo TX1 a RX1 en una portadora
# Description: bladeRF 2.0 micro xA9: transmite dos tonos en +/-5 MHz y los mide con su propio receptor, conectado por cable. Sirve para elegir niveles seguros y ver si el receptor sigue al transmisor. Sin codigo Python
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
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



class exp18_a9_lazo_tx_rx(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-18 xA9: lazo TX1 a RX1 en una portadora", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-18 xA9: lazo TX1 a RX1 en una portadora")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp18_a9_lazo_tx_rx")

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
        self.tope = tope = 30
        self.nivel_sup = nivel_sup = -120
        self.nivel_inf = nivel_inf = -120
        self.ganancia_tx = ganancia_tx = 0
        self.tx_gain = tx_gain = min(ganancia_tx, tope)
        self.portadora = portadora = 75
        self.nivel_mayor = nivel_mayor = max(nivel_inf, nivel_sup)
        self.amp = amp = 0.45
        self.samp_rate = samp_rate = 20e6
        self.nivel_estimado = nivel_estimado = tx_gain - 56 + 20 * math.log10(amp)
        self.freq = freq = portadora * 1e6
        self.f_tono = f_tono = 5e6
        self.estado = estado = 'SIN SENAL' if nivel_mayor < -75 else ('BAJO: se puede subir la ganancia de RX' if nivel_mayor < -30 else ('BIEN' if nivel_mayor < -12 else 'ALTO: bajar la ganancia de RX'))
        self.taps = taps = firdes.low_pass(1.0, samp_rate, 100e3, 400e3, window.WIN_HAMMING, 6.76)
        self.rx_gain = rx_gain = 0
        self.largo_promedio = largo_promedio = 100000
        self.hab_sup = hab_sup = 1
        self.hab_inf = hab_inf = 1
        self.et_tx = et_tx = '%.0f y %.0f MHz, ganancia %d dB, unos %.0f dBm por tono' % ((freq - f_tono) / 1e6, (freq + f_tono) / 1e6, tx_gain, nivel_estimado)
        self.et_sup = et_sup = nivel_sup
        self.et_inf = et_inf = nivel_inf
        self.et_estado = et_estado = estado
        self.et_dif = et_dif = (nivel_sup - nivel_inf)
        self.decim = decim = int(samp_rate / 1e6)
        self.ancho_banda = ancho_banda = 18e6

        ##################################################
        # Blocks
        ##################################################

        self.sonda_sup = blocks.probe_signal_f()
        self.sonda_inf = blocks.probe_signal_f()
        # Create the options list
        self._rx_gain_options = [0, 10, 20, 30, 40, 50, 60]
        # Create the labels list
        self._rx_gain_labels = ['0 dB', '10 dB', '20 dB', '30 dB', '40 dB', '50 dB', '60 dB']
        # Create the combo box
        self._rx_gain_tool_bar = Qt.QToolBar(self)
        self._rx_gain_tool_bar.addWidget(Qt.QLabel("Ganancia de RX" + ": "))
        self._rx_gain_combo_box = Qt.QComboBox()
        self._rx_gain_tool_bar.addWidget(self._rx_gain_combo_box)
        for _label in self._rx_gain_labels: self._rx_gain_combo_box.addItem(_label)
        self._rx_gain_callback = lambda i: Qt.QMetaObject.invokeMethod(self._rx_gain_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._rx_gain_options.index(i)))
        self._rx_gain_callback(self.rx_gain)
        self._rx_gain_combo_box.currentIndexChanged.connect(
            lambda i: self.set_rx_gain(self._rx_gain_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._rx_gain_tool_bar, 2, 2, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_sup_check_box = Qt.QCheckBox("Tono superior")
        self._hab_sup_choices = {True: 1, False: 0}
        self._hab_sup_choices_inv = dict((v,k) for k,v in self._hab_sup_choices.items())
        self._hab_sup_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_sup_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_sup_choices_inv[i]))
        self._hab_sup_callback(self.hab_sup)
        _hab_sup_check_box.stateChanged.connect(lambda i: self.set_hab_sup(self._hab_sup_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_sup_check_box, 2, 1, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_inf_check_box = Qt.QCheckBox("Tono inferior")
        self._hab_inf_choices = {True: 1, False: 0}
        self._hab_inf_choices_inv = dict((v,k) for k,v in self._hab_inf_choices.items())
        self._hab_inf_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_inf_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_inf_choices_inv[i]))
        self._hab_inf_callback(self.hab_inf)
        _hab_inf_check_box.stateChanged.connect(lambda i: self.set_hab_inf(self._hab_inf_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_inf_check_box, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_options = [0.05, 0.1, 0.2, 0.45]
        # Create the labels list
        self._amp_labels = ['0.05', '0.1', '0.2', '0.45']
        # Create the combo box
        self._amp_tool_bar = Qt.QToolBar(self)
        self._amp_tool_bar.addWidget(Qt.QLabel("Amplitud de cada tono" + ": "))
        self._amp_combo_box = Qt.QComboBox()
        self._amp_tool_bar.addWidget(self._amp_combo_box)
        for _label in self._amp_labels: self._amp_combo_box.addItem(_label)
        self._amp_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_options.index(i)))
        self._amp_callback(self.amp)
        self._amp_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp(self._amp_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_tool_bar, 1, 4, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.tono_superior = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, (amp * hab_sup), 0, 0)
        self.tono_inferior = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-f_tono), (amp * hab_inf), 0, 0)
        self.suma = blocks.add_vcc(1)
        self.promedio_sup = blocks.moving_average_ff(largo_promedio, (1.0 / largo_promedio), 4000, 1)
        self.promedio_inf = blocks.moving_average_ff(largo_promedio, (1.0 / largo_promedio), 4000, 1)
        self.potencia_sup = blocks.complex_to_mag_squared(1)
        self.potencia_inf = blocks.complex_to_mag_squared(1)
        # Create the options list
        self._portadora_options = [75, 135, 195, 255, 315, 335, 415]
        # Create the labels list
        self._portadora_labels = ['75 MHz', '135 MHz', '195 MHz', '255 MHz', '315 MHz', '335 MHz', '415 MHz']
        # Create the combo box
        self._portadora_tool_bar = Qt.QToolBar(self)
        self._portadora_tool_bar.addWidget(Qt.QLabel("Portadora" + ": "))
        self._portadora_combo_box = Qt.QComboBox()
        self._portadora_tool_bar.addWidget(self._portadora_combo_box)
        for _label in self._portadora_labels: self._portadora_combo_box.addItem(_label)
        self._portadora_callback = lambda i: Qt.QMetaObject.invokeMethod(self._portadora_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._portadora_options.index(i)))
        self._portadora_callback(self.portadora)
        self._portadora_combo_box.currentIndexChanged.connect(
            lambda i: self.set_portadora(self._portadora_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._portadora_tool_bar, 1, 0, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.osmosdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + 'bladerf=321e0fa5875945d99b11070bb0a76d31'
        )
        self.osmosdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(freq, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(rx_gain, 0)
        self.osmosdr_source_0.set_if_gain(0, 0)
        self.osmosdr_source_0.set_bb_gain(0, 0)
        self.osmosdr_source_0.set_antenna('', 0)
        self.osmosdr_source_0.set_bandwidth(ancho_banda, 0)
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
        def _nivel_sup_probe():
          self.flowgraph_started.wait()
          while True:

            val = self.sonda_sup.level()
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_nivel_sup,val))
              except AttributeError:
                self.set_nivel_sup(val)
            except AttributeError:
              pass
            time.sleep(1.0 / (5))
        _nivel_sup_thread = threading.Thread(target=_nivel_sup_probe)
        _nivel_sup_thread.daemon = True
        _nivel_sup_thread.start()
        def _nivel_inf_probe():
          self.flowgraph_started.wait()
          while True:

            val = self.sonda_inf.level()
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_nivel_inf,val))
              except AttributeError:
                self.set_nivel_inf(val)
            except AttributeError:
              pass
            time.sleep(1.0 / (5))
        _nivel_inf_thread = threading.Thread(target=_nivel_inf_probe)
        _nivel_inf_thread.daemon = True
        _nivel_inf_thread.start()
        # Create the options list
        self._ganancia_tx_options = [0, 10, 20, 30]
        # Create the labels list
        self._ganancia_tx_labels = ['0 dB', '10 dB', '20 dB', '30 dB']
        # Create the combo box
        self._ganancia_tx_tool_bar = Qt.QToolBar(self)
        self._ganancia_tx_tool_bar.addWidget(Qt.QLabel("Ganancia de TX" + ": "))
        self._ganancia_tx_combo_box = Qt.QComboBox()
        self._ganancia_tx_tool_bar.addWidget(self._ganancia_tx_combo_box)
        for _label in self._ganancia_tx_labels: self._ganancia_tx_combo_box.addItem(_label)
        self._ganancia_tx_callback = lambda i: Qt.QMetaObject.invokeMethod(self._ganancia_tx_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._ganancia_tx_options.index(i)))
        self._ganancia_tx_callback(self.ganancia_tx)
        self._ganancia_tx_combo_box.currentIndexChanged.connect(
            lambda i: self.set_ganancia_tx(self._ganancia_tx_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._ganancia_tx_tool_bar, 1, 2, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.filtro_sup = filter.freq_xlating_fir_filter_ccf(decim, taps, f_tono, samp_rate)
        self.filtro_inf = filter.freq_xlating_fir_filter_ccf(decim, taps, (-f_tono), samp_rate)
        self._et_tx_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:13pt'><b>" + str(x) + "</b></span>":
            self._et_tx_formatter = lambda x: "<span style='font-size:13pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_tx_formatter = lambda x: str(x)

        self._et_tx_tool_bar.addWidget(Qt.QLabel("<span style='font-size:13pt'>Transmite: </span>"))
        self._et_tx_label = Qt.QLabel(str(self._et_tx_formatter(self.et_tx)))
        self._et_tx_tool_bar.addWidget(self._et_tx_label)
        self.top_grid_layout.addWidget(self._et_tx_tool_bar, 0, 0, 1, 6)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_sup_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>%.1f dB</b></span>" % x:
            self._et_sup_formatter = lambda x: "<span style='font-size:15pt'><b>%.1f dB</b></span>" % x
        else:
            self._et_sup_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_sup_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>RX superior: </span>"))
        self._et_sup_label = Qt.QLabel(str(self._et_sup_formatter(self.et_sup)))
        self._et_sup_tool_bar.addWidget(self._et_sup_label)
        self.top_grid_layout.addWidget(self._et_sup_tool_bar, 3, 2, 1, 2)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_inf_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>%.1f dB</b></span>" % x:
            self._et_inf_formatter = lambda x: "<span style='font-size:15pt'><b>%.1f dB</b></span>" % x
        else:
            self._et_inf_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_inf_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>RX inferior: </span>"))
        self._et_inf_label = Qt.QLabel(str(self._et_inf_formatter(self.et_inf)))
        self._et_inf_tool_bar.addWidget(self._et_inf_label)
        self.top_grid_layout.addWidget(self._et_inf_tool_bar, 3, 0, 1, 2)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_estado_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:13pt'><b>" + str(x) + "</b></span>":
            self._et_estado_formatter = lambda x: "<span style='font-size:13pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_estado_formatter = lambda x: str(x)

        self._et_estado_tool_bar.addWidget(Qt.QLabel("<span style='font-size:13pt'>Receptor: </span>"))
        self._et_estado_label = Qt.QLabel(str(self._et_estado_formatter(self.et_estado)))
        self._et_estado_tool_bar.addWidget(self._et_estado_label)
        self.top_grid_layout.addWidget(self._et_estado_tool_bar, 4, 0, 1, 6)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_dif_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>%+.1f dB</b></span>" % x:
            self._et_dif_formatter = lambda x: "<span style='font-size:15pt'><b>%+.1f dB</b></span>" % x
        else:
            self._et_dif_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_dif_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Superior - inferior: </span>"))
        self._et_dif_label = Qt.QLabel(str(self._et_dif_formatter(self.et_dif)))
        self._et_dif_tool_bar.addWidget(self._et_dif_label)
        self.top_grid_layout.addWidget(self._et_dif_tool_bar, 3, 4, 1, 2)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.espectro = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            freq, #fc
            samp_rate, #bw
            "Lo que recibe RX1 (para ver la forma; los niveles que valen son los de arriba)", #name
            1,
            None # parent
        )
        self.espectro.set_update_time(0.20)
        self.espectro.set_y_axis((-120), 0)
        self.espectro.set_y_label('Nivel', 'dB')
        self.espectro.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.espectro.enable_autoscale(False)
        self.espectro.enable_grid(True)
        self.espectro.set_fft_average(0.2)
        self.espectro.enable_axis_labels(True)
        self.espectro.enable_control_panel(False)
        self.espectro.set_fft_window_normalized(False)

        self.espectro.disable_legend()


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.espectro.set_line_label(i, "Data {0}".format(i))
            else:
                self.espectro.set_line_label(i, labels[i])
            self.espectro.set_line_width(i, widths[i])
            self.espectro.set_line_color(i, colors[i])
            self.espectro.set_line_alpha(i, alphas[i])

        self._espectro_win = sip.wrapinstance(self.espectro.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._espectro_win, 5, 0, 1, 6)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.a_db_sup = blocks.nlog10_ff(10, 1, 0)
        self.a_db_inf = blocks.nlog10_ff(10, 1, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.a_db_inf, 0), (self.sonda_inf, 0))
        self.connect((self.a_db_sup, 0), (self.sonda_sup, 0))
        self.connect((self.filtro_inf, 0), (self.potencia_inf, 0))
        self.connect((self.filtro_sup, 0), (self.potencia_sup, 0))
        self.connect((self.osmosdr_source_0, 0), (self.espectro, 0))
        self.connect((self.osmosdr_source_0, 0), (self.filtro_inf, 0))
        self.connect((self.osmosdr_source_0, 0), (self.filtro_sup, 0))
        self.connect((self.potencia_inf, 0), (self.promedio_inf, 0))
        self.connect((self.potencia_sup, 0), (self.promedio_sup, 0))
        self.connect((self.promedio_inf, 0), (self.a_db_inf, 0))
        self.connect((self.promedio_sup, 0), (self.a_db_sup, 0))
        self.connect((self.suma, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.tono_inferior, 0), (self.suma, 1))
        self.connect((self.tono_superior, 0), (self.suma, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp18_a9_lazo_tx_rx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_tope(self):
        return self.tope

    def set_tope(self, tope):
        self.tope = tope
        self.set_tx_gain(min(self.ganancia_tx, self.tope))

    def get_nivel_sup(self):
        return self.nivel_sup

    def set_nivel_sup(self, nivel_sup):
        self.nivel_sup = nivel_sup
        self.set_nivel_mayor(max(self.nivel_inf, self.nivel_sup))
        self.set_et_sup(self.nivel_sup)
        self.set_et_dif((self.nivel_sup - self.nivel_inf))

    def get_nivel_inf(self):
        return self.nivel_inf

    def set_nivel_inf(self, nivel_inf):
        self.nivel_inf = nivel_inf
        self.set_nivel_mayor(max(self.nivel_inf, self.nivel_sup))
        self.set_et_inf(self.nivel_inf)
        self.set_et_dif((self.nivel_sup - self.nivel_inf))

    def get_ganancia_tx(self):
        return self.ganancia_tx

    def set_ganancia_tx(self, ganancia_tx):
        self.ganancia_tx = ganancia_tx
        self._ganancia_tx_callback(self.ganancia_tx)
        self.set_tx_gain(min(self.ganancia_tx, self.tope))

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.set_nivel_estimado(self.tx_gain - 56 + 20 * math.log10(self.amp))
        self.set_et_tx('%.0f y %.0f MHz, ganancia %d dB, unos %.0f dBm por tono' % ((self.freq - self.f_tono) / 1e6, (self.freq + self.f_tono) / 1e6, self.tx_gain, self.nivel_estimado))
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)

    def get_portadora(self):
        return self.portadora

    def set_portadora(self, portadora):
        self.portadora = portadora
        self._portadora_callback(self.portadora)
        self.set_freq(self.portadora * 1e6)

    def get_nivel_mayor(self):
        return self.nivel_mayor

    def set_nivel_mayor(self, nivel_mayor):
        self.nivel_mayor = nivel_mayor
        self.set_estado('SIN SENAL' if self.nivel_mayor < -75 else ('BAJO: se puede subir la ganancia de RX' if self.nivel_mayor < -30 else ('BIEN' if self.nivel_mayor < -12 else 'ALTO: bajar la ganancia de RX')))

    def get_amp(self):
        return self.amp

    def set_amp(self, amp):
        self.amp = amp
        self._amp_callback(self.amp)
        self.set_nivel_estimado(self.tx_gain - 56 + 20 * math.log10(self.amp))
        self.tono_superior.set_amplitude((self.amp * self.hab_sup))
        self.tono_inferior.set_amplitude((self.amp * self.hab_inf))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_decim(int(self.samp_rate / 1e6))
        self.set_taps(firdes.low_pass(1.0, self.samp_rate, 100e3, 400e3, window.WIN_HAMMING, 6.76))
        self.tono_superior.set_sampling_freq(self.samp_rate)
        self.tono_inferior.set_sampling_freq(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)
        self.espectro.set_frequency_range(self.freq, self.samp_rate)

    def get_nivel_estimado(self):
        return self.nivel_estimado

    def set_nivel_estimado(self, nivel_estimado):
        self.nivel_estimado = nivel_estimado
        self.set_et_tx('%.0f y %.0f MHz, ganancia %d dB, unos %.0f dBm por tono' % ((self.freq - self.f_tono) / 1e6, (self.freq + self.f_tono) / 1e6, self.tx_gain, self.nivel_estimado))

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_et_tx('%.0f y %.0f MHz, ganancia %d dB, unos %.0f dBm por tono' % ((self.freq - self.f_tono) / 1e6, (self.freq + self.f_tono) / 1e6, self.tx_gain, self.nivel_estimado))
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)
        self.osmosdr_source_0.set_center_freq(self.freq, 0)
        self.espectro.set_frequency_range(self.freq, self.samp_rate)

    def get_f_tono(self):
        return self.f_tono

    def set_f_tono(self, f_tono):
        self.f_tono = f_tono
        self.set_et_tx('%.0f y %.0f MHz, ganancia %d dB, unos %.0f dBm por tono' % ((self.freq - self.f_tono) / 1e6, (self.freq + self.f_tono) / 1e6, self.tx_gain, self.nivel_estimado))
        self.tono_superior.set_frequency(self.f_tono)
        self.tono_inferior.set_frequency((-self.f_tono))
        self.filtro_sup.set_center_freq(self.f_tono)
        self.filtro_inf.set_center_freq((-self.f_tono))

    def get_estado(self):
        return self.estado

    def set_estado(self, estado):
        self.estado = estado
        self.set_et_estado(self.estado)

    def get_taps(self):
        return self.taps

    def set_taps(self, taps):
        self.taps = taps
        self.filtro_sup.set_taps(self.taps)
        self.filtro_inf.set_taps(self.taps)

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain
        self._rx_gain_callback(self.rx_gain)
        self.osmosdr_source_0.set_gain(self.rx_gain, 0)

    def get_largo_promedio(self):
        return self.largo_promedio

    def set_largo_promedio(self, largo_promedio):
        self.largo_promedio = largo_promedio
        self.promedio_sup.set_length_and_scale(self.largo_promedio, (1.0 / self.largo_promedio))
        self.promedio_inf.set_length_and_scale(self.largo_promedio, (1.0 / self.largo_promedio))

    def get_hab_sup(self):
        return self.hab_sup

    def set_hab_sup(self, hab_sup):
        self.hab_sup = hab_sup
        self._hab_sup_callback(self.hab_sup)
        self.tono_superior.set_amplitude((self.amp * self.hab_sup))

    def get_hab_inf(self):
        return self.hab_inf

    def set_hab_inf(self, hab_inf):
        self.hab_inf = hab_inf
        self._hab_inf_callback(self.hab_inf)
        self.tono_inferior.set_amplitude((self.amp * self.hab_inf))

    def get_et_tx(self):
        return self.et_tx

    def set_et_tx(self, et_tx):
        self.et_tx = et_tx
        Qt.QMetaObject.invokeMethod(self._et_tx_label, "setText", Qt.Q_ARG("QString", str(self._et_tx_formatter(self.et_tx))))

    def get_et_sup(self):
        return self.et_sup

    def set_et_sup(self, et_sup):
        self.et_sup = et_sup
        Qt.QMetaObject.invokeMethod(self._et_sup_label, "setText", Qt.Q_ARG("QString", str(self._et_sup_formatter(self.et_sup))))

    def get_et_inf(self):
        return self.et_inf

    def set_et_inf(self, et_inf):
        self.et_inf = et_inf
        Qt.QMetaObject.invokeMethod(self._et_inf_label, "setText", Qt.Q_ARG("QString", str(self._et_inf_formatter(self.et_inf))))

    def get_et_estado(self):
        return self.et_estado

    def set_et_estado(self, et_estado):
        self.et_estado = et_estado
        Qt.QMetaObject.invokeMethod(self._et_estado_label, "setText", Qt.Q_ARG("QString", str(self._et_estado_formatter(self.et_estado))))

    def get_et_dif(self):
        return self.et_dif

    def set_et_dif(self, et_dif):
        self.et_dif = et_dif
        Qt.QMetaObject.invokeMethod(self._et_dif_label, "setText", Qt.Q_ARG("QString", str(self._et_dif_formatter(self.et_dif))))

    def get_decim(self):
        return self.decim

    def set_decim(self, decim):
        self.decim = decim

    def get_ancho_banda(self):
        return self.ancho_banda

    def set_ancho_banda(self, ancho_banda):
        self.ancho_banda = ancho_banda
        self.osmosdr_sink_0.set_bandwidth(self.ancho_banda, 0)
        self.osmosdr_source_0.set_bandwidth(self.ancho_banda, 0)




def main(top_block_cls=exp18_a9_lazo_tx_rx, options=None):

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
