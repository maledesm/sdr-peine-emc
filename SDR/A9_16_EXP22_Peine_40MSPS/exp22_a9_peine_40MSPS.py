#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-22 xA9: peine de 50 MHz a 1 GHz a 40 MSPS, una linea cada 20 MHz
# Description: bladeRF 2.0 micro xA9: peine de 50 a 990 MHz, 48 lineas cada 20 MHz, con 40 MSPS (24 portadoras con dos tonos en +/-10 MHz). Prueba si la placa aguanta esa tasa: mirar el LED. Sin calibrar, las lineas salen unos 3 dB por debajo del nivel calibrado. El boton Generar calibracion lee la captura del analizador, carga el valor de cada linea y el flujo la sube hasta el nivel calibrado. La calibracion se guarda en un archivo y se puede importar. SOLO para medir con el analizador: nunca con el cable en RX1
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


def snipfcn_archivos_de_calibracion(self):
    # ============================================================================
    # ARCHIVOS DE CALIBRACION
    # Es el unico codigo Python del flujo. Hace falta porque los bloques no saben
    # escribir ni leer archivos.
    #   Boton "Generar calibracion": pide la captura (.csv) que guardo el analizador
    #   con el peine SIN calibrar, busca el pico de cada linea, lo carga en su
    #   contador y guarda el archivo de calibracion.
    #   Boton "Guardar calibracion": escribe en un archivo de texto los 48 valores
    #   cargados en la ventana, uno por renglon, junto a su frecuencia.
    #   Boton "Importar calibracion previa": lee ese archivo y pone cada valor en
    #   su contador.
    # ============================================================================
    import os
    import time

    PRIMERA_LINEA = 50        # MHz
    SEPARACION = 20           # MHz entre una linea y la siguiente
    CERCA = 4                 # MHz: hasta que distancia de una linea se busca su pico

    # Los 48 contadores de la ventana, en orden de frecuencia (50, 70, ... 990 MHz).
    # d_widget es la casilla con flechas que se ve en pantalla.
    contadores = [
        self._m_50_win.d_widget, self._m_70_win.d_widget, self._m_90_win.d_widget,
        self._m_110_win.d_widget, self._m_130_win.d_widget, self._m_150_win.d_widget,
        self._m_170_win.d_widget, self._m_190_win.d_widget, self._m_210_win.d_widget,
        self._m_230_win.d_widget, self._m_250_win.d_widget, self._m_270_win.d_widget,
        self._m_290_win.d_widget, self._m_310_win.d_widget, self._m_330_win.d_widget,
        self._m_350_win.d_widget, self._m_370_win.d_widget, self._m_390_win.d_widget,
        self._m_410_win.d_widget, self._m_430_win.d_widget, self._m_450_win.d_widget,
        self._m_470_win.d_widget, self._m_490_win.d_widget, self._m_510_win.d_widget,
        self._m_530_win.d_widget, self._m_550_win.d_widget, self._m_570_win.d_widget,
        self._m_590_win.d_widget, self._m_610_win.d_widget, self._m_630_win.d_widget,
        self._m_650_win.d_widget, self._m_670_win.d_widget, self._m_690_win.d_widget,
        self._m_710_win.d_widget, self._m_730_win.d_widget, self._m_750_win.d_widget,
        self._m_770_win.d_widget, self._m_790_win.d_widget, self._m_810_win.d_widget,
        self._m_830_win.d_widget, self._m_850_win.d_widget, self._m_870_win.d_widget,
        self._m_890_win.d_widget, self._m_910_win.d_widget, self._m_930_win.d_widget,
        self._m_950_win.d_widget, self._m_970_win.d_widget, self._m_990_win.d_widget,
    ]


    def guardar():
        valores = self.get_medidos()                 # los 48 valores de la ventana
        try:
            archivo = open(self.get_archivo(), 'w')
            # primer renglon: cuando se guardo y con que ganancia se leyeron los valores
            archivo.write('# guardada el ' + time.strftime('%d-%m-%Y %H:%M') +
                          ', valores leidos con ganancia %d dB\n' % self.get_ganancia_de_lectura())
            for k in range(len(valores)):
                frecuencia = PRIMERA_LINEA + SEPARACION * k
                archivo.write('%d %.1f\n' % (frecuencia, valores[k]))
            archivo.close()
        except Exception:
            self.set_estado_archivo('NO se pudo guardar')
            return False
        self.set_estado_archivo('guardada a las ' + time.strftime('%H:%M:%S'))
        return True


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


    def leer_captura(nombre):
        # Lee una captura del analizador: un renglon por punto, con la frecuencia y
        # el nivel separados por una coma. Devuelve dos listas: MHz y dBm.
        frecuencias = []
        niveles = []
        archivo = open(nombre)
        for renglon in archivo:
            partes = renglon.replace(';', ',').split(',')
            try:
                frecuencia = float(partes[0])
                nivel = float(partes[1])
            except Exception:
                continue                             # renglon de titulo o vacio: se saltea
            if frecuencia > 100000:
                frecuencia = frecuencia / 1e6        # estaba en Hz: se pasa a MHz
            frecuencias.append(frecuencia)
            niveles.append(nivel)
        archivo.close()
        return frecuencias, niveles


    def pico_de_la_linea(frecuencias, niveles, linea):
        # Devuelve el nivel mas alto que hay en la captura a menos de 4 MHz de la
        # linea. El pico casi nunca cae justo en la frecuencia de la linea, por eso
        # se busca cerca. Las lineas vecinas estan a 20 MHz: quedan afuera.
        # Si la captura no llega hasta esa frecuencia, devuelve None.
        if linea < min(frecuencias) or linea > max(frecuencias):
            return None
        pico = None
        for j in range(len(frecuencias)):
            if abs(frecuencias[j] - linea) <= CERCA:
                if pico is None or niveles[j] > pico:
                    pico = niveles[j]
        return pico


    def generar():
        # La captura tiene que ser del peine sin calibrar: con los contadores en 0
        if self.get_cargadas() > 0:
            self.set_estado_archivo('NO se genero: ya hay valores cargados. Cerrar el programa, '
                                    'abrirlo de nuevo y capturar el peine sin calibrar')
            return

        # 1) Elegir la captura. Se pueden elegir varias a la vez
        elegido = Qt.QFileDialog.getOpenFileNames(self, 'Elegir la captura del peine SIN calibrar', '',
                                                  'Capturas del analizador (*.csv)')
        nombres = elegido[0]
        if len(nombres) == 0:
            return                                   # se cerro la ventana sin elegir nada

        # 2) Leer cada captura
        capturas = []
        for nombre in nombres:
            try:
                frecuencias, niveles = leer_captura(nombre)
            except Exception:
                frecuencias = []
            if len(frecuencias) == 0:
                self.set_estado_archivo('NO se genero: no se pudo leer ' + os.path.basename(nombre))
                return
            capturas.append([frecuencias, niveles])

        # 3) Buscar el pico de cada linea
        ganancia = self.get_ganancia()               # ganancia de TX elegida en la ventana
        esperado = self.get_nivel_sin_calibrar()     # nivel aproximado de una linea sin calibrar
        valores = []                                 # un valor por linea; None si no hay dato
        for k in range(len(contadores)):
            linea = PRIMERA_LINEA + SEPARACION * k
            leidos = []
            for captura in capturas:
                pico = pico_de_la_linea(captura[0], captura[1], linea)
                if pico is not None:
                    leidos.append(pico)
            if len(leidos) == 0:
                valores.append(None)                 # ninguna captura llega hasta esta linea
                continue
            # Con varias capturas se usa el valor mas bajo: MAX HOLD a veces retiene
            # un pico momentaneo, y es raro que caiga dos veces en la misma linea
            valor = min(leidos)
            # Control: si el valor esta lejos de lo esperado, la captura no sirve
            if valor > esperado + 6 or valor < esperado - 8:
                self.set_estado_archivo('NO se genero: en %d MHz se leyo %.1f dBm y con ganancia %d dB '
                                        'se esperaba cerca de %d dBm' % (linea, valor, ganancia, esperado))
                return
            valores.append(valor)

        # 4) Cargar los contadores. El flujo espera valores leidos con la ganancia
        #    de lectura (45 dB): se resta lo que haya de mas en la ganancia usada
        diferencia = ganancia - self.get_ganancia_de_lectura()
        cuantas = 0
        for k in range(len(contadores)):
            if valores[k] is not None:
                contadores[k].setValue(round(valores[k] - diferencia, 1))
                cuantas = cuantas + 1
        if cuantas == 0:
            self.set_estado_archivo('NO se genero: la captura no llega a ninguna linea del peine')
            return

        # 5) Guardar el archivo de calibracion
        if guardar():
            self.set_estado_archivo('generada a las %s con %d captura(s): %d lineas, leidas con ganancia %d dB'
                                    % (time.strftime('%H:%M:%S'), len(capturas), cuantas, ganancia))


    # GNU Radio llama a set_boton_guardar(1) cuando se aprieta el boton y a
    # set_boton_guardar(0) cuando se suelta. Aca se define que hace esa llamada.
    def al_tocar_guardar(valor):
        if valor == 1:
            guardar()


    def al_tocar_importar(valor):
        if valor == 1:
            importar()


    # Este se hace al soltar el boton: si se hiciera al apretarlo, el boton quedaria
    # hundido mientras esta abierta la ventana para elegir el archivo.
    def al_tocar_generar(valor):
        if valor == 0:
            generar()


    self.set_boton_guardar = al_tocar_guardar
    self.set_boton_importar = al_tocar_importar
    self.set_boton_generar = al_tocar_generar


