#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-16 xA9: seis tonos y tasa de muestreo
# Description: bladeRF 2.0 micro xA9: seis tonos en +/-5, +/-10 y +/-20 MHz con habilitacion y amplitud propias, y selector de tasa de muestreo para encontrar la maxima sin cortes
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5.QtCore import QObject, pyqtSlot
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
    # Ajustes de aspecto que los bloques de GNU Radio no permiten configurar.
    # 1) Etiquetas de estado con letra grande.
    for nombre in ('et_suma', 'et_escala'):
        barra = getattr(self, '_%s_tool_bar' % nombre)
        ancho = 120
        for accion in barra.actions():
            etiqueta = barra.widgetForAction(accion)
            etiqueta.setStyleSheet('font-size: 15pt; font-weight: bold')
            ancho += etiqueta.sizeHint().width()
        barra.setMinimumWidth(ancho)

    # 2) Si un tono no entra en la tasa elegida, su casilla y su amplitud quedan en gris y no se pueden tocar.
    #    (El flujo igual lo deja apagado por su cuenta: esto es solo para que se vea.)
    tonos = ('m20', 'm10', 'm5', 'p5', 'p10', 'p20')
    def actualizar_disponibles():
        for columna, t in enumerate(tonos):
            entra = bool(getattr(self, 'cabe_' + t))
            self.top_grid_layout.itemAtPosition(5, columna).widget().setEnabled(entra)   # casilla de habilitar
            getattr(self, '_amp_%s_group_box' % t).setEnabled(entra)                     # botones de amplitud
    cambiar_tasa = self.set_samp_rate
    def cambiar_tasa_y_actualizar(valor):
        cambiar_tasa(valor)
        actualizar_disponibles()
    self.set_samp_rate = cambiar_tasa_y_actualizar
    actualizar_disponibles()

    # 3) Tamano inicial de la ventana segun su contenido.
    self.resize(self.top_widget.minimumSizeHint().width() + 60, self.top_widget.minimumSizeHint().height() + 70)


def snippets_main_after_init(tb):
    snipfcn_aspecto(tb)

