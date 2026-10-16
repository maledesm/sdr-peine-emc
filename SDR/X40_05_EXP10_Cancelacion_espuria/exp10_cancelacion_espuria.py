#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-10 cancelacion de la espuria de -937 kHz
# Description: EXP-10: espuria de LO-937 kHz. Correccion aditiva (e) para la replica de la fuga y multiplicativa (d) para la replica del tono, mas la correccion de imagen del EXP-09
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



class exp10_cancelacion_espuria(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-10 cancelacion de la espuria de -937 kHz", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-10 cancelacion de la espuria de -937 kHz")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp10_cancelacion_espuria")

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
        self.esp_grueso_khz = esp_grueso_khz = -937.2
        self.esp_fino_hz = esp_fino_hz = 0
        self.tono_on = tono_on = 1
        self.tone_freq = tone_freq = 200e3
        self.phi_deg = phi_deg = 15
        self.k_db = k_db = -34.5
        self.img_on = img_on = 0
        self.freq = freq = 400e6
        self.f_esp = f_esp = esp_grueso_khz*1e3 + esp_fino_hz
        self.e_phi = e_phi = 0
        self.e_on = e_on = 0
        self.e_db = e_db = -59
        self.d_phi = d_phi = 0
        self.d_on = d_on = 0
        self.d_db = d_db = -52
        self.amp = amp = 0.5
        self.tx_gain = tx_gain = 17
        self.samp_rate = samp_rate = 2e6
        self.pico_bb = pico_bb = (amp*tono_on*(1 + img_on*10**(k_db/20))*(1 + d_on*10**(d_db/20)) + e_on*10**(e_db/20))
        self.f_tono = f_tono = ((freq + tone_freq) / 1e6)
        self.f_imagen = f_imagen = ((freq - tone_freq) / 1e6)
        self.f_gem_tono = f_gem_tono = ((freq + tone_freq - f_esp) / 1e6)
        self.f_gem_fuga = f_gem_fuga = ((freq - f_esp) / 1e6)
        self.f_fuga = f_fuga = (freq / 1e6)
        self.f_esp_tono = f_esp_tono = ((freq + tone_freq + f_esp) / 1e6)
        self.f_esp_hz = f_esp_hz = f_esp
        self.f_esp_fuga = f_esp_fuga = ((freq + f_esp) / 1e6)
        self.ecoef = ecoef = e_on * 10**(e_db/20) * np.exp(1j*np.deg2rad(e_phi))
        self.dcoef = dcoef = d_on * 10**(d_db/20) * np.exp(1j*np.deg2rad(d_phi))
        self.c = c = img_on * 10**(k_db/20) * np.exp(1j*np.deg2rad(phi_deg))

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
        # Create the options list
        self._tono_on_options = [0, 1]
        # Create the labels list
        self._tono_on_labels = ['Apagado', 'Encendido']
        # Create the combo box
        # Create the radio buttons
        self._tono_on_group_box = Qt.QGroupBox("Tono principal" + ": ")
        self._tono_on_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._tono_on_button_group = variable_chooser_button_group()
        self._tono_on_group_box.setLayout(self._tono_on_box)
        for i, _label in enumerate(self._tono_on_labels):
            radio_button = Qt.QRadioButton(_label)
            self._tono_on_box.addWidget(radio_button)
            self._tono_on_button_group.addButton(radio_button, i)
        self._tono_on_callback = lambda i: Qt.QMetaObject.invokeMethod(self._tono_on_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._tono_on_options.index(i)))
        self._tono_on_callback(self.tono_on)
        self._tono_on_button_group.buttonClicked[int].connect(
            lambda i: self.set_tono_on(self._tono_on_options[i]))
        self.top_grid_layout.addWidget(self._tono_on_group_box, 1, 1, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
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
        self.top_grid_layout.addWidget(self._tone_freq_group_box, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._samp_rate_options = [2000000.0, 4000000.0]
        # Create the labels list
        self._samp_rate_labels = ['2 MSPS', '4 MSPS']
        # Create the combo box
        # Create the radio buttons
        self._samp_rate_group_box = Qt.QGroupBox("Tasa de muestreo" + ": ")
        self._samp_rate_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._samp_rate_button_group = variable_chooser_button_group()
        self._samp_rate_group_box.setLayout(self._samp_rate_box)
        for i, _label in enumerate(self._samp_rate_labels):
            radio_button = Qt.QRadioButton(_label)
            self._samp_rate_box.addWidget(radio_button)
            self._samp_rate_button_group.addButton(radio_button, i)
        self._samp_rate_callback = lambda i: Qt.QMetaObject.invokeMethod(self._samp_rate_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._samp_rate_options.index(i)))
        self._samp_rate_callback(self.samp_rate)
        self._samp_rate_button_group.buttonClicked[int].connect(
            lambda i: self.set_samp_rate(self._samp_rate_options[i]))
        self.top_grid_layout.addWidget(self._samp_rate_group_box, 0, 3, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
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
        self.top_grid_layout.addWidget(self._freq_group_box, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
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
        self.top_grid_layout.addWidget(self._amp_tool_bar, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._pico_bb_tool_bar = Qt.QToolBar(self)

        if None:
            self._pico_bb_formatter = None
        else:
            self._pico_bb_formatter = lambda x: eng_notation.num_to_str(x)

        self._pico_bb_tool_bar.addWidget(Qt.QLabel("Pico de banda base (debe ser < 1)"))
        self._pico_bb_label = Qt.QLabel(str(self._pico_bb_formatter(self.pico_bb)))
        self._pico_bb_tool_bar.addWidget(self._pico_bb_label)
        self.top_grid_layout.addWidget(self._pico_bb_tool_bar, 1, 2, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._phi_deg_range = qtgui.Range(-180, 180, 0.5, 15, 250)
        self._phi_deg_win = qtgui.RangeWidget(self._phi_deg_range, self.set_phi_deg, "Imagen: fase de c (grados)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._phi_deg_win, 2, 2, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
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
        self.osmosdr_sink_0.set_bandwidth((0.75 * samp_rate), 0)
        self._k_db_range = qtgui.Range(-50, -20, 0.1, -34.5, 250)
        self._k_db_win = qtgui.RangeWidget(self._k_db_range, self.set_k_db, "Imagen: nivel |c| (dB)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._k_db_win, 2, 1, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._img_on_options = [0, 1]
        # Create the labels list
        self._img_on_labels = ['Apagada', 'Encendida']
        # Create the combo box
        # Create the radio buttons
        self._img_on_group_box = Qt.QGroupBox("Correccion de imagen (EXP-09)" + ": ")
        self._img_on_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._img_on_button_group = variable_chooser_button_group()
        self._img_on_group_box.setLayout(self._img_on_box)
        for i, _label in enumerate(self._img_on_labels):
            radio_button = Qt.QRadioButton(_label)
            self._img_on_box.addWidget(radio_button)
            self._img_on_button_group.addButton(radio_button, i)
        self._img_on_callback = lambda i: Qt.QMetaObject.invokeMethod(self._img_on_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._img_on_options.index(i)))
        self._img_on_callback(self.img_on)
        self._img_on_button_group.buttonClicked[int].connect(
            lambda i: self.set_img_on(self._img_on_options[i]))
        self.top_grid_layout.addWidget(self._img_on_group_box, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._f_tono_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_tono_formatter = None
        else:
            self._f_tono_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_tono_tool_bar.addWidget(Qt.QLabel("Tono (MHz)"))
        self._f_tono_label = Qt.QLabel(str(self._f_tono_formatter(self.f_tono)))
        self._f_tono_tool_bar.addWidget(self._f_tono_label)
        self.top_grid_layout.addWidget(self._f_tono_tool_bar, 6, 0, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._f_imagen_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_imagen_formatter = None
        else:
            self._f_imagen_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_imagen_tool_bar.addWidget(Qt.QLabel("Imagen (MHz)"))
        self._f_imagen_label = Qt.QLabel(str(self._f_imagen_formatter(self.f_imagen)))
        self._f_imagen_tool_bar.addWidget(self._f_imagen_label)
        self.top_grid_layout.addWidget(self._f_imagen_tool_bar, 6, 1, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._f_gem_tono_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_gem_tono_formatter = None
        else:
            self._f_gem_tono_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_gem_tono_tool_bar.addWidget(Qt.QLabel("Gemela del tono (MHz)"))
        self._f_gem_tono_label = Qt.QLabel(str(self._f_gem_tono_formatter(self.f_gem_tono)))
        self._f_gem_tono_tool_bar.addWidget(self._f_gem_tono_label)
        self.top_grid_layout.addWidget(self._f_gem_tono_tool_bar, 7, 3, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._f_gem_fuga_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_gem_fuga_formatter = None
        else:
            self._f_gem_fuga_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_gem_fuga_tool_bar.addWidget(Qt.QLabel("Gemela de la fuga (MHz)"))
        self._f_gem_fuga_label = Qt.QLabel(str(self._f_gem_fuga_formatter(self.f_gem_fuga)))
        self._f_gem_fuga_tool_bar.addWidget(self._f_gem_fuga_label)
        self.top_grid_layout.addWidget(self._f_gem_fuga_tool_bar, 7, 2, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._f_fuga_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_fuga_formatter = None
        else:
            self._f_fuga_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_fuga_tool_bar.addWidget(Qt.QLabel("Fuga de portadora (MHz)"))
        self._f_fuga_label = Qt.QLabel(str(self._f_fuga_formatter(self.f_fuga)))
        self._f_fuga_tool_bar.addWidget(self._f_fuga_label)
        self.top_grid_layout.addWidget(self._f_fuga_tool_bar, 6, 2, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._f_esp_tono_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_esp_tono_formatter = None
        else:
            self._f_esp_tono_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_esp_tono_tool_bar.addWidget(Qt.QLabel("Replica del tono (MHz)"))
        self._f_esp_tono_label = Qt.QLabel(str(self._f_esp_tono_formatter(self.f_esp_tono)))
        self._f_esp_tono_tool_bar.addWidget(self._f_esp_tono_label)
        self.top_grid_layout.addWidget(self._f_esp_tono_tool_bar, 7, 1, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._f_esp_hz_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_esp_hz_formatter = None
        else:
            self._f_esp_hz_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_esp_hz_tool_bar.addWidget(Qt.QLabel("Corrimiento de la espuria aplicado (Hz)"))
        self._f_esp_hz_label = Qt.QLabel(str(self._f_esp_hz_formatter(self.f_esp_hz)))
        self._f_esp_hz_tool_bar.addWidget(self._f_esp_hz_label)
        self.top_grid_layout.addWidget(self._f_esp_hz_tool_bar, 1, 3, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._f_esp_fuga_tool_bar = Qt.QToolBar(self)

        if None:
            self._f_esp_fuga_formatter = None
        else:
            self._f_esp_fuga_formatter = lambda x: eng_notation.num_to_str(x)

        self._f_esp_fuga_tool_bar.addWidget(Qt.QLabel("Replica de la fuga (MHz)"))
        self._f_esp_fuga_label = Qt.QLabel(str(self._f_esp_fuga_formatter(self.f_esp_fuga)))
        self._f_esp_fuga_tool_bar.addWidget(self._f_esp_fuga_label)
        self.top_grid_layout.addWidget(self._f_esp_fuga_tool_bar, 7, 0, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._esp_grueso_khz_range = qtgui.Range(-945, -930, 0.01, -937.2, 250)
        self._esp_grueso_khz_win = qtgui.RangeWidget(self._esp_grueso_khz_range, self.set_esp_grueso_khz, "Espuria: corrimiento grueso (kHz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._esp_grueso_khz_win, 3, 0, 1, 2)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._esp_fino_hz_range = qtgui.Range(-50, 50, 0.01, 0, 250)
        self._esp_fino_hz_win = qtgui.RangeWidget(self._esp_fino_hz_range, self.set_esp_fino_hz, "Espuria: ajuste fino (Hz)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._esp_fino_hz_win, 3, 2, 1, 2)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._e_phi_range = qtgui.Range(-180, 180, 0.5, 0, 250)
        self._e_phi_win = qtgui.RangeWidget(self._e_phi_range, self.set_e_phi, "e: fase (grados)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._e_phi_win, 4, 2, 1, 2)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._e_on_options = [0, 1]
        # Create the labels list
        self._e_on_labels = ['Apagada', 'Encendida']
        # Create the combo box
        # Create the radio buttons
        self._e_on_group_box = Qt.QGroupBox("Cancelacion replica de la fuga (e)" + ": ")
        self._e_on_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._e_on_button_group = variable_chooser_button_group()
        self._e_on_group_box.setLayout(self._e_on_box)
        for i, _label in enumerate(self._e_on_labels):
            radio_button = Qt.QRadioButton(_label)
            self._e_on_box.addWidget(radio_button)
            self._e_on_button_group.addButton(radio_button, i)
        self._e_on_callback = lambda i: Qt.QMetaObject.invokeMethod(self._e_on_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._e_on_options.index(i)))
        self._e_on_callback(self.e_on)
        self._e_on_button_group.buttonClicked[int].connect(
            lambda i: self.set_e_on(self._e_on_options[i]))
        self.top_grid_layout.addWidget(self._e_on_group_box, 4, 0, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._e_db_range = qtgui.Range(-90, -30, 0.1, -59, 250)
        self._e_db_win = qtgui.RangeWidget(self._e_db_range, self.set_e_db, "e: nivel (dBFS)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._e_db_win, 4, 1, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._d_phi_range = qtgui.Range(-180, 180, 0.5, 0, 250)
        self._d_phi_win = qtgui.RangeWidget(self._d_phi_range, self.set_d_phi, "d: fase (grados)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._d_phi_win, 5, 2, 1, 2)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._d_on_options = [0, 1]
        # Create the labels list
        self._d_on_labels = ['Apagada', 'Encendida']
        # Create the combo box
        # Create the radio buttons
        self._d_on_group_box = Qt.QGroupBox("Cancelacion replica del tono (d)" + ": ")
        self._d_on_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._d_on_button_group = variable_chooser_button_group()
        self._d_on_group_box.setLayout(self._d_on_box)
        for i, _label in enumerate(self._d_on_labels):
            radio_button = Qt.QRadioButton(_label)
            self._d_on_box.addWidget(radio_button)
            self._d_on_button_group.addButton(radio_button, i)
        self._d_on_callback = lambda i: Qt.QMetaObject.invokeMethod(self._d_on_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._d_on_options.index(i)))
        self._d_on_callback(self.d_on)
        self._d_on_button_group.buttonClicked[int].connect(
            lambda i: self.set_d_on(self._d_on_options[i]))
        self.top_grid_layout.addWidget(self._d_on_group_box, 5, 0, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._d_db_range = qtgui.Range(-70, -30, 0.1, -52, 250)
        self._d_db_win = qtgui.RangeWidget(self._d_db_range, self.set_d_db, "d: nivel (dB respecto del tono)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._d_db_win, 5, 1, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_multiply_esp = blocks.multiply_vcc(1)
        self.blocks_multiply_const_img = blocks.multiply_const_cc(c)
        self.blocks_multiply_const_e = blocks.multiply_const_cc(ecoef)
        self.blocks_multiply_const_d = blocks.multiply_const_cc(dcoef)
        self.blocks_conjugate_cc_0 = blocks.conjugate_cc()
        self.blocks_add_img = blocks.add_vcc(1)
        self.blocks_add_final = blocks.add_vcc(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, tone_freq, (amp * tono_on), 0, 0)
        self.analog_sig_source_esp = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_esp, 1, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_esp, 0), (self.blocks_multiply_const_e, 0))
        self.connect((self.analog_sig_source_esp, 0), (self.blocks_multiply_esp, 1))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_add_img, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_conjugate_cc_0, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_esp, 0))
        self.connect((self.blocks_add_final, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.blocks_add_img, 0), (self.blocks_add_final, 0))
        self.connect((self.blocks_conjugate_cc_0, 0), (self.blocks_multiply_const_img, 0))
        self.connect((self.blocks_multiply_const_d, 0), (self.blocks_add_final, 1))
        self.connect((self.blocks_multiply_const_e, 0), (self.blocks_add_final, 2))
        self.connect((self.blocks_multiply_const_img, 0), (self.blocks_add_img, 1))
        self.connect((self.blocks_multiply_esp, 0), (self.blocks_multiply_const_d, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp10_cancelacion_espuria")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_esp_grueso_khz(self):
        return self.esp_grueso_khz

    def set_esp_grueso_khz(self, esp_grueso_khz):
        self.esp_grueso_khz = esp_grueso_khz
        self.set_f_esp(self.esp_grueso_khz*1e3 + self.esp_fino_hz)

    def get_esp_fino_hz(self):
        return self.esp_fino_hz

    def set_esp_fino_hz(self, esp_fino_hz):
        self.esp_fino_hz = esp_fino_hz
        self.set_f_esp(self.esp_grueso_khz*1e3 + self.esp_fino_hz)

    def get_tono_on(self):
        return self.tono_on

    def set_tono_on(self, tono_on):
        self.tono_on = tono_on
        self.set_pico_bb((self.amp*self.tono_on*(1 + self.img_on*10**(self.k_db/20))*(1 + self.d_on*10**(self.d_db/20)) + self.e_on*10**(self.e_db/20)))
        self._tono_on_callback(self.tono_on)
        self.analog_sig_source_x_0.set_amplitude((self.amp * self.tono_on))

    def get_tone_freq(self):
        return self.tone_freq

    def set_tone_freq(self, tone_freq):
        self.tone_freq = tone_freq
        self.set_f_esp_tono(((self.freq + self.tone_freq + self.f_esp) / 1e6))
        self.set_f_gem_tono(((self.freq + self.tone_freq - self.f_esp) / 1e6))
        self.set_f_imagen(((self.freq - self.tone_freq) / 1e6))
        self.set_f_tono(((self.freq + self.tone_freq) / 1e6))
        self._tone_freq_callback(self.tone_freq)
        self.analog_sig_source_x_0.set_frequency(self.tone_freq)

    def get_phi_deg(self):
        return self.phi_deg

    def set_phi_deg(self, phi_deg):
        self.phi_deg = phi_deg
        self.set_c(self.img_on * 10**(self.k_db/20) * np.exp(1j*np.deg2rad(self.phi_deg)))

    def get_k_db(self):
        return self.k_db

    def set_k_db(self, k_db):
        self.k_db = k_db
        self.set_c(self.img_on * 10**(self.k_db/20) * np.exp(1j*np.deg2rad(self.phi_deg)))
        self.set_pico_bb((self.amp*self.tono_on*(1 + self.img_on*10**(self.k_db/20))*(1 + self.d_on*10**(self.d_db/20)) + self.e_on*10**(self.e_db/20)))

    def get_img_on(self):
        return self.img_on

    def set_img_on(self, img_on):
        self.img_on = img_on
        self.set_c(self.img_on * 10**(self.k_db/20) * np.exp(1j*np.deg2rad(self.phi_deg)))
        self._img_on_callback(self.img_on)
        self.set_pico_bb((self.amp*self.tono_on*(1 + self.img_on*10**(self.k_db/20))*(1 + self.d_on*10**(self.d_db/20)) + self.e_on*10**(self.e_db/20)))

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_f_esp_fuga(((self.freq + self.f_esp) / 1e6))
        self.set_f_esp_tono(((self.freq + self.tone_freq + self.f_esp) / 1e6))
        self.set_f_fuga((self.freq / 1e6))
        self.set_f_gem_fuga(((self.freq - self.f_esp) / 1e6))
        self.set_f_gem_tono(((self.freq + self.tone_freq - self.f_esp) / 1e6))
        self.set_f_imagen(((self.freq - self.tone_freq) / 1e6))
        self.set_f_tono(((self.freq + self.tone_freq) / 1e6))
        self._freq_callback(self.freq)
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_f_esp(self):
        return self.f_esp

    def set_f_esp(self, f_esp):
        self.f_esp = f_esp
        self.set_f_esp_fuga(((self.freq + self.f_esp) / 1e6))
        self.set_f_esp_hz(self.f_esp)
        self.set_f_esp_tono(((self.freq + self.tone_freq + self.f_esp) / 1e6))
        self.set_f_gem_fuga(((self.freq - self.f_esp) / 1e6))
        self.set_f_gem_tono(((self.freq + self.tone_freq - self.f_esp) / 1e6))
        self.analog_sig_source_esp.set_frequency(self.f_esp)

    def get_e_phi(self):
        return self.e_phi

    def set_e_phi(self, e_phi):
        self.e_phi = e_phi
        self.set_ecoef(self.e_on * 10**(self.e_db/20) * np.exp(1j*np.deg2rad(self.e_phi)))

    def get_e_on(self):
        return self.e_on

    def set_e_on(self, e_on):
        self.e_on = e_on
        self._e_on_callback(self.e_on)
        self.set_ecoef(self.e_on * 10**(self.e_db/20) * np.exp(1j*np.deg2rad(self.e_phi)))
        self.set_pico_bb((self.amp*self.tono_on*(1 + self.img_on*10**(self.k_db/20))*(1 + self.d_on*10**(self.d_db/20)) + self.e_on*10**(self.e_db/20)))

    def get_e_db(self):
        return self.e_db

    def set_e_db(self, e_db):
        self.e_db = e_db
        self.set_ecoef(self.e_on * 10**(self.e_db/20) * np.exp(1j*np.deg2rad(self.e_phi)))
        self.set_pico_bb((self.amp*self.tono_on*(1 + self.img_on*10**(self.k_db/20))*(1 + self.d_on*10**(self.d_db/20)) + self.e_on*10**(self.e_db/20)))

    def get_d_phi(self):
        return self.d_phi

    def set_d_phi(self, d_phi):
        self.d_phi = d_phi
        self.set_dcoef(self.d_on * 10**(self.d_db/20) * np.exp(1j*np.deg2rad(self.d_phi)))

    def get_d_on(self):
        return self.d_on

    def set_d_on(self, d_on):
        self.d_on = d_on
        self._d_on_callback(self.d_on)
        self.set_dcoef(self.d_on * 10**(self.d_db/20) * np.exp(1j*np.deg2rad(self.d_phi)))
        self.set_pico_bb((self.amp*self.tono_on*(1 + self.img_on*10**(self.k_db/20))*(1 + self.d_on*10**(self.d_db/20)) + self.e_on*10**(self.e_db/20)))

    def get_d_db(self):
        return self.d_db

    def set_d_db(self, d_db):
        self.d_db = d_db
        self.set_dcoef(self.d_on * 10**(self.d_db/20) * np.exp(1j*np.deg2rad(self.d_phi)))
        self.set_pico_bb((self.amp*self.tono_on*(1 + self.img_on*10**(self.k_db/20))*(1 + self.d_on*10**(self.d_db/20)) + self.e_on*10**(self.e_db/20)))

    def get_amp(self):
        return self.amp

    def set_amp(self, amp):
        self.amp = amp
        self._amp_callback(self.amp)
        self.set_pico_bb((self.amp*self.tono_on*(1 + self.img_on*10**(self.k_db/20))*(1 + self.d_on*10**(self.d_db/20)) + self.e_on*10**(self.e_db/20)))
        self.analog_sig_source_x_0.set_amplitude((self.amp * self.tono_on))

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
        self._samp_rate_callback(self.samp_rate)
        self.analog_sig_source_esp.set_sampling_freq(self.samp_rate)
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)
        self.osmosdr_sink_0.set_bandwidth((0.75 * self.samp_rate), 0)

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

    def get_f_imagen(self):
        return self.f_imagen

    def set_f_imagen(self, f_imagen):
        self.f_imagen = f_imagen
        Qt.QMetaObject.invokeMethod(self._f_imagen_label, "setText", Qt.Q_ARG("QString", str(self._f_imagen_formatter(self.f_imagen))))

    def get_f_gem_tono(self):
        return self.f_gem_tono

    def set_f_gem_tono(self, f_gem_tono):
        self.f_gem_tono = f_gem_tono
        Qt.QMetaObject.invokeMethod(self._f_gem_tono_label, "setText", Qt.Q_ARG("QString", str(self._f_gem_tono_formatter(self.f_gem_tono))))

    def get_f_gem_fuga(self):
        return self.f_gem_fuga

    def set_f_gem_fuga(self, f_gem_fuga):
        self.f_gem_fuga = f_gem_fuga
        Qt.QMetaObject.invokeMethod(self._f_gem_fuga_label, "setText", Qt.Q_ARG("QString", str(self._f_gem_fuga_formatter(self.f_gem_fuga))))

    def get_f_fuga(self):
        return self.f_fuga

    def set_f_fuga(self, f_fuga):
        self.f_fuga = f_fuga
        Qt.QMetaObject.invokeMethod(self._f_fuga_label, "setText", Qt.Q_ARG("QString", str(self._f_fuga_formatter(self.f_fuga))))

    def get_f_esp_tono(self):
        return self.f_esp_tono

    def set_f_esp_tono(self, f_esp_tono):
        self.f_esp_tono = f_esp_tono
        Qt.QMetaObject.invokeMethod(self._f_esp_tono_label, "setText", Qt.Q_ARG("QString", str(self._f_esp_tono_formatter(self.f_esp_tono))))

    def get_f_esp_hz(self):
        return self.f_esp_hz

    def set_f_esp_hz(self, f_esp_hz):
        self.f_esp_hz = f_esp_hz
        Qt.QMetaObject.invokeMethod(self._f_esp_hz_label, "setText", Qt.Q_ARG("QString", str(self._f_esp_hz_formatter(self.f_esp_hz))))

    def get_f_esp_fuga(self):
        return self.f_esp_fuga

    def set_f_esp_fuga(self, f_esp_fuga):
        self.f_esp_fuga = f_esp_fuga
        Qt.QMetaObject.invokeMethod(self._f_esp_fuga_label, "setText", Qt.Q_ARG("QString", str(self._f_esp_fuga_formatter(self.f_esp_fuga))))

    def get_ecoef(self):
        return self.ecoef

    def set_ecoef(self, ecoef):
        self.ecoef = ecoef
        self.blocks_multiply_const_e.set_k(self.ecoef)

    def get_dcoef(self):
        return self.dcoef

    def set_dcoef(self, dcoef):
        self.dcoef = dcoef
        self.blocks_multiply_const_d.set_k(self.dcoef)

    def get_c(self):
        return self.c

    def set_c(self, c):
        self.c = c
        self.blocks_multiply_const_img.set_k(self.c)




def main(top_block_cls=exp10_cancelacion_espuria, options=None):

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