def snippets_main_after_init(tb):
    snipfcn_archivos_de_calibracion(tb)

class exp22_a9_peine_40MSPS(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-22 xA9: peine de 50 MHz a 1 GHz a 40 MSPS, una linea cada 20 MHz", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-22 xA9: peine de 50 MHz a 1 GHz a 40 MSPS, una linea cada 20 MHz")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp22_a9_peine_40MSPS")

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
        self.m_990 = m_990 = 0
        self.m_970 = m_970 = 0
        self.m_950 = m_950 = 0
        self.m_930 = m_930 = 0
        self.m_910 = m_910 = 0
        self.m_90 = m_90 = 0
        self.m_890 = m_890 = 0
        self.m_870 = m_870 = 0
        self.m_850 = m_850 = 0
        self.m_830 = m_830 = 0
        self.m_810 = m_810 = 0
        self.m_790 = m_790 = 0
        self.m_770 = m_770 = 0
        self.m_750 = m_750 = 0
        self.m_730 = m_730 = 0
        self.m_710 = m_710 = 0
        self.m_70 = m_70 = 0
        self.m_690 = m_690 = 0
        self.m_670 = m_670 = 0
        self.m_650 = m_650 = 0
        self.m_630 = m_630 = 0
        self.m_610 = m_610 = 0
        self.m_590 = m_590 = 0
        self.m_570 = m_570 = 0
        self.m_550 = m_550 = 0
        self.m_530 = m_530 = 0
        self.m_510 = m_510 = 0
        self.m_50 = m_50 = 0
        self.m_490 = m_490 = 0
        self.m_470 = m_470 = 0
        self.m_450 = m_450 = 0
        self.m_430 = m_430 = 0
        self.m_410 = m_410 = 0
        self.m_390 = m_390 = 0
        self.m_370 = m_370 = 0
        self.m_350 = m_350 = 0
        self.m_330 = m_330 = 0
        self.m_310 = m_310 = 0
        self.m_290 = m_290 = 0
        self.m_270 = m_270 = 0
        self.m_250 = m_250 = 0
        self.m_230 = m_230 = 0
        self.m_210 = m_210 = 0
        self.m_190 = m_190 = 0
        self.m_170 = m_170 = 0
        self.m_150 = m_150 = 0
        self.m_130 = m_130 = 0
        self.m_110 = m_110 = 0
        self.orden_recorrido = orden_recorrido = 0
        self.n_port = n_port = 24
        self.medidos = medidos = [m_50, m_70, m_90, m_110, m_130, m_150, m_170, m_190, m_210, m_230, m_250, m_270, m_290, m_310, m_330, m_350, m_370, m_390, m_410, m_430, m_450, m_470, m_490, m_510, m_530, m_550, m_570, m_590, m_610, m_630, m_650, m_670, m_690, m_710, m_730, m_750, m_770, m_790, m_810, m_830, m_850, m_870, m_890, m_910, m_930, m_950, m_970, m_990]
        self.ganancia_de_lectura = ganancia_de_lectura = 45
        self.pasos_por_pasada = pasos_por_pasada = n_port + 1 if orden_recorrido == 1 else n_port
        self.paso = paso = -1
        self.comp = comp = [(0.0 if leido == 0 else (ganancia_de_lectura - 65) - leido) for leido in medidos]
        self.posicion = posicion = max(paso, 0) % pasos_por_pasada
        self.orden = orden = sorted(range(n_port), key=lambda p: comp[2 * p] + comp[2 * p + 1]) if orden_recorrido == 1 else list(range(n_port))
        self.indice = indice = orden[posicion] if posicion < n_port else n_port
        self.pausa = pausa = 1
        self.paso_port = paso_port = 40e6
        self.pasada = pasada = max(paso, 0) // pasos_por_pasada + 1
        self.indice_freq = indice_freq = orden[n_port - 1] if indice >= n_port else indice
        self.ganancia = ganancia = 45
        self.f_primera = f_primera = 60e6
        self.entre_pasadas = entre_pasadas = 1 if indice >= n_port else 0
        self.archivo = archivo = 'calibracion_peine.txt'
        self.amp_max = amp_max = 0.47
        self.amp_base = amp_base = 0.25
        self.sin_margen = sin_margen = sum(1 for db in comp if amp_base * 10 ** (db / 20.0) > amp_max)
        self.permanencia = permanencia = 6.0
        self.nivel_sin_calibrar = nivel_sin_calibrar = ganancia - 68
        self.linea_de_punto = linea_de_punto = [j * 2 * n_port // 512 for j in range(512)]
        self.freq = freq = f_primera + paso_port * indice_freq
        self.f_tono = f_tono = 10e6
        self.etapa = etapa = 'PAUSA (sin emitir)' if pausa == 1 else ('INICIACION' if paso < 0 else ('SILENCIO ENTRE PASADAS' if entre_pasadas == 1 else 'TRANSMISION, pasada %d' % pasada))
        self.estado_archivo = estado_archivo = 'hay una guardada, sin importar' if os.path.exists(archivo) else 'todavia no hay ninguna guardada'
        self.emite = emite = 1 if (pausa == 0 and paso >= 0) else 0
        self.cargadas = cargadas = sum(1 for leido in medidos if leido != 0)
        self.amp_tabla = amp_tabla = [min(amp_base * 10 ** (db / 20.0), amp_max) for db in comp] + [0.0, 0.0]
        self.tx_gain = tx_gain = ganancia if pausa == 0 else 0
        self.samp_rate = samp_rate = 40e6
        self.muestras_por_bloque = muestras_por_bloque = 16384
        self.lista_de_pasos = lista_de_pasos = list(range(100000))
        self.et_titulo = et_titulo = 'referido a la ganancia de %d dB. Lo carga Generar calibracion; tambien se puede corregir a mano' % ganancia_de_lectura
        self.et_tiempos = et_tiempos = '%d min %02d s (%.0f s por portadora)' % (permanencia * pasos_por_pasada // 60, permanencia * pasos_por_pasada % 60, permanencia)
        self.et_portadora = et_portadora = '%.0f MHz (paso %d de %d)' % (freq / 1e6, posicion + 1, pasos_por_pasada)
        self.et_nivel = et_nivel = 'sin calibrar unos %d dBm, calibradas %d dBm' % (nivel_sin_calibrar, ganancia - 65)
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
        self.boton_generar = boton_generar = 0
        self.bloques_usb = bloques_usb = 128
        self.ancho_banda = ancho_banda = 36e6
        self.amp_sup_tx = amp_sup_tx = amp_tabla[2 * indice + 1] if emite == 1 else 0
        self.amp_inf_tx = amp_inf_tx = amp_tabla[2 * indice] if emite == 1 else 0

        ##################################################
        # Blocks
        ##################################################

        self.tono_superior = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, amp_sup_tx, 0, 0)
        self.tono_inferior = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, (-f_tono), amp_inf_tx, 0, 0)
        self.suma = blocks.add_vcc(1)
        self.ritmo_grafico = blocks.throttle( gr.sizeof_float*512, 2000, True, 0 if "time" == "auto" else max( int(float(0.01) * 2000) if "time" == "time" else int(0.01), 1) )
        _pausa_check_box = Qt.QCheckBox("PAUSA: la salida queda en silencio. Destildar para transmitir")
        self._pausa_choices = {True: 1, False: 0}
        self._pausa_choices_inv = dict((v,k) for k,v in self._pausa_choices.items())
        self._pausa_callback = lambda i: Qt.QMetaObject.invokeMethod(_pausa_check_box, "setChecked", Qt.Q_ARG("bool", self._pausa_choices_inv[i]))
        self._pausa_callback(self.pausa)
        _pausa_check_box.stateChanged.connect(lambda i: self.set_pausa(self._pausa_choices[bool(i)]))
        self.top_grid_layout.addWidget(_pausa_check_box, 1, 0, 1, 4)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
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
            args="numchan=" + str(1) + " " + "bladerf=321e0fa5875945d99b11070bb0a76d31,buffers=" + str(bloques_usb) + ",buflen=" + str(muestras_por_bloque)
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
        self.top_grid_layout.addWidget(self._orden_recorrido_tool_bar, 1, 8, 1, 4)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_990_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_990_win = qtgui.RangeWidget(self._m_990_range, self.set_m_990, "<div align='right'>990:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_990_win, 10, 11, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(11, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_970_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_970_win = qtgui.RangeWidget(self._m_970_range, self.set_m_970, "<div align='right'>970:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_970_win, 10, 10, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 11):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_950_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_950_win = qtgui.RangeWidget(self._m_950_range, self.set_m_950, "<div align='right'>950:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_950_win, 10, 9, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_930_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_930_win = qtgui.RangeWidget(self._m_930_range, self.set_m_930, "<div align='right'>930:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_930_win, 10, 8, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_910_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_910_win = qtgui.RangeWidget(self._m_910_range, self.set_m_910, "<div align='right'>910:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_910_win, 10, 7, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_90_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_90_win = qtgui.RangeWidget(self._m_90_range, self.set_m_90, "<div align='right'>90:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_90_win, 7, 2, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_890_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_890_win = qtgui.RangeWidget(self._m_890_range, self.set_m_890, "<div align='right'>890:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_890_win, 10, 6, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_870_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_870_win = qtgui.RangeWidget(self._m_870_range, self.set_m_870, "<div align='right'>870:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_870_win, 10, 5, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_850_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_850_win = qtgui.RangeWidget(self._m_850_range, self.set_m_850, "<div align='right'>850:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_850_win, 10, 4, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_830_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_830_win = qtgui.RangeWidget(self._m_830_range, self.set_m_830, "<div align='right'>830:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_830_win, 10, 3, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_810_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_810_win = qtgui.RangeWidget(self._m_810_range, self.set_m_810, "<div align='right'>810:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_810_win, 10, 2, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_790_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_790_win = qtgui.RangeWidget(self._m_790_range, self.set_m_790, "<div align='right'>790:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_790_win, 10, 1, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_770_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_770_win = qtgui.RangeWidget(self._m_770_range, self.set_m_770, "<div align='right'>770:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_770_win, 10, 0, 1, 1)
        for r in range(10, 11):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_750_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_750_win = qtgui.RangeWidget(self._m_750_range, self.set_m_750, "<div align='right'>750:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_750_win, 9, 11, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(11, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_730_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_730_win = qtgui.RangeWidget(self._m_730_range, self.set_m_730, "<div align='right'>730:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_730_win, 9, 10, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 11):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_710_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_710_win = qtgui.RangeWidget(self._m_710_range, self.set_m_710, "<div align='right'>710:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_710_win, 9, 9, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_70_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_70_win = qtgui.RangeWidget(self._m_70_range, self.set_m_70, "<div align='right'>70:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_70_win, 7, 1, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_690_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_690_win = qtgui.RangeWidget(self._m_690_range, self.set_m_690, "<div align='right'>690:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_690_win, 9, 8, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_670_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_670_win = qtgui.RangeWidget(self._m_670_range, self.set_m_670, "<div align='right'>670:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_670_win, 9, 7, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_650_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_650_win = qtgui.RangeWidget(self._m_650_range, self.set_m_650, "<div align='right'>650:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_650_win, 9, 6, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_630_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_630_win = qtgui.RangeWidget(self._m_630_range, self.set_m_630, "<div align='right'>630:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_630_win, 9, 5, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_610_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_610_win = qtgui.RangeWidget(self._m_610_range, self.set_m_610, "<div align='right'>610:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_610_win, 9, 4, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_590_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_590_win = qtgui.RangeWidget(self._m_590_range, self.set_m_590, "<div align='right'>590:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_590_win, 9, 3, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_570_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_570_win = qtgui.RangeWidget(self._m_570_range, self.set_m_570, "<div align='right'>570:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_570_win, 9, 2, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_550_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_550_win = qtgui.RangeWidget(self._m_550_range, self.set_m_550, "<div align='right'>550:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_550_win, 9, 1, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_530_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_530_win = qtgui.RangeWidget(self._m_530_range, self.set_m_530, "<div align='right'>530:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_530_win, 9, 0, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_510_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_510_win = qtgui.RangeWidget(self._m_510_range, self.set_m_510, "<div align='right'>510:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_510_win, 8, 11, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(11, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_50_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_50_win = qtgui.RangeWidget(self._m_50_range, self.set_m_50, "<div align='right'>50:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_50_win, 7, 0, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_490_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_490_win = qtgui.RangeWidget(self._m_490_range, self.set_m_490, "<div align='right'>490:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_490_win, 8, 10, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 11):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_470_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_470_win = qtgui.RangeWidget(self._m_470_range, self.set_m_470, "<div align='right'>470:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_470_win, 8, 9, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_450_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_450_win = qtgui.RangeWidget(self._m_450_range, self.set_m_450, "<div align='right'>450:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_450_win, 8, 8, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_430_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_430_win = qtgui.RangeWidget(self._m_430_range, self.set_m_430, "<div align='right'>430:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_430_win, 8, 7, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_410_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_410_win = qtgui.RangeWidget(self._m_410_range, self.set_m_410, "<div align='right'>410:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_410_win, 8, 6, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_390_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_390_win = qtgui.RangeWidget(self._m_390_range, self.set_m_390, "<div align='right'>390:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_390_win, 8, 5, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_370_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_370_win = qtgui.RangeWidget(self._m_370_range, self.set_m_370, "<div align='right'>370:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_370_win, 8, 4, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_350_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_350_win = qtgui.RangeWidget(self._m_350_range, self.set_m_350, "<div align='right'>350:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_350_win, 8, 3, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_330_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_330_win = qtgui.RangeWidget(self._m_330_range, self.set_m_330, "<div align='right'>330:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_330_win, 8, 2, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_310_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_310_win = qtgui.RangeWidget(self._m_310_range, self.set_m_310, "<div align='right'>310:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_310_win, 8, 1, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_290_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_290_win = qtgui.RangeWidget(self._m_290_range, self.set_m_290, "<div align='right'>290:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_290_win, 8, 0, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_270_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_270_win = qtgui.RangeWidget(self._m_270_range, self.set_m_270, "<div align='right'>270:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_270_win, 7, 11, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(11, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_250_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_250_win = qtgui.RangeWidget(self._m_250_range, self.set_m_250, "<div align='right'>250:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_250_win, 7, 10, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 11):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_230_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_230_win = qtgui.RangeWidget(self._m_230_range, self.set_m_230, "<div align='right'>230:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_230_win, 7, 9, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_210_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_210_win = qtgui.RangeWidget(self._m_210_range, self.set_m_210, "<div align='right'>210:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_210_win, 7, 8, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_190_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_190_win = qtgui.RangeWidget(self._m_190_range, self.set_m_190, "<div align='right'>190:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_190_win, 7, 7, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_170_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_170_win = qtgui.RangeWidget(self._m_170_range, self.set_m_170, "<div align='right'>170:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_170_win, 7, 6, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_150_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_150_win = qtgui.RangeWidget(self._m_150_range, self.set_m_150, "<div align='right'>150:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_150_win, 7, 5, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_130_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_130_win = qtgui.RangeWidget(self._m_130_range, self.set_m_130, "<div align='right'>130:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_130_win, 7, 4, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_110_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_110_win = qtgui.RangeWidget(self._m_110_range, self.set_m_110, "<div align='right'>110:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_110_win, 7, 3, 1, 1)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.grafico = qtgui.vector_sink_f(
            512,
            ((f_primera - f_tono) / 1e6 - 10),
            (2 * n_port * 20.0 / 512),
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
        self.top_grid_layout.addWidget(self._grafico_win, 11, 0, 1, 12)
        for r in range(11, 12):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._ganancia_options = [45, 55, 65]
        # Create the labels list
        self._ganancia_labels = ['45 dB: lineas en -20 dBm', '55 dB: lineas en -10 dBm', '65 dB: lineas en 0 dBm']
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
        self.top_grid_layout.addWidget(self._ganancia_tool_bar, 1, 4, 1, 4)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_titulo_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'>" + str(x) + "</span>":
            self._et_titulo_formatter = lambda x: "<span style='font-size:11pt'>" + str(x) + "</span>"
        else:
            self._et_titulo_formatter = lambda x: str(x)

        self._et_titulo_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'><b>Valor de cada linea (MHz) con el peine sin calibrar, en dBm: </b></span>"))
        self._et_titulo_label = Qt.QLabel(str(self._et_titulo_formatter(self.et_titulo)))
        self._et_titulo_tool_bar.addWidget(self._et_titulo_label)
        self.top_grid_layout.addWidget(self._et_titulo_tool_bar, 6, 0, 1, 12)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_tiempos_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_tiempos_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_tiempos_formatter = lambda x: str(x)

        self._et_tiempos_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Pasada completa: </span>"))
        self._et_tiempos_label = Qt.QLabel(str(self._et_tiempos_formatter(self.et_tiempos)))
        self._et_tiempos_tool_bar.addWidget(self._et_tiempos_label)
        self.top_grid_layout.addWidget(self._et_tiempos_tool_bar, 2, 8, 1, 4)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_portadora_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>":
            self._et_portadora_formatter = lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_portadora_formatter = lambda x: str(x)

        self._et_portadora_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Portadora: </span>"))
        self._et_portadora_label = Qt.QLabel(str(self._et_portadora_formatter(self.et_portadora)))
        self._et_portadora_tool_bar.addWidget(self._et_portadora_label)
        self.top_grid_layout.addWidget(self._et_portadora_tool_bar, 0, 4, 1, 4)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_nivel_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_nivel_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_nivel_formatter = lambda x: str(x)

        self._et_nivel_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Con esta ganancia: </span>"))
        self._et_nivel_label = Qt.QLabel(str(self._et_nivel_formatter(self.et_nivel)))
        self._et_nivel_tool_bar.addWidget(self._et_nivel_label)
        self.top_grid_layout.addWidget(self._et_nivel_tool_bar, 2, 0, 1, 4)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_margen_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_margen_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_margen_formatter = lambda x: str(x)

        self._et_margen_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Lineas que piden mas de lo que hay: </span>"))
        self._et_margen_label = Qt.QLabel(str(self._et_margen_formatter(self.et_margen)))
        self._et_margen_tool_bar.addWidget(self._et_margen_label)
        self.top_grid_layout.addWidget(self._et_margen_tool_bar, 3, 4, 1, 4)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_lineas_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>":
            self._et_lineas_formatter = lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_lineas_formatter = lambda x: str(x)

        self._et_lineas_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Lineas: </span>"))
        self._et_lineas_label = Qt.QLabel(str(self._et_lineas_formatter(self.et_lineas)))
        self._et_lineas_tool_bar.addWidget(self._et_lineas_label)
        self.top_grid_layout.addWidget(self._et_lineas_tool_bar, 0, 8, 1, 4)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_etapa_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>":
            self._et_etapa_formatter = lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_etapa_formatter = lambda x: str(x)

        self._et_etapa_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Etapa: </span>"))
        self._et_etapa_label = Qt.QLabel(str(self._et_etapa_formatter(self.et_etapa)))
        self._et_etapa_tool_bar.addWidget(self._et_etapa_label)
        self.top_grid_layout.addWidget(self._et_etapa_tool_bar, 0, 0, 1, 4)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_comp_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_comp_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_comp_formatter = lambda x: str(x)

        self._et_comp_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Compensacion de estas dos lineas: </span>"))
        self._et_comp_label = Qt.QLabel(str(self._et_comp_formatter(self.et_comp)))
        self._et_comp_tool_bar.addWidget(self._et_comp_label)
        self.top_grid_layout.addWidget(self._et_comp_tool_bar, 2, 4, 1, 4)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_cargadas_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_cargadas_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_cargadas_formatter = lambda x: str(x)

        self._et_cargadas_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Lineas con valor cargado: </span>"))
        self._et_cargadas_label = Qt.QLabel(str(self._et_cargadas_formatter(self.et_cargadas)))
        self._et_cargadas_tool_bar.addWidget(self._et_cargadas_label)
        self.top_grid_layout.addWidget(self._et_cargadas_tool_bar, 3, 0, 1, 4)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_archivo_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_archivo_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_archivo_formatter = lambda x: str(x)

        self._et_archivo_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Calibracion en archivo: </span>"))
        self._et_archivo_label = Qt.QLabel(str(self._et_archivo_formatter(self.et_archivo)))
        self._et_archivo_tool_bar.addWidget(self._et_archivo_label)
        self.top_grid_layout.addWidget(self._et_archivo_tool_bar, 5, 0, 1, 12)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.datos_comp = blocks.vector_source_f(curva_comp, True, 512, [])
        self.datos_actual = blocks.vector_source_f(curva_actual, True, 512, [])
        _boton_importar_push_button = Qt.QPushButton('Importar calibracion previa')
        _boton_importar_push_button = Qt.QPushButton('Importar calibracion previa')
        self._boton_importar_choices = {'Pressed': 1, 'Released': 0}
        _boton_importar_push_button.pressed.connect(lambda: self.set_boton_importar(self._boton_importar_choices['Pressed']))
        _boton_importar_push_button.released.connect(lambda: self.set_boton_importar(self._boton_importar_choices['Released']))
        self.top_grid_layout.addWidget(_boton_importar_push_button, 4, 8, 1, 4)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_guardar_push_button = Qt.QPushButton('Guardar calibracion')
        _boton_guardar_push_button = Qt.QPushButton('Guardar calibracion')
        self._boton_guardar_choices = {'Pressed': 1, 'Released': 0}
        _boton_guardar_push_button.pressed.connect(lambda: self.set_boton_guardar(self._boton_guardar_choices['Pressed']))
        _boton_guardar_push_button.released.connect(lambda: self.set_boton_guardar(self._boton_guardar_choices['Released']))
        self.top_grid_layout.addWidget(_boton_guardar_push_button, 4, 4, 1, 4)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_generar_push_button = Qt.QPushButton('Generar calibracion (desde la captura .csv del analizador)')
        _boton_generar_push_button = Qt.QPushButton('Generar calibracion (desde la captura .csv del analizador)')
        self._boton_generar_choices = {'Pressed': 1, 'Released': 0}
        _boton_generar_push_button.pressed.connect(lambda: self.set_boton_generar(self._boton_generar_choices['Pressed']))
        _boton_generar_push_button.released.connect(lambda: self.set_boton_generar(self._boton_generar_choices['Released']))
        self.top_grid_layout.addWidget(_boton_generar_push_button, 4, 0, 1, 4)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
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
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp22_a9_peine_40MSPS")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_m_990(self):
        return self.m_990

    def set_m_990(self, m_990):
        self.m_990 = m_990
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_970(self):
        return self.m_970

    def set_m_970(self, m_970):
        self.m_970 = m_970
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_950(self):
        return self.m_950

    def set_m_950(self, m_950):
        self.m_950 = m_950
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_930(self):
        return self.m_930

    def set_m_930(self, m_930):
        self.m_930 = m_930
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_910(self):
        return self.m_910

    def set_m_910(self, m_910):
        self.m_910 = m_910
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_90(self):
        return self.m_90

    def set_m_90(self, m_90):
        self.m_90 = m_90
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_890(self):
        return self.m_890

    def set_m_890(self, m_890):
        self.m_890 = m_890
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_870(self):
        return self.m_870

    def set_m_870(self, m_870):
        self.m_870 = m_870
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_850(self):
        return self.m_850

    def set_m_850(self, m_850):
        self.m_850 = m_850
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_830(self):
        return self.m_830

    def set_m_830(self, m_830):
        self.m_830 = m_830
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_810(self):
        return self.m_810

    def set_m_810(self, m_810):
        self.m_810 = m_810
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_790(self):
        return self.m_790

    def set_m_790(self, m_790):
        self.m_790 = m_790
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_770(self):
        return self.m_770

    def set_m_770(self, m_770):
        self.m_770 = m_770
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_750(self):
        return self.m_750

    def set_m_750(self, m_750):
        self.m_750 = m_750
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_730(self):
        return self.m_730

    def set_m_730(self, m_730):
        self.m_730 = m_730
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_710(self):
        return self.m_710

    def set_m_710(self, m_710):
        self.m_710 = m_710
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_70(self):
        return self.m_70

    def set_m_70(self, m_70):
        self.m_70 = m_70
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_690(self):
        return self.m_690

    def set_m_690(self, m_690):
        self.m_690 = m_690
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_670(self):
        return self.m_670

    def set_m_670(self, m_670):
        self.m_670 = m_670
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_650(self):
        return self.m_650

    def set_m_650(self, m_650):
        self.m_650 = m_650
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_630(self):
        return self.m_630

    def set_m_630(self, m_630):
        self.m_630 = m_630
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_610(self):
        return self.m_610

    def set_m_610(self, m_610):
        self.m_610 = m_610
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_590(self):
        return self.m_590

    def set_m_590(self, m_590):
        self.m_590 = m_590
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_570(self):
        return self.m_570

    def set_m_570(self, m_570):
        self.m_570 = m_570
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_550(self):
        return self.m_550

    def set_m_550(self, m_550):
        self.m_550 = m_550
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_530(self):
        return self.m_530

    def set_m_530(self, m_530):
        self.m_530 = m_530
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_510(self):
        return self.m_510

    def set_m_510(self, m_510):
        self.m_510 = m_510
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_50(self):
        return self.m_50

    def set_m_50(self, m_50):
        self.m_50 = m_50
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_490(self):
        return self.m_490

    def set_m_490(self, m_490):
        self.m_490 = m_490
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_470(self):
        return self.m_470

    def set_m_470(self, m_470):
        self.m_470 = m_470
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_450(self):
        return self.m_450

    def set_m_450(self, m_450):
        self.m_450 = m_450
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_430(self):
        return self.m_430

    def set_m_430(self, m_430):
        self.m_430 = m_430
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_410(self):
        return self.m_410

    def set_m_410(self, m_410):
        self.m_410 = m_410
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_390(self):
        return self.m_390

    def set_m_390(self, m_390):
        self.m_390 = m_390
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_370(self):
        return self.m_370

    def set_m_370(self, m_370):
        self.m_370 = m_370
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_350(self):
        return self.m_350

    def set_m_350(self, m_350):
        self.m_350 = m_350
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_330(self):
        return self.m_330

    def set_m_330(self, m_330):
        self.m_330 = m_330
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_310(self):
        return self.m_310

    def set_m_310(self, m_310):
        self.m_310 = m_310
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_290(self):
        return self.m_290

    def set_m_290(self, m_290):
        self.m_290 = m_290
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_270(self):
        return self.m_270

    def set_m_270(self, m_270):
        self.m_270 = m_270
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_250(self):
        return self.m_250

    def set_m_250(self, m_250):
        self.m_250 = m_250
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_230(self):
        return self.m_230

    def set_m_230(self, m_230):
        self.m_230 = m_230
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_210(self):
        return self.m_210

    def set_m_210(self, m_210):
        self.m_210 = m_210
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_190(self):
        return self.m_190

    def set_m_190(self, m_190):
        self.m_190 = m_190
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_170(self):
        return self.m_170

    def set_m_170(self, m_170):
        self.m_170 = m_170
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_150(self):
        return self.m_150

    def set_m_150(self, m_150):
        self.m_150 = m_150
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_130(self):
        return self.m_130

    def set_m_130(self, m_130):
        self.m_130 = m_130
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

    def get_m_110(self):
        return self.m_110

    def set_m_110(self, m_110):
        self.m_110 = m_110
        self.set_medidos([self.m_50, self.m_70, self.m_90, self.m_110, self.m_130, self.m_150, self.m_170, self.m_190, self.m_210, self.m_230, self.m_250, self.m_270, self.m_290, self.m_310, self.m_330, self.m_350, self.m_370, self.m_390, self.m_410, self.m_430, self.m_450, self.m_470, self.m_490, self.m_510, self.m_530, self.m_550, self.m_570, self.m_590, self.m_610, self.m_630, self.m_650, self.m_670, self.m_690, self.m_710, self.m_730, self.m_750, self.m_770, self.m_790, self.m_810, self.m_830, self.m_850, self.m_870, self.m_890, self.m_910, self.m_930, self.m_950, self.m_970, self.m_990])

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
        self.set_linea_de_punto([j * 2 * self.n_port // 512 for j in range(512)])
        self.grafico.set_x_axis(((self.f_primera - self.f_tono) / 1e6 - 10), (2 * self.n_port * 20.0 / 512))

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
        self.set_et_titulo('referido a la ganancia de %d dB. Lo carga Generar calibracion; tambien se puede corregir a mano' % self.ganancia_de_lectura)

    def get_pasos_por_pasada(self):
        return self.pasos_por_pasada

    def set_pasos_por_pasada(self, pasos_por_pasada):
        self.pasos_por_pasada = pasos_por_pasada
        self.set_posicion(max(self.paso, 0) % self.pasos_por_pasada)
        self.set_pasada(max(self.paso, 0) // self.pasos_por_pasada + 1)
        self.set_et_portadora('%.0f MHz (paso %d de %d)' % (self.freq / 1e6, self.posicion + 1, self.pasos_por_pasada))
        self.set_et_tiempos('%d min %02d s (%.0f s por portadora)' % (self.permanencia * self.pasos_por_pasada // 60, self.permanencia * self.pasos_por_pasada % 60, self.permanencia))

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

    def get_ganancia(self):
        return self.ganancia

    def set_ganancia(self, ganancia):
        self.ganancia = ganancia
        self._ganancia_callback(self.ganancia)
        self.set_tx_gain(self.ganancia if self.pausa == 0 else 0)
        self.set_nivel_sin_calibrar(self.ganancia - 68)
        self.set_et_nivel('sin calibrar unos %d dBm, calibradas %d dBm' % (self.nivel_sin_calibrar, self.ganancia - 65))

    def get_f_primera(self):
        return self.f_primera

    def set_f_primera(self, f_primera):
        self.f_primera = f_primera
        self.set_freq(self.f_primera + self.paso_port * self.indice_freq)
        self.grafico.set_x_axis(((self.f_primera - self.f_tono) / 1e6 - 10), (2 * self.n_port * 20.0 / 512))

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
        self.set_et_tiempos('%d min %02d s (%.0f s por portadora)' % (self.permanencia * self.pasos_por_pasada // 60, self.permanencia * self.pasos_por_pasada % 60, self.permanencia))

    def get_nivel_sin_calibrar(self):
        return self.nivel_sin_calibrar

    def set_nivel_sin_calibrar(self, nivel_sin_calibrar):
        self.nivel_sin_calibrar = nivel_sin_calibrar
        self.set_et_nivel('sin calibrar unos %d dBm, calibradas %d dBm' % (self.nivel_sin_calibrar, self.ganancia - 65))

    def get_linea_de_punto(self):
        return self.linea_de_punto

    def set_linea_de_punto(self, linea_de_punto):
        self.linea_de_punto = linea_de_punto
        self.set_curva_comp([self.comp[k] for k in self.linea_de_punto])
        self.set_curva_actual([(self.comp[k] if (k // 2 == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

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
        self.grafico.set_x_axis(((self.f_primera - self.f_tono) / 1e6 - 10), (2 * self.n_port * 20.0 / 512))

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

    def get_muestras_por_bloque(self):
        return self.muestras_por_bloque

    def set_muestras_por_bloque(self, muestras_por_bloque):
        self.muestras_por_bloque = muestras_por_bloque

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

    def get_boton_generar(self):
        return self.boton_generar

    def set_boton_generar(self, boton_generar):
        self.boton_generar = boton_generar

    def get_bloques_usb(self):
        return self.bloques_usb

    def set_bloques_usb(self, bloques_usb):
        self.bloques_usb = bloques_usb

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




def main(top_block_cls=exp22_a9_peine_40MSPS, options=None):

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
