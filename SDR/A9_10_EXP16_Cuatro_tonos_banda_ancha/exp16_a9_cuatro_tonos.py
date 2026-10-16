#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-16 xA9: cuatro tonos en banda ancha
# Description: bladeRF 2.0 micro xA9 a 50 MSPS: cuatro tonos en +/-10 y +/-20 MHz, cada uno con habilitacion, amplitud y fase propias. Para superponer un tono a la imagen de otro
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


def snipfcn_aspecto(self):
    # Las etiquetas de GNU Radio no tienen tamano de letra: se lo cambiamos aca.
    for nombre in ('et_suma', 'et_escala'):
        barra = getattr(self, '_%s_tool_bar' % nombre)
        ancho = 120
        for accion in barra.actions():
            etiqueta = barra.widgetForAction(accion)
            etiqueta.setStyleSheet('font-size: 15pt; font-weight: bold')
            ancho += etiqueta.sizeHint().width()
        barra.setMinimumWidth(ancho)
    # Los deslizadores verticales de fase necesitan altura para moverlos con precision.
    for tono in ('m20', 'm10', 'p10', 'p20'):
        getattr(self, '_fase_%s_win' % tono).setMinimumHeight(200)
    self.resize(self.top_widget.minimumSizeHint().width() + 60,
                self.top_widget.minimumSizeHint().height() + 70)


def snippets_main_after_init(tb):
    snipfcn_aspecto(tb)

