#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-15 xA9: ganancia y amplitud
# Description: bladeRF 2.0 micro xA9: portadora en 100 MHz, tono a 200 kHz, ganancia y amplitud ajustables en forma fina
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import analog
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
import osmosdr
import time
import threading


def snipfcn_aspecto(self):
    # Las etiquetas de GNU Radio no tienen tamano de letra: se lo cambiamos aca.
    for nombre in ('et_ganancia', 'et_limite', 'et_amp'):
        barra = getattr(self, '_%s_tool_bar' % nombre)
        ancho = 60
        for accion in barra.actions():
            etiqueta = barra.widgetForAction(accion)
            etiqueta.setStyleSheet('font-size: 15pt; font-weight: bold')
            ancho += etiqueta.sizeHint().width()
        barra.setMinimumWidth(ancho + 60)
    self.resize(self.top_widget.minimumSizeHint().width() + 60, 330)


def snippets_main_after_init(tb):
    snipfcn_aspecto(tb)

class exp15_a9_ganancia_amplitud(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-15 xA9: ganancia y amplitud", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-15 xA9: ganancia y amplitud")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp15_a9_ganancia_amplitud")

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
        self.tope = tope = 0
        self.ganancia = ganancia = 0
        self.tx_gain = tx_gain = min(ganancia, tope)
        self.amp = amp = 0.5
        self.samp_rate = samp_rate = 2e6
        self.freq = freq = 100e6
        self.f_tono = f_tono = 200e3
        self.et_limite = et_limite = 1 if ganancia > tope else 0
        self.et_ganancia = et_ganancia = tx_gain
        self.et_amp = et_amp = amp

        ##################################################
        # Blocks
        ##################################################

        self._amp_range = qtgui.Range(0, 1, 0.01, 0.5, 400)
        self._amp_win = qtgui.RangeWidget(self._amp_range, self.set_amp, "Amplitud del tono (0 a 1)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._amp_win, 2, 0, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._tope_options = [0, 20, 40, 55, 66]
        # Create the labels list
        self._tope_labels = ['0 dB', '20 dB', '40 dB', '55 dB', '66 dB (maximo)']
        # Create the combo box
        # Create the radio buttons
        self._tope_group_box = Qt.QGroupBox("Tope de seguridad de la ganancia" + ": ")
        self._tope_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._tope_button_group = variable_chooser_button_group()
        self._tope_group_box.setLayout(self._tope_box)
        for i, _label in enumerate(self._tope_labels):
            radio_button = Qt.QRadioButton(_label)
            self._tope_box.addWidget(radio_button)
            self._tope_button_group.addButton(radio_button, i)
        self._tope_callback = lambda i: Qt.QMetaObject.invokeMethod(self._tope_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._tope_options.index(i)))
        self._tope_callback(self.tope)
        self._tope_button_group.buttonClicked[int].connect(
            lambda i: self.set_tope(self._tope_options[i]))
        self.top_grid_layout.addWidget(self._tope_group_box, 0, 0, 1, 3)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
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
        self.osmosdr_sink_0.set_bandwidth(1.5e6, 0)
        self._ganancia_range = qtgui.Range(-23.75, 66, 0.25, 0, 400)
        self._ganancia_win = qtgui.RangeWidget(self._ganancia_range, self.set_ganancia, "Ganancia pedida (dB)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._ganancia_win, 1, 0, 1, 3)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_limite_tool_bar = Qt.QToolBar(self)

        if lambda x: 'LIMITANDO' if x else 'sin limitar':
            self._et_limite_formatter = lambda x: 'LIMITANDO' if x else 'sin limitar'
        else:
            self._et_limite_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_limite_tool_bar.addWidget(Qt.QLabel("Tope: "))
        self._et_limite_label = Qt.QLabel(str(self._et_limite_formatter(self.et_limite)))
        self._et_limite_tool_bar.addWidget(self._et_limite_label)
        self.top_grid_layout.addWidget(self._et_limite_tool_bar, 3, 1, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_ganancia_tool_bar = Qt.QToolBar(self)

        if lambda x: ('%.2f dB' % x):
            self._et_ganancia_formatter = lambda x: ('%.2f dB' % x)
        else:
            self._et_ganancia_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_ganancia_tool_bar.addWidget(Qt.QLabel("Ganancia aplicada: "))
        self._et_ganancia_label = Qt.QLabel(str(self._et_ganancia_formatter(self.et_ganancia)))
        self._et_ganancia_tool_bar.addWidget(self._et_ganancia_label)
        self.top_grid_layout.addWidget(self._et_ganancia_tool_bar, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_amp_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.2f' % x:
            self._et_amp_formatter = lambda x: '%.2f' % x
        else:
            self._et_amp_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_amp_tool_bar.addWidget(Qt.QLabel("Amplitud: "))
        self._et_amp_label = Qt.QLabel(str(self._et_amp_formatter(self.et_amp)))
        self._et_amp_tool_bar.addWidget(self._et_amp_label)
        self.top_grid_layout.addWidget(self._et_amp_tool_bar, 3, 2, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, amp, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.osmosdr_sink_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp15_a9_ganancia_amplitud")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_tope(self):
        return self.tope

    def set_tope(self, tope):
        self.tope = tope
        self._tope_callback(self.tope)
        self.set_et_limite(1 if self.ganancia > self.tope else 0)
        self.set_tx_gain(min(self.ganancia, self.tope))

    def get_ganancia(self):
        return self.ganancia

    def set_ganancia(self, ganancia):
        self.ganancia = ganancia
        self.set_et_limite(1 if self.ganancia > self.tope else 0)
        self.set_tx_gain(min(self.ganancia, self.tope))

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.set_et_ganancia(self.tx_gain)
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)

    def get_amp(self):
        return self.amp

    def set_amp(self, amp):
        self.amp = amp
        self.set_et_amp(self.amp)
        self.analog_sig_source_x_0.set_amplitude(self.amp)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_f_tono(self):
        return self.f_tono

    def set_f_tono(self, f_tono):
        self.f_tono = f_tono
        self.analog_sig_source_x_0.set_frequency(self.f_tono)

    def get_et_limite(self):
        return self.et_limite

    def set_et_limite(self, et_limite):
        self.et_limite = et_limite
        Qt.QMetaObject.invokeMethod(self._et_limite_label, "setText", Qt.Q_ARG("QString", str(self._et_limite_formatter(self.et_limite))))

    def get_et_ganancia(self):
        return self.et_ganancia

    def set_et_ganancia(self, et_ganancia):
        self.et_ganancia = et_ganancia
        Qt.QMetaObject.invokeMethod(self._et_ganancia_label, "setText", Qt.Q_ARG("QString", str(self._et_ganancia_formatter(self.et_ganancia))))

    def get_et_amp(self):
        return self.et_amp

    def set_et_amp(self, et_amp):
        self.et_amp = et_amp
        Qt.QMetaObject.invokeMethod(self._et_amp_label, "setText", Qt.Q_ARG("QString", str(self._et_amp_formatter(self.et_amp))))




def main(top_block_cls=exp15_a9_ganancia_amplitud, options=None):

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
