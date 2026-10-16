#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-25 xA9: lineas cada 40 MHz desde 60 MHz, con silencio en cada salto
# Description: bladeRF 2.0 micro xA9: 24 lineas cada 40 MHz, un tono por portadora, con la portadora 10 MHz por encima de la linea y 40 MSPS. Con las lineas desde 60 MHz, los armonicos del oscilador y la imagen del muestreo caen sobre otras lineas del peine; desde 50 MHz caen en el medio. Calibracion desde la captura del analizador, siempre a 0 dBm, con opcion de subir todo 3 dB. SOLO para medir con el analizador: nunca con el cable en RX1
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
    #   Boton "Guardar calibracion": escribe en un archivo de texto los 24 valores
    #   cargados en la ventana, uno por renglon, junto a su frecuencia.
    #   Boton "Importar calibracion previa": lee ese archivo y pone cada valor en
    #   su contador.
    # ============================================================================
    import os
    import time

    PRIMERA_LINEA = 60        # MHz
    SEPARACION = 40           # MHz entre una linea y la siguiente
    CERCA = 4                 # MHz: hasta que distancia de una linea se busca su pico

    # Los 24 contadores de la ventana, en orden de frecuencia (60, 100, ... 980 MHz).
    # d_widget es la casilla con flechas que se ve en pantalla.
    contadores = [
        self._m_60_win.d_widget, self._m_100_win.d_widget, self._m_140_win.d_widget,
        self._m_180_win.d_widget, self._m_220_win.d_widget, self._m_260_win.d_widget,
        self._m_300_win.d_widget, self._m_340_win.d_widget, self._m_380_win.d_widget,
        self._m_420_win.d_widget, self._m_460_win.d_widget, self._m_500_win.d_widget,
        self._m_540_win.d_widget, self._m_580_win.d_widget, self._m_620_win.d_widget,
        self._m_660_win.d_widget, self._m_700_win.d_widget, self._m_740_win.d_widget,
        self._m_780_win.d_widget, self._m_820_win.d_widget, self._m_860_win.d_widget,
        self._m_900_win.d_widget, self._m_940_win.d_widget, self._m_980_win.d_widget,
    ]


    def guardar():
        valores = self.get_medidos()                 # los 24 valores de la ventana
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
        # se busca cerca. Las lineas vecinas estan a 40 MHz: quedan afuera.
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


    # ============================================================================
    # NO RESINTONIZAR DE MAS
    # El paso del barrido cambia 4 veces por linea (encendido, encendido, apagado,
    # apagado) y GNU Radio vuelve a mandar la frecuencia a la placa en cada cambio,
    # aunque sea la misma. La placa resintoniza igual, y eso con el tono encendido
    # lo perturba. Aca se hace que la frecuencia se mande solo cuando cambia.
    # ============================================================================
    mandar_frecuencia = self.set_freq


    def mandar_frecuencia_si_cambia(frecuencia):
        if frecuencia != self.get_freq():
            mandar_frecuencia(frecuencia)


    self.set_freq = mandar_frecuencia_si_cambia


def snippets_main_after_init(tb):
    snipfcn_archivos_de_calibracion(tb)