class exp16_a9_cuatro_tonos(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-16 xA9: cuatro tonos en banda ancha", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-16 xA9: cuatro tonos en banda ancha")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp16_a9_cuatro_tonos")

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
        self.hab_p20 = hab_p20 = 0
        self.hab_p10 = hab_p10 = 1
        self.hab_m20 = hab_m20 = 0
        self.hab_m10 = hab_m10 = 0
        self.amp_p20 = amp_p20 = 0.5
        self.amp_p10 = amp_p10 = 0.5
        self.amp_m20 = amp_m20 = 0.5
        self.amp_m10 = amp_m10 = 0.5
        self.suma_max = suma_max = 0.95
        self.suma = suma = hab_m20*amp_m20 + hab_m10*amp_m10 + hab_p10*amp_p10 + hab_p20*amp_p20
        self.freq = freq = 100000000
        self.fase_p20 = fase_p20 = 0
        self.fase_p10 = fase_p10 = 0
        self.fase_m20 = fase_m20 = 0
        self.fase_m10 = fase_m10 = 0
        self.escala = escala = min(1.0, suma_max / suma) if suma > 0 else 1.0
        self.tx_gain = tx_gain = 0
        self.samp_rate = samp_rate = 50e6
        self.sale_p20 = sale_p20 = ((freq + (20000000)) / 1e6)
        self.sale_p10 = sale_p10 = ((freq + (10000000)) / 1e6)
        self.sale_m20 = sale_m20 = ((freq + (-20000000)) / 1e6)
        self.sale_m10 = sale_m10 = ((freq + (-10000000)) / 1e6)
        self.lee_p20 = lee_p20 = fase_p20
        self.lee_p10 = lee_p10 = fase_p10
        self.lee_m20 = lee_m20 = fase_m20
        self.lee_m10 = lee_m10 = fase_m10
        self.k_p20 = k_p20 = hab_p20 * amp_p20 * escala * np.exp(1j*np.deg2rad(fase_p20))
        self.k_p10 = k_p10 = hab_p10 * amp_p10 * escala * np.exp(1j*np.deg2rad(fase_p10))
        self.k_m20 = k_m20 = hab_m20 * amp_m20 * escala * np.exp(1j*np.deg2rad(fase_m20))
        self.k_m10 = k_m10 = hab_m10 * amp_m10 * escala * np.exp(1j*np.deg2rad(fase_m10))
        self.et_suma = et_suma = suma
        self.et_escala = et_escala = escala
        self.ancho_banda = ancho_banda = 50e6

        ##################################################
        # Blocks
        ##################################################

        # Create the options list
        self._tx_gain_options = [0, 15, 30, 45, 55, 60]
        # Create the labels list
        self._tx_gain_labels = ['0 dB', '15 dB', '30 dB', '45 dB', '55 dB', '60 dB']
        # Create the combo box
        # Create the radio buttons
        self._tx_gain_group_box = Qt.QGroupBox("Ganancia de transmision (dB)" + ": ")
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
        self.top_grid_layout.addWidget(self._tx_gain_group_box, 1, 0, 1, 4)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._freq_options = [100000000, 500000000, 1000000000, 1500000000, 2000000000, 3000000000, 4000000000, 5000000000]
        # Create the labels list
        self._freq_labels = ['100 MHz', '500 MHz', '1 GHz', '1,5 GHz', '2 GHz', '3 GHz', '4 GHz', '5 GHz']
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
        self.top_grid_layout.addWidget(self._freq_group_box, 0, 0, 1, 4)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.suma_tonos = blocks.add_vcc(1)
        self._sale_p20_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._sale_p20_formatter = lambda x: '%.0f MHz' % x
        else:
            self._sale_p20_formatter = lambda x: eng_notation.num_to_str(x)

        self._sale_p20_tool_bar.addWidget(Qt.QLabel("+20 MHz sale en "))
        self._sale_p20_label = Qt.QLabel(str(self._sale_p20_formatter(self.sale_p20)))
        self._sale_p20_tool_bar.addWidget(self._sale_p20_label)
        self.top_grid_layout.addWidget(self._sale_p20_tool_bar, 3, 3, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._sale_p10_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._sale_p10_formatter = lambda x: '%.0f MHz' % x
        else:
            self._sale_p10_formatter = lambda x: eng_notation.num_to_str(x)

        self._sale_p10_tool_bar.addWidget(Qt.QLabel("+10 MHz sale en "))
        self._sale_p10_label = Qt.QLabel(str(self._sale_p10_formatter(self.sale_p10)))
        self._sale_p10_tool_bar.addWidget(self._sale_p10_label)
        self.top_grid_layout.addWidget(self._sale_p10_tool_bar, 3, 2, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._sale_m20_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._sale_m20_formatter = lambda x: '%.0f MHz' % x
        else:
            self._sale_m20_formatter = lambda x: eng_notation.num_to_str(x)

        self._sale_m20_tool_bar.addWidget(Qt.QLabel("-20 MHz sale en "))
        self._sale_m20_label = Qt.QLabel(str(self._sale_m20_formatter(self.sale_m20)))
        self._sale_m20_tool_bar.addWidget(self._sale_m20_label)
        self.top_grid_layout.addWidget(self._sale_m20_tool_bar, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._sale_m10_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._sale_m10_formatter = lambda x: '%.0f MHz' % x
        else:
            self._sale_m10_formatter = lambda x: eng_notation.num_to_str(x)

        self._sale_m10_tool_bar.addWidget(Qt.QLabel("-10 MHz sale en "))
        self._sale_m10_label = Qt.QLabel(str(self._sale_m10_formatter(self.sale_m10)))
        self._sale_m10_tool_bar.addWidget(self._sale_m10_label)
        self.top_grid_layout.addWidget(self._sale_m10_tool_bar, 3, 1, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
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
        self.osmosdr_sink_0.set_bandwidth(ancho_banda, 0)
        self.mult_p20 = blocks.multiply_const_cc(k_p20)
        self.mult_p10 = blocks.multiply_const_cc(k_p10)
        self.mult_m20 = blocks.multiply_const_cc(k_m20)
        self.mult_m10 = blocks.multiply_const_cc(k_m10)
        self._lee_p20_tool_bar = Qt.QToolBar(self)

        if lambda x: '%+.0f grados' % x:
            self._lee_p20_formatter = lambda x: '%+.0f grados' % x
        else:
            self._lee_p20_formatter = lambda x: eng_notation.num_to_str(x)

        self._lee_p20_tool_bar.addWidget(Qt.QLabel("Fase +20 MHz: "))
        self._lee_p20_label = Qt.QLabel(str(self._lee_p20_formatter(self.lee_p20)))
        self._lee_p20_tool_bar.addWidget(self._lee_p20_label)
        self.top_grid_layout.addWidget(self._lee_p20_tool_bar, 7, 3, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._lee_p10_tool_bar = Qt.QToolBar(self)

        if lambda x: '%+.0f grados' % x:
            self._lee_p10_formatter = lambda x: '%+.0f grados' % x
        else:
            self._lee_p10_formatter = lambda x: eng_notation.num_to_str(x)

        self._lee_p10_tool_bar.addWidget(Qt.QLabel("Fase +10 MHz: "))
        self._lee_p10_label = Qt.QLabel(str(self._lee_p10_formatter(self.lee_p10)))
        self._lee_p10_tool_bar.addWidget(self._lee_p10_label)
        self.top_grid_layout.addWidget(self._lee_p10_tool_bar, 7, 2, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._lee_m20_tool_bar = Qt.QToolBar(self)

        if lambda x: '%+.0f grados' % x:
            self._lee_m20_formatter = lambda x: '%+.0f grados' % x
        else:
            self._lee_m20_formatter = lambda x: eng_notation.num_to_str(x)

        self._lee_m20_tool_bar.addWidget(Qt.QLabel("Fase -20 MHz: "))
        self._lee_m20_label = Qt.QLabel(str(self._lee_m20_formatter(self.lee_m20)))
        self._lee_m20_tool_bar.addWidget(self._lee_m20_label)
        self.top_grid_layout.addWidget(self._lee_m20_tool_bar, 7, 0, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._lee_m10_tool_bar = Qt.QToolBar(self)

        if lambda x: '%+.0f grados' % x:
            self._lee_m10_formatter = lambda x: '%+.0f grados' % x
        else:
            self._lee_m10_formatter = lambda x: eng_notation.num_to_str(x)

        self._lee_m10_tool_bar.addWidget(Qt.QLabel("Fase -10 MHz: "))
        self._lee_m10_label = Qt.QLabel(str(self._lee_m10_formatter(self.lee_m10)))
        self._lee_m10_tool_bar.addWidget(self._lee_m10_label)
        self.top_grid_layout.addWidget(self._lee_m10_tool_bar, 7, 1, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_p20_check_box = Qt.QCheckBox("Habilitar +20 MHz")
        self._hab_p20_choices = {True: 1, False: 0}
        self._hab_p20_choices_inv = dict((v,k) for k,v in self._hab_p20_choices.items())
        self._hab_p20_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_p20_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_p20_choices_inv[i]))
        self._hab_p20_callback(self.hab_p20)
        _hab_p20_check_box.stateChanged.connect(lambda i: self.set_hab_p20(self._hab_p20_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_p20_check_box, 4, 3, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_p10_check_box = Qt.QCheckBox("Habilitar +10 MHz")
        self._hab_p10_choices = {True: 1, False: 0}
        self._hab_p10_choices_inv = dict((v,k) for k,v in self._hab_p10_choices.items())
        self._hab_p10_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_p10_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_p10_choices_inv[i]))
        self._hab_p10_callback(self.hab_p10)
        _hab_p10_check_box.stateChanged.connect(lambda i: self.set_hab_p10(self._hab_p10_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_p10_check_box, 4, 2, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_m20_check_box = Qt.QCheckBox("Habilitar -20 MHz")
        self._hab_m20_choices = {True: 1, False: 0}
        self._hab_m20_choices_inv = dict((v,k) for k,v in self._hab_m20_choices.items())
        self._hab_m20_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_m20_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_m20_choices_inv[i]))
        self._hab_m20_callback(self.hab_m20)
        _hab_m20_check_box.stateChanged.connect(lambda i: self.set_hab_m20(self._hab_m20_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_m20_check_box, 4, 0, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_m10_check_box = Qt.QCheckBox("Habilitar -10 MHz")
        self._hab_m10_choices = {True: 1, False: 0}
        self._hab_m10_choices_inv = dict((v,k) for k,v in self._hab_m10_choices.items())
        self._hab_m10_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_m10_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_m10_choices_inv[i]))
        self._hab_m10_callback(self.hab_m10)
        _hab_m10_check_box.stateChanged.connect(lambda i: self.set_hab_m10(self._hab_m10_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_m10_check_box, 4, 1, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.fuente_p20 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 20000000, 1, 0, 0)
        self.fuente_p10 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 10000000, 1, 0, 0)
        self.fuente_m20 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-20000000), 1, 0, 0)
        self.fuente_m10 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-10000000), 1, 0, 0)
        self._fase_p20_range = qtgui.Range(-180, 180, 1, 0, 160)
        self._fase_p20_win = qtgui.RangeWidget(self._fase_p20_range, self.set_fase_p20, "Fase", "slider", float, QtCore.Qt.Vertical)
        self.top_grid_layout.addWidget(self._fase_p20_win, 6, 3, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._fase_p10_range = qtgui.Range(-180, 180, 1, 0, 160)
        self._fase_p10_win = qtgui.RangeWidget(self._fase_p10_range, self.set_fase_p10, "Fase", "slider", float, QtCore.Qt.Vertical)
        self.top_grid_layout.addWidget(self._fase_p10_win, 6, 2, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._fase_m20_range = qtgui.Range(-180, 180, 1, 0, 160)
        self._fase_m20_win = qtgui.RangeWidget(self._fase_m20_range, self.set_fase_m20, "Fase", "slider", float, QtCore.Qt.Vertical)
        self.top_grid_layout.addWidget(self._fase_m20_win, 6, 0, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._fase_m10_range = qtgui.Range(-180, 180, 1, 0, 160)
        self._fase_m10_win = qtgui.RangeWidget(self._fase_m10_range, self.set_fase_m10, "Fase", "slider", float, QtCore.Qt.Vertical)
        self.top_grid_layout.addWidget(self._fase_m10_win, 6, 1, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_suma_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.3f' % x:
            self._et_suma_formatter = lambda x: '%.3f' % x
        else:
            self._et_suma_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_suma_tool_bar.addWidget(Qt.QLabel("Suma de amplitudes: "))
        self._et_suma_label = Qt.QLabel(str(self._et_suma_formatter(self.et_suma)))
        self._et_suma_tool_bar.addWidget(self._et_suma_label)
        self.top_grid_layout.addWidget(self._et_suma_tool_bar, 2, 0, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_escala_tool_bar = Qt.QToolBar(self)

        if lambda x: 'x1 (sin cambios)' if x >= 1 else ('x%.2f (REDUCIDA)' % x):
            self._et_escala_formatter = lambda x: 'x1 (sin cambios)' if x >= 1 else ('x%.2f (REDUCIDA)' % x)
        else:
            self._et_escala_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_escala_tool_bar.addWidget(Qt.QLabel("Escala aplicada: "))
        self._et_escala_label = Qt.QLabel(str(self._et_escala_formatter(self.et_escala)))
        self._et_escala_tool_bar.addWidget(self._et_escala_label)
        self.top_grid_layout.addWidget(self._et_escala_tool_bar, 2, 2, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_p20_options = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        # Create the labels list
        self._amp_p20_labels = ['0.005', '0.01', '0.02', '0.05', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']
        # Create the combo box
        # Create the radio buttons
        self._amp_p20_group_box = Qt.QGroupBox("Amplitud +20 MHz" + ": ")
        self._amp_p20_box = Qt.QVBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._amp_p20_button_group = variable_chooser_button_group()
        self._amp_p20_group_box.setLayout(self._amp_p20_box)
        for i, _label in enumerate(self._amp_p20_labels):
            radio_button = Qt.QRadioButton(_label)
            self._amp_p20_box.addWidget(radio_button)
            self._amp_p20_button_group.addButton(radio_button, i)
        self._amp_p20_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_p20_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._amp_p20_options.index(i)))
        self._amp_p20_callback(self.amp_p20)
        self._amp_p20_button_group.buttonClicked[int].connect(
            lambda i: self.set_amp_p20(self._amp_p20_options[i]))
        self.top_grid_layout.addWidget(self._amp_p20_group_box, 5, 3, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_p10_options = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        # Create the labels list
        self._amp_p10_labels = ['0.005', '0.01', '0.02', '0.05', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']
        # Create the combo box
        # Create the radio buttons
        self._amp_p10_group_box = Qt.QGroupBox("Amplitud +10 MHz" + ": ")
        self._amp_p10_box = Qt.QVBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._amp_p10_button_group = variable_chooser_button_group()
        self._amp_p10_group_box.setLayout(self._amp_p10_box)
        for i, _label in enumerate(self._amp_p10_labels):
            radio_button = Qt.QRadioButton(_label)
            self._amp_p10_box.addWidget(radio_button)
            self._amp_p10_button_group.addButton(radio_button, i)
        self._amp_p10_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_p10_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._amp_p10_options.index(i)))
        self._amp_p10_callback(self.amp_p10)
        self._amp_p10_button_group.buttonClicked[int].connect(
            lambda i: self.set_amp_p10(self._amp_p10_options[i]))
        self.top_grid_layout.addWidget(self._amp_p10_group_box, 5, 2, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_m20_options = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        # Create the labels list
        self._amp_m20_labels = ['0.005', '0.01', '0.02', '0.05', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']
        # Create the combo box
        # Create the radio buttons
        self._amp_m20_group_box = Qt.QGroupBox("Amplitud -20 MHz" + ": ")
        self._amp_m20_box = Qt.QVBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._amp_m20_button_group = variable_chooser_button_group()
        self._amp_m20_group_box.setLayout(self._amp_m20_box)
        for i, _label in enumerate(self._amp_m20_labels):
            radio_button = Qt.QRadioButton(_label)
            self._amp_m20_box.addWidget(radio_button)
            self._amp_m20_button_group.addButton(radio_button, i)
        self._amp_m20_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_m20_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._amp_m20_options.index(i)))
        self._amp_m20_callback(self.amp_m20)
        self._amp_m20_button_group.buttonClicked[int].connect(
            lambda i: self.set_amp_m20(self._amp_m20_options[i]))
        self.top_grid_layout.addWidget(self._amp_m20_group_box, 5, 0, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_m10_options = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        # Create the labels list
        self._amp_m10_labels = ['0.005', '0.01', '0.02', '0.05', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']
        # Create the combo box
        # Create the radio buttons
        self._amp_m10_group_box = Qt.QGroupBox("Amplitud -10 MHz" + ": ")
        self._amp_m10_box = Qt.QVBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._amp_m10_button_group = variable_chooser_button_group()
        self._amp_m10_group_box.setLayout(self._amp_m10_box)
        for i, _label in enumerate(self._amp_m10_labels):
            radio_button = Qt.QRadioButton(_label)
            self._amp_m10_box.addWidget(radio_button)
            self._amp_m10_button_group.addButton(radio_button, i)
        self._amp_m10_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_m10_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._amp_m10_options.index(i)))
        self._amp_m10_callback(self.amp_m10)
        self._amp_m10_button_group.buttonClicked[int].connect(
            lambda i: self.set_amp_m10(self._amp_m10_options[i]))
        self.top_grid_layout.addWidget(self._amp_m10_group_box, 5, 1, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.fuente_m10, 0), (self.mult_m10, 0))
        self.connect((self.fuente_m20, 0), (self.mult_m20, 0))
        self.connect((self.fuente_p10, 0), (self.mult_p10, 0))
        self.connect((self.fuente_p20, 0), (self.mult_p20, 0))
        self.connect((self.mult_m10, 0), (self.suma_tonos, 1))
        self.connect((self.mult_m20, 0), (self.suma_tonos, 0))
        self.connect((self.mult_p10, 0), (self.suma_tonos, 2))
        self.connect((self.mult_p20, 0), (self.suma_tonos, 3))
        self.connect((self.suma_tonos, 0), (self.osmosdr_sink_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp16_a9_cuatro_tonos")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_hab_p20(self):
        return self.hab_p20

    def set_hab_p20(self, hab_p20):
        self.hab_p20 = hab_p20
        self._hab_p20_callback(self.hab_p20)
        self.set_suma(self.hab_m20*self.amp_m20 + self.hab_m10*self.amp_m10 + self.hab_p10*self.amp_p10 + self.hab_p20*self.amp_p20)
        self.set_k_p20(self.hab_p20 * self.amp_p20 * self.escala * np.exp(1j*np.deg2rad(self.fase_p20)))

    def get_hab_p10(self):
        return self.hab_p10

    def set_hab_p10(self, hab_p10):
        self.hab_p10 = hab_p10
        self._hab_p10_callback(self.hab_p10)
        self.set_suma(self.hab_m20*self.amp_m20 + self.hab_m10*self.amp_m10 + self.hab_p10*self.amp_p10 + self.hab_p20*self.amp_p20)
        self.set_k_p10(self.hab_p10 * self.amp_p10 * self.escala * np.exp(1j*np.deg2rad(self.fase_p10)))

    def get_hab_m20(self):
        return self.hab_m20

    def set_hab_m20(self, hab_m20):
        self.hab_m20 = hab_m20
        self._hab_m20_callback(self.hab_m20)
        self.set_suma(self.hab_m20*self.amp_m20 + self.hab_m10*self.amp_m10 + self.hab_p10*self.amp_p10 + self.hab_p20*self.amp_p20)
        self.set_k_m20(self.hab_m20 * self.amp_m20 * self.escala * np.exp(1j*np.deg2rad(self.fase_m20)))

    def get_hab_m10(self):
        return self.hab_m10

    def set_hab_m10(self, hab_m10):
        self.hab_m10 = hab_m10
        self._hab_m10_callback(self.hab_m10)
        self.set_suma(self.hab_m20*self.amp_m20 + self.hab_m10*self.amp_m10 + self.hab_p10*self.amp_p10 + self.hab_p20*self.amp_p20)
        self.set_k_m10(self.hab_m10 * self.amp_m10 * self.escala * np.exp(1j*np.deg2rad(self.fase_m10)))

    def get_amp_p20(self):
        return self.amp_p20

    def set_amp_p20(self, amp_p20):
        self.amp_p20 = amp_p20
        self._amp_p20_callback(self.amp_p20)
        self.set_suma(self.hab_m20*self.amp_m20 + self.hab_m10*self.amp_m10 + self.hab_p10*self.amp_p10 + self.hab_p20*self.amp_p20)
        self.set_k_p20(self.hab_p20 * self.amp_p20 * self.escala * np.exp(1j*np.deg2rad(self.fase_p20)))

    def get_amp_p10(self):
        return self.amp_p10

    def set_amp_p10(self, amp_p10):
        self.amp_p10 = amp_p10
        self._amp_p10_callback(self.amp_p10)
        self.set_suma(self.hab_m20*self.amp_m20 + self.hab_m10*self.amp_m10 + self.hab_p10*self.amp_p10 + self.hab_p20*self.amp_p20)
        self.set_k_p10(self.hab_p10 * self.amp_p10 * self.escala * np.exp(1j*np.deg2rad(self.fase_p10)))

    def get_amp_m20(self):
        return self.amp_m20

    def set_amp_m20(self, amp_m20):
        self.amp_m20 = amp_m20
        self._amp_m20_callback(self.amp_m20)
        self.set_suma(self.hab_m20*self.amp_m20 + self.hab_m10*self.amp_m10 + self.hab_p10*self.amp_p10 + self.hab_p20*self.amp_p20)
        self.set_k_m20(self.hab_m20 * self.amp_m20 * self.escala * np.exp(1j*np.deg2rad(self.fase_m20)))

    def get_amp_m10(self):
        return self.amp_m10

    def set_amp_m10(self, amp_m10):
        self.amp_m10 = amp_m10
        self._amp_m10_callback(self.amp_m10)
        self.set_suma(self.hab_m20*self.amp_m20 + self.hab_m10*self.amp_m10 + self.hab_p10*self.amp_p10 + self.hab_p20*self.amp_p20)
        self.set_k_m10(self.hab_m10 * self.amp_m10 * self.escala * np.exp(1j*np.deg2rad(self.fase_m10)))

    def get_suma_max(self):
        return self.suma_max

    def set_suma_max(self, suma_max):
        self.suma_max = suma_max
        self.set_escala(min(1.0, self.suma_max / self.suma) if self.suma > 0 else 1.0)

    def get_suma(self):
        return self.suma

    def set_suma(self, suma):
        self.suma = suma
        self.set_et_suma(self.suma)
        self.set_escala(min(1.0, self.suma_max / self.suma) if self.suma > 0 else 1.0)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self._freq_callback(self.freq)
        self.set_sale_m20(((self.freq + (-20000000)) / 1e6))
        self.set_sale_m10(((self.freq + (-10000000)) / 1e6))
        self.set_sale_p10(((self.freq + (10000000)) / 1e6))
        self.set_sale_p20(((self.freq + (20000000)) / 1e6))
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_fase_p20(self):
        return self.fase_p20

    def set_fase_p20(self, fase_p20):
        self.fase_p20 = fase_p20
        self.set_lee_p20(self.fase_p20)
        self.set_k_p20(self.hab_p20 * self.amp_p20 * self.escala * np.exp(1j*np.deg2rad(self.fase_p20)))

    def get_fase_p10(self):
        return self.fase_p10

    def set_fase_p10(self, fase_p10):
        self.fase_p10 = fase_p10
        self.set_lee_p10(self.fase_p10)
        self.set_k_p10(self.hab_p10 * self.amp_p10 * self.escala * np.exp(1j*np.deg2rad(self.fase_p10)))

    def get_fase_m20(self):
        return self.fase_m20

    def set_fase_m20(self, fase_m20):
        self.fase_m20 = fase_m20
        self.set_lee_m20(self.fase_m20)
        self.set_k_m20(self.hab_m20 * self.amp_m20 * self.escala * np.exp(1j*np.deg2rad(self.fase_m20)))

    def get_fase_m10(self):
        return self.fase_m10

    def set_fase_m10(self, fase_m10):
        self.fase_m10 = fase_m10
        self.set_lee_m10(self.fase_m10)
        self.set_k_m10(self.hab_m10 * self.amp_m10 * self.escala * np.exp(1j*np.deg2rad(self.fase_m10)))

    def get_escala(self):
        return self.escala

    def set_escala(self, escala):
        self.escala = escala
        self.set_et_escala(self.escala)
        self.set_k_m20(self.hab_m20 * self.amp_m20 * self.escala * np.exp(1j*np.deg2rad(self.fase_m20)))
        self.set_k_m10(self.hab_m10 * self.amp_m10 * self.escala * np.exp(1j*np.deg2rad(self.fase_m10)))
        self.set_k_p10(self.hab_p10 * self.amp_p10 * self.escala * np.exp(1j*np.deg2rad(self.fase_p10)))
        self.set_k_p20(self.hab_p20 * self.amp_p20 * self.escala * np.exp(1j*np.deg2rad(self.fase_p20)))

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
        self.fuente_m20.set_sampling_freq(self.samp_rate)
        self.fuente_m10.set_sampling_freq(self.samp_rate)
        self.fuente_p10.set_sampling_freq(self.samp_rate)
        self.fuente_p20.set_sampling_freq(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)

    def get_sale_p20(self):
        return self.sale_p20

    def set_sale_p20(self, sale_p20):
        self.sale_p20 = sale_p20
        Qt.QMetaObject.invokeMethod(self._sale_p20_label, "setText", Qt.Q_ARG("QString", str(self._sale_p20_formatter(self.sale_p20))))

    def get_sale_p10(self):
        return self.sale_p10

    def set_sale_p10(self, sale_p10):
        self.sale_p10 = sale_p10
        Qt.QMetaObject.invokeMethod(self._sale_p10_label, "setText", Qt.Q_ARG("QString", str(self._sale_p10_formatter(self.sale_p10))))

    def get_sale_m20(self):
        return self.sale_m20

    def set_sale_m20(self, sale_m20):
        self.sale_m20 = sale_m20
        Qt.QMetaObject.invokeMethod(self._sale_m20_label, "setText", Qt.Q_ARG("QString", str(self._sale_m20_formatter(self.sale_m20))))

    def get_sale_m10(self):
        return self.sale_m10

    def set_sale_m10(self, sale_m10):
        self.sale_m10 = sale_m10
        Qt.QMetaObject.invokeMethod(self._sale_m10_label, "setText", Qt.Q_ARG("QString", str(self._sale_m10_formatter(self.sale_m10))))

    def get_lee_p20(self):
        return self.lee_p20

    def set_lee_p20(self, lee_p20):
        self.lee_p20 = lee_p20
        Qt.QMetaObject.invokeMethod(self._lee_p20_label, "setText", Qt.Q_ARG("QString", str(self._lee_p20_formatter(self.lee_p20))))

    def get_lee_p10(self):
        return self.lee_p10

    def set_lee_p10(self, lee_p10):
        self.lee_p10 = lee_p10
        Qt.QMetaObject.invokeMethod(self._lee_p10_label, "setText", Qt.Q_ARG("QString", str(self._lee_p10_formatter(self.lee_p10))))

    def get_lee_m20(self):
        return self.lee_m20

    def set_lee_m20(self, lee_m20):
        self.lee_m20 = lee_m20
        Qt.QMetaObject.invokeMethod(self._lee_m20_label, "setText", Qt.Q_ARG("QString", str(self._lee_m20_formatter(self.lee_m20))))

    def get_lee_m10(self):
        return self.lee_m10

    def set_lee_m10(self, lee_m10):
        self.lee_m10 = lee_m10
        Qt.QMetaObject.invokeMethod(self._lee_m10_label, "setText", Qt.Q_ARG("QString", str(self._lee_m10_formatter(self.lee_m10))))

    def get_k_p20(self):
        return self.k_p20

    def set_k_p20(self, k_p20):
        self.k_p20 = k_p20
        self.mult_p20.set_k(self.k_p20)

    def get_k_p10(self):
        return self.k_p10

    def set_k_p10(self, k_p10):
        self.k_p10 = k_p10
        self.mult_p10.set_k(self.k_p10)

    def get_k_m20(self):
        return self.k_m20

    def set_k_m20(self, k_m20):
        self.k_m20 = k_m20
        self.mult_m20.set_k(self.k_m20)

    def get_k_m10(self):
        return self.k_m10

    def set_k_m10(self, k_m10):
        self.k_m10 = k_m10
        self.mult_m10.set_k(self.k_m10)

    def get_et_suma(self):
        return self.et_suma

    def set_et_suma(self, et_suma):
        self.et_suma = et_suma
        Qt.QMetaObject.invokeMethod(self._et_suma_label, "setText", Qt.Q_ARG("QString", str(self._et_suma_formatter(self.et_suma))))

    def get_et_escala(self):
        return self.et_escala

    def set_et_escala(self, et_escala):
        self.et_escala = et_escala
        Qt.QMetaObject.invokeMethod(self._et_escala_label, "setText", Qt.Q_ARG("QString", str(self._et_escala_formatter(self.et_escala))))

    def get_ancho_banda(self):
        return self.ancho_banda

    def set_ancho_banda(self, ancho_banda):
        self.ancho_banda = ancho_banda
        self.osmosdr_sink_0.set_bandwidth(self.ancho_banda, 0)




def main(top_block_cls=exp16_a9_cuatro_tonos, options=None):

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
