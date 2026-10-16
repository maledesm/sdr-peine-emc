#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-14 peine calibrado con ecualizador
# Description: Peine por tandas de 300 a 510 MHz, calibracion de la placa al arrancar y una amplitud elegible por tono (ecualizador). Ganancia fija en 30
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


def snipfcn_calibracion(self):
    # Corre ANTES de que el osmocom Sink abra la placa, cuando todavia esta libre.
    # Deja instalada la tabla de fuga: la biblioteca de la placa la carga sola y la aplica en cada sintonia.
    import os, shutil, subprocess, time

    cli = r"C:\Program Files\bladeRF\x64\bladeRF-cli.exe"
    carpeta = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(os.environ["APPDATA"], "Nuand", "bladeRF")    # donde la biblioteca busca las tablas

    def correr(comandos):
        """Ejecuta comandos de bladeRF-cli y muestra la salida en la consola."""
        args = [cli]
        for c in comandos:
            args += ["-e", c]
        p = subprocess.Popen(args, cwd=carpeta, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for linea in p.stdout:
            print("   [bladeRF-cli] " + linea.rstrip())
        p.wait()

    print("=== EXP-14: calibracion antes de transmitir ===")
    t_inicio = time.time()
    os.makedirs(destino, exist_ok=True)

    if self.calibrar_lms:
        print("1) calibrate lms")
        correr(["calibrate lms"])

    if self.generar_tabla:
        print("2) Generando la tabla de fuga para las portadoras del peine.")
        for f in os.listdir(carpeta):                       # borrar tablas de corridas anteriores
            if f.endswith("_dc_tx.tbl"):
                os.remove(os.path.join(carpeta, f))
        f_min = "%dM" % round(min(self.portadoras) / 1e6)
        f_max = "%dM" % round(max(self.portadoras) / 1e6)
        correr(["set gain tx1 %d" % self.ganancia_tabla, "calibrate table dc tx %s %s 20M" % (f_min, f_max)])
        for f in os.listdir(carpeta):
            if f.endswith("_dc_tx.tbl"):
                shutil.copyfile(os.path.join(carpeta, f), os.path.join(destino, f))

    # Si una corrida anterior dejo la tabla desactivada y no hay una activa, volver a activarla.
    for f in os.listdir(destino):
        if f.endswith("_dc_tx.tbl.desactivada"):
            activa = os.path.join(destino, f[:-len(".desactivada")])
            if os.path.isfile(activa):
                os.remove(os.path.join(destino, f))
            else:
                os.replace(os.path.join(destino, f), activa)

    instaladas = [f for f in os.listdir(destino) if f.endswith("_dc_tx.tbl")]
    print("3) Tabla de fuga instalada: " + (", ".join(instaladas) or "NINGUNA"))
    print("=== Fin de la calibracion ===")

    lineas = ["Calibracion terminada en %.0f segundos." % (time.time() - t_inicio), "",
              "calibrate lms: " + ("ejecutada" if self.calibrar_lms else "omitida"),
              "Tabla de fuga: " + ("generada ahora" if self.generar_tabla else "la de una corrida anterior"),
              "Tabla instalada: " + ("si" if instaladas else "NO HAY NINGUNA"),
              "", "Al aceptar se abre la placa y empieza a transmitir."]
    try:
        import winsound
        for _ in range(3):
            winsound.Beep(1000, 250)
    except Exception:
        pass
    try:
        Qt.QMessageBox.information(None, "EXP-14: calibracion terminada", chr(10).join(lineas))
    except Exception as e:
        print("No se pudo mostrar el cartel: %s" % e)
    print("=== Abriendo la placa para transmitir ===")

def snipfcn_aspecto(self):
    # Ajustes de aspecto que los bloques de GNU Radio no permiten configurar.
    # 1) Etiquetas de estado con letra grande, y con ancho minimo para que no se corten.
    extra = {'et_pico': 130, 'et_paso': 30}
    for nombre in ('et_portadora', 'et_inferior', 'et_superior', 'et_paso', 'et_pico'):
        barra = getattr(self, '_%s_tool_bar' % nombre)
        ancho = 30 + extra.get(nombre, 0)
        for accion in barra.actions():
            etiqueta = barra.widgetForAction(accion)
            etiqueta.setStyleSheet('font-size: 15pt; font-weight: bold')
            ancho += etiqueta.sizeHint().width()
        barra.setMinimumWidth(ancho)
    # 2) Selectores de amplitud: sin su etiqueta propia (la frecuencia esta en la fila de arriba) y sin cortarse.
    for f in range(300, 511, 10):
        barra = getattr(self, '_amp_%d_tool_bar' % f)
        barra.actions()[0].setVisible(False)
        selector = getattr(self, '_amp_%d_combo_box' % f)
        selector.setFixedWidth(56)
        barra.setMinimumWidth(62)
    # 3) Menos espacio entre columnas y tamano inicial de la ventana segun su contenido.
    self.top_grid_layout.setHorizontalSpacing(2)
    self.resize(self.top_widget.minimumSizeHint().width() + 50, 270)


def snippets_main_after_init(tb):
    snipfcn_aspecto(tb)

def snippets_init_before_blocks(tb):
    snipfcn_calibracion(tb)

class exp14_peine_ecualizado(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-14 peine calibrado con ecualizador", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-14 peine calibrado con ecualizador")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp14_peine_ecualizado")

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
        self.portadoras = portadoras = [305e6 + 20e6*i for i in range(11)]
        self.indice_medido = indice_medido = 0
        self.portadora_manual = portadora_manual = 305000000
        self.modo = modo = 0
        self.indice = indice = min(max(int(round(indice_medido)), 0), len(portadoras) - 1)
        self.amp_510 = amp_510 = 0.4
        self.amp_500 = amp_500 = 0.4
        self.amp_490 = amp_490 = 0.4
        self.amp_480 = amp_480 = 0.4
        self.amp_470 = amp_470 = 0.4
        self.amp_460 = amp_460 = 0.4
        self.amp_450 = amp_450 = 0.4
        self.amp_440 = amp_440 = 0.4
        self.amp_430 = amp_430 = 0.4
        self.amp_420 = amp_420 = 0.4
        self.amp_410 = amp_410 = 0.4
        self.amp_400 = amp_400 = 0.4
        self.amp_390 = amp_390 = 0.4
        self.amp_380 = amp_380 = 0.4
        self.amp_370 = amp_370 = 0.4
        self.amp_360 = amp_360 = 0.4
        self.amp_350 = amp_350 = 0.4
        self.amp_340 = amp_340 = 0.4
        self.amp_330 = amp_330 = 0.4
        self.amp_320 = amp_320 = 0.4
        self.amp_310 = amp_310 = 0.4
        self.amp_300 = amp_300 = 0.4
        self.indice_activo = indice_activo = int(round((portadora_manual - portadoras[0]) / 20e6)) if modo == 1 else indice
        self.amps_sup = amps_sup = [amp_310, amp_330, amp_350, amp_370, amp_390, amp_410, amp_430, amp_450, amp_470, amp_490, amp_510]
        self.amps_inf = amps_inf = [amp_300, amp_320, amp_340, amp_360, amp_380, amp_400, amp_420, amp_440, amp_460, amp_480, amp_500]
        self.tx_gain = tx_gain = 30
        self.freq = freq = portadoras[indice_activo]
        self.f_tono = f_tono = 5e6
        self.a_sup = a_sup = amps_sup[indice_activo]
        self.a_inf = a_inf = amps_inf[indice_activo]
        self.tasa_ctrl = tasa_ctrl = 10e3
        self.samp_rate = samp_rate = 20e6
        self.permanencia = permanencia = 2
        self.generar_tabla = generar_tabla = True
        self.ganancia_tabla = ganancia_tabla = tx_gain
        self.et_superior = et_superior = ((freq + f_tono) / 1e6)
        self.et_portadora = et_portadora = (freq / 1e6)
        self.et_pico = et_pico = (a_inf + a_sup)
        self.et_paso = et_paso = (indice_activo + 1)
        self.et_inferior = et_inferior = ((freq - f_tono) / 1e6)
        self.enc_mhz = enc_mhz = ''
        self.enc_amp = enc_amp = ''
        self.enc_510 = enc_510 = ''
        self.enc_500 = enc_500 = ''
        self.enc_490 = enc_490 = ''
        self.enc_480 = enc_480 = ''
        self.enc_470 = enc_470 = ''
        self.enc_460 = enc_460 = ''
        self.enc_450 = enc_450 = ''
        self.enc_440 = enc_440 = ''
        self.enc_430 = enc_430 = ''
        self.enc_420 = enc_420 = ''
        self.enc_410 = enc_410 = ''
        self.enc_400 = enc_400 = ''
        self.enc_390 = enc_390 = ''
        self.enc_380 = enc_380 = ''
        self.enc_370 = enc_370 = ''
        self.enc_360 = enc_360 = ''
        self.enc_350 = enc_350 = ''
        self.enc_340 = enc_340 = ''
        self.enc_330 = enc_330 = ''
        self.enc_320 = enc_320 = ''
        self.enc_310 = enc_310 = ''
        self.enc_300 = enc_300 = ''
        self.calibrar_lms = calibrar_lms = True

        ##################################################
        # Blocks
        ##################################################
        snippets_init_before_blocks(self)
        self._permanencia_range = qtgui.Range(1, 20, 0.5, 2, 250)
        self._permanencia_win = qtgui.RangeWidget(self._permanencia_range, self.set_permanencia, "Permanencia por portadora (s)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._permanencia_win, 0, 12, 1, 11)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(12, 23):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_probe_signal_x_0 = blocks.probe_signal_f()
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
        self.top_grid_layout.addWidget(self._portadora_manual_tool_bar, 0, 6, 1, 6)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 12):
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
        self.top_grid_layout.addWidget(self._modo_group_box, 0, 0, 1, 6)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
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
        self._et_superior_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._et_superior_formatter = lambda x: '%.0f MHz' % x
        else:
            self._et_superior_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_superior_tool_bar.addWidget(Qt.QLabel("Superior: "))
        self._et_superior_label = Qt.QLabel(str(self._et_superior_formatter(self.et_superior)))
        self._et_superior_tool_bar.addWidget(self._et_superior_label)
        self.top_grid_layout.addWidget(self._et_superior_tool_bar, 1, 10, 1, 5)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 15):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_portadora_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._et_portadora_formatter = lambda x: '%.0f MHz' % x
        else:
            self._et_portadora_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_portadora_tool_bar.addWidget(Qt.QLabel("Portadora: "))
        self._et_portadora_label = Qt.QLabel(str(self._et_portadora_formatter(self.et_portadora)))
        self._et_portadora_tool_bar.addWidget(self._et_portadora_label)
        self.top_grid_layout.addWidget(self._et_portadora_tool_bar, 1, 0, 1, 5)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_pico_tool_bar = Qt.QToolBar(self)

        if lambda x: ('%.2f' % x) if x <= 1 else ('%.2f RECORTA' % x):
            self._et_pico_formatter = lambda x: ('%.2f' % x) if x <= 1 else ('%.2f RECORTA' % x)
        else:
            self._et_pico_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_pico_tool_bar.addWidget(Qt.QLabel("Pico: "))
        self._et_pico_label = Qt.QLabel(str(self._et_pico_formatter(self.et_pico)))
        self._et_pico_tool_bar.addWidget(self._et_pico_label)
        self.top_grid_layout.addWidget(self._et_pico_tool_bar, 1, 18, 1, 5)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(18, 23):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_paso_tool_bar = Qt.QToolBar(self)

        if lambda x: '%d de 11' % x:
            self._et_paso_formatter = lambda x: '%d de 11' % x
        else:
            self._et_paso_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_paso_tool_bar.addWidget(Qt.QLabel("Paso: "))
        self._et_paso_label = Qt.QLabel(str(self._et_paso_formatter(self.et_paso)))
        self._et_paso_tool_bar.addWidget(self._et_paso_label)
        self.top_grid_layout.addWidget(self._et_paso_tool_bar, 1, 15, 1, 3)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(15, 18):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_inferior_tool_bar = Qt.QToolBar(self)

        if lambda x: '%.0f MHz' % x:
            self._et_inferior_formatter = lambda x: '%.0f MHz' % x
        else:
            self._et_inferior_formatter = lambda x: eng_notation.num_to_str(x)

        self._et_inferior_tool_bar.addWidget(Qt.QLabel("Inferior: "))
        self._et_inferior_label = Qt.QLabel(str(self._et_inferior_formatter(self.et_inferior)))
        self._et_inferior_tool_bar.addWidget(self._et_inferior_label)
        self.top_grid_layout.addWidget(self._et_inferior_tool_bar, 1, 5, 1, 5)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_mhz_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_mhz_formatter = None
        else:
            self._enc_mhz_formatter = lambda x: str(x)

        self._enc_mhz_tool_bar.addWidget(Qt.QLabel("MHz"))
        self._enc_mhz_label = Qt.QLabel(str(self._enc_mhz_formatter(self.enc_mhz)))
        self._enc_mhz_tool_bar.addWidget(self._enc_mhz_label)
        self.top_grid_layout.addWidget(self._enc_mhz_tool_bar, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_amp_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_amp_formatter = None
        else:
            self._enc_amp_formatter = lambda x: str(x)

        self._enc_amp_tool_bar.addWidget(Qt.QLabel("Amplitud"))
        self._enc_amp_label = Qt.QLabel(str(self._enc_amp_formatter(self.enc_amp)))
        self._enc_amp_tool_bar.addWidget(self._enc_amp_label)
        self.top_grid_layout.addWidget(self._enc_amp_tool_bar, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_510_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_510_formatter = None
        else:
            self._enc_510_formatter = lambda x: str(x)

        self._enc_510_tool_bar.addWidget(Qt.QLabel("510"))
        self._enc_510_label = Qt.QLabel(str(self._enc_510_formatter(self.enc_510)))
        self._enc_510_tool_bar.addWidget(self._enc_510_label)
        self.top_grid_layout.addWidget(self._enc_510_tool_bar, 2, 22, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(22, 23):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_500_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_500_formatter = None
        else:
            self._enc_500_formatter = lambda x: str(x)

        self._enc_500_tool_bar.addWidget(Qt.QLabel("500"))
        self._enc_500_label = Qt.QLabel(str(self._enc_500_formatter(self.enc_500)))
        self._enc_500_tool_bar.addWidget(self._enc_500_label)
        self.top_grid_layout.addWidget(self._enc_500_tool_bar, 2, 21, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(21, 22):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_490_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_490_formatter = None
        else:
            self._enc_490_formatter = lambda x: str(x)

        self._enc_490_tool_bar.addWidget(Qt.QLabel("490"))
        self._enc_490_label = Qt.QLabel(str(self._enc_490_formatter(self.enc_490)))
        self._enc_490_tool_bar.addWidget(self._enc_490_label)
        self.top_grid_layout.addWidget(self._enc_490_tool_bar, 2, 20, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(20, 21):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_480_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_480_formatter = None
        else:
            self._enc_480_formatter = lambda x: str(x)

        self._enc_480_tool_bar.addWidget(Qt.QLabel("480"))
        self._enc_480_label = Qt.QLabel(str(self._enc_480_formatter(self.enc_480)))
        self._enc_480_tool_bar.addWidget(self._enc_480_label)
        self.top_grid_layout.addWidget(self._enc_480_tool_bar, 2, 19, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(19, 20):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_470_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_470_formatter = None
        else:
            self._enc_470_formatter = lambda x: str(x)

        self._enc_470_tool_bar.addWidget(Qt.QLabel("470"))
        self._enc_470_label = Qt.QLabel(str(self._enc_470_formatter(self.enc_470)))
        self._enc_470_tool_bar.addWidget(self._enc_470_label)
        self.top_grid_layout.addWidget(self._enc_470_tool_bar, 2, 18, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(18, 19):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_460_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_460_formatter = None
        else:
            self._enc_460_formatter = lambda x: str(x)

        self._enc_460_tool_bar.addWidget(Qt.QLabel("460"))
        self._enc_460_label = Qt.QLabel(str(self._enc_460_formatter(self.enc_460)))
        self._enc_460_tool_bar.addWidget(self._enc_460_label)
        self.top_grid_layout.addWidget(self._enc_460_tool_bar, 2, 17, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(17, 18):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_450_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_450_formatter = None
        else:
            self._enc_450_formatter = lambda x: str(x)

        self._enc_450_tool_bar.addWidget(Qt.QLabel("450"))
        self._enc_450_label = Qt.QLabel(str(self._enc_450_formatter(self.enc_450)))
        self._enc_450_tool_bar.addWidget(self._enc_450_label)
        self.top_grid_layout.addWidget(self._enc_450_tool_bar, 2, 16, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(16, 17):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_440_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_440_formatter = None
        else:
            self._enc_440_formatter = lambda x: str(x)

        self._enc_440_tool_bar.addWidget(Qt.QLabel("440"))
        self._enc_440_label = Qt.QLabel(str(self._enc_440_formatter(self.enc_440)))
        self._enc_440_tool_bar.addWidget(self._enc_440_label)
        self.top_grid_layout.addWidget(self._enc_440_tool_bar, 2, 15, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(15, 16):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_430_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_430_formatter = None
        else:
            self._enc_430_formatter = lambda x: str(x)

        self._enc_430_tool_bar.addWidget(Qt.QLabel("430"))
        self._enc_430_label = Qt.QLabel(str(self._enc_430_formatter(self.enc_430)))
        self._enc_430_tool_bar.addWidget(self._enc_430_label)
        self.top_grid_layout.addWidget(self._enc_430_tool_bar, 2, 14, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(14, 15):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_420_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_420_formatter = None
        else:
            self._enc_420_formatter = lambda x: str(x)

        self._enc_420_tool_bar.addWidget(Qt.QLabel("420"))
        self._enc_420_label = Qt.QLabel(str(self._enc_420_formatter(self.enc_420)))
        self._enc_420_tool_bar.addWidget(self._enc_420_label)
        self.top_grid_layout.addWidget(self._enc_420_tool_bar, 2, 13, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(13, 14):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_410_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_410_formatter = None
        else:
            self._enc_410_formatter = lambda x: str(x)

        self._enc_410_tool_bar.addWidget(Qt.QLabel("410"))
        self._enc_410_label = Qt.QLabel(str(self._enc_410_formatter(self.enc_410)))
        self._enc_410_tool_bar.addWidget(self._enc_410_label)
        self.top_grid_layout.addWidget(self._enc_410_tool_bar, 2, 12, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(12, 13):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_400_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_400_formatter = None
        else:
            self._enc_400_formatter = lambda x: str(x)

        self._enc_400_tool_bar.addWidget(Qt.QLabel("400"))
        self._enc_400_label = Qt.QLabel(str(self._enc_400_formatter(self.enc_400)))
        self._enc_400_tool_bar.addWidget(self._enc_400_label)
        self.top_grid_layout.addWidget(self._enc_400_tool_bar, 2, 11, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(11, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_390_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_390_formatter = None
        else:
            self._enc_390_formatter = lambda x: str(x)

        self._enc_390_tool_bar.addWidget(Qt.QLabel("390"))
        self._enc_390_label = Qt.QLabel(str(self._enc_390_formatter(self.enc_390)))
        self._enc_390_tool_bar.addWidget(self._enc_390_label)
        self.top_grid_layout.addWidget(self._enc_390_tool_bar, 2, 10, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 11):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_380_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_380_formatter = None
        else:
            self._enc_380_formatter = lambda x: str(x)

        self._enc_380_tool_bar.addWidget(Qt.QLabel("380"))
        self._enc_380_label = Qt.QLabel(str(self._enc_380_formatter(self.enc_380)))
        self._enc_380_tool_bar.addWidget(self._enc_380_label)
        self.top_grid_layout.addWidget(self._enc_380_tool_bar, 2, 9, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_370_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_370_formatter = None
        else:
            self._enc_370_formatter = lambda x: str(x)

        self._enc_370_tool_bar.addWidget(Qt.QLabel("370"))
        self._enc_370_label = Qt.QLabel(str(self._enc_370_formatter(self.enc_370)))
        self._enc_370_tool_bar.addWidget(self._enc_370_label)
        self.top_grid_layout.addWidget(self._enc_370_tool_bar, 2, 8, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_360_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_360_formatter = None
        else:
            self._enc_360_formatter = lambda x: str(x)

        self._enc_360_tool_bar.addWidget(Qt.QLabel("360"))
        self._enc_360_label = Qt.QLabel(str(self._enc_360_formatter(self.enc_360)))
        self._enc_360_tool_bar.addWidget(self._enc_360_label)
        self.top_grid_layout.addWidget(self._enc_360_tool_bar, 2, 7, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_350_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_350_formatter = None
        else:
            self._enc_350_formatter = lambda x: str(x)

        self._enc_350_tool_bar.addWidget(Qt.QLabel("350"))
        self._enc_350_label = Qt.QLabel(str(self._enc_350_formatter(self.enc_350)))
        self._enc_350_tool_bar.addWidget(self._enc_350_label)
        self.top_grid_layout.addWidget(self._enc_350_tool_bar, 2, 6, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_340_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_340_formatter = None
        else:
            self._enc_340_formatter = lambda x: str(x)

        self._enc_340_tool_bar.addWidget(Qt.QLabel("340"))
        self._enc_340_label = Qt.QLabel(str(self._enc_340_formatter(self.enc_340)))
        self._enc_340_tool_bar.addWidget(self._enc_340_label)
        self.top_grid_layout.addWidget(self._enc_340_tool_bar, 2, 5, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_330_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_330_formatter = None
        else:
            self._enc_330_formatter = lambda x: str(x)

        self._enc_330_tool_bar.addWidget(Qt.QLabel("330"))
        self._enc_330_label = Qt.QLabel(str(self._enc_330_formatter(self.enc_330)))
        self._enc_330_tool_bar.addWidget(self._enc_330_label)
        self.top_grid_layout.addWidget(self._enc_330_tool_bar, 2, 4, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_320_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_320_formatter = None
        else:
            self._enc_320_formatter = lambda x: str(x)

        self._enc_320_tool_bar.addWidget(Qt.QLabel("320"))
        self._enc_320_label = Qt.QLabel(str(self._enc_320_formatter(self.enc_320)))
        self._enc_320_tool_bar.addWidget(self._enc_320_label)
        self.top_grid_layout.addWidget(self._enc_320_tool_bar, 2, 3, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_310_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_310_formatter = None
        else:
            self._enc_310_formatter = lambda x: str(x)

        self._enc_310_tool_bar.addWidget(Qt.QLabel("310"))
        self._enc_310_label = Qt.QLabel(str(self._enc_310_formatter(self.enc_310)))
        self._enc_310_tool_bar.addWidget(self._enc_310_label)
        self.top_grid_layout.addWidget(self._enc_310_tool_bar, 2, 2, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._enc_300_tool_bar = Qt.QToolBar(self)

        if None:
            self._enc_300_formatter = None
        else:
            self._enc_300_formatter = lambda x: str(x)

        self._enc_300_tool_bar.addWidget(Qt.QLabel("300"))
        self._enc_300_label = Qt.QLabel(str(self._enc_300_formatter(self.enc_300)))
        self._enc_300_tool_bar.addWidget(self._enc_300_label)
        self.top_grid_layout.addWidget(self._enc_300_tool_bar, 2, 1, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_vector_source_x_0 = blocks.vector_source_f(list(range(len(portadoras))), True, 1, [])
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_float*1, tasa_ctrl, True, 0 if "time" == "auto" else max( int(float(0.05) * tasa_ctrl) if "time" == "time" else int(0.05), 1) )
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_float*1, (int(permanencia * tasa_ctrl)))
        self.blocks_multiply_const_sup = blocks.multiply_const_cc(a_sup)
        self.blocks_multiply_const_inf = blocks.multiply_const_cc(a_inf)
        self.blocks_conjugate_cc_0 = blocks.conjugate_cc()
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, 1, 0, 0)
        # Create the options list
        self._amp_510_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_510_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_510_tool_bar = Qt.QToolBar(self)
        self._amp_510_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_510_combo_box = Qt.QComboBox()
        self._amp_510_tool_bar.addWidget(self._amp_510_combo_box)
        for _label in self._amp_510_labels: self._amp_510_combo_box.addItem(_label)
        self._amp_510_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_510_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_510_options.index(i)))
        self._amp_510_callback(self.amp_510)
        self._amp_510_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_510(self._amp_510_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_510_tool_bar, 3, 22, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(22, 23):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_500_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_500_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_500_tool_bar = Qt.QToolBar(self)
        self._amp_500_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_500_combo_box = Qt.QComboBox()
        self._amp_500_tool_bar.addWidget(self._amp_500_combo_box)
        for _label in self._amp_500_labels: self._amp_500_combo_box.addItem(_label)
        self._amp_500_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_500_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_500_options.index(i)))
        self._amp_500_callback(self.amp_500)
        self._amp_500_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_500(self._amp_500_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_500_tool_bar, 3, 21, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(21, 22):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_490_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_490_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_490_tool_bar = Qt.QToolBar(self)
        self._amp_490_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_490_combo_box = Qt.QComboBox()
        self._amp_490_tool_bar.addWidget(self._amp_490_combo_box)
        for _label in self._amp_490_labels: self._amp_490_combo_box.addItem(_label)
        self._amp_490_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_490_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_490_options.index(i)))
        self._amp_490_callback(self.amp_490)
        self._amp_490_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_490(self._amp_490_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_490_tool_bar, 3, 20, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(20, 21):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_480_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_480_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_480_tool_bar = Qt.QToolBar(self)
        self._amp_480_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_480_combo_box = Qt.QComboBox()
        self._amp_480_tool_bar.addWidget(self._amp_480_combo_box)
        for _label in self._amp_480_labels: self._amp_480_combo_box.addItem(_label)
        self._amp_480_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_480_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_480_options.index(i)))
        self._amp_480_callback(self.amp_480)
        self._amp_480_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_480(self._amp_480_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_480_tool_bar, 3, 19, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(19, 20):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_470_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_470_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_470_tool_bar = Qt.QToolBar(self)
        self._amp_470_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_470_combo_box = Qt.QComboBox()
        self._amp_470_tool_bar.addWidget(self._amp_470_combo_box)
        for _label in self._amp_470_labels: self._amp_470_combo_box.addItem(_label)
        self._amp_470_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_470_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_470_options.index(i)))
        self._amp_470_callback(self.amp_470)
        self._amp_470_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_470(self._amp_470_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_470_tool_bar, 3, 18, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(18, 19):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_460_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_460_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_460_tool_bar = Qt.QToolBar(self)
        self._amp_460_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_460_combo_box = Qt.QComboBox()
        self._amp_460_tool_bar.addWidget(self._amp_460_combo_box)
        for _label in self._amp_460_labels: self._amp_460_combo_box.addItem(_label)
        self._amp_460_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_460_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_460_options.index(i)))
        self._amp_460_callback(self.amp_460)
        self._amp_460_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_460(self._amp_460_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_460_tool_bar, 3, 17, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(17, 18):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_450_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_450_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_450_tool_bar = Qt.QToolBar(self)
        self._amp_450_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_450_combo_box = Qt.QComboBox()
        self._amp_450_tool_bar.addWidget(self._amp_450_combo_box)
        for _label in self._amp_450_labels: self._amp_450_combo_box.addItem(_label)
        self._amp_450_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_450_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_450_options.index(i)))
        self._amp_450_callback(self.amp_450)
        self._amp_450_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_450(self._amp_450_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_450_tool_bar, 3, 16, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(16, 17):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_440_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_440_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_440_tool_bar = Qt.QToolBar(self)
        self._amp_440_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_440_combo_box = Qt.QComboBox()
        self._amp_440_tool_bar.addWidget(self._amp_440_combo_box)
        for _label in self._amp_440_labels: self._amp_440_combo_box.addItem(_label)
        self._amp_440_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_440_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_440_options.index(i)))
        self._amp_440_callback(self.amp_440)
        self._amp_440_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_440(self._amp_440_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_440_tool_bar, 3, 15, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(15, 16):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_430_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_430_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_430_tool_bar = Qt.QToolBar(self)
        self._amp_430_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_430_combo_box = Qt.QComboBox()
        self._amp_430_tool_bar.addWidget(self._amp_430_combo_box)
        for _label in self._amp_430_labels: self._amp_430_combo_box.addItem(_label)
        self._amp_430_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_430_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_430_options.index(i)))
        self._amp_430_callback(self.amp_430)
        self._amp_430_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_430(self._amp_430_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_430_tool_bar, 3, 14, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(14, 15):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_420_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_420_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_420_tool_bar = Qt.QToolBar(self)
        self._amp_420_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_420_combo_box = Qt.QComboBox()
        self._amp_420_tool_bar.addWidget(self._amp_420_combo_box)
        for _label in self._amp_420_labels: self._amp_420_combo_box.addItem(_label)
        self._amp_420_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_420_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_420_options.index(i)))
        self._amp_420_callback(self.amp_420)
        self._amp_420_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_420(self._amp_420_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_420_tool_bar, 3, 13, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(13, 14):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_410_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_410_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_410_tool_bar = Qt.QToolBar(self)
        self._amp_410_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_410_combo_box = Qt.QComboBox()
        self._amp_410_tool_bar.addWidget(self._amp_410_combo_box)
        for _label in self._amp_410_labels: self._amp_410_combo_box.addItem(_label)
        self._amp_410_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_410_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_410_options.index(i)))
        self._amp_410_callback(self.amp_410)
        self._amp_410_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_410(self._amp_410_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_410_tool_bar, 3, 12, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(12, 13):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_400_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_400_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_400_tool_bar = Qt.QToolBar(self)
        self._amp_400_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_400_combo_box = Qt.QComboBox()
        self._amp_400_tool_bar.addWidget(self._amp_400_combo_box)
        for _label in self._amp_400_labels: self._amp_400_combo_box.addItem(_label)
        self._amp_400_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_400_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_400_options.index(i)))
        self._amp_400_callback(self.amp_400)
        self._amp_400_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_400(self._amp_400_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_400_tool_bar, 3, 11, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(11, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_390_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_390_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_390_tool_bar = Qt.QToolBar(self)
        self._amp_390_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_390_combo_box = Qt.QComboBox()
        self._amp_390_tool_bar.addWidget(self._amp_390_combo_box)
        for _label in self._amp_390_labels: self._amp_390_combo_box.addItem(_label)
        self._amp_390_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_390_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_390_options.index(i)))
        self._amp_390_callback(self.amp_390)
        self._amp_390_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_390(self._amp_390_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_390_tool_bar, 3, 10, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 11):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_380_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_380_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_380_tool_bar = Qt.QToolBar(self)
        self._amp_380_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_380_combo_box = Qt.QComboBox()
        self._amp_380_tool_bar.addWidget(self._amp_380_combo_box)
        for _label in self._amp_380_labels: self._amp_380_combo_box.addItem(_label)
        self._amp_380_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_380_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_380_options.index(i)))
        self._amp_380_callback(self.amp_380)
        self._amp_380_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_380(self._amp_380_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_380_tool_bar, 3, 9, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_370_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_370_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_370_tool_bar = Qt.QToolBar(self)
        self._amp_370_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_370_combo_box = Qt.QComboBox()
        self._amp_370_tool_bar.addWidget(self._amp_370_combo_box)
        for _label in self._amp_370_labels: self._amp_370_combo_box.addItem(_label)
        self._amp_370_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_370_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_370_options.index(i)))
        self._amp_370_callback(self.amp_370)
        self._amp_370_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_370(self._amp_370_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_370_tool_bar, 3, 8, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_360_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_360_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_360_tool_bar = Qt.QToolBar(self)
        self._amp_360_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_360_combo_box = Qt.QComboBox()
        self._amp_360_tool_bar.addWidget(self._amp_360_combo_box)
        for _label in self._amp_360_labels: self._amp_360_combo_box.addItem(_label)
        self._amp_360_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_360_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_360_options.index(i)))
        self._amp_360_callback(self.amp_360)
        self._amp_360_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_360(self._amp_360_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_360_tool_bar, 3, 7, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_350_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_350_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_350_tool_bar = Qt.QToolBar(self)
        self._amp_350_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_350_combo_box = Qt.QComboBox()
        self._amp_350_tool_bar.addWidget(self._amp_350_combo_box)
        for _label in self._amp_350_labels: self._amp_350_combo_box.addItem(_label)
        self._amp_350_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_350_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_350_options.index(i)))
        self._amp_350_callback(self.amp_350)
        self._amp_350_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_350(self._amp_350_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_350_tool_bar, 3, 6, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_340_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_340_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_340_tool_bar = Qt.QToolBar(self)
        self._amp_340_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_340_combo_box = Qt.QComboBox()
        self._amp_340_tool_bar.addWidget(self._amp_340_combo_box)
        for _label in self._amp_340_labels: self._amp_340_combo_box.addItem(_label)
        self._amp_340_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_340_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_340_options.index(i)))
        self._amp_340_callback(self.amp_340)
        self._amp_340_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_340(self._amp_340_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_340_tool_bar, 3, 5, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_330_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_330_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_330_tool_bar = Qt.QToolBar(self)
        self._amp_330_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_330_combo_box = Qt.QComboBox()
        self._amp_330_tool_bar.addWidget(self._amp_330_combo_box)
        for _label in self._amp_330_labels: self._amp_330_combo_box.addItem(_label)
        self._amp_330_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_330_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_330_options.index(i)))
        self._amp_330_callback(self.amp_330)
        self._amp_330_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_330(self._amp_330_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_330_tool_bar, 3, 4, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_320_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_320_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_320_tool_bar = Qt.QToolBar(self)
        self._amp_320_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_320_combo_box = Qt.QComboBox()
        self._amp_320_tool_bar.addWidget(self._amp_320_combo_box)
        for _label in self._amp_320_labels: self._amp_320_combo_box.addItem(_label)
        self._amp_320_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_320_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_320_options.index(i)))
        self._amp_320_callback(self.amp_320)
        self._amp_320_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_320(self._amp_320_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_320_tool_bar, 3, 3, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_310_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_310_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_310_tool_bar = Qt.QToolBar(self)
        self._amp_310_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_310_combo_box = Qt.QComboBox()
        self._amp_310_tool_bar.addWidget(self._amp_310_combo_box)
        for _label in self._amp_310_labels: self._amp_310_combo_box.addItem(_label)
        self._amp_310_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_310_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_310_options.index(i)))
        self._amp_310_callback(self.amp_310)
        self._amp_310_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_310(self._amp_310_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_310_tool_bar, 3, 2, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._amp_300_options = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
        # Create the labels list
        self._amp_300_labels = ['0.10', '0.15', '0.20', '0.25', '0.30', '0.35', '0.40', '0.45', '0.50', '0.55', '0.60', '0.65', '0.70']
        # Create the combo box
        self._amp_300_tool_bar = Qt.QToolBar(self)
        self._amp_300_tool_bar.addWidget(Qt.QLabel(" " + ": "))
        self._amp_300_combo_box = Qt.QComboBox()
        self._amp_300_tool_bar.addWidget(self._amp_300_combo_box)
        for _label in self._amp_300_labels: self._amp_300_combo_box.addItem(_label)
        self._amp_300_callback = lambda i: Qt.QMetaObject.invokeMethod(self._amp_300_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._amp_300_options.index(i)))
        self._amp_300_callback(self.amp_300)
        self._amp_300_combo_box.currentIndexChanged.connect(
            lambda i: self.set_amp_300(self._amp_300_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._amp_300_tool_bar, 3, 1, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_conjugate_cc_0, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_const_sup, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.blocks_conjugate_cc_0, 0), (self.blocks_multiply_const_inf, 0))
        self.connect((self.blocks_multiply_const_inf, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_multiply_const_sup, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_repeat_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_probe_signal_x_0, 0))
        self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_repeat_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp14_peine_ecualizado")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_portadoras(self):
        return self.portadoras

    def set_portadoras(self, portadoras):
        self.portadoras = portadoras
        self.set_indice(min(max(int(round(self.indice_medido)), 0), len(self.portadoras) - 1))
        self.set_indice_activo(int(round((self.portadora_manual - self.portadoras[0]) / 20e6)) if self.modo == 1 else self.indice)
        self.set_freq(self.portadoras[self.indice_activo])
        self.blocks_vector_source_x_0.set_data(list(range(len(self.portadoras))), [])

    def get_indice_medido(self):
        return self.indice_medido

    def set_indice_medido(self, indice_medido):
        self.indice_medido = indice_medido
        self.set_indice(min(max(int(round(self.indice_medido)), 0), len(self.portadoras) - 1))

    def get_portadora_manual(self):
        return self.portadora_manual

    def set_portadora_manual(self, portadora_manual):
        self.portadora_manual = portadora_manual
        self._portadora_manual_callback(self.portadora_manual)
        self.set_indice_activo(int(round((self.portadora_manual - self.portadoras[0]) / 20e6)) if self.modo == 1 else self.indice)

    def get_modo(self):
        return self.modo

    def set_modo(self, modo):
        self.modo = modo
        self._modo_callback(self.modo)
        self.set_indice_activo(int(round((self.portadora_manual - self.portadoras[0]) / 20e6)) if self.modo == 1 else self.indice)

    def get_indice(self):
        return self.indice

    def set_indice(self, indice):
        self.indice = indice
        self.set_indice_activo(int(round((self.portadora_manual - self.portadoras[0]) / 20e6)) if self.modo == 1 else self.indice)

    def get_amp_510(self):
        return self.amp_510

    def set_amp_510(self, amp_510):
        self.amp_510 = amp_510
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_510_callback(self.amp_510)

    def get_amp_500(self):
        return self.amp_500

    def set_amp_500(self, amp_500):
        self.amp_500 = amp_500
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_500_callback(self.amp_500)

    def get_amp_490(self):
        return self.amp_490

    def set_amp_490(self, amp_490):
        self.amp_490 = amp_490
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_490_callback(self.amp_490)

    def get_amp_480(self):
        return self.amp_480

    def set_amp_480(self, amp_480):
        self.amp_480 = amp_480
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_480_callback(self.amp_480)

    def get_amp_470(self):
        return self.amp_470

    def set_amp_470(self, amp_470):
        self.amp_470 = amp_470
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_470_callback(self.amp_470)

    def get_amp_460(self):
        return self.amp_460

    def set_amp_460(self, amp_460):
        self.amp_460 = amp_460
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_460_callback(self.amp_460)

    def get_amp_450(self):
        return self.amp_450

    def set_amp_450(self, amp_450):
        self.amp_450 = amp_450
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_450_callback(self.amp_450)

    def get_amp_440(self):
        return self.amp_440

    def set_amp_440(self, amp_440):
        self.amp_440 = amp_440
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_440_callback(self.amp_440)

    def get_amp_430(self):
        return self.amp_430

    def set_amp_430(self, amp_430):
        self.amp_430 = amp_430
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_430_callback(self.amp_430)

    def get_amp_420(self):
        return self.amp_420

    def set_amp_420(self, amp_420):
        self.amp_420 = amp_420
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_420_callback(self.amp_420)

    def get_amp_410(self):
        return self.amp_410

    def set_amp_410(self, amp_410):
        self.amp_410 = amp_410
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_410_callback(self.amp_410)

    def get_amp_400(self):
        return self.amp_400

    def set_amp_400(self, amp_400):
        self.amp_400 = amp_400
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_400_callback(self.amp_400)

    def get_amp_390(self):
        return self.amp_390

    def set_amp_390(self, amp_390):
        self.amp_390 = amp_390
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_390_callback(self.amp_390)

    def get_amp_380(self):
        return self.amp_380

    def set_amp_380(self, amp_380):
        self.amp_380 = amp_380
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_380_callback(self.amp_380)

    def get_amp_370(self):
        return self.amp_370

    def set_amp_370(self, amp_370):
        self.amp_370 = amp_370
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_370_callback(self.amp_370)

    def get_amp_360(self):
        return self.amp_360

    def set_amp_360(self, amp_360):
        self.amp_360 = amp_360
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_360_callback(self.amp_360)

    def get_amp_350(self):
        return self.amp_350

    def set_amp_350(self, amp_350):
        self.amp_350 = amp_350
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_350_callback(self.amp_350)

    def get_amp_340(self):
        return self.amp_340

    def set_amp_340(self, amp_340):
        self.amp_340 = amp_340
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_340_callback(self.amp_340)

    def get_amp_330(self):
        return self.amp_330

    def set_amp_330(self, amp_330):
        self.amp_330 = amp_330
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_330_callback(self.amp_330)

    def get_amp_320(self):
        return self.amp_320

    def set_amp_320(self, amp_320):
        self.amp_320 = amp_320
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_320_callback(self.amp_320)

    def get_amp_310(self):
        return self.amp_310

    def set_amp_310(self, amp_310):
        self.amp_310 = amp_310
        self.set_amps_sup([self.amp_310, self.amp_330, self.amp_350, self.amp_370, self.amp_390, self.amp_410, self.amp_430, self.amp_450, self.amp_470, self.amp_490, self.amp_510])
        self._amp_310_callback(self.amp_310)

    def get_amp_300(self):
        return self.amp_300

    def set_amp_300(self, amp_300):
        self.amp_300 = amp_300
        self.set_amps_inf([self.amp_300, self.amp_320, self.amp_340, self.amp_360, self.amp_380, self.amp_400, self.amp_420, self.amp_440, self.amp_460, self.amp_480, self.amp_500])
        self._amp_300_callback(self.amp_300)

    def get_indice_activo(self):
        return self.indice_activo

    def set_indice_activo(self, indice_activo):
        self.indice_activo = indice_activo
        self.set_et_paso((self.indice_activo + 1))
        self.set_freq(self.portadoras[self.indice_activo])
        self.set_a_inf(self.amps_inf[self.indice_activo])
        self.set_a_sup(self.amps_sup[self.indice_activo])

    def get_amps_sup(self):
        return self.amps_sup

    def set_amps_sup(self, amps_sup):
        self.amps_sup = amps_sup
        self.set_a_sup(self.amps_sup[self.indice_activo])

    def get_amps_inf(self):
        return self.amps_inf

    def set_amps_inf(self, amps_inf):
        self.amps_inf = amps_inf
        self.set_a_inf(self.amps_inf[self.indice_activo])

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)
        self.set_ganancia_tabla(self.tx_gain)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_et_portadora((self.freq / 1e6))
        self.set_et_inferior(((self.freq - self.f_tono) / 1e6))
        self.set_et_superior(((self.freq + self.f_tono) / 1e6))
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

    def get_f_tono(self):
        return self.f_tono

    def set_f_tono(self, f_tono):
        self.f_tono = f_tono
        self.set_et_inferior(((self.freq - self.f_tono) / 1e6))
        self.set_et_superior(((self.freq + self.f_tono) / 1e6))
        self.analog_sig_source_x_0.set_frequency(self.f_tono)

    def get_a_sup(self):
        return self.a_sup

    def set_a_sup(self, a_sup):
        self.a_sup = a_sup
        self.set_et_pico((self.a_inf + self.a_sup))
        self.blocks_multiply_const_sup.set_k(self.a_sup)

    def get_a_inf(self):
        return self.a_inf

    def set_a_inf(self, a_inf):
        self.a_inf = a_inf
        self.set_et_pico((self.a_inf + self.a_sup))
        self.blocks_multiply_const_inf.set_k(self.a_inf)

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

    def get_generar_tabla(self):
        return self.generar_tabla

    def set_generar_tabla(self, generar_tabla):
        self.generar_tabla = generar_tabla

    def get_ganancia_tabla(self):
        return self.ganancia_tabla

    def set_ganancia_tabla(self, ganancia_tabla):
        self.ganancia_tabla = ganancia_tabla

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

    def get_enc_mhz(self):
        return self.enc_mhz

    def set_enc_mhz(self, enc_mhz):
        self.enc_mhz = enc_mhz
        Qt.QMetaObject.invokeMethod(self._enc_mhz_label, "setText", Qt.Q_ARG("QString", str(self._enc_mhz_formatter(self.enc_mhz))))

    def get_enc_amp(self):
        return self.enc_amp

    def set_enc_amp(self, enc_amp):
        self.enc_amp = enc_amp
        Qt.QMetaObject.invokeMethod(self._enc_amp_label, "setText", Qt.Q_ARG("QString", str(self._enc_amp_formatter(self.enc_amp))))

    def get_enc_510(self):
        return self.enc_510

    def set_enc_510(self, enc_510):
        self.enc_510 = enc_510
        Qt.QMetaObject.invokeMethod(self._enc_510_label, "setText", Qt.Q_ARG("QString", str(self._enc_510_formatter(self.enc_510))))

    def get_enc_500(self):
        return self.enc_500

    def set_enc_500(self, enc_500):
        self.enc_500 = enc_500
        Qt.QMetaObject.invokeMethod(self._enc_500_label, "setText", Qt.Q_ARG("QString", str(self._enc_500_formatter(self.enc_500))))

    def get_enc_490(self):
        return self.enc_490

    def set_enc_490(self, enc_490):
        self.enc_490 = enc_490
        Qt.QMetaObject.invokeMethod(self._enc_490_label, "setText", Qt.Q_ARG("QString", str(self._enc_490_formatter(self.enc_490))))

    def get_enc_480(self):
        return self.enc_480

    def set_enc_480(self, enc_480):
        self.enc_480 = enc_480
        Qt.QMetaObject.invokeMethod(self._enc_480_label, "setText", Qt.Q_ARG("QString", str(self._enc_480_formatter(self.enc_480))))

    def get_enc_470(self):
        return self.enc_470

    def set_enc_470(self, enc_470):
        self.enc_470 = enc_470
        Qt.QMetaObject.invokeMethod(self._enc_470_label, "setText", Qt.Q_ARG("QString", str(self._enc_470_formatter(self.enc_470))))

    def get_enc_460(self):
        return self.enc_460

    def set_enc_460(self, enc_460):
        self.enc_460 = enc_460
        Qt.QMetaObject.invokeMethod(self._enc_460_label, "setText", Qt.Q_ARG("QString", str(self._enc_460_formatter(self.enc_460))))

    def get_enc_450(self):
        return self.enc_450

    def set_enc_450(self, enc_450):
        self.enc_450 = enc_450
        Qt.QMetaObject.invokeMethod(self._enc_450_label, "setText", Qt.Q_ARG("QString", str(self._enc_450_formatter(self.enc_450))))

    def get_enc_440(self):
        return self.enc_440

    def set_enc_440(self, enc_440):
        self.enc_440 = enc_440
        Qt.QMetaObject.invokeMethod(self._enc_440_label, "setText", Qt.Q_ARG("QString", str(self._enc_440_formatter(self.enc_440))))

    def get_enc_430(self):
        return self.enc_430

    def set_enc_430(self, enc_430):
        self.enc_430 = enc_430
        Qt.QMetaObject.invokeMethod(self._enc_430_label, "setText", Qt.Q_ARG("QString", str(self._enc_430_formatter(self.enc_430))))

    def get_enc_420(self):
        return self.enc_420

    def set_enc_420(self, enc_420):
        self.enc_420 = enc_420
        Qt.QMetaObject.invokeMethod(self._enc_420_label, "setText", Qt.Q_ARG("QString", str(self._enc_420_formatter(self.enc_420))))

    def get_enc_410(self):
        return self.enc_410

    def set_enc_410(self, enc_410):
        self.enc_410 = enc_410
        Qt.QMetaObject.invokeMethod(self._enc_410_label, "setText", Qt.Q_ARG("QString", str(self._enc_410_formatter(self.enc_410))))

    def get_enc_400(self):
        return self.enc_400

    def set_enc_400(self, enc_400):
        self.enc_400 = enc_400
        Qt.QMetaObject.invokeMethod(self._enc_400_label, "setText", Qt.Q_ARG("QString", str(self._enc_400_formatter(self.enc_400))))

    def get_enc_390(self):
        return self.enc_390

    def set_enc_390(self, enc_390):
        self.enc_390 = enc_390
        Qt.QMetaObject.invokeMethod(self._enc_390_label, "setText", Qt.Q_ARG("QString", str(self._enc_390_formatter(self.enc_390))))

    def get_enc_380(self):
        return self.enc_380

    def set_enc_380(self, enc_380):
        self.enc_380 = enc_380
        Qt.QMetaObject.invokeMethod(self._enc_380_label, "setText", Qt.Q_ARG("QString", str(self._enc_380_formatter(self.enc_380))))

    def get_enc_370(self):
        return self.enc_370

    def set_enc_370(self, enc_370):
        self.enc_370 = enc_370
        Qt.QMetaObject.invokeMethod(self._enc_370_label, "setText", Qt.Q_ARG("QString", str(self._enc_370_formatter(self.enc_370))))

    def get_enc_360(self):
        return self.enc_360

    def set_enc_360(self, enc_360):
        self.enc_360 = enc_360
        Qt.QMetaObject.invokeMethod(self._enc_360_label, "setText", Qt.Q_ARG("QString", str(self._enc_360_formatter(self.enc_360))))

    def get_enc_350(self):
        return self.enc_350

    def set_enc_350(self, enc_350):
        self.enc_350 = enc_350
        Qt.QMetaObject.invokeMethod(self._enc_350_label, "setText", Qt.Q_ARG("QString", str(self._enc_350_formatter(self.enc_350))))

    def get_enc_340(self):
        return self.enc_340

    def set_enc_340(self, enc_340):
        self.enc_340 = enc_340
        Qt.QMetaObject.invokeMethod(self._enc_340_label, "setText", Qt.Q_ARG("QString", str(self._enc_340_formatter(self.enc_340))))

    def get_enc_330(self):
        return self.enc_330

    def set_enc_330(self, enc_330):
        self.enc_330 = enc_330
        Qt.QMetaObject.invokeMethod(self._enc_330_label, "setText", Qt.Q_ARG("QString", str(self._enc_330_formatter(self.enc_330))))

    def get_enc_320(self):
        return self.enc_320

    def set_enc_320(self, enc_320):
        self.enc_320 = enc_320
        Qt.QMetaObject.invokeMethod(self._enc_320_label, "setText", Qt.Q_ARG("QString", str(self._enc_320_formatter(self.enc_320))))

    def get_enc_310(self):
        return self.enc_310

    def set_enc_310(self, enc_310):
        self.enc_310 = enc_310
        Qt.QMetaObject.invokeMethod(self._enc_310_label, "setText", Qt.Q_ARG("QString", str(self._enc_310_formatter(self.enc_310))))

    def get_enc_300(self):
        return self.enc_300

    def set_enc_300(self, enc_300):
        self.enc_300 = enc_300
        Qt.QMetaObject.invokeMethod(self._enc_300_label, "setText", Qt.Q_ARG("QString", str(self._enc_300_formatter(self.enc_300))))

    def get_calibrar_lms(self):
        return self.calibrar_lms

    def set_calibrar_lms(self, calibrar_lms):
        self.calibrar_lms = calibrar_lms




def main(top_block_cls=exp14_peine_ecualizado, options=None):

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