class exp16_a9_seis_tonos_tasa(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-16 xA9: seis tonos y tasa de muestreo", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-16 xA9: seis tonos y tasa de muestreo")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp16_a9_seis_tonos_tasa")

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
        self.samp_rate = samp_rate = 25e6
        self.fraccion_util = fraccion_util = 0.4
        self.hab_p5 = hab_p5 = 0
        self.hab_p20 = hab_p20 = 0
        self.hab_p10 = hab_p10 = 1
        self.hab_m5 = hab_m5 = 0
        self.hab_m20 = hab_m20 = 0
        self.hab_m10 = hab_m10 = 0
        self.cabe_p5 = cabe_p5 = 1 if 5000000 <= fraccion_util * samp_rate else 0
        self.cabe_p20 = cabe_p20 = 1 if 20000000 <= fraccion_util * samp_rate else 0
        self.cabe_p10 = cabe_p10 = 1 if 10000000 <= fraccion_util * samp_rate else 0
        self.cabe_m5 = cabe_m5 = 1 if 5000000 <= fraccion_util * samp_rate else 0
        self.cabe_m20 = cabe_m20 = 1 if 20000000 <= fraccion_util * samp_rate else 0
        self.cabe_m10 = cabe_m10 = 1 if 10000000 <= fraccion_util * samp_rate else 0
        self.amp_p5 = amp_p5 = 0.5
        self.amp_p20 = amp_p20 = 0.5
        self.amp_p10 = amp_p10 = 0.5
        self.amp_m5 = amp_m5 = 0.5
        self.amp_m20 = amp_m20 = 0.5
        self.amp_m10 = amp_m10 = 0.5
        self.act_p5 = act_p5 = hab_p5 * cabe_p5
        self.act_p20 = act_p20 = hab_p20 * cabe_p20
        self.act_p10 = act_p10 = hab_p10 * cabe_p10
        self.act_m5 = act_m5 = hab_m5 * cabe_m5
        self.act_m20 = act_m20 = hab_m20 * cabe_m20
        self.act_m10 = act_m10 = hab_m10 * cabe_m10
        self.suma_max = suma_max = 0.95
        self.suma = suma = act_m20*amp_m20 + act_m10*amp_m10 + act_m5*amp_m5 + act_p5*amp_p5 + act_p10*amp_p10 + act_p20*amp_p20
        self.escala = escala = min(1.0, suma_max / suma) if suma > 0 else 1.0
        self.n_tabla = n_tabla = np.arange(int(round(samp_rate / 5e6)) * 1000)
        self.k_p5 = k_p5 = act_p5 * amp_p5 * escala
        self.k_p20 = k_p20 = act_p20 * amp_p20 * escala
        self.k_p10 = k_p10 = act_p10 * amp_p10 * escala
        self.k_m5 = k_m5 = act_m5 * amp_m5 * escala
        self.k_m20 = k_m20 = act_m20 * amp_m20 * escala
        self.k_m10 = k_m10 = act_m10 * amp_m10 * escala
        self.freq = freq = 100000000
        self.tx_gain = tx_gain = 0
        self.tabla = tabla = (k_m20*np.exp(2j*np.pi*(-20000000)*n_tabla/samp_rate) + k_m10*np.exp(2j*np.pi*(-10000000)*n_tabla/samp_rate) + k_m5*np.exp(2j*np.pi*(-5000000)*n_tabla/samp_rate) + k_p5*np.exp(2j*np.pi*(5000000)*n_tabla/samp_rate) + k_p10*np.exp(2j*np.pi*(10000000)*n_tabla/samp_rate) + k_p20*np.exp(2j*np.pi*(20000000)*n_tabla/samp_rate) + 0j*n_tabla).tolist()
        self.sale_p5 = sale_p5 = ((freq + (5000000)) / 1e6)
        self.sale_p20 = sale_p20 = ((freq + (20000000)) / 1e6)
        self.sale_p10 = sale_p10 = ((freq + (10000000)) / 1e6)
        self.sale_m5 = sale_m5 = ((freq + (-5000000)) / 1e6)
        self.sale_m20 = sale_m20 = ((freq + (-20000000)) / 1e6)
        self.sale_m10 = sale_m10 = ((freq + (-10000000)) / 1e6)
        self.et_suma = et_suma = suma
        self.et_escala = et_escala = escala
        self.est_p5 = est_p5 = cabe_p5
        self.est_p20 = est_p20 = cabe_p20
        self.est_p10 = est_p10 = cabe_p10
        self.est_m5 = est_m5 = cabe_m5
        self.est_m20 = est_m20 = cabe_m20
        self.est_m10 = est_m10 = cabe_m10
        self.ancho_banda = ancho_banda = min(0.9 * samp_rate, 56e6)

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
        self.top_grid_layout.addWidget(self._tx_gain_group_box, 1, 0, 1, 6)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._samp_rate_options = [15000000.0, 20000000.0, 25000000.0, 30000000.0, 40000000.0, 50000000.0]
        # Create the labels list
        self._samp_rate_labels = ['15 MSPS', '20 MSPS', '25 MSPS', '30 MSPS', '40 MSPS', '50 MSPS']
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
        self.top_grid_layout.addWidget(self._samp_rate_group_box, 2, 0, 1, 6)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
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
        self.top_grid_layout.addWidget(self._freq_group_box, 0, 0, 1, 6)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._sale_p5_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._sale_p5_formatter = lambda x: '%.0f MHz' % x
        else:
            self._sale_p5_formatter = lambda x: eng_notation.num_to_str(x)

        self._sale_p5_tool_bar.addWidget(Qt.QLabel("+5 MHz sale en "))
        self._sale_p5_label = Qt.QLabel(str(self._sale_p5_formatter(self.sale_p5)))
        self._sale_p5_tool_bar.addWidget(self._sale_p5_label)
        self.top_grid_layout.addWidget(self._sale_p5_tool_bar, 4, 3, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._sale_p20_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._sale_p20_formatter = lambda x: '%.0f MHz' % x
        else:
            self._sale_p20_formatter = lambda x: eng_notation.num_to_str(x)

        self._sale_p20_tool_bar.addWidget(Qt.QLabel("+20 MHz sale en "))
        self._sale_p20_label = Qt.QLabel(str(self._sale_p20_formatter(self.sale_p20)))
        self._sale_p20_tool_bar.addWidget(self._sale_p20_label)
        self.top_grid_layout.addWidget(self._sale_p20_tool_bar, 4, 5, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._sale_p10_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._sale_p10_formatter = lambda x: '%.0f MHz' % x
        else:
            self._sale_p10_formatter = lambda x: eng_notation.num_to_str(x)

        self._sale_p10_tool_bar.addWidget(Qt.QLabel("+10 MHz sale en "))
        self._sale_p10_label = Qt.QLabel(str(self._sale_p10_formatter(self.sale_p10)))
        self._sale_p10_tool_bar.addWidget(self._sale_p10_label)
        self.top_grid_layout.addWidget(self._sale_p10_tool_bar, 4, 4, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._sale_m5_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._sale_m5_formatter = lambda x: '%.0f MHz' % x
        else:
            self._sale_m5_formatter = lambda x: eng_notation.num_to_str(x)

        self._sale_m5_tool_bar.addWidget(Qt.QLabel("-5 MHz sale en "))
        self._sale_m5_label = Qt.QLabel(str(self._sale_m5_formatter(self.sale_m5)))
        self._sale_m5_tool_bar.addWidget(self._sale_m5_label)
        self.top_grid_layout.addWidget(self._sale_m5_tool_bar, 4, 2, 1, 1)
        for r in range(4, 5):
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
        self.top_grid_layout.addWidget(self._sale_m20_tool_bar, 4, 0, 1, 1)
        for r in range(4, 5):
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
        self.top_grid_layout.addWidget(self._sale_m10_tool_bar, 4, 1, 1, 1)
        for r in range(4, 5):
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
        _hab_p5_check_box = Qt.QCheckBox("Habilitar +5 MHz")
        self._hab_p5_choices = {True: 1, False: 0}
        self._hab_p5_choices_inv = dict((v,k) for k,v in self._hab_p5_choices.items())
        self._hab_p5_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_p5_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_p5_choices_inv[i]))
        self._hab_p5_callback(self.hab_p5)
        _hab_p5_check_box.stateChanged.connect(lambda i: self.set_hab_p5(self._hab_p5_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_p5_check_box, 5, 3, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_p20_check_box = Qt.QCheckBox("Habilitar +20 MHz")
        self._hab_p20_choices = {True: 1, False: 0}
        self._hab_p20_choices_inv = dict((v,k) for k,v in self._hab_p20_choices.items())
        self._hab_p20_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_p20_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_p20_choices_inv[i]))
        self._hab_p20_callback(self.hab_p20)
        _hab_p20_check_box.stateChanged.connect(lambda i: self.set_hab_p20(self._hab_p20_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_p20_check_box, 5, 5, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_p10_check_box = Qt.QCheckBox("Habilitar +10 MHz")
        self._hab_p10_choices = {True: 1, False: 0}
        self._hab_p10_choices_inv = dict((v,k) for k,v in self._hab_p10_choices.items())
        self._hab_p10_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_p10_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_p10_choices_inv[i]))
        self._hab_p10_callback(self.hab_p10)
        _hab_p10_check_box.stateChanged.connect(lambda i: self.set_hab_p10(self._hab_p10_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_p10_check_box, 5, 4, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_m5_check_box = Qt.QCheckBox("Habilitar -5 MHz")
        self._hab_m5_choices = {True: 1, False: 0}
        self._hab_m5_choices_inv = dict((v,k) for k,v in self._hab_m5_choices.items())
        self._hab_m5_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_m5_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_m5_choices_inv[i]))
        self._hab_m5_callback(self.hab_m5)
        _hab_m5_check_box.stateChanged.connect(lambda i: self.set_hab_m5(self._hab_m5_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_m5_check_box, 5, 2, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_m20_check_box = Qt.QCheckBox("Habilitar -20 MHz")
        self._hab_m20_choices = {True: 1, False: 0}
        self._hab_m20_choices_inv = dict((v,k) for k,v in self._hab_m20_choices.items())
        self._hab_m20_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_m20_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_m20_choices_inv[i]))
        self._hab_m20_callback(self.hab_m20)
        _hab_m20_check_box.stateChanged.connect(lambda i: self.set_hab_m20(self._hab_m20_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_m20_check_box, 5, 0, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        _hab_m10_check_box = Qt.QCheckBox("Habilitar -10 MHz")
        self._hab_m10_choices = {True: 1, False: 0}
        self._hab_m10_choices_inv = dict((v,k) for k,v in self._hab_m10_choices.items())
        self._hab_m10_callback = lambda i: Qt.QMetaObject.invokeMethod(_hab_m10_check_box, "setChecked", Qt.Q_ARG("bool", self._hab_m10_choices_inv[i]))
        self._hab_m10_callback(self.hab_m10)
        _hab_m10_check_box.stateChanged.connect(lambda i: self.set_hab_m10(self._hab_m10_choices[bool(i)]))
        self.top_grid_layout.addWidget(_hab_m10_check_box, 5, 1, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.fuente_tabla = blocks.vector_source_c(tabla, True, 1, [])
        self._et_suma_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.3f' % x:
            self._et_suma_formatter = lambda x: '%.3f' % x
        else:
            self._et_suma_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_suma_tool_bar.addWidget(Qt.QLabel("Suma de amplitudes: "))
        self._et_suma_label = Qt.QLabel(str(self._et_suma_formatter(self.et_suma)))
        self._et_suma_tool_bar.addWidget(self._et_suma_label)
        self.top_grid_layout.addWidget(self._et_suma_tool_bar, 3, 0, 1, 3)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_escala_tool_bar = Qt.QToolBar(self)

        if lambda x: 'x1 (sin cambios)' if x >= 1 else ('x%.2f (REDUCIDA)' % x):
            self._et_escala_formatter = lambda x: 'x1 (sin cambios)' if x >= 1 else ('x%.2f (REDUCIDA)' % x)
        else:
            self._et_escala_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_escala_tool_bar.addWidget(Qt.QLabel("Escala aplicada: "))
        self._et_escala_label = Qt.QLabel(str(self._et_escala_formatter(self.et_escala)))
        self._et_escala_tool_bar.addWidget(self._et_escala_label)
        self.top_grid_layout.addWidget(self._et_escala_tool_bar, 3, 3, 1, 3)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._est_p5_tool_bar = Qt.QToolBar(self)

        if lambda x: 'disponible' if x else 'NO ENTRA con esta tasa':
            self._est_p5_formatter = lambda x: 'disponible' if x else 'NO ENTRA con esta tasa'
        else:
            self._est_p5_formatter = lambda x: eng_notation.num_to_str(x)

        self._est_p5_tool_bar.addWidget(Qt.QLabel(" "))
        self._est_p5_label = Qt.QLabel(str(self._est_p5_formatter(self.est_p5)))
        self._est_p5_tool_bar.addWidget(self._est_p5_label)
        self.top_grid_layout.addWidget(self._est_p5_tool_bar, 6, 3, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._est_p20_tool_bar = Qt.QToolBar(self)

        if lambda x: 'disponible' if x else 'NO ENTRA con esta tasa':
            self._est_p20_formatter = lambda x: 'disponible' if x else 'NO ENTRA con esta tasa'
        else:
            self._est_p20_formatter = lambda x: eng_notation.num_to_str(x)

        self._est_p20_tool_bar.addWidget(Qt.QLabel(" "))
        self._est_p20_label = Qt.QLabel(str(self._est_p20_formatter(self.est_p20)))
        self._est_p20_tool_bar.addWidget(self._est_p20_label)
        self.top_grid_layout.addWidget(self._est_p20_tool_bar, 6, 5, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._est_p10_tool_bar = Qt.QToolBar(self)

        if lambda x: 'disponible' if x else 'NO ENTRA con esta tasa':
            self._est_p10_formatter = lambda x: 'disponible' if x else 'NO ENTRA con esta tasa'
        else:
            self._est_p10_formatter = lambda x: eng_notation.num_to_str(x)

        self._est_p10_tool_bar.addWidget(Qt.QLabel(" "))
        self._est_p10_label = Qt.QLabel(str(self._est_p10_formatter(self.est_p10)))
        self._est_p10_tool_bar.addWidget(self._est_p10_label)
        self.top_grid_layout.addWidget(self._est_p10_tool_bar, 6, 4, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._est_m5_tool_bar = Qt.QToolBar(self)

        if lambda x: 'disponible' if x else 'NO ENTRA con esta tasa':
            self._est_m5_formatter = lambda x: 'disponible' if x else 'NO ENTRA con esta tasa'
        else:
            self._est_m5_formatter = lambda x: eng_notation.num_to_str(x)

        self._est_m5_tool_bar.addWidget(Qt.QLabel(" "))
        self._est_m5_label = Qt.QLabel(str(self._est_m5_formatter(self.est_m5)))
        self._est_m5_tool_bar.addWidget(self._est_m5_label)
        self.top_grid_layout.addWidget(self._est_m5_tool_bar, 6, 2, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._est_m20_tool_bar = Qt.QToolBar(self)

        if lambda x: 'disponible' if x else 'NO ENTRA con esta tasa':
            self._est_m20_formatter = lambda x: 'disponible' if x else 'NO ENTRA con esta tasa'
        else:
            self._est_m20_formatter = lambda x: eng_notation.num_to_str(x)

        self._est_m20_tool_bar.addWidget(Qt.QLabel(" "))
        self._est_m20_label = Qt.QLabel(str(self._est_m20_formatter(self.est_m20)))
        self._est_m20_tool_bar.addWidget(self._est_m20_label)
        self.top_grid_layout.addWidget(self._est_m20_tool_bar, 6, 0, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._est_m10_tool_bar = Qt.QToolBar(self)

        if lambda x: 'disponible' if x else 'NO ENTRA con esta tasa':
            self._est_m10_formatter = lambda x: 'disponible' if x else 'NO ENTRA con esta tasa'
        else:
            self._est_m10_formatter = lambda x: eng_notation.num_to_str(x)

        self._est_m10_tool_bar.addWidget(Qt.QLabel(" "))
        self._est_m10_label = Qt.QLabel(str(self._est_m10_formatter(self.est_m10)))
        self._est_m10_tool_bar.addWidget(self._est_m10_label)
        self.top_grid_layout.addWidget(self._est_m10_tool_bar, 6, 1, 1, 1)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_p5_options = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        # Create the labels list
        self._amp_p5_labels = ['0.005', '0.01', '0.02', '0.05', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']
        # Create the combo box
        # Create the radio buttons
        self._amp_p5_group_box = Qt.QGroupBox("Amplitud +5 MHz" + ": ")
        self._amp_p5_box = Qt.QVBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._amp_p5_button_group = variable_chooser_button_group()
        self._amp_p5_group_box.setLayout(self._amp_p5_box)
        for i, _label in enumerate(self._amp_p5_labels):
            radio_button = Qt.QRadioButton(_label)
            self._amp_p5_box.addWidget(radio_button)
            self._amp_p5_button_group.addButton(radio_button, i)
        self._amp_p5_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_p5_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._amp_p5_options.index(i)))
        self._amp_p5_callback(self.amp_p5)
        self._amp_p5_button_group.buttonClicked[int].connect(
            lambda i: self.set_amp_p5(self._amp_p5_options[i]))
        self.top_grid_layout.addWidget(self._amp_p5_group_box, 7, 3, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
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
        self.top_grid_layout.addWidget(self._amp_p20_group_box, 7, 5, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
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
        self.top_grid_layout.addWidget(self._amp_p10_group_box, 7, 4, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_m5_options = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        # Create the labels list
        self._amp_m5_labels = ['0.005', '0.01', '0.02', '0.05', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9']
        # Create the combo box
        # Create the radio buttons
        self._amp_m5_group_box = Qt.QGroupBox("Amplitud -5 MHz" + ": ")
        self._amp_m5_box = Qt.QVBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._amp_m5_button_group = variable_chooser_button_group()
        self._amp_m5_group_box.setLayout(self._amp_m5_box)
        for i, _label in enumerate(self._amp_m5_labels):
            radio_button = Qt.QRadioButton(_label)
            self._amp_m5_box.addWidget(radio_button)
            self._amp_m5_button_group.addButton(radio_button, i)
        self._amp_m5_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_m5_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._amp_m5_options.index(i)))
        self._amp_m5_callback(self.amp_m5)
        self._amp_m5_button_group.buttonClicked[int].connect(
            lambda i: self.set_amp_m5(self._amp_m5_options[i]))
        self.top_grid_layout.addWidget(self._amp_m5_group_box, 7, 2, 1, 1)
        for r in range(7, 8):
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
        self.top_grid_layout.addWidget(self._amp_m20_group_box, 7, 0, 1, 1)
        for r in range(7, 8):
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
        self.top_grid_layout.addWidget(self._amp_m10_group_box, 7, 1, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.fuente_tabla, 0), (self.osmosdr_sink_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp16_a9_seis_tonos_tasa")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_ancho_banda(min(0.9 * self.samp_rate, 56e6))
        self._samp_rate_callback(self.samp_rate)
        self.set_cabe_m20(1 if 20000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_m10(1 if 10000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_m5(1 if 5000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_p5(1 if 5000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_p10(1 if 10000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_p20(1 if 20000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_n_tabla(np.arange(int(round(self.samp_rate / 5e6)) * 1000))
        self.set_tabla((self.k_m20*np.exp(2j*np.pi*(-20000000)*self.n_tabla/self.samp_rate) + self.k_m10*np.exp(2j*np.pi*(-10000000)*self.n_tabla/self.samp_rate) + self.k_m5*np.exp(2j*np.pi*(-5000000)*self.n_tabla/self.samp_rate) + self.k_p5*np.exp(2j*np.pi*(5000000)*self.n_tabla/self.samp_rate) + self.k_p10*np.exp(2j*np.pi*(10000000)*self.n_tabla/self.samp_rate) + self.k_p20*np.exp(2j*np.pi*(20000000)*self.n_tabla/self.samp_rate) + 0j*self.n_tabla).tolist())
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)

    def get_fraccion_util(self):
        return self.fraccion_util

    def set_fraccion_util(self, fraccion_util):
        self.fraccion_util = fraccion_util
        self.set_cabe_m20(1 if 20000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_m10(1 if 10000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_m5(1 if 5000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_p5(1 if 5000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_p10(1 if 10000000 <= self.fraccion_util * self.samp_rate else 0)
        self.set_cabe_p20(1 if 20000000 <= self.fraccion_util * self.samp_rate else 0)

    def get_hab_p5(self):
        return self.hab_p5

    def set_hab_p5(self, hab_p5):
        self.hab_p5 = hab_p5
        self._hab_p5_callback(self.hab_p5)
        self.set_act_p5(self.hab_p5 * self.cabe_p5)

    def get_hab_p20(self):
        return self.hab_p20

    def set_hab_p20(self, hab_p20):
        self.hab_p20 = hab_p20
        self._hab_p20_callback(self.hab_p20)
        self.set_act_p20(self.hab_p20 * self.cabe_p20)

    def get_hab_p10(self):
        return self.hab_p10

    def set_hab_p10(self, hab_p10):
        self.hab_p10 = hab_p10
        self._hab_p10_callback(self.hab_p10)
        self.set_act_p10(self.hab_p10 * self.cabe_p10)

    def get_hab_m5(self):
        return self.hab_m5

    def set_hab_m5(self, hab_m5):
        self.hab_m5 = hab_m5
        self._hab_m5_callback(self.hab_m5)
        self.set_act_m5(self.hab_m5 * self.cabe_m5)

    def get_hab_m20(self):
        return self.hab_m20

    def set_hab_m20(self, hab_m20):
        self.hab_m20 = hab_m20
        self._hab_m20_callback(self.hab_m20)
        self.set_act_m20(self.hab_m20 * self.cabe_m20)

    def get_hab_m10(self):
        return self.hab_m10

    def set_hab_m10(self, hab_m10):
        self.hab_m10 = hab_m10
        self._hab_m10_callback(self.hab_m10)
        self.set_act_m10(self.hab_m10 * self.cabe_m10)

    def get_cabe_p5(self):
        return self.cabe_p5

    def set_cabe_p5(self, cabe_p5):
        self.cabe_p5 = cabe_p5
        self.set_est_p5(self.cabe_p5)
        self.set_act_p5(self.hab_p5 * self.cabe_p5)

    def get_cabe_p20(self):
        return self.cabe_p20

    def set_cabe_p20(self, cabe_p20):
        self.cabe_p20 = cabe_p20
        self.set_est_p20(self.cabe_p20)
        self.set_act_p20(self.hab_p20 * self.cabe_p20)

    def get_cabe_p10(self):
        return self.cabe_p10

    def set_cabe_p10(self, cabe_p10):
        self.cabe_p10 = cabe_p10
        self.set_est_p10(self.cabe_p10)
        self.set_act_p10(self.hab_p10 * self.cabe_p10)

    def get_cabe_m5(self):
        return self.cabe_m5

    def set_cabe_m5(self, cabe_m5):
        self.cabe_m5 = cabe_m5
        self.set_est_m5(self.cabe_m5)
        self.set_act_m5(self.hab_m5 * self.cabe_m5)

    def get_cabe_m20(self):
        return self.cabe_m20

    def set_cabe_m20(self, cabe_m20):
        self.cabe_m20 = cabe_m20
        self.set_est_m20(self.cabe_m20)
        self.set_act_m20(self.hab_m20 * self.cabe_m20)

    def get_cabe_m10(self):
        return self.cabe_m10

    def set_cabe_m10(self, cabe_m10):
        self.cabe_m10 = cabe_m10
        self.set_est_m10(self.cabe_m10)
        self.set_act_m10(self.hab_m10 * self.cabe_m10)

    def get_amp_p5(self):
        return self.amp_p5

    def set_amp_p5(self, amp_p5):
        self.amp_p5 = amp_p5
        self._amp_p5_callback(self.amp_p5)
        self.set_k_p5(self.act_p5 * self.amp_p5 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_amp_p20(self):
        return self.amp_p20

    def set_amp_p20(self, amp_p20):
        self.amp_p20 = amp_p20
        self._amp_p20_callback(self.amp_p20)
        self.set_k_p20(self.act_p20 * self.amp_p20 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_amp_p10(self):
        return self.amp_p10

    def set_amp_p10(self, amp_p10):
        self.amp_p10 = amp_p10
        self._amp_p10_callback(self.amp_p10)
        self.set_k_p10(self.act_p10 * self.amp_p10 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_amp_m5(self):
        return self.amp_m5

    def set_amp_m5(self, amp_m5):
        self.amp_m5 = amp_m5
        self._amp_m5_callback(self.amp_m5)
        self.set_k_m5(self.act_m5 * self.amp_m5 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_amp_m20(self):
        return self.amp_m20

    def set_amp_m20(self, amp_m20):
        self.amp_m20 = amp_m20
        self._amp_m20_callback(self.amp_m20)
        self.set_k_m20(self.act_m20 * self.amp_m20 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_amp_m10(self):
        return self.amp_m10

    def set_amp_m10(self, amp_m10):
        self.amp_m10 = amp_m10
        self._amp_m10_callback(self.amp_m10)
        self.set_k_m10(self.act_m10 * self.amp_m10 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_act_p5(self):
        return self.act_p5

    def set_act_p5(self, act_p5):
        self.act_p5 = act_p5
        self.set_k_p5(self.act_p5 * self.amp_p5 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_act_p20(self):
        return self.act_p20

    def set_act_p20(self, act_p20):
        self.act_p20 = act_p20
        self.set_k_p20(self.act_p20 * self.amp_p20 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_act_p10(self):
        return self.act_p10

    def set_act_p10(self, act_p10):
        self.act_p10 = act_p10
        self.set_k_p10(self.act_p10 * self.amp_p10 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_act_m5(self):
        return self.act_m5

    def set_act_m5(self, act_m5):
        self.act_m5 = act_m5
        self.set_k_m5(self.act_m5 * self.amp_m5 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_act_m20(self):
        return self.act_m20

    def set_act_m20(self, act_m20):
        self.act_m20 = act_m20
        self.set_k_m20(self.act_m20 * self.amp_m20 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

    def get_act_m10(self):
        return self.act_m10

    def set_act_m10(self, act_m10):
        self.act_m10 = act_m10
        self.set_k_m10(self.act_m10 * self.amp_m10 * self.escala)
        self.set_suma(self.act_m20*self.amp_m20 + self.act_m10*self.amp_m10 + self.act_m5*self.amp_m5 + self.act_p5*self.amp_p5 + self.act_p10*self.amp_p10 + self.act_p20*self.amp_p20)

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

    def get_escala(self):
        return self.escala

    def set_escala(self, escala):
        self.escala = escala
        self.set_et_escala(self.escala)
        self.set_k_m20(self.act_m20 * self.amp_m20 * self.escala)
        self.set_k_m10(self.act_m10 * self.amp_m10 * self.escala)
        self.set_k_m5(self.act_m5 * self.amp_m5 * self.escala)
        self.set_k_p5(self.act_p5 * self.amp_p5 * self.escala)
        self.set_k_p10(self.act_p10 * self.amp_p10 * self.escala)
        self.set_k_p20(self.act_p20 * self.amp_p20 * self.escala)

    def get_n_tabla(self):
        return self.n_tabla

    def set_n_tabla(self, n_tabla):
        self.n_tabla = n_tabla
        self.set_tabla((self.k_m20*np.exp(2j*np.pi*(-20000000)*self.n_tabla/self.samp_rate) + self.k_m10*np.exp(2j*np.pi*(-10000000)*self.n_tabla/self.samp_rate) + self.k_m5*np.exp(2j*np.pi*(-5000000)*self.n_tabla/self.samp_rate) + self.k_p5*np.exp(2j*np.pi*(5000000)*self.n_tabla/self.samp_rate) + self.k_p10*np.exp(2j*np.pi*(10000000)*self.n_tabla/self.samp_rate) + self.k_p20*np.exp(2j*np.pi*(20000000)*self.n_tabla/self.samp_rate) + 0j*self.n_tabla).tolist())

    def get_k_p5(self):
        return self.k_p5

    def set_k_p5(self, k_p5):
        self.k_p5 = k_p5
        self.set_tabla((self.k_m20*np.exp(2j*np.pi*(-20000000)*self.n_tabla/self.samp_rate) + self.k_m10*np.exp(2j*np.pi*(-10000000)*self.n_tabla/self.samp_rate) + self.k_m5*np.exp(2j*np.pi*(-5000000)*self.n_tabla/self.samp_rate) + self.k_p5*np.exp(2j*np.pi*(5000000)*self.n_tabla/self.samp_rate) + self.k_p10*np.exp(2j*np.pi*(10000000)*self.n_tabla/self.samp_rate) + self.k_p20*np.exp(2j*np.pi*(20000000)*self.n_tabla/self.samp_rate) + 0j*self.n_tabla).tolist())

    def get_k_p20(self):
        return self.k_p20

    def set_k_p20(self, k_p20):
        self.k_p20 = k_p20
        self.set_tabla((self.k_m20*np.exp(2j*np.pi*(-20000000)*self.n_tabla/self.samp_rate) + self.k_m10*np.exp(2j*np.pi*(-10000000)*self.n_tabla/self.samp_rate) + self.k_m5*np.exp(2j*np.pi*(-5000000)*self.n_tabla/self.samp_rate) + self.k_p5*np.exp(2j*np.pi*(5000000)*self.n_tabla/self.samp_rate) + self.k_p10*np.exp(2j*np.pi*(10000000)*self.n_tabla/self.samp_rate) + self.k_p20*np.exp(2j*np.pi*(20000000)*self.n_tabla/self.samp_rate) + 0j*self.n_tabla).tolist())

    def get_k_p10(self):
        return self.k_p10

    def set_k_p10(self, k_p10):
        self.k_p10 = k_p10
        self.set_tabla((self.k_m20*np.exp(2j*np.pi*(-20000000)*self.n_tabla/self.samp_rate) + self.k_m10*np.exp(2j*np.pi*(-10000000)*self.n_tabla/self.samp_rate) + self.k_m5*np.exp(2j*np.pi*(-5000000)*self.n_tabla/self.samp_rate) + self.k_p5*np.exp(2j*np.pi*(5000000)*self.n_tabla/self.samp_rate) + self.k_p10*np.exp(2j*np.pi*(10000000)*self.n_tabla/self.samp_rate) + self.k_p20*np.exp(2j*np.pi*(20000000)*self.n_tabla/self.samp_rate) + 0j*self.n_tabla).tolist())

    def get_k_m5(self):
        return self.k_m5

    def set_k_m5(self, k_m5):
        self.k_m5 = k_m5
        self.set_tabla((self.k_m20*np.exp(2j*np.pi*(-20000000)*self.n_tabla/self.samp_rate) + self.k_m10*np.exp(2j*np.pi*(-10000000)*self.n_tabla/self.samp_rate) + self.k_m5*np.exp(2j*np.pi*(-5000000)*self.n_tabla/self.samp_rate) + self.k_p5*np.exp(2j*np.pi*(5000000)*self.n_tabla/self.samp_rate) + self.k_p10*np.exp(2j*np.pi*(10000000)*self.n_tabla/self.samp_rate) + self.k_p20*np.exp(2j*np.pi*(20000000)*self.n_tabla/self.samp_rate) + 0j*self.n_tabla).tolist())

    def get_k_m20(self):
        return self.k_m20

    def set_k_m20(self, k_m20):
        self.k_m20 = k_m20
        self.set_tabla((self.k_m20*np.exp(2j*np.pi*(-20000000)*self.n_tabla/self.samp_rate) + self.k_m10*np.exp(2j*np.pi*(-10000000)*self.n_tabla/self.samp_rate) + self.k_m5*np.exp(2j*np.pi*(-5000000)*self.n_tabla/self.samp_rate) + self.k_p5*np.exp(2j*np.pi*(5000000)*self.n_tabla/self.samp_rate) + self.k_p10*np.exp(2j*np.pi*(10000000)*self.n_tabla/self.samp_rate) + self.k_p20*np.exp(2j*np.pi*(20000000)*self.n_tabla/self.samp_rate) + 0j*self.n_tabla).tolist())

    def get_k_m10(self):
        return self.k_m10

    def set_k_m10(self, k_m10):
        self.k_m10 = k_m10
        self.set_tabla((self.k_m20*np.exp(2j*np.pi*(-20000000)*self.n_tabla/self.samp_rate) + self.k_m10*np.exp(2j*np.pi*(-10000000)*self.n_tabla/self.samp_rate) + self.k_m5*np.exp(2j*np.pi*(-5000000)*self.n_tabla/self.samp_rate) + self.k_p5*np.exp(2j*np.pi*(5000000)*self.n_tabla/self.samp_rate) + self.k_p10*np.exp(2j*np.pi*(10000000)*self.n_tabla/self.samp_rate) + self.k_p20*np.exp(2j*np.pi*(20000000)*self.n_tabla/self.samp_rate) + 0j*self.n_tabla).tolist())

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self._freq_callback(self.freq)
        self.set_sale_m20(((self.freq + (-20000000)) / 1e6))
        self.set_sale_m10(((self.freq + (-10000000)) / 1e6))
        self.set_sale_m5(((self.freq + (-5000000)) / 1e6))
        self.set_sale_p5(((self.freq + (5000000)) / 1e6))
        self.set_sale_p10(((self.freq + (10000000)) / 1e6))
        self.set_sale_p20(((self.freq + (20000000)) / 1e6))
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self._tx_gain_callback(self.tx_gain)
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)

    def get_tabla(self):
        return self.tabla

    def set_tabla(self, tabla):
        self.tabla = tabla
        self.fuente_tabla.set_data(self.tabla, [])

    def get_sale_p5(self):
        return self.sale_p5

    def set_sale_p5(self, sale_p5):
        self.sale_p5 = sale_p5
        Qt.QMetaObject.invokeMethod(self._sale_p5_label, "setText", Qt.Q_ARG("QString", str(self._sale_p5_formatter(self.sale_p5))))

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

    def get_sale_m5(self):
        return self.sale_m5

    def set_sale_m5(self, sale_m5):
        self.sale_m5 = sale_m5
        Qt.QMetaObject.invokeMethod(self._sale_m5_label, "setText", Qt.Q_ARG("QString", str(self._sale_m5_formatter(self.sale_m5))))

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

    def get_est_p5(self):
        return self.est_p5

    def set_est_p5(self, est_p5):
        self.est_p5 = est_p5
        Qt.QMetaObject.invokeMethod(self._est_p5_label, "setText", Qt.Q_ARG("QString", str(self._est_p5_formatter(self.est_p5))))

    def get_est_p20(self):
        return self.est_p20

    def set_est_p20(self, est_p20):
        self.est_p20 = est_p20
        Qt.QMetaObject.invokeMethod(self._est_p20_label, "setText", Qt.Q_ARG("QString", str(self._est_p20_formatter(self.est_p20))))

    def get_est_p10(self):
        return self.est_p10

    def set_est_p10(self, est_p10):
        self.est_p10 = est_p10
        Qt.QMetaObject.invokeMethod(self._est_p10_label, "setText", Qt.Q_ARG("QString", str(self._est_p10_formatter(self.est_p10))))

    def get_est_m5(self):
        return self.est_m5

    def set_est_m5(self, est_m5):
        self.est_m5 = est_m5
        Qt.QMetaObject.invokeMethod(self._est_m5_label, "setText", Qt.Q_ARG("QString", str(self._est_m5_formatter(self.est_m5))))

    def get_est_m20(self):
        return self.est_m20

    def set_est_m20(self, est_m20):
        self.est_m20 = est_m20
        Qt.QMetaObject.invokeMethod(self._est_m20_label, "setText", Qt.Q_ARG("QString", str(self._est_m20_formatter(self.est_m20))))

    def get_est_m10(self):
        return self.est_m10

    def set_est_m10(self, est_m10):
        self.est_m10 = est_m10
        Qt.QMetaObject.invokeMethod(self._est_m10_label, "setText", Qt.Q_ARG("QString", str(self._est_m10_formatter(self.est_m10))))

    def get_ancho_banda(self):
        return self.ancho_banda

    def set_ancho_banda(self, ancho_banda):
        self.ancho_banda = ancho_banda
        self.osmosdr_sink_0.set_bandwidth(self.ancho_banda, 0)




def main(top_block_cls=exp16_a9_seis_tonos_tasa, options=None):

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
