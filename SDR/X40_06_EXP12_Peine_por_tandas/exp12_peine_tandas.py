#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-12 peine por tandas 300 a 510 MHz
# Description: Peine por tandas: 11 portadoras de 305 a 505 MHz, dos tonos en +/-5 MHz por portadora. Barrido automatico con bloques estandar (Vector Source, Repeat, Throttle, Probe Signal, Function Probe)
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
import numpy as np
import osmosdr
import time
import threading



class exp12_peine_tandas(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-12 peine por tandas 300 a 510 MHz", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-12 peine por tandas 300 a 510 MHz")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp12_peine_tandas")

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
        self.indice_medido = indice_medido = 0
        self.portadoras = portadoras = [305e6 + 20e6*i for i in range(11)]
        self.portadora_manual = portadora_manual = 305000000
        self.modo = modo = 0
        self.indice = indice = min(max(int(round(indice_medido)), 0), 10)
        self.freq = freq = portadora_manual if modo == 1 else portadoras[indice]
        self.fase_inf = fase_inf = 0
        self.f_tono = f_tono = 5e6
        self.amp = amp = 0.4
        self.tx_gain = tx_gain = 17
        self.tasa_ctrl = tasa_ctrl = 10e3
        self.samp_rate = samp_rate = 20e6
        self.permanencia = permanencia = 2
        self.et_superior = et_superior = ((freq + f_tono) / 1e6)
        self.et_portadora = et_portadora = (freq / 1e6)
        self.et_pico = et_pico = (2 * amp)
        self.et_paso = et_paso = (indice + 1)
        self.et_inferior = et_inferior = ((freq - f_tono) / 1e6)
        self.c_inf = c_inf = np.exp(1j*np.deg2rad(fase_inf))

        ##################################################
        # Blocks
        ##################################################

        # Create the options list
        self._tx_gain_options = [17, 20, 25, 30]
        # Create the labels list
        self._tx_gain_labels = ['17', '20', '25', '30']
        # Create the combo box
        # Create the radio buttons
        self._tx_gain_group_box = Qt.QGroupBox("Ganancia TX (dB)" + ": ")
        self._tx_gain_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._tx_gain_button_group = variable_chooser_button_group()
        self._tx_gain_group_box.setLayout(self._tx_gain_box)
        for i, _label in enumerate(self._tx_gain_labels):
            radio_button = Qt.QRadioButton(_label)
            self._tx_gain_box.addWidget(radio_button)
            self._tx_gain_button_group.addButton(radio_button, i)
        self._tx_gain_callback = lambda i: Qt.QMetaObject.invokeMethod(self._tx_gain_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._tx_gain_options.index(i)))
        self._tx_gain_callback(self.tx_gain)
        self._tx_gain_button_group.buttonClicked[int].connect(
            lambda i: self.set_tx_gain(self._tx_gain_options[i]))
        self.top_grid_layout.addWidget(self._tx_gain_group_box, 0, 2, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._permanencia_range = qtgui.Range(1, 20, 0.5, 2, 250)
        self._permanencia_win = qtgui.RangeWidget(self._permanencia_range, self.set_permanencia, "Permanencia por portadora (s)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._permanencia_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_probe_signal_x_0 = blocks.probe_signal_f()
        self._amp_range = qtgui.Range(0.05, 0.45, 0.01, 0.4, 250)
        self._amp_win = qtgui.RangeWidget(self._amp_range, self.set_amp, "Amplitud de cada tono", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._amp_win, 1, 1, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._portadora_manual_options = [305000000, 325000000, 345000000, 365000000, 385000000, 405000000, 425000000, 445000000, 465000000, 485000000, 505000000]
        # Create the labels list
        self._portadora_manual_labels = ['305 MHz', '325 MHz', '345 MHz', '365 MHz', '385 MHz', '405 MHz', '425 MHz', '445 MHz', '465 MHz', '485 MHz', '505 MHz']
        # Create the combo box
        self._portadora_manual_tool_bar = Qt.QToolBar(self)
        self._portadora_manual_tool_bar.addWidget(Qt.QLabel("Portadora en modo manual" + ": "))
        self._portadora_manual_combo_box = Qt.QComboBox()
        self._portadora_manual_tool_bar.addWidget(self._portadora_manual_combo_box)
        for _label in self._portadora_manual_labels: self._portadora_manual_combo_box.addItem(_label)
        self._portadora_manual_callback = lambda i: Qt.QMetaObject.invokeMethod(self._portadora_manual_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._portadora_manual_options.index(i)))
        self._portadora_manual_callback(self.portadora_manual)
        self._portadora_manual_combo_box.currentIndexChanged.connect(
            lambda i: self.set_portadora_manual(self._portadora_manual_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._portadora_manual_tool_bar, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.osmosdr_sink_0 = osmosdr.sink(
            args="numchan=" + str(1) + " " + 'bladerf=0'
        )
        self.osmosdr_sink_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_sink_0.set_sample_rate(samp_rate)
        self.osmosdr_sink_0.set_center_freq(freq, 0)
        self.osmosdr_sink_0.set_freq_corr(0, 0)
        self.osmosdr_sink_0.set_gain(tx_gain, 0)
        self.osmosdr_sink_0.set_if_gain(0, 0)
        self.osmosdr_sink_0.set_bb_gain(0, 0)
        self.osmosdr_sink_0.set_antenna('', 0)
        self.osmosdr_sink_0.set_bandwidth(14e6, 0)
        # Create the options list
        self._modo_options = [0, 1]
        # Create the labels list
        self._modo_labels = ['Automatico', 'Manual']
        # Create the combo box
        # Create the radio buttons
        self._modo_group_box = Qt.QGroupBox("Modo" + ": ")
        self._modo_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._modo_button_group = variable_chooser_button_group()
        self._modo_group_box.setLayout(self._modo_box)
        for i, _label in enumerate(self._modo_labels):
            radio_button = Qt.QRadioButton(_label)
            self._modo_box.addWidget(radio_button)
            self._modo_button_group.addButton(radio_button, i)
        self._modo_callback = lambda i: Qt.QMetaObject.invokeMethod(self._modo_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._modo_options.index(i)))
        self._modo_callback(self.modo)
        self._modo_button_group.buttonClicked[int].connect(
            lambda i: self.set_modo(self._modo_options[i]))
        self.top_grid_layout.addWidget(self._modo_group_box, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        def _indice_medido_probe():
          self.flowgraph_started.wait()
          while True:

            val = self.blocks_probe_signal_x_0.level()
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_indice_medido,val))
              except AttributeError:
                self.set_indice_medido(val)
            except AttributeError:
              pass
            time.sleep(1.0 / (2))
        _indice_medido_thread = threading.Thread(target=_indice_medido_probe)
        _indice_medido_thread.daemon = True
        _indice_medido_thread.start()
        self._fase_inf_range = qtgui.Range(-180, 180, 1, 0, 250)
        self._fase_inf_win = qtgui.RangeWidget(self._fase_inf_range, self.set_fase_inf, "Fase del tono inferior (grados)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._fase_inf_win, 1, 2, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_superior_tool_bar = Qt.QToolBar(self)

        if None:
            self._et_superior_formatter = None
        else:
            self._et_superior_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_superior_tool_bar.addWidget(Qt.QLabel("Linea superior (MHz)"))
        self._et_superior_label = Qt.QLabel(str(self._et_superior_formatter(self.et_superior)))
        self._et_superior_tool_bar.addWidget(self._et_superior_label)
        self.top_grid_layout.addWidget(self._et_superior_tool_bar, 2, 2, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_portadora_tool_bar = Qt.QToolBar(self)

        if None:
            self._et_portadora_formatter = None
        else:
            self._et_portadora_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_portadora_tool_bar.addWidget(Qt.QLabel("Portadora actual (MHz)"))
        self._et_portadora_label = Qt.QLabel(str(self._et_portadora_formatter(self.et_portadora)))
        self._et_portadora_tool_bar.addWidget(self._et_portadora_label)
        self.top_grid_layout.addWidget(self._et_portadora_tool_bar, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_pico_tool_bar = Qt.QToolBar(self)

        if None:
            self._et_pico_formatter = None
        else:
            self._et_pico_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_pico_tool_bar.addWidget(Qt.QLabel("Pico de banda base (debe ser < 1)"))
        self._et_pico_label = Qt.QLabel(str(self._et_pico_formatter(self.et_pico)))
        self._et_pico_tool_bar.addWidget(self._et_pico_label)
        self.top_grid_layout.addWidget(self._et_pico_tool_bar, 3, 1, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_paso_tool_bar = Qt.QToolBar(self)

        if None:
            self._et_paso_formatter = None
        else:
            self._et_paso_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_paso_tool_bar.addWidget(Qt.QLabel("Paso del barrido (1 a 11)"))
        self._et_paso_label = Qt.QLabel(str(self._et_paso_formatter(self.et_paso)))
        self._et_paso_tool_bar.addWidget(self._et_paso_label)
        self.top_grid_layout.addWidget(self._et_paso_tool_bar, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_inferior_tool_bar = Qt.QToolBar(self)

        if None:
            self._et_inferior_formatter = None
        else:
            self._et_inferior_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_inferior_tool_bar.addWidget(Qt.QLabel("Linea inferior (MHz)"))
        self._et_inferior_label = Qt.QLabel(str(self._et_inferior_formatter(self.et_inferior)))
        self._et_inferior_tool_bar.addWidget(self._et_inferior_label)
        self.top_grid_layout.addWidget(self._et_inferior_tool_bar, 2, 1, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_vector_source_x_0 = blocks.vector_source_f(list(range(11)), True, 1, [])
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_float*1, tasa_ctrl, True, 0 if "time" == "auto" else max( int(float(0.05) * tasa_ctrl) if "time" == "time" else int(0.05), 1) )
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_float*1, (int(permanencia * tasa_ctrl)))
        self.blocks_multiply_const_inf = blocks.multiply_const_cc(c_inf)
        self.blocks_conjugate_cc_0 = blocks.conjugate_cc()
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, amp, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_conjugate_cc_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.blocks_conjugate_cc_0, 0), (self.blocks_multiply_const_inf, 0))
        self.connect((self.blocks_multiply_const_inf, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_repeat_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_probe_signal_x_0, 0))
        self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_repeat_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp12_peine_tandas")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_indice_medido(self):
        return self.indice_medido

    def set_indice_medido(self, indice_medido):
        self.indice_medido = indice_medido
        self.set_indice(min(max(int(round(self.indice_medido)), 0), 10))

    def get_portadoras(self):
        return self.portadoras

    def set_portadoras(self, portadoras):
        self.portadoras = portadoras
        self.set_freq(self.portadora_manual if self.modo == 1 else self.portadoras[self.indice])

    def get_portadora_manual(self):
        return self.portadora_manual

    def set_portadora_manual(self, portadora_manual):
        self.portadora_manual = portadora_manual
        self._portadora_manual_callback(self.portadora_manual)
        self.set_freq(self.portadora_manual if self.modo == 1 else self.portadoras[self.indice])

    def get_modo(self):
        return self.modo

    def set_modo(self, modo):
        self.modo = modo
        self._modo_callback(self.modo)
        self.set_freq(self.portadora_manual if self.modo == 1 else self.portadoras[self.indice])

    def get_indice(self):
        return self.indice

    def set_indice(self, indice):
        self.indice = indice
        self.set_et_paso((self.indice + 1))
        self.set_freq(self.portadora_manual if self.modo == 1 else self.portadoras[self.indice])

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_et_portadora((self.freq / 1e6))
        self.set_et_inferior(((self.freq - self.f_tono) / 1e6))
        self.set_et_superior(((self.freq + self.f_tono) / 1e6))
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_fase_inf(self):
        return self.fase_inf

    def set_fase_inf(self, fase_inf):
        self.fase_inf = fase_inf
        self.set_c_inf(np.exp(1j*np.deg2rad(self.fase_inf)))

    def get_f_tono(self):
        return self.f_tono

    def set_f_tono(self, f_tono):
        self.f_tono = f_tono
        self.set_et_inferior(((self.freq - self.f_tono) / 1e6))
        self.set_et_superior(((self.freq + self.f_tono) / 1e6))
        self.analog_sig_source_x_0.set_frequency(self.f_tono)

    def get_amp(self):
        return self.amp

    def set_amp(self, amp):
        self.amp = amp
        self.set_et_pico((2 * self.amp))
        self.analog_sig_source_x_0.set_amplitude(self.amp)

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self._tx_gain_callback(self.tx_gain)
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)

    def get_tasa_ctrl(self):
        return self.tasa_ctrl

    def set_tasa_ctrl(self, tasa_ctrl):
        self.tasa_ctrl = tasa_ctrl
        self.blocks_repeat_0.set_interpolation((int(self.permanencia * self.tasa_ctrl)))
        self.blocks_throttle2_0.set_sample_rate(self.tasa_ctrl)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)

    def get_permanencia(self):
        return self.permanencia

    def set_permanencia(self, permanencia):
        self.permanencia = permanencia
        self.blocks_repeat_0.set_interpolation((int(self.permanencia * self.tasa_ctrl)))

    def get_et_superior(self):
        return self.et_superior

    def set_et_superior(self, et_superior):
        self.et_superior = et_superior
        Qt.QMetaObject.invokeMethod(self._et_superior_label, "setText", Qt.Q_ARG("QString", str(self._et_superior_formatter(self.et_superior))))

    def get_et_portadora(self):
        return self.et_portadora

    def set_et_portadora(self, et_portadora):
        self.et_portadora = et_portadora
        Qt.QMetaObject.invokeMethod(self._et_portadora_label, "setText", Qt.Q_ARG("QString", str(self._et_portadora_formatter(self.et_portadora))))

    def get_et_pico(self):
        return self.et_pico

    def set_et_pico(self, et_pico):
        self.et_pico = et_pico
        Qt.QMetaObject.invokeMethod(self._et_pico_label, "setText", Qt.Q_ARG("QString", str(self._et_pico_formatter(self.et_pico))))

    def get_et_paso(self):
        return self.et_paso

    def set_et_paso(self, et_paso):
        self.et_paso = et_paso
        Qt.QMetaObject.invokeMethod(self._et_paso_label, "setText", Qt.Q_ARG("QString", str(self._et_paso_formatter(self.et_paso))))

    def get_et_inferior(self):
        return self.et_inferior

    def set_et_inferior(self, et_inferior):
        self.et_inferior = et_inferior
        Qt.QMetaObject.invokeMethod(self._et_inferior_label, "setText", Qt.Q_ARG("QString", str(self._et_inferior_formatter(self.et_inferior))))

    def get_c_inf(self):
        return self.c_inf

    def set_c_inf(self, c_inf):
        self.c_inf = c_inf
        self.blocks_multiply_const_inf.set_k(self.c_inf)




def main(top_block_cls=exp12_peine_tandas, options=None):

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