class exp25_a9_peine_con_silencio_desde60(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-25 xA9: lineas cada 40 MHz desde 60 MHz, con silencio en cada salto", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-25 xA9: lineas cada 40 MHz desde 60 MHz, con silencio en cada salto")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp25_a9_peine_con_silencio_desde60")

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
        self.m_980 = m_980 = 0
        self.m_940 = m_940 = 0
        self.m_900 = m_900 = 0
        self.m_860 = m_860 = 0
        self.m_820 = m_820 = 0
        self.m_780 = m_780 = 0
        self.m_740 = m_740 = 0
        self.m_700 = m_700 = 0
        self.m_660 = m_660 = 0
        self.m_620 = m_620 = 0
        self.m_60 = m_60 = 0
        self.m_580 = m_580 = 0
        self.m_540 = m_540 = 0
        self.m_500 = m_500 = 0
        self.m_460 = m_460 = 0
        self.m_420 = m_420 = 0
        self.m_380 = m_380 = 0
        self.m_340 = m_340 = 0
        self.m_300 = m_300 = 0
        self.m_260 = m_260 = 0
        self.m_220 = m_220 = 0
        self.m_180 = m_180 = 0
        self.m_140 = m_140 = 0
        self.m_100 = m_100 = 0
        self.paso = paso = -1
        self.orden_recorrido = orden_recorrido = 0
        self.n_lineas = n_lineas = 24
        self.medidos = medidos = [m_60, m_100, m_140, m_180, m_220, m_260, m_300, m_340, m_380, m_420, m_460, m_500, m_540, m_580, m_620, m_660, m_700, m_740, m_780, m_820, m_860, m_900, m_940, m_980]
        self.ganancia_de_lectura = ganancia_de_lectura = 45
        self.pasos_por_pasada = pasos_por_pasada = n_lineas + 1 if orden_recorrido == 1 else n_lineas
        self.comp = comp = [(0.0 if leido == 0 else (ganancia_de_lectura - 65) - leido) for leido in medidos]
        self.ciclo = ciclo = (max(paso, 0) + 1) // 4
        self.posicion = posicion = ciclo % pasos_por_pasada
        self.orden = orden = sorted(range(n_lineas), key=lambda p: comp[p]) if orden_recorrido == 1 else list(range(n_lineas))
        self.indice = indice = orden[posicion] if posicion < n_lineas else n_lineas
        self.subida = subida = 0
        self.separacion = separacion = 10
        self.paso_lineas = paso_lineas = 40e6
        self.indice_freq = indice_freq = orden[n_lineas - 1] if indice >= n_lineas else indice
        self.f_primera = f_primera = 60e6
        self.samp_rate = samp_rate = 40e6
        self.pedido = pedido = [(0.0 if leido == 0 else comp[k] + subida) for k, leido in enumerate(medidos)]
        self.pausa = pausa = 1
        self.pasada = pasada = ciclo // pasos_por_pasada + 1
        self.linea = linea = f_primera + paso_lineas * indice_freq
        self.ganancia = ganancia = 45
        self.fase = fase = max(paso, 0) % 4
        self.f_tono = f_tono = -separacion * 1e6
        self.entre_pasadas = entre_pasadas = 1 if indice >= n_lineas else 0
        self.archivo = archivo = 'calibracion_peine_desde60.txt'
        self.amp_max = amp_max = 0.95
        self.amp_base = amp_base = 0.25
        self.sin_margen = sin_margen = sum(1 for db in pedido if amp_base * 10 ** (db / 20.0) > amp_max)
        self.permanencia = permanencia = 6.0
        self.nivel_sin_calibrar = nivel_sin_calibrar = ganancia - 68
        self.linea_de_punto = linea_de_punto = [j * n_lineas // 512 for j in range(512)]
        self.freq = freq = linea - f_tono
        self.etapa = etapa = 'PAUSA (sin emitir)' if pausa == 1 else ('INICIACION' if paso < 0 else ('SILENCIO (salto de frecuencia), pasada %d' % pasada if (entre_pasadas == 1 or fase >= 2) else 'TRANSMISION, pasada %d' % pasada))
        self.estado_archivo = estado_archivo = 'hay una guardada, sin importar' if os.path.exists(archivo) else 'todavia no hay ninguna guardada'
        self.emite = emite = 1 if (pausa == 0 and paso >= 0 and fase < 2) else 0
        self.cargadas = cargadas = sum(1 for leido in medidos if leido != 0)
        self.ancho_banda = ancho_banda = 0.9 * samp_rate
        self.amp_tabla = amp_tabla = [min(amp_base * 10 ** (db / 20.0), amp_max) for db in pedido] + [0.0]
        self.tx_gain = tx_gain = ganancia if pausa == 0 else 0
        self.muestras_por_bloque = muestras_por_bloque = 16384
        self.lista_de_pasos = lista_de_pasos = list(range(100000))
        self.et_titulo = et_titulo = 'referido a la ganancia de %d dB (lo leido menos %d dB con el selector en 65). Lo carga Generar calibracion' % (ganancia_de_lectura, 65 - ganancia_de_lectura)
        self.et_tiempos = et_tiempos = '%d min %02d s (%.0f s encendido y %.0f s apagado por linea)' % (2 * permanencia * pasos_por_pasada // 60, 2 * permanencia * pasos_por_pasada % 60, permanencia, permanencia)
        self.et_tasa = et_tasa = '%.0f MSPS, filtro de %.1f MHz' % (samp_rate / 1e6, ancho_banda / 1e6)
        self.et_portadora = et_portadora = '%.0f MHz' % (freq / 1e6)
        self.et_nivel = et_nivel = 'sin calibrar unos %d dBm, calibradas %d dBm' % (nivel_sin_calibrar, ganancia - 65 + subida)
        self.et_margen = et_margen = sin_margen
        self.et_linea = et_linea = '%.0f MHz (paso %d de %d)' % (linea / 1e6, posicion + 1, pasos_por_pasada)
        self.et_etapa = et_etapa = etapa
        self.et_espurias = et_espurias = 'fuga en %.0f MHz, imagen en %.0f MHz' % (freq / 1e6, (freq - f_tono) / 1e6)
        self.et_comp = et_comp = '%.3f (%+.1f dB sobre la base)' % (amp_tabla[indice_freq], pedido[indice_freq])
        self.et_cargadas = et_cargadas = '%d de %d' % (cargadas, n_lineas)
        self.et_archivo = et_archivo = estado_archivo
        self.curva_comp = curva_comp = [pedido[k] for k in linea_de_punto]
        self.curva_actual = curva_actual = [(pedido[k] if (k == indice and emite == 1) else -2) for k in linea_de_punto]
        self.boton_importar = boton_importar = 0
        self.boton_guardar = boton_guardar = 0
        self.boton_generar = boton_generar = 0
        self.bloques_usb = bloques_usb = 128
        self.amp_tx = amp_tx = amp_tabla[indice] if emite == 1 else 0

        ##################################################
        # Blocks
        ##################################################

        self.tono = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, amp_tx, 0, 0)
        # Create the options list
        self._subida_options = [0, 3]
        # Create the labels list
        self._subida_labels = ['Calibrado', 'Calibrado + 3 dB']
        # Create the combo box
        self._subida_tool_bar = Qt.QToolBar(self)
        self._subida_tool_bar.addWidget(Qt.QLabel("Nivel" + ": "))
        self._subida_combo_box = Qt.QComboBox()
        self._subida_tool_bar.addWidget(self._subida_combo_box)
        for _label in self._subida_labels: self._subida_combo_box.addItem(_label)
        self._subida_callback = lambda i: Qt.QMetaObject.invokeMethod(self._subida_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._subida_options.index(i)))
        self._subida_callback(self.subida)
        self._subida_combo_box.currentIndexChanged.connect(
            lambda i: self.set_subida(self._subida_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._subida_tool_bar, 1, 4, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.ritmo_grafico = blocks.throttle( gr.sizeof_float*512, 2000, True, 0 if "time" == "auto" else max( int(float(0.01) * 2000) if "time" == "time" else int(0.01), 1) )
        _pausa_check_box = Qt.QCheckBox("PAUSA: la salida queda en silencio. Destildar para transmitir")
        self._pausa_choices = {True: 1, False: 0}
        self._pausa_choices_inv = dict((v,k) for k,v in self._pausa_choices.items())
        self._pausa_callback = lambda i: Qt.QMetaObject.invokeMethod(_pausa_check_box, "setChecked", Qt.Q_ARG("bool", self._pausa_choices_inv[i]))
        self._pausa_callback(self.pausa)
        _pausa_check_box.stateChanged.connect(lambda i: self.set_pausa(self._pausa_choices[bool(i)]))
        self.top_grid_layout.addWidget(_pausa_check_box, 1, 0, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
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
            time.sleep(1.0 / ((2.0 / permanencia)))
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
        self._orden_recorrido_labels = ['Por frecuencia', 'De menor a mayor nivel']
        # Create the combo box
        self._orden_recorrido_tool_bar = Qt.QToolBar(self)
        self._orden_recorrido_tool_bar.addWidget(Qt.QLabel("Orden" + ": "))
        self._orden_recorrido_combo_box = Qt.QComboBox()
        self._orden_recorrido_tool_bar.addWidget(self._orden_recorrido_combo_box)
        for _label in self._orden_recorrido_labels: self._orden_recorrido_combo_box.addItem(_label)
        self._orden_recorrido_callback = lambda i: Qt.QMetaObject.invokeMethod(self._orden_recorrido_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._orden_recorrido_options.index(i)))
        self._orden_recorrido_callback(self.orden_recorrido)
        self._orden_recorrido_combo_box.currentIndexChanged.connect(
            lambda i: self.set_orden_recorrido(self._orden_recorrido_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._orden_recorrido_tool_bar, 1, 8, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_980_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_980_win = qtgui.RangeWidget(self._m_980_range, self.set_m_980, "<div align='right'>980:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_980_win, 9, 11, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(11, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_940_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_940_win = qtgui.RangeWidget(self._m_940_range, self.set_m_940, "<div align='right'>940:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_940_win, 9, 10, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 11):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_900_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_900_win = qtgui.RangeWidget(self._m_900_range, self.set_m_900, "<div align='right'>900:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_900_win, 9, 9, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_860_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_860_win = qtgui.RangeWidget(self._m_860_range, self.set_m_860, "<div align='right'>860:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_860_win, 9, 8, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_820_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_820_win = qtgui.RangeWidget(self._m_820_range, self.set_m_820, "<div align='right'>820:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_820_win, 9, 7, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_780_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_780_win = qtgui.RangeWidget(self._m_780_range, self.set_m_780, "<div align='right'>780:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_780_win, 9, 6, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_740_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_740_win = qtgui.RangeWidget(self._m_740_range, self.set_m_740, "<div align='right'>740:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_740_win, 9, 5, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_700_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_700_win = qtgui.RangeWidget(self._m_700_range, self.set_m_700, "<div align='right'>700:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_700_win, 9, 4, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_660_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_660_win = qtgui.RangeWidget(self._m_660_range, self.set_m_660, "<div align='right'>660:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_660_win, 9, 3, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_620_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_620_win = qtgui.RangeWidget(self._m_620_range, self.set_m_620, "<div align='right'>620:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_620_win, 9, 2, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_60_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_60_win = qtgui.RangeWidget(self._m_60_range, self.set_m_60, "<div align='right'>60:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_60_win, 8, 0, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_580_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_580_win = qtgui.RangeWidget(self._m_580_range, self.set_m_580, "<div align='right'>580:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_580_win, 9, 1, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_540_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_540_win = qtgui.RangeWidget(self._m_540_range, self.set_m_540, "<div align='right'>540:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_540_win, 9, 0, 1, 1)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_500_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_500_win = qtgui.RangeWidget(self._m_500_range, self.set_m_500, "<div align='right'>500:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_500_win, 8, 11, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(11, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_460_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_460_win = qtgui.RangeWidget(self._m_460_range, self.set_m_460, "<div align='right'>460:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_460_win, 8, 10, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(10, 11):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_420_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_420_win = qtgui.RangeWidget(self._m_420_range, self.set_m_420, "<div align='right'>420:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_420_win, 8, 9, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_380_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_380_win = qtgui.RangeWidget(self._m_380_range, self.set_m_380, "<div align='right'>380:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_380_win, 8, 8, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_340_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_340_win = qtgui.RangeWidget(self._m_340_range, self.set_m_340, "<div align='right'>340:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_340_win, 8, 7, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_300_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_300_win = qtgui.RangeWidget(self._m_300_range, self.set_m_300, "<div align='right'>300:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_300_win, 8, 6, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_260_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_260_win = qtgui.RangeWidget(self._m_260_range, self.set_m_260, "<div align='right'>260:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_260_win, 8, 5, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(5, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_220_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_220_win = qtgui.RangeWidget(self._m_220_range, self.set_m_220, "<div align='right'>220:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_220_win, 8, 4, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 5):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_180_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_180_win = qtgui.RangeWidget(self._m_180_range, self.set_m_180, "<div align='right'>180:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_180_win, 8, 3, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_140_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_140_win = qtgui.RangeWidget(self._m_140_range, self.set_m_140, "<div align='right'>140:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_140_win, 8, 2, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._m_100_range = qtgui.Range(-40, 3, 0.1, 0, 50)
        self._m_100_win = qtgui.RangeWidget(self._m_100_range, self.set_m_100, "<div align='right'>100:&nbsp;</div>", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._m_100_win, 8, 1, 1, 1)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.grafico = qtgui.vector_sink_f(
            512,
            ((f_primera - paso_lineas / 2) / 1e6),
            (n_lineas * paso_lineas / 1e6 / 512),
            "Frecuencia de la linea",
            "Sobre la base",
            "Lo que se le suma a cada linea",
            2, # Number of inputs
            None # parent
        )
        self.grafico.set_update_time(0.10)
        self.grafico.set_y_axis((-2), 12)
        self.grafico.enable_autoscale(False)
        self.grafico.enable_grid(True)
        self.grafico.set_x_axis_units("MHz")
        self.grafico.set_y_axis_units("dB")
        self.grafico.set_ref_level(0)


        labels = ["Pedido a cada linea", "Linea que sale ahora", '', '', '',
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
        self.top_grid_layout.addWidget(self._grafico_win, 10, 0, 1, 12)
        for r in range(10, 11):
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
        self.top_grid_layout.addWidget(self._ganancia_tool_bar, 1, 2, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(2, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_titulo_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'>" + str(x) + "</span>":
            self._et_titulo_formatter = lambda x: "<span style='font-size:11pt'>" + str(x) + "</span>"
        else:
            self._et_titulo_formatter = lambda x: str(x)

        self._et_titulo_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'><b>Valor de cada linea (MHz) sin calibrar, en dBm: </b></span>"))
        self._et_titulo_label = Qt.QLabel(str(self._et_titulo_formatter(self.et_titulo)))
        self._et_titulo_tool_bar.addWidget(self._et_titulo_label)
        self.top_grid_layout.addWidget(self._et_titulo_tool_bar, 7, 0, 1, 10)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_tiempos_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_tiempos_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_tiempos_formatter = lambda x: str(x)

        self._et_tiempos_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Pasada completa: </span>"))
        self._et_tiempos_label = Qt.QLabel(str(self._et_tiempos_formatter(self.et_tiempos)))
        self._et_tiempos_tool_bar.addWidget(self._et_tiempos_label)
        self.top_grid_layout.addWidget(self._et_tiempos_tool_bar, 3, 7, 1, 3)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_tasa_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_tasa_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_tasa_formatter = lambda x: str(x)

        self._et_tasa_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Tasa de muestreo: </span>"))
        self._et_tasa_label = Qt.QLabel(str(self._et_tasa_formatter(self.et_tasa)))
        self._et_tasa_tool_bar.addWidget(self._et_tasa_label)
        self.top_grid_layout.addWidget(self._et_tasa_tool_bar, 6, 0, 1, 10)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_portadora_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>":
            self._et_portadora_formatter = lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_portadora_formatter = lambda x: str(x)

        self._et_portadora_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Portadora: </span>"))
        self._et_portadora_label = Qt.QLabel(str(self._et_portadora_formatter(self.et_portadora)))
        self._et_portadora_tool_bar.addWidget(self._et_portadora_label)
        self.top_grid_layout.addWidget(self._et_portadora_tool_bar, 0, 7, 1, 3)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 10):
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
        self.top_grid_layout.addWidget(self._et_margen_tool_bar, 3, 4, 1, 3)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_linea_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>":
            self._et_linea_formatter = lambda x: "<span style='font-size:15pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_linea_formatter = lambda x: str(x)

        self._et_linea_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Linea: </span>"))
        self._et_linea_label = Qt.QLabel(str(self._et_linea_formatter(self.et_linea)))
        self._et_linea_tool_bar.addWidget(self._et_linea_label)
        self.top_grid_layout.addWidget(self._et_linea_tool_bar, 0, 4, 1, 3)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 7):
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
        self._et_espurias_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_espurias_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_espurias_formatter = lambda x: str(x)

        self._et_espurias_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>De esta linea: </span>"))
        self._et_espurias_label = Qt.QLabel(str(self._et_espurias_formatter(self.et_espurias)))
        self._et_espurias_tool_bar.addWidget(self._et_espurias_label)
        self.top_grid_layout.addWidget(self._et_espurias_tool_bar, 2, 7, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_comp_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>":
            self._et_comp_formatter = lambda x: "<span style='font-size:11pt'><b>" + str(x) + "</b></span>"
        else:
            self._et_comp_formatter = lambda x: str(x)

        self._et_comp_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Amplitud de esta linea: </span>"))
        self._et_comp_label = Qt.QLabel(str(self._et_comp_formatter(self.et_comp)))
        self._et_comp_tool_bar.addWidget(self._et_comp_label)
        self.top_grid_layout.addWidget(self._et_comp_tool_bar, 2, 4, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 7):
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
        self.top_grid_layout.addWidget(self._et_archivo_tool_bar, 5, 0, 1, 10)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.datos_comp = blocks.vector_source_f(curva_comp, True, 512, [])
        self.datos_actual = blocks.vector_source_f(curva_actual, True, 512, [])
        _boton_importar_push_button = Qt.QPushButton('Importar calibracion previa')
        _boton_importar_push_button = Qt.QPushButton('Importar calibracion previa')
        self._boton_importar_choices = {'Pressed': 1, 'Released': 0}
        _boton_importar_push_button.pressed.connect(lambda: self.set_boton_importar(self._boton_importar_choices['Pressed']))
        _boton_importar_push_button.released.connect(lambda: self.set_boton_importar(self._boton_importar_choices['Released']))
        self.top_grid_layout.addWidget(_boton_importar_push_button, 4, 7, 1, 3)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(7, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_guardar_push_button = Qt.QPushButton('Guardar calibracion')
        _boton_guardar_push_button = Qt.QPushButton('Guardar calibracion')
        self._boton_guardar_choices = {'Pressed': 1, 'Released': 0}
        _boton_guardar_push_button.pressed.connect(lambda: self.set_boton_guardar(self._boton_guardar_choices['Pressed']))
        _boton_guardar_push_button.released.connect(lambda: self.set_boton_guardar(self._boton_guardar_choices['Released']))
        self.top_grid_layout.addWidget(_boton_guardar_push_button, 4, 4, 1, 3)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 7):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_generar_push_button = Qt.QPushButton('Generar calibracion (desde la captura .csv)')
        _boton_generar_push_button = Qt.QPushButton('Generar calibracion (desde la captura .csv)')
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
        self.connect((self.tono, 0), (self.osmosdr_sink_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp25_a9_peine_con_silencio_desde60")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_m_980(self):
        return self.m_980

    def set_m_980(self, m_980):
        self.m_980 = m_980
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_940(self):
        return self.m_940

    def set_m_940(self, m_940):
        self.m_940 = m_940
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_900(self):
        return self.m_900

    def set_m_900(self, m_900):
        self.m_900 = m_900
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_860(self):
        return self.m_860

    def set_m_860(self, m_860):
        self.m_860 = m_860
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_820(self):
        return self.m_820

    def set_m_820(self, m_820):
        self.m_820 = m_820
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_780(self):
        return self.m_780

    def set_m_780(self, m_780):
        self.m_780 = m_780
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_740(self):
        return self.m_740

    def set_m_740(self, m_740):
        self.m_740 = m_740
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_700(self):
        return self.m_700

    def set_m_700(self, m_700):
        self.m_700 = m_700
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_660(self):
        return self.m_660

    def set_m_660(self, m_660):
        self.m_660 = m_660
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_620(self):
        return self.m_620

    def set_m_620(self, m_620):
        self.m_620 = m_620
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_60(self):
        return self.m_60

    def set_m_60(self, m_60):
        self.m_60 = m_60
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_580(self):
        return self.m_580

    def set_m_580(self, m_580):
        self.m_580 = m_580
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_540(self):
        return self.m_540

    def set_m_540(self, m_540):
        self.m_540 = m_540
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_500(self):
        return self.m_500

    def set_m_500(self, m_500):
        self.m_500 = m_500
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_460(self):
        return self.m_460

    def set_m_460(self, m_460):
        self.m_460 = m_460
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_420(self):
        return self.m_420

    def set_m_420(self, m_420):
        self.m_420 = m_420
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_380(self):
        return self.m_380

    def set_m_380(self, m_380):
        self.m_380 = m_380
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_340(self):
        return self.m_340

    def set_m_340(self, m_340):
        self.m_340 = m_340
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_300(self):
        return self.m_300

    def set_m_300(self, m_300):
        self.m_300 = m_300
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_260(self):
        return self.m_260

    def set_m_260(self, m_260):
        self.m_260 = m_260
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_220(self):
        return self.m_220

    def set_m_220(self, m_220):
        self.m_220 = m_220
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_180(self):
        return self.m_180

    def set_m_180(self, m_180):
        self.m_180 = m_180
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_140(self):
        return self.m_140

    def set_m_140(self, m_140):
        self.m_140 = m_140
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_m_100(self):
        return self.m_100

    def set_m_100(self, m_100):
        self.m_100 = m_100
        self.set_medidos([self.m_60, self.m_100, self.m_140, self.m_180, self.m_220, self.m_260, self.m_300, self.m_340, self.m_380, self.m_420, self.m_460, self.m_500, self.m_540, self.m_580, self.m_620, self.m_660, self.m_700, self.m_740, self.m_780, self.m_820, self.m_860, self.m_900, self.m_940, self.m_980])

    def get_paso(self):
        return self.paso

    def set_paso(self, paso):
        self.paso = paso
        self.set_fase(max(self.paso, 0) % 4)
        self.set_ciclo((max(self.paso, 0) + 1) // 4)
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0 and self.fase < 2) else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO (salto de frecuencia), pasada %d' % self.pasada if (self.entre_pasadas == 1 or self.fase >= 2) else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_orden_recorrido(self):
        return self.orden_recorrido

    def set_orden_recorrido(self, orden_recorrido):
        self.orden_recorrido = orden_recorrido
        self.set_pasos_por_pasada(self.n_lineas + 1 if self.orden_recorrido == 1 else self.n_lineas)
        self.set_orden(sorted(range(self.n_lineas), key=lambda p: self.comp[p]) if self.orden_recorrido == 1 else list(range(self.n_lineas)))
        self._orden_recorrido_callback(self.orden_recorrido)

    def get_n_lineas(self):
        return self.n_lineas

    def set_n_lineas(self, n_lineas):
        self.n_lineas = n_lineas
        self.set_pasos_por_pasada(self.n_lineas + 1 if self.orden_recorrido == 1 else self.n_lineas)
        self.set_orden(sorted(range(self.n_lineas), key=lambda p: self.comp[p]) if self.orden_recorrido == 1 else list(range(self.n_lineas)))
        self.set_indice(self.orden[self.posicion] if self.posicion < self.n_lineas else self.n_lineas)
        self.set_entre_pasadas(1 if self.indice >= self.n_lineas else 0)
        self.set_indice_freq(self.orden[self.n_lineas - 1] if self.indice >= self.n_lineas else self.indice)
        self.set_et_cargadas('%d de %d' % (self.cargadas, self.n_lineas))
        self.set_linea_de_punto([j * self.n_lineas // 512 for j in range(512)])
        self.grafico.set_x_axis(((self.f_primera - self.paso_lineas / 2) / 1e6), (self.n_lineas * self.paso_lineas / 1e6 / 512))

    def get_medidos(self):
        return self.medidos

    def set_medidos(self, medidos):
        self.medidos = medidos
        self.set_comp([(0.0 if leido == 0 else (self.ganancia_de_lectura - 65) - leido) for leido in self.medidos])
        self.set_pedido([(0.0 if leido == 0 else self.comp[k] + self.subida) for k, leido in enumerate(self.medidos)])
        self.set_cargadas(sum(1 for leido in self.medidos if leido != 0))

    def get_ganancia_de_lectura(self):
        return self.ganancia_de_lectura

    def set_ganancia_de_lectura(self, ganancia_de_lectura):
        self.ganancia_de_lectura = ganancia_de_lectura
        self.set_comp([(0.0 if leido == 0 else (self.ganancia_de_lectura - 65) - leido) for leido in self.medidos])
        self.set_et_titulo('referido a la ganancia de %d dB (lo leido menos %d dB con el selector en 65). Lo carga Generar calibracion' % (self.ganancia_de_lectura, 65 - self.ganancia_de_lectura))

    def get_pasos_por_pasada(self):
        return self.pasos_por_pasada

    def set_pasos_por_pasada(self, pasos_por_pasada):
        self.pasos_por_pasada = pasos_por_pasada
        self.set_posicion(self.ciclo % self.pasos_por_pasada)
        self.set_pasada(self.ciclo // self.pasos_por_pasada + 1)
        self.set_et_linea('%.0f MHz (paso %d de %d)' % (self.linea / 1e6, self.posicion + 1, self.pasos_por_pasada))
        self.set_et_tiempos('%d min %02d s (%.0f s encendido y %.0f s apagado por linea)' % (2 * self.permanencia * self.pasos_por_pasada // 60, 2 * self.permanencia * self.pasos_por_pasada % 60, self.permanencia, self.permanencia))

    def get_comp(self):
        return self.comp

    def set_comp(self, comp):
        self.comp = comp
        self.set_orden(sorted(range(self.n_lineas), key=lambda p: self.comp[p]) if self.orden_recorrido == 1 else list(range(self.n_lineas)))
        self.set_pedido([(0.0 if leido == 0 else self.comp[k] + self.subida) for k, leido in enumerate(self.medidos)])

    def get_ciclo(self):
        return self.ciclo

    def set_ciclo(self, ciclo):
        self.ciclo = ciclo
        self.set_posicion(self.ciclo % self.pasos_por_pasada)
        self.set_pasada(self.ciclo // self.pasos_por_pasada + 1)

    def get_posicion(self):
        return self.posicion

    def set_posicion(self, posicion):
        self.posicion = posicion
        self.set_indice(self.orden[self.posicion] if self.posicion < self.n_lineas else self.n_lineas)
        self.set_et_linea('%.0f MHz (paso %d de %d)' % (self.linea / 1e6, self.posicion + 1, self.pasos_por_pasada))

    def get_orden(self):
        return self.orden

    def set_orden(self, orden):
        self.orden = orden
        self.set_indice(self.orden[self.posicion] if self.posicion < self.n_lineas else self.n_lineas)
        self.set_indice_freq(self.orden[self.n_lineas - 1] if self.indice >= self.n_lineas else self.indice)

    def get_indice(self):
        return self.indice

    def set_indice(self, indice):
        self.indice = indice
        self.set_entre_pasadas(1 if self.indice >= self.n_lineas else 0)
        self.set_indice_freq(self.orden[self.n_lineas - 1] if self.indice >= self.n_lineas else self.indice)
        self.set_amp_tx(self.amp_tabla[self.indice] if self.emite == 1 else 0)
        self.set_curva_actual([(self.pedido[k] if (k == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

    def get_subida(self):
        return self.subida

    def set_subida(self, subida):
        self.subida = subida
        self._subida_callback(self.subida)
        self.set_pedido([(0.0 if leido == 0 else self.comp[k] + self.subida) for k, leido in enumerate(self.medidos)])
        self.set_et_nivel('sin calibrar unos %d dBm, calibradas %d dBm' % (self.nivel_sin_calibrar, self.ganancia - 65 + self.subida))

    def get_separacion(self):
        return self.separacion

    def set_separacion(self, separacion):
        self.separacion = separacion
        self.set_f_tono(-self.separacion * 1e6)

    def get_paso_lineas(self):
        return self.paso_lineas

    def set_paso_lineas(self, paso_lineas):
        self.paso_lineas = paso_lineas
        self.set_linea(self.f_primera + self.paso_lineas * self.indice_freq)
        self.grafico.set_x_axis(((self.f_primera - self.paso_lineas / 2) / 1e6), (self.n_lineas * self.paso_lineas / 1e6 / 512))

    def get_indice_freq(self):
        return self.indice_freq

    def set_indice_freq(self, indice_freq):
        self.indice_freq = indice_freq
        self.set_linea(self.f_primera + self.paso_lineas * self.indice_freq)
        self.set_et_comp('%.3f (%+.1f dB sobre la base)' % (self.amp_tabla[self.indice_freq], self.pedido[self.indice_freq]))

    def get_f_primera(self):
        return self.f_primera

    def set_f_primera(self, f_primera):
        self.f_primera = f_primera
        self.set_linea(self.f_primera + self.paso_lineas * self.indice_freq)
        self.grafico.set_x_axis(((self.f_primera - self.paso_lineas / 2) / 1e6), (self.n_lineas * self.paso_lineas / 1e6 / 512))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_ancho_banda(0.9 * self.samp_rate)
        self.set_et_tasa('%.0f MSPS, filtro de %.1f MHz' % (self.samp_rate / 1e6, self.ancho_banda / 1e6))
        self.tono.set_sampling_freq(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)

    def get_pedido(self):
        return self.pedido

    def set_pedido(self, pedido):
        self.pedido = pedido
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.pedido] + [0.0])
        self.set_sin_margen(sum(1 for db in self.pedido if self.amp_base * 10 ** (db / 20.0) > self.amp_max))
        self.set_et_comp('%.3f (%+.1f dB sobre la base)' % (self.amp_tabla[self.indice_freq], self.pedido[self.indice_freq]))
        self.set_curva_comp([self.pedido[k] for k in self.linea_de_punto])
        self.set_curva_actual([(self.pedido[k] if (k == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

    def get_pausa(self):
        return self.pausa

    def set_pausa(self, pausa):
        self.pausa = pausa
        self._pausa_callback(self.pausa)
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0 and self.fase < 2) else 0)
        self.set_tx_gain(self.ganancia if self.pausa == 0 else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO (salto de frecuencia), pasada %d' % self.pasada if (self.entre_pasadas == 1 or self.fase >= 2) else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_pasada(self):
        return self.pasada

    def set_pasada(self, pasada):
        self.pasada = pasada
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO (salto de frecuencia), pasada %d' % self.pasada if (self.entre_pasadas == 1 or self.fase >= 2) else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_linea(self):
        return self.linea

    def set_linea(self, linea):
        self.linea = linea
        self.set_freq(self.linea - self.f_tono)
        self.set_et_linea('%.0f MHz (paso %d de %d)' % (self.linea / 1e6, self.posicion + 1, self.pasos_por_pasada))

    def get_ganancia(self):
        return self.ganancia

    def set_ganancia(self, ganancia):
        self.ganancia = ganancia
        self._ganancia_callback(self.ganancia)
        self.set_tx_gain(self.ganancia if self.pausa == 0 else 0)
        self.set_nivel_sin_calibrar(self.ganancia - 68)
        self.set_et_nivel('sin calibrar unos %d dBm, calibradas %d dBm' % (self.nivel_sin_calibrar, self.ganancia - 65 + self.subida))

    def get_fase(self):
        return self.fase

    def set_fase(self, fase):
        self.fase = fase
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0 and self.fase < 2) else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO (salto de frecuencia), pasada %d' % self.pasada if (self.entre_pasadas == 1 or self.fase >= 2) else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_f_tono(self):
        return self.f_tono

    def set_f_tono(self, f_tono):
        self.f_tono = f_tono
        self.set_freq(self.linea - self.f_tono)
        self.set_et_espurias('fuga en %.0f MHz, imagen en %.0f MHz' % (self.freq / 1e6, (self.freq - self.f_tono) / 1e6))
        self.tono.set_frequency(self.f_tono)

    def get_entre_pasadas(self):
        return self.entre_pasadas

    def set_entre_pasadas(self, entre_pasadas):
        self.entre_pasadas = entre_pasadas
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('SILENCIO (salto de frecuencia), pasada %d' % self.pasada if (self.entre_pasadas == 1 or self.fase >= 2) else 'TRANSMISION, pasada %d' % self.pasada)))

    def get_archivo(self):
        return self.archivo

    def set_archivo(self, archivo):
        self.archivo = archivo
        self.set_estado_archivo('hay una guardada, sin importar' if os.path.exists(self.archivo) else 'todavia no hay ninguna guardada')

    def get_amp_max(self):
        return self.amp_max

    def set_amp_max(self, amp_max):
        self.amp_max = amp_max
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.pedido] + [0.0])
        self.set_sin_margen(sum(1 for db in self.pedido if self.amp_base * 10 ** (db / 20.0) > self.amp_max))

    def get_amp_base(self):
        return self.amp_base

    def set_amp_base(self, amp_base):
        self.amp_base = amp_base
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.pedido] + [0.0])
        self.set_sin_margen(sum(1 for db in self.pedido if self.amp_base * 10 ** (db / 20.0) > self.amp_max))

    def get_sin_margen(self):
        return self.sin_margen

    def set_sin_margen(self, sin_margen):
        self.sin_margen = sin_margen
        self.set_et_margen(self.sin_margen)

    def get_permanencia(self):
        return self.permanencia

    def set_permanencia(self, permanencia):
        self.permanencia = permanencia
        self.set_et_tiempos('%d min %02d s (%.0f s encendido y %.0f s apagado por linea)' % (2 * self.permanencia * self.pasos_por_pasada // 60, 2 * self.permanencia * self.pasos_por_pasada % 60, self.permanencia, self.permanencia))

    def get_nivel_sin_calibrar(self):
        return self.nivel_sin_calibrar

    def set_nivel_sin_calibrar(self, nivel_sin_calibrar):
        self.nivel_sin_calibrar = nivel_sin_calibrar
        self.set_et_nivel('sin calibrar unos %d dBm, calibradas %d dBm' % (self.nivel_sin_calibrar, self.ganancia - 65 + self.subida))

    def get_linea_de_punto(self):
        return self.linea_de_punto

    def set_linea_de_punto(self, linea_de_punto):
        self.linea_de_punto = linea_de_punto
        self.set_curva_comp([self.pedido[k] for k in self.linea_de_punto])
        self.set_curva_actual([(self.pedido[k] if (k == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_et_portadora('%.0f MHz' % (self.freq / 1e6))
        self.set_et_espurias('fuga en %.0f MHz, imagen en %.0f MHz' % (self.freq / 1e6, (self.freq - self.f_tono) / 1e6))
        self.osmosdr_sink_0.set_center_freq(self.freq, 0)

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
        self.set_amp_tx(self.amp_tabla[self.indice] if self.emite == 1 else 0)
        self.set_curva_actual([(self.pedido[k] if (k == self.indice and self.emite == 1) else -2) for k in self.linea_de_punto])

    def get_cargadas(self):
        return self.cargadas

    def set_cargadas(self, cargadas):
        self.cargadas = cargadas
        self.set_et_cargadas('%d de %d' % (self.cargadas, self.n_lineas))

    def get_ancho_banda(self):
        return self.ancho_banda

    def set_ancho_banda(self, ancho_banda):
        self.ancho_banda = ancho_banda
        self.set_et_tasa('%.0f MSPS, filtro de %.1f MHz' % (self.samp_rate / 1e6, self.ancho_banda / 1e6))
        self.osmosdr_sink_0.set_bandwidth(self.ancho_banda, 0)

    def get_amp_tabla(self):
        return self.amp_tabla

    def set_amp_tabla(self, amp_tabla):
        self.amp_tabla = amp_tabla
        self.set_amp_tx(self.amp_tabla[self.indice] if self.emite == 1 else 0)
        self.set_et_comp('%.3f (%+.1f dB sobre la base)' % (self.amp_tabla[self.indice_freq], self.pedido[self.indice_freq]))

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.osmosdr_sink_0.set_gain(self.tx_gain, 0)

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

    def get_et_tasa(self):
        return self.et_tasa

    def set_et_tasa(self, et_tasa):
        self.et_tasa = et_tasa
        Qt.QMetaObject.invokeMethod(self._et_tasa_label, "setText", Qt.Q_ARG("QString", str(self._et_tasa_formatter(self.et_tasa))))

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

    def get_et_linea(self):
        return self.et_linea

    def set_et_linea(self, et_linea):
        self.et_linea = et_linea
        Qt.QMetaObject.invokeMethod(self._et_linea_label, "setText", Qt.Q_ARG("QString", str(self._et_linea_formatter(self.et_linea))))

    def get_et_etapa(self):
        return self.et_etapa

    def set_et_etapa(self, et_etapa):
        self.et_etapa = et_etapa
        Qt.QMetaObject.invokeMethod(self._et_etapa_label, "setText", Qt.Q_ARG("QString", str(self._et_etapa_formatter(self.et_etapa))))

    def get_et_espurias(self):
        return self.et_espurias

    def set_et_espurias(self, et_espurias):
        self.et_espurias = et_espurias
        Qt.QMetaObject.invokeMethod(self._et_espurias_label, "setText", Qt.Q_ARG("QString", str(self._et_espurias_formatter(self.et_espurias))))

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

    def get_amp_tx(self):
        return self.amp_tx

    def set_amp_tx(self, amp_tx):
        self.amp_tx = amp_tx
        self.tono.set_amplitude(self.amp_tx)




def main(top_block_cls=exp25_a9_peine_con_silencio_desde60, options=None):

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
