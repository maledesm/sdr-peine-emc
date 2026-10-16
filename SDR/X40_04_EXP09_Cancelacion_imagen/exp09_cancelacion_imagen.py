#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-09 cancelacion de imagen por pre-correccion IQ
# Description: EXP-09 cancelacion de la imagen sumando c*conj(x) - bladeRF x40 contra tinySA por cable
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



class exp09_cancelacion_imagen(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-09 cancelacion de imagen por pre-correccion IQ", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-09 cancelacion de imagen por pre-correccion IQ")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp09_cancelacion_imagen")

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
        self.tone_freq = tone_freq = 200e3
        self.phi_deg = phi_deg = 0
        self.k_db = k_db = -34
        self.freq = freq = 400e6
        self.corr_on = corr_on = 0
        self.amp = amp = 0.5
        self.tx_gain = tx_gain = 17
        self.samp_rate = samp_rate = 2e6
        self.pico_bb = pico_bb = (amp * (1 + corr_on * 10**(k_db/20)))
        self.f_tono = f_tono = ((freq + tone_freq) / 1e6)
        self.f_stop = f_stop = ((freq + 0.8e6) / 1e6)
        self.f_start = f_start = ((freq - 1.2e6) / 1e6)
        self.f_imagen = f_imagen = ((freq - tone_freq) / 1e6)
        self.f_fuga = f_fuga = (freq / 1e6)
        self.c = c = corr_on * 10**(k_db/20) * np.exp(1j*np.deg2rad(phi_deg))

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
        self.top_layout.addWidget(self._tx_gain_group_box)
        # Create the options list
        self._tone_freq_options = [200000.0, 600000.0]
        # Create the labels list
        self._tone_freq_labels = ['200 kHz', '600 kHz']
        # Create the combo box
        # Create the radio buttons
        self._tone_freq_group_box = Qt.QGroupBox("Tono de banda base" + ": ")
        self._tone_freq_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._tone_freq_button_group = variable_chooser_button_group()
        self._tone_freq_group_box.setLayout(self._tone_freq_box)
        for i, _label in enumerate(self._tone_freq_labels):
            radio_button = Qt.QRadioButton(_label)
            self._tone_freq_box.addWidget(radio_button)
            self._tone_freq_button_group.addButton(radio_button, i)
        self._tone_freq_callback = lambda i: Qt.QMetaObject.invokeMethod(self._tone_freq_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._tone_freq_options.index(i)))
        self._tone_freq_callback(self.tone_freq)
        self._tone_freq_button_group.buttonClicked[int].connect(
            lambda i: self.set_tone_freq(self._tone_freq_options[i]))
        self.top_layout.addWidget(self._tone_freq_group_box)
        # Create the options list
        self._freq_options = [400000000.0, 600000000.0]
        # Create the labels list
        self._freq_labels = ['400 MHz', '600 MHz']
        # Create the combo box
        # Create the radio buttons
        self._freq_group_box = Qt.QGroupBox("Portadora" + ": ")
        self._freq_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._freq_button_group = variable_chooser_button_group()
        self._freq_group_box.setLayout(self._freq_box)
        for i, _label in enumerate(self._freq_labels):
            radio_button = Qt.QRadioButton(_label)
            self._freq_box.addWidget(radio_button)
            self._freq_button_group.addButton(radio_button, i)
        self._freq_callback = lambda i: Qt.QMetaObject.invokeMethod(self._freq_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._freq_options.index(i)))
        self._freq_callback(self.freq)
        self._freq_button_group.buttonClicked[int].connect(
            lambda i: self.set_freq(self._freq_options[i]))
        self.top_layout.addWidget(self._freq_group_box)
        # Create the options list
        self._amp_options = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        # Create the labels list
        self._amp_labels = ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7']
        # Create the combo box
        self._amp_tool_bar = Qt.QToolBar(self)
        self._amp_tool_bar.addWidget(Qt.QLabel("Amplitud digital" + ": "))
        self._amp_combo_box = Qt.QComboBox()
        self._amp_tool_bar.addWidget(self._amp_combo_box)
        for _label in self._amp_labels: self._amp_combo_box.addItem(_label)
        self._amp_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_options.index(i)))
        self._amp_callback(self.amp)
        self._amp_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp(self._amp_options[i]))
        # Create the radio buttons
        self.top_layout.addWidget(self._amp_tool_bar)
        self._pico_bb_tool_bar = Qt.QToolBar(self)

        if None:
            self._pico_bb_formatter = None
        else:
            self._pico_bb_formatter = lambda x: eng_notation.num_to_str(x)

        self._pico_bb_tool_bar.addWidget(Qt.QLabel("Pico de banda base (debe ser < 1)"))
        self._pico_bb_label = Qt.QLabel(str(self._pico_bb_formatter(self.pico_bb)))
        self._pico_bb_tool_bar.addWidget(self._pico_bb_label)
        self.top_layout.addWidget(self._pico_bb_tool_bar)
        self._phi_deg_range = qtgui.Range(-180, 180, 0.5, 0, 400)
        self._phi_deg_win = qtgui.RangeWidget(self._phi_deg_range, self.set_phi_deg, "Fase de la correccion (grados)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._phi_deg_win)
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
        self.osmosdr_sink_0.set_bandwidth(0, 0)
        self._k_db_range = qtgui.Range(-50, -20, 0.1, -34, 400)
        self._k_db_win = qtgui.RangeWidget(self._k_db_range, self.set_k_db, "Nivel de la correccion |c| (dB respecto del tono)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._k_db_win)
        self._f_tono_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_tono_formatter = None
        else:
            self._f_tono_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_tono_tool_bar.addWidget(Qt.QLabel("Tono util (MHz)"))
        self._f_tono_label = Qt.QLabel(str(self._f_tono_formatter(self.f_tono)))
        self._f_tono_tool_bar.addWidget(self._f_tono_label)
        self.top_layout.addWidget(self._f_tono_tool_bar)
        self._f_stop_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_stop_formatter = None
        else:
            self._f_stop_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_stop_tool_bar.addWidget(Qt.QLabel("tinySA STOP (MHz)"))
        self._f_stop_label = Qt.QLabel(str(self._f_stop_formatter(self.f_stop)))
        self._f_stop_tool_bar.addWidget(self._f_stop_label)
        self.top_layout.addWidget(self._f_stop_tool_bar)
        self._f_start_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_start_formatter = None
        else:
            self._f_start_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_start_tool_bar.addWidget(Qt.QLabel("tinySA START (MHz)"))
        self._f_start_label = Qt.QLabel(str(self._f_start_formatter(self.f_start)))
        self._f_start_tool_bar.addWidget(self._f_start_label)
        self.top_layout.addWidget(self._f_start_tool_bar)
        self._f_imagen_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_imagen_formatter = None
        else:
            self._f_imagen_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_imagen_tool_bar.addWidget(Qt.QLabel("Imagen (MHz)"))
        self._f_imagen_label = Qt.QLabel(str(self._f_imagen_formatter(self.f_imagen)))
        self._f_imagen_tool_bar.addWidget(self._f_imagen_label)
        self.top_layout.addWidget(self._f_imagen_tool_bar)
        self._f_fuga_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_fuga_formatter = None
        else:
            self._f_fuga_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_fuga_tool_bar.addWidget(Qt.QLabel("Fuga de portadora (MHz)"))
        self._f_fuga_label = Qt.QLabel(str(self._f_fuga_formatter(self.f_fuga)))
        self._f_fuga_tool_bar.addWidget(self._f_fuga_label)
        self.top_layout.addWidget(self._f_fuga_tool_bar)
        # Create the options list
        self._corr_on_options = [0, 1]
        # Create the labels list
        self._corr_on_labels = ['Apagada', 'Encendida']
        # Create the combo box
        # Create the radio buttons
        self._corr_on_group_box = Qt.QGroupBox("Correccion" + ": ")
        self._corr_on_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._corr_on_button_group = variable_chooser_button_group()
        self._corr_on_group_box.setLayout(self._corr_on_box)
        for i, _label in enumerate(self._corr_on_labels):
            radio_button = Qt.QRadioButton(_label)
            self._corr_on_box.addWidget(radio_button)
            self._corr_on_button_group.addButton(radio_button, i)
        self._corr_on_callback = lambda i: Qt.QMetaObject.invokeMethod(self._corr_on_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._corr_on_options.index(i)))
        self._corr_on_callback(self.corr_on)
        self._corr_on_button_group.buttonClicked[int].connect(
            lambda i: self.set_corr_on(self._corr_on_options[i]))
        self.top_layout.addWidget(self._corr_on_group_box)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(c)
        self.blocks_conjugate_cc_0 = blocks.conjugate_cc()
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, tone_freq, amp, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_conjugate_cc_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.blocks_conjugate_cc_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_add_xx_0, 1))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp09_cancelacion_imagen")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_tone_freq(self):
        return self.tone_freq

    def set_tone_freq(self, tone_freq):
        self.tone_freq = tone_freq
        self.set_f_imagen(((self.freq - self.tone_freq) / 1e6))
        self.set_f_tono(((self.freq + self.tone_freq) / 1e6))
        self._tone_freq_callback(self.tone_freq)
        self.analog_sig_source_x_0.set_frequency(self.tone_freq)

    def get_phi_deg(self):
        return self.phi_deg

    def set_phi_deg(self, phi_deg):
        self.phi_deg = phi_deg
        self.set_c(self.corr_on * 10**(self.k_db/20) * np.exp(1j*np.deg2rad(self.phi_deg)))

    def get_k_db(self):
        return self.k_db

    def set_k_db(self, k_db):
        self.k_db = k_db
        self.set_c(self.corr_on * 10**(self.k_db/20) * np.exp(1j*np.deg2rad(self.phi_deg)))
        self.set_pico_bb((self.amp * (1 + self.corr_on * 10**(self.k_db/20))))

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_f_fuga((self.freq / 1e6))
        self.set_f_imagen(((self.freq - self.tone_freq) / 1e6))
        self.set_f_start(((self.freq - 1.2e6) / 1e6))
        self.set_f_stop(((self.freq + 0.8e6) / 1e6))
        self.set_f_tono(((self.freq + self.tone_freq) / 1e6))
        self._freq_callback(self.freq)
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_corr_on(self):
        return self.corr_on

    def set_corr_on(self, corr_on):
        self.corr_on = corr_on
        self._corr_on_callback(self.corr_on)
        self.set_c(self.corr_on * 10**(self.k_db/20) * np.exp(1j*np.deg2rad(self.phi_deg)))
        self.set_pico_bb((self.amp * (1 + self.corr_on * 10**(self.k_db/20))))

    def get_amp(self):
        return self.amp

    def set_amp(self, amp):
        self.amp = amp
        self._amp_callback(self.amp)
        self.analog_sig_source_x_0.set_amplitude(self.amp)
        self.set_pico_bb((self.amp * (1 + self.corr_on * 10**(self.k_db/20))))

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self._tx_gain_callback(self.tx_gain)
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)

    def get_pico_bb(self):
        return self.pico_bb

    def set_pico_bb(self, pico_bb):
        self.pico_bb = pico_bb
        Qt.QMetaObject.invokeMethod(self._pico_bb_label, "setText", Qt.Q_ARG("QString", str(self._pico_bb_formatter(self.pico_bb))))

    def get_f_tono(self):
        return self.f_tono

    def set_f_tono(self, f_tono):
        self.f_tono = f_tono
        Qt.QMetaObject.invokeMethod(self._f_tono_label, "setText", Qt.Q_ARG("QString", str(self._f_tono_formatter(self.f_tono))))

    def get_f_stop(self):
        return self.f_stop

    def set_f_stop(self, f_stop):
        self.f_stop = f_stop
        Qt.QMetaObject.invokeMethod(self._f_stop_label, "setText", Qt.Q_ARG("QString", str(self._f_stop_formatter(self.f_stop))))

    def get_f_start(self):
        return self.f_start

    def set_f_start(self, f_start):
        self.f_start = f_start
        Qt.QMetaObject.invokeMethod(self._f_start_label, "setText", Qt.Q_ARG("QString", str(self._f_start_formatter(self.f_start))))

    def get_f_imagen(self):
        return self.f_imagen

    def set_f_imagen(self, f_imagen):
        self.f_imagen = f_imagen
        Qt.QMetaObject.invokeMethod(self._f_imagen_label, "setText", Qt.Q_ARG("QString", str(self._f_imagen_formatter(self.f_imagen))))

    def get_f_fuga(self):
        return self.f_fuga

    def set_f_fuga(self, f_fuga):
        self.f_fuga = f_fuga
        Qt.QMetaObject.invokeMethod(self._f_fuga_label, "setText", Qt.Q_ARG("QString", str(self._f_fuga_formatter(self.f_fuga))))

    def get_c(self):
        return self.c

    def set_c(self, c):
        self.c = c
        self.blocks_multiply_const_vxx_0.set_k(self.c)




def main(top_block_cls=exp09_cancelacion_imagen, options=None):

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
