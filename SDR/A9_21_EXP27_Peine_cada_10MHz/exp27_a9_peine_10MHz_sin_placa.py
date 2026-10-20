#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: EXP-27 SIN PLACA: simulacion del peine cada 10 MHz (no transmite nada)
# Description: SIMULACION, sin la SDR: el tono va a un Null Sink. bladeRF 2.0 micro xA9: 96 lineas cada 10 MHz de 50 a 1000 MHz, un tono por portadora, con la portadora 6,25 o 10 MHz por encima de la linea y 40 MSPS. Calibracion conducida con la tinySA hacia un objetivo por linea, calibracion irradiada desde las trazas del receptor hacia la mascara de CISPR 11 y perfil de referencia. Usa sus propios archivos, con el prefijo simulacion_
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
import math
import sip
import threading
import time


def snipfcn_archivos_de_calibracion(self):
    # ============================================================================
    # ARCHIVOS DE CALIBRACION Y DE OBJETIVO
    # Es el unico codigo Python del flujo. Hace falta porque los bloques no saben
    # leer ni escribir archivos.
    #   1. "Calibracion conducida": pide la captura (.csv) de la tinySA con el
    #      peine tal como esta saliendo, busca el pico de cada linea y calcula
    #      cuanto entrega la placa en cada una. Sirve sin calibrar o ya
    #      calibrado: se puede repetir para afinar.
    #   "Guardar calibracion" e "Importar calibracion": escriben y leen esos 96
    #      valores en un archivo de texto.
    #   "Importar objetivo": lee un archivo con el nivel por cable que tiene que
    #      tener cada linea (el objetivo inicial o un perfil de referencia).
    #   2. "Calibracion irradiada": pide las trazas (.DAT) del receptor, toma en
    #      cada linea el mayor nivel de todas y corrige el objetivo con lo que le
    #      falta o le sobra para llegar al limite de la mascara.
    #   3. "Guardar perfil de referencia": pide una captura (.csv) del peine ya
    #      calibrado y guarda el nivel de cada linea como un archivo de objetivo.
    # ============================================================================
    import math
    import os
    import time

    PRIMERA_LINEA = 50        # MHz
    SEPARACION = 10           # MHz entre una linea y la siguiente
    CANTIDAD = 96             # lineas, de 50 a 1000 MHz
    CERCA_TINYSA = 3          # MHz: hasta que distancia de una linea se busca su pico en la tinySA
    CERCA_RECEPTOR = 1        # MHz: lo mismo en las trazas del receptor
    MAXIMA_CORRECCION = 10    # dB: una correccion mas grande que esto no se aplica


    def frecuencia_de_linea(k):
        return PRIMERA_LINEA + SEPARACION * k


    def limite_de_la_mascara(frecuencia):
        # CISPR 11:2024 a 3 m en camara semianecoica, cuasi-pico, en dBuV/m.
        # En 230 MHz justo vale el limite mas bajo.
        if self.get_mascara() == 0:              # grupo 1 clase A
            if frecuencia <= 230:
                return 50.0
            return 57.0
        else:                                     # grupo 1 clase B
            if frecuencia <= 230:
                return 40.0
            return 47.0


    # ---------------------------------------------------------------- lectura de archivos

    def leer_captura(nombre):
        # Lee una captura de la tinySA (.csv) o una traza del receptor (.DAT): un
        # renglon por punto, con la frecuencia y el nivel separados por coma o por
        # punto y coma. Devuelve dos listas: MHz y nivel (dBm o dBuV/m).
        # errors='ignore' saltea letras raras, como la u de dBuV/m del receptor.
        frecuencias = []
        niveles = []
        archivo = open(nombre, errors='ignore')
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


    def leer_varias(nombres):
        # Lee varias capturas. Devuelve la lista de capturas, o None si alguna falla
        capturas = []
        for nombre in nombres:
            try:
                frecuencias, niveles = leer_captura(nombre)
            except Exception:
                frecuencias = []
            if len(frecuencias) == 0:
                return None
            capturas.append([frecuencias, niveles])
        return capturas


    def pico_de_la_linea(frecuencias, niveles, linea, cerca):
        # Devuelve el nivel mas alto que hay en la captura a menos de 'cerca' MHz de
        # la linea. Si la captura no llega hasta esa frecuencia, devuelve None.
        if linea < min(frecuencias) or linea > max(frecuencias):
            return None
        pico = None
        for j in range(len(frecuencias)):
            if abs(frecuencias[j] - linea) <= cerca:
                if pico is None or niveles[j] > pico:
                    pico = niveles[j]
        return pico


    def leer_archivo_de_valores(nombre):
        # Lee un archivo con un renglon por linea: frecuencia y valor. Los renglones
        # que empiezan con # son comentarios. Devuelve los 96 valores.
        archivo = open(nombre)
        valores = []
        for renglon in archivo:
            if renglon.startswith('#') or renglon.strip() == '':
                continue
            partes = renglon.split()
            valores.append(float(partes[1]))
        archivo.close()
        if len(valores) != CANTIDAD:
            raise ValueError('el archivo no tiene 96 valores')
        return valores


    def portadora_del_encabezado(nombre):
        # Busca en el primer renglon del archivo la palabra 'portadora' y devuelve
        # el numero que le sigue (MHz entre la linea y la portadora). Si no esta,
        # devuelve 0: no se sabe con cual separacion se hizo.
        archivo = open(nombre)
        primero = archivo.readline()
        archivo.close()
        partes = primero.replace(',', ' ').split()
        for i in range(len(partes) - 1):
            if partes[i] == 'portadora':
                try:
                    return float(partes[i + 1])
                except Exception:
                    return 0.0
        return 0.0


    def escribir_archivo_de_valores(nombre, encabezado, valores):
        archivo = open(nombre, 'w')
        archivo.write('# ' + encabezado + '\n')
        for k in range(CANTIDAD):
            archivo.write('%d %.1f\n' % (frecuencia_de_linea(k), valores[k]))
        archivo.close()


    # ---------------------------------------------------------------- calibracion conducida

    def guardar_calibracion():
        try:
            # Se anota con que separacion de la portadora se hizo: la respuesta de la
            # placa cambia un poco de una a otra
            escribir_archivo_de_valores(self.get_archivo_cal(),
                                        'guardada el ' + time.strftime('%d-%m-%Y %H:%M') +
                                        ', valores leidos con ganancia %d dB' % self.get_ganancia_de_lectura() +
                                        ', portadora %g MHz sobre la linea' % self.get_separacion_cal(),
                                        self.get_medidos())
        except Exception:
            self.set_estado_cal('NO se pudo guardar')
            return False
        self.set_estado_cal('guardada a las ' + time.strftime('%H:%M:%S'))
        return True


    def importar_calibracion():
        if not os.path.exists(self.get_archivo_cal()):
            self.set_estado_cal('no hay ninguna calibracion guardada')
            return
        try:
            valores = leer_archivo_de_valores(self.get_archivo_cal())
        except Exception:
            self.set_estado_cal('el archivo no se pudo leer: no se importo nada')
            return
        self.set_medidos(valores)                    # al cambiar medidos, el flujo se actualiza solo
        self.set_separacion_cal(portadora_del_encabezado(self.get_archivo_cal()))
        self.set_estado_cal('importada a las ' + time.strftime('%H:%M:%S'))


    def generar_conducida():
        # La captura tiene que ser del peine tal como esta saliendo ahora: sin
        # calibrar (la primera vez) o con la calibracion que esta cargada. El
        # programa sabe con que amplitud y que ganancia salio cada linea, y con eso
        # saca cuanto entrega la placa. No cambiar la ganancia ni el objetivo entre
        # la captura y el boton.
        elegido = Qt.QFileDialog.getOpenFileNames(self, 'Elegir la captura de la tinySA con el peine tal como esta saliendo',
                                                  '', 'Capturas de la tinySA (*.csv)')
        nombres = elegido[0]
        if len(nombres) == 0:
            return                                   # se cerro la ventana sin elegir nada
        capturas = leer_varias(nombres)
        if capturas is None:
            self.set_estado_cal('NO se genero: no se pudo leer alguna de las capturas')
            return

        ganancia = self.get_ganancia()               # ganancia de TX elegida en la ventana
        amplitudes = self.get_amp_tabla()            # con que amplitud salio cada linea
        anteriores = self.get_medidos()              # lo que habia cargado (0 = sin dato)
        estimados = self.get_nivel_estimado()        # lo que se esperaba leer en cada linea
        valores = []                                 # un valor por linea, o None si no hay dato
        for k in range(CANTIDAD):
            if anteriores[k] != 0:
                esperado = estimados[k]
            else:
                esperado = self.get_nivel_sin_calibrar()
            leidos = []
            for captura in capturas:
                pico = pico_de_la_linea(captura[0], captura[1], frecuencia_de_linea(k), CERCA_TINYSA)
                if pico is not None:
                    leidos.append(pico)
            if len(leidos) == 0:
                valores.append(None)                 # ninguna captura llega hasta esta linea
                continue
            # Con varias capturas se usa el valor mas bajo: MAX HOLD a veces retiene
            # un pico momentaneo, y es raro que caiga dos veces en la misma linea
            valor = min(leidos)
            # Control: si el valor esta lejos de lo esperado, la captura no sirve
            if valor > esperado + 6 or valor < esperado - 10:
                self.set_estado_cal('NO se genero: en %d MHz se leyo %.1f dBm y se esperaba cerca de %.1f dBm'
                                    % (frecuencia_de_linea(k), valor, esperado))
                return
            # Lo que entrega la placa con la amplitud base y la ganancia de lectura
            # (45 dB): a lo leido se le descuenta cuanto se subio la amplitud de esa
            # linea y cuanto de mas tiene la ganancia usada
            subida = 20 * math.log10(amplitudes[k] / self.get_amp_base())
            de_mas = ganancia - self.get_ganancia_de_lectura()
            valores.append(round(valor - subida - de_mas, 1))

        # Las lineas que la captura no alcanza se quedan con lo que tenian
        nuevos = list(anteriores)
        cuantas = 0
        for k in range(CANTIDAD):
            if valores[k] is not None:
                nuevos[k] = valores[k]
                cuantas = cuantas + 1
        if cuantas == 0:
            self.set_estado_cal('NO se genero: la captura no llega a ninguna linea del peine')
            return
        self.set_medidos(nuevos)
        self.set_separacion_cal(self.get_separacion())   # la calibracion vale para la separacion actual
        if guardar_calibracion():
            self.set_estado_cal('generada a las %s con %d captura(s): %d lineas, leidas con ganancia %d dB'
                                % (time.strftime('%H:%M:%S'), len(capturas), cuantas, ganancia))


    # ---------------------------------------------------------------- objetivo

    def cargar_objetivo(nombre):
        valores = leer_archivo_de_valores(nombre)
        self.set_objetivo(valores)
        return valores


    def importar_objetivo():
        elegido = Qt.QFileDialog.getOpenFileName(self, 'Elegir el archivo de objetivo o un perfil de referencia',
                                                 '', 'Objetivos y perfiles (*.txt)')
        nombre = elegido[0]
        if nombre == '':
            return
        try:
            valores = cargar_objetivo(nombre)
        except Exception:
            self.set_estado_obj('NO se importo: el archivo no tiene 96 lineas con su valor')
            return
        # Un perfil de referencia se hizo con una separacion de la portadora: se
        # avisa si la ventana tiene la otra, porque los armonicos irradiados cambian
        portadora = portadora_del_encabezado(nombre)
        aviso = ''
        if portadora != 0 and portadora != self.get_separacion():
            aviso = ' (OJO: es de la portadora a %g MHz y la ventana tiene %g MHz)' % (portadora, self.get_separacion())
        # Se copia como objetivo actual, para que quede al volver a abrir el programa
        if os.path.abspath(nombre) != os.path.abspath(self.get_archivo_obj()):
            encabezado = 'copiado de ' + os.path.basename(nombre) + ' el ' + time.strftime('%d-%m-%Y %H:%M')
            if portadora != 0:
                encabezado = encabezado + ', portadora %g MHz sobre la linea' % portadora
            escribir_archivo_de_valores(self.get_archivo_obj(), encabezado, valores)
        self.set_estado_obj('importado de ' + os.path.basename(nombre) + ' a las ' + time.strftime('%H:%M:%S') + aviso)


    def calibracion_irradiada():
        # Las trazas tienen que ser del peine saliendo con el objetivo actual: todas
        # las lineas calibradas por cable y ninguna sin margen
        if self.get_cargadas() < CANTIDAD or self.get_sin_margen() > 0:
            self.set_estado_obj('NO se corrigio: hace falta la calibracion conducida de las 96 lineas '
                                'y que ninguna se quede sin margen (subir la ganancia)')
            return
        # y la calibracion conducida tiene que ser de la misma separacion que la ventana
        if self.get_separacion_cal() != 0 and self.get_separacion_cal() != self.get_separacion():
            self.set_estado_obj('NO se corrigio: la calibracion conducida es de la portadora a %g MHz '
                                'y la ventana tiene %g MHz' % (self.get_separacion_cal(), self.get_separacion()))
            return
        elegido = Qt.QFileDialog.getOpenFileNames(self, 'Elegir las trazas del receptor (una por altura)',
                                                  '', 'Trazas del receptor (*.DAT *.dat)')
        nombres = elegido[0]
        if len(nombres) == 0:
            return
        trazas = leer_varias(nombres)
        if trazas is None:
            self.set_estado_obj('NO se corrigio: no se pudo leer alguna de las trazas')
            return

        objetivo = list(self.get_objetivo())
        correcciones = []
        sin_corregir = 0
        medido = []                                  # para el grafico: 0 si no hay dato
        for k in range(CANTIDAD):
            frecuencia = frecuencia_de_linea(k)
            # el mayor nivel de la linea entre todas las trazas (las tres alturas)
            mayor = None
            for traza in trazas:
                pico = pico_de_la_linea(traza[0], traza[1], frecuencia, CERCA_RECEPTOR)
                if pico is not None and (mayor is None or pico > mayor):
                    mayor = pico
            if mayor is None:
                medido.append(0.0)
                sin_corregir = sin_corregir + 1      # las trazas no llegan a esta linea
                continue
            medido.append(round(mayor, 1))
            diferencia = limite_de_la_mascara(frecuencia) - mayor
            if abs(diferencia) > MAXIMA_CORRECCION:
                sin_corregir = sin_corregir + 1      # demasiado lejos: algo no anduvo
                continue
            objetivo[k] = round(objetivo[k] + diferencia, 1)
            correcciones.append(diferencia)

        # Lo medido queda en el grafico y en un archivo, aunque no se corrija nada
        self.set_medido_irradiado(medido)
        texto = time.strftime('%d-%m-%Y %H:%M') + ', %d traza(s)' % len(nombres)
        encabezado = texto + ': '
        for nombre in nombres:
            encabezado = encabezado + os.path.basename(nombre) + ' '
        escribir_archivo_de_valores(self.get_archivo_irr(), encabezado, medido)
        self.set_estado_irr(texto)

        if len(correcciones) == 0:
            self.set_estado_obj('NO se corrigio: ninguna linea quedo a menos de %d dB del limite' % MAXIMA_CORRECCION)
            return
        # Antes de pisar el objetivo se guarda una copia del anterior
        if os.path.exists(self.get_archivo_obj()):
            escribir_archivo_de_valores(self.get_prefijo() + 'objetivo_anterior.txt', 'objetivo antes de la correccion del ' +
                                        time.strftime('%d-%m-%Y %H:%M'), self.get_objetivo())
        self.set_objetivo(objetivo)
        escribir_archivo_de_valores(self.get_archivo_obj(),
                                    'corregido el ' + time.strftime('%d-%m-%Y %H:%M') + ' con %d traza(s) del receptor'
                                    % len(trazas), objetivo)
        self.set_estado_obj('corregido a las %s: %d lineas, de %+.1f a %+.1f dB, %d sin corregir'
                            % (time.strftime('%H:%M:%S'), len(correcciones), min(correcciones), max(correcciones),
                               sin_corregir))


    def guardar_referencia():
        elegido = Qt.QFileDialog.getOpenFileNames(self, 'Elegir la captura de la tinySA con el peine YA calibrado',
                                                  '', 'Capturas de la tinySA (*.csv)')
        nombres = elegido[0]
        if len(nombres) == 0:
            return
        capturas = leer_varias(nombres)
        if capturas is None:
            self.set_estado_obj('NO se guardo: no se pudo leer alguna de las capturas')
            return
        valores = []
        for k in range(CANTIDAD):
            leidos = []
            for captura in capturas:
                pico = pico_de_la_linea(captura[0], captura[1], frecuencia_de_linea(k), CERCA_TINYSA)
                if pico is not None:
                    leidos.append(pico)
            if len(leidos) == 0:
                self.set_estado_obj('NO se guardo: las capturas no llegan a %d MHz' % frecuencia_de_linea(k))
                return
            valores.append(min(leidos))              # como en la calibracion conducida
        nombre = self.get_prefijo() + 'perfil_referencia_' + time.strftime('%Y-%m-%d_%H%M') + '.txt'
        escribir_archivo_de_valores(nombre, 'perfil de referencia medido por cable el ' +
                                    time.strftime('%d-%m-%Y %H:%M') + ' con ganancia %d dB' % self.get_ganancia() +
                                    ', portadora %g MHz sobre la linea' % self.get_separacion(),
                                    valores)
        diferencias = []
        objetivo = self.get_objetivo()
        for k in range(CANTIDAD):
            diferencias.append(valores[k] - objetivo[k])
        self.set_estado_obj('perfil guardado en %s. Medido menos objetivo: de %+.1f a %+.1f dB'
                            % (nombre, min(diferencias), max(diferencias)))


    # Al abrir el programa se carga el objetivo guardado. Si todavia no hay uno, se
    # carga el objetivo inicial que viene con el experimento
    if os.path.exists(self.get_archivo_obj()):
        al_abrir = self.get_archivo_obj()
    else:
        al_abrir = 'objetivo_inicial_clase_A.txt'
    if os.path.exists(al_abrir):
        try:
            cargar_objetivo(al_abrir)
            self.set_estado_obj('cargado al abrir (' + al_abrir + ')')
        except Exception:
            self.set_estado_obj('el archivo de objetivo no se pudo leer: todas las lineas en -35 dBm')

    # Tambien se carga lo medido en la ultima calibracion irradiada, para el grafico
    if os.path.exists(self.get_archivo_irr()):
        try:
            self.set_medido_irradiado(leer_archivo_de_valores(self.get_archivo_irr()))
            archivo = open(self.get_archivo_irr())
            self.set_estado_irr(archivo.readline()[2:].split(':')[0])   # fecha y cantidad de trazas
            archivo.close()
        except Exception:
            self.set_estado_irr('el archivo de la ultima irradiada no se pudo leer')

    # Solo en la simulacion: se carga sola la calibracion conducida simulada, para
    # que se vean todas las curvas sin apretar nada. Con la placa no se carga sola.
    if self.get_prefijo() == 'simulacion_' and os.path.exists(self.get_archivo_cal()):
        importar_calibracion()

    # Colores pastel en los graficos. En GRC el bloque solo ofrece colores
    # fuertes, pero desde aca acepta cualquiera. Las curvas se cuentan desde 0.
    self.grafico.set_line_color(0, '#6fa8dc')             # objetivo: azul
    self.grafico.set_line_color(1, '#93c47d')             # lo que sale: verde
    self.grafico.set_line_color(2, '#e06666')             # linea actual: rojo
    self.grafico.set_line_color(3, '#b4a7d6')             # respuesta de la placa: violeta
    self.grafico_irradiado.set_line_color(0, '#e06666')   # mascara: rojo
    self.grafico_irradiado.set_line_color(1, '#6fa8dc')   # medido: azul

    # Alto de la ventana: las filas de texto (0 a 9) quedan con lo justo y todo lo
    # que sobra va a los graficos (filas 10 a 13), que nunca bajan de 205 px. Asi
    # la ventana entra en una pantalla de 1080p con la escala en 125 %, y en una
    # pantalla mas alta los graficos crecen solos.
    self._grafico_win.setMinimumHeight(205)
    self._grafico_irradiado_win.setMinimumHeight(205)
    for fila in range(10):
        self.top_grid_layout.setRowStretch(fila, 0)
    for fila in range(10, 14):
        self.top_grid_layout.setRowStretch(fila, 1)
    self.top_grid_layout.setVerticalSpacing(2)
    self.top_grid_layout.setContentsMargins(6, 4, 6, 4)

    # Letra y botones de la ventana
    self.setStyleSheet('QWidget { font-size: 10pt; } QPushButton { font-size: 11pt; min-height: 30px; }')

    # Colores para ubicarse rapido: PAUSA en rojo, CONGELAR en azul, y los botones
    # de los tres pasos del procedimiento con un fondo de color cada uno
    for casilla in self.findChildren(Qt.QCheckBox):
        if casilla.text().startswith('PAUSA'):
            casilla.setStyleSheet('color: #c0392b; font-weight: bold;')
        if casilla.text().startswith('CONGELAR'):
            casilla.setStyleSheet('color: #2e86c1; font-weight: bold;')
    for boton in self.findChildren(Qt.QPushButton):
        if boton.text().startswith('1.'):
            boton.setStyleSheet('background-color: #d6e6f5;')     # azul pastel
        if boton.text().startswith('2.'):
            boton.setStyleSheet('background-color: #d9ead3;')     # verde pastel
        if boton.text().startswith('3.'):
            boton.setStyleSheet('background-color: #fff2cc;')     # amarillo pastel


    # ---------------------------------------------------------------- botones
    # GNU Radio llama a set_boton_...(1) cuando se aprieta un boton y a
    # set_boton_...(0) cuando se suelta. Aca se define que hace esa llamada.
    # Los que abren una ventana para elegir archivos actuan al soltar el boton:
    # si actuaran al apretarlo, el boton quedaria hundido mientras la ventana
    # esta abierta.
    def al_tocar_guardar_cal(valor):
        if valor == 1:
            guardar_calibracion()


    def al_tocar_importar_cal(valor):
        if valor == 1:
            importar_calibracion()


    def al_tocar_conducida(valor):
        if valor == 0:
            generar_conducida()


    def al_tocar_importar_obj(valor):
        if valor == 0:
            importar_objetivo()


    def al_tocar_irradiada(valor):
        if valor == 0:
            calibracion_irradiada()


    def al_tocar_referencia(valor):
        if valor == 0:
            guardar_referencia()


    self.set_boton_guardar_cal = al_tocar_guardar_cal
    self.set_boton_importar_cal = al_tocar_importar_cal
    self.set_boton_conducida = al_tocar_conducida
    self.set_boton_importar_obj = al_tocar_importar_obj
    self.set_boton_irradiada = al_tocar_irradiada
    self.set_boton_referencia = al_tocar_referencia


    # ============================================================================
    # NO RESINTONIZAR DE MAS
    # El paso del barrido cambia 10 veces por segundo y GNU Radio vuelve a mandar la
    # frecuencia a la placa en cada cambio, aunque sea la misma. La placa
    # resintoniza igual, y eso con el tono encendido lo perturba. Aca se hace que
    # la frecuencia se mande solo cuando cambia.
    # ============================================================================
    mandar_frecuencia = self.set_freq


    def mandar_frecuencia_si_cambia(frecuencia):
        if frecuencia != self.get_freq():
            mandar_frecuencia(frecuencia)


    self.set_freq = mandar_frecuencia_si_cambia


    # ============================================================================
    # CONGELAR EL BARRIDO
    # Mientras la casilla CONGELAR esta tildada, el paso del barrido no avanza: la
    # placa se queda en la linea que estaba saliendo. (El flujo, por su lado, deja
    # el tono encendido mientras este congelado.)
    # ============================================================================
    avanzar_paso = self.set_paso


    def avanzar_paso_si_no_esta_congelado(valor):
        if self.get_congelar() == 0:
            avanzar_paso(valor)
        else:
            # se devuelve el numero a la lista: al destildar, el barrido sigue donde estaba
            self.get_lista_de_pasos().append(valor)


    self.set_paso = avanzar_paso_si_no_esta_congelado


def snippets_main_after_init(tb):
    snipfcn_archivos_de_calibracion(tb)

class exp27_a9_peine_10MHz_sin_placa(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "EXP-27 SIN PLACA: simulacion del peine cada 10 MHz (no transmite nada)", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("EXP-27 SIN PLACA: simulacion del peine cada 10 MHz (no transmite nada)")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp27_a9_peine_10MHz_sin_placa")

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
        self.silencio = silencio = 0
        self.permanencia = permanencia = 7
        self.corte = corte = 0.5
        self.paso = paso = -1
        self.encendido = encendido = int(round(10 * permanencia))
        self.apagado = apagado = int(round(10 * (corte + (permanencia if silencio == 1 else 0))))
        self.por_linea = por_linea = encendido + apagado
        self.decima = decima = max(paso, 0)
        self.n_lineas = n_lineas = 96
        self.ciclo = ciclo = decima // por_linea
        self.posicion = posicion = ciclo % n_lineas
        self.objetivo = objetivo = [-35.0] * n_lineas
        self.medidos = medidos = [0.0] * n_lineas
        self.ganancia_de_lectura = ganancia_de_lectura = 45
        self.ganancia = ganancia = 31
        self.fijo = fijo = (-1)
        self.separacion = separacion = 6.25
        self.prefijo = prefijo = 'simulacion_'
        self.pedido = pedido = [((objetivo[k] - (medidos[k] + ganancia - ganancia_de_lectura)) if medidos[k] != 0 else 0.0) for k in range(n_lineas)]
        self.paso_lineas = paso_lineas = 10e6
        self.indice = indice = fijo if fijo >= 0 else posicion
        self.f_primera = f_primera = 50e6
        self.dentro = dentro = decima % por_linea
        self.antes = antes = apagado // 2
        self.amp_max = amp_max = 0.95
        self.amp_base = amp_base = 0.25
        self.pausa = pausa = 1
        self.linea = linea = f_primera + paso_lineas * indice
        self.f_tono = f_tono = -separacion * 1e6
        self.en_corte = en_corte = 0 if antes <= dentro < antes + encendido else 1
        self.congelar = congelar = 0
        self.cargadas = cargadas = sum(1 for leido in medidos if leido != 0)
        self.archivo_cal = archivo_cal = prefijo + 'calibracion_conducida.txt'
        self.amp_tabla = amp_tabla = [min(amp_base * 10 ** (db / 20.0), amp_max) for db in pedido]
        self.texto_salida = texto_salida = 'SIN PLACA (simulacion)'
        self.sin_margen = sin_margen = sum(1 for db in pedido if amp_base * 10 ** (db / 20.0) > amp_max)
        self.separacion_cal = separacion_cal = 0.0
        self.samp_rate = samp_rate = 40e6
        self.pasada = pasada = ciclo // n_lineas + 1
        self.nivel_estimado = nivel_estimado = [((medidos[k] + ganancia - ganancia_de_lectura) + 20 * math.log10(amp_tabla[k] / amp_base)) if medidos[k] != 0 else -100 for k in range(n_lineas)]
        self.medido_irradiado = medido_irradiado = [0.0] * n_lineas
        self.mascara = mascara = 0
        self.ganancia_minima = ganancia_minima = int(math.ceil(ganancia_de_lectura + max([objetivo[k] - medidos[k] for k in range(n_lineas) if medidos[k] != 0]) - 20 * math.log10(amp_max / amp_base))) if cargadas > 0 else 0
        self.freq = freq = linea - f_tono
        self.etapa = etapa = 'PAUSA (sin emitir)' if pausa == 1 else ('INICIACION' if paso < 0 else ('LINEA FIJA, emision continua' if fijo >= 0 else ('LINEA CONGELADA, emision continua' if congelar == 1 else ('CORTE (salto de linea)' if en_corte == 1 else 'EMITIENDO'))))
        self.estado_obj = estado_obj = 'no hay objetivo guardado: todas las lineas en -35 dBm'
        self.estado_irr = estado_irr = 'todavia no hay ninguna'
        self.estado_cal = estado_cal = 'hay una guardada, sin importar' if os.path.exists(archivo_cal) else 'todavia no hay ninguna guardada'
        self.emite = emite = 1 if (pausa == 0 and paso >= 0 and (fijo >= 0 or congelar == 1 or en_corte == 0)) else 0
        self.tx_gain = tx_gain = ganancia if pausa == 0 else 0
        self.nivel_sin_calibrar = nivel_sin_calibrar = ganancia - 68
        self.nivel_respuesta = nivel_respuesta = [(medidos[k] + ganancia - ganancia_de_lectura) if medidos[k] != 0 else -100 for k in range(n_lineas)]
        self.muestras_por_bloque = muestras_por_bloque = 16384
        self.lista_de_pasos = lista_de_pasos = list(range(1000000 - 1, -1, -1))
        self.limite_lineas = limite_lineas = [((50.0 if f_primera / 1e6 + 10 * k <= 230 else 57.0) if mascara == 0 else (40.0 if f_primera / 1e6 + 10 * k <= 230 else 47.0)) for k in range(n_lineas)]
        self.et_tiempos = et_tiempos = '%d min %02d s (%.1f s encendida y %.1f s apagada por linea)' % (n_lineas * por_linea // 600, (n_lineas * por_linea // 10) % 60, encendido / 10.0, apagado / 10.0)
        self.et_salida = et_salida = texto_salida + ', %.0f MSPS' % (samp_rate / 1e6)
        self.et_portadora = et_portadora = '%.2f MHz' % (freq / 1e6)
        self.et_obj = et_obj = estado_obj
        self.et_nivel = et_nivel = 'amplitud %.3f, sale unos %.1f dBm (objetivo %.1f dBm)' % (amp_tabla[indice], nivel_estimado[indice], objetivo[indice])
        self.et_margen = et_margen = sin_margen
        self.et_linea = et_linea = ('%.0f MHz (fija)' % (linea / 1e6)) if fijo >= 0 else '%.0f MHz (paso %d de %d, pasada %d)' % (linea / 1e6, posicion + 1, n_lineas, pasada)
        self.et_irr = et_irr = estado_irr
        self.et_gmin = et_gmin = ('%d dB' % ganancia_minima) if cargadas > 0 else 'sin calibracion conducida'
        self.et_etapa = et_etapa = etapa
        self.et_espurias = et_espurias = 'fuga %.2f, imagen %.2f, 3C+S %.2f, 5C-S %.2f' % (freq / 1e6, freq / 1e6 + separacion, 3 * freq / 1e6 + separacion, 5 * freq / 1e6 - separacion)
        self.et_cargadas = et_cargadas = ('%d/%d' % (cargadas, n_lineas)) + ((', es de %g MHz: NO coincide' % separacion_cal) if (cargadas > 0 and separacion_cal != 0 and separacion_cal != separacion) else ((', de %g MHz' % separacion_cal) if separacion_cal != 0 else ''))
        self.et_cal = et_cal = estado_cal
        self.curva_irradiada = curva_irradiada = [(v if v != 0 else -100) for v in medido_irradiado]
        self.curva_actual = curva_actual = [(objetivo[k] if (k == indice and emite == 1) else -100) for k in range(n_lineas)]
        self.boton_referencia = boton_referencia = 0
        self.boton_irradiada = boton_irradiada = 0
        self.boton_importar_obj = boton_importar_obj = 0
        self.boton_importar_cal = boton_importar_cal = 0
        self.boton_guardar_cal = boton_guardar_cal = 0
        self.boton_conducida = boton_conducida = 0
        self.bloques_usb = bloques_usb = 128
        self.archivo_obj = archivo_obj = prefijo + 'objetivo.txt'
        self.archivo_irr = archivo_irr = prefijo + 'ultima_irradiada.txt'
        self.ancho_banda = ancho_banda = 0.9 * samp_rate
        self.amp_tx = amp_tx = amp_tabla[indice] if emite == 1 else 0

        ##################################################
        # Blocks
        ##################################################

        self.tono = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, f_tono, amp_tx, 0, 0)
        _silencio_check_box = Qt.QCheckBox("Silencio largo: cada linea queda apagada otro tanto")
        self._silencio_choices = {True: 1, False: 0}
        self._silencio_choices_inv = dict((v,k) for k,v in self._silencio_choices.items())
        self._silencio_callback = lambda i: Qt.QMetaObject.invokeMethod(_silencio_check_box, "setChecked", Qt.Q_ARG("bool", self._silencio_choices_inv[i]))
        self._silencio_callback(self.silencio)
        _silencio_check_box.stateChanged.connect(lambda i: self.set_silencio(self._silencio_choices[bool(i)]))
        self.top_grid_layout.addWidget(_silencio_check_box, 1, 8, 1, 4)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._separacion_options = [6.25, 10]
        # Create the labels list
        self._separacion_labels = ['6,25 MHz', '10 MHz']
        # Create the combo box
        self._separacion_tool_bar = Qt.QToolBar(self)
        self._separacion_tool_bar.addWidget(Qt.QLabel("Portadora sobre la linea" + ": "))
        self._separacion_combo_box = Qt.QComboBox()
        self._separacion_tool_bar.addWidget(self._separacion_combo_box)
        for _label in self._separacion_labels: self._separacion_combo_box.addItem(_label)
        self._separacion_callback = lambda i: Qt.QMetaObject.invokeMethod(self._separacion_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._separacion_options.index(i)))
        self._separacion_callback(self.separacion)
        self._separacion_combo_box.currentIndexChanged.connect(
            lambda i: self.set_separacion(self._separacion_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._separacion_tool_bar, 2, 3, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.salida_nula = blocks.null_sink(gr.sizeof_gr_complex*1)
        self.ritmo_simulacion = blocks.throttle( gr.sizeof_gr_complex*1, 1e6, True, 0 if "auto" == "auto" else max( int(float(0.1) * 1e6) if "auto" == "time" else int(0.1), 1) )
        self.ritmo_grafico_2 = blocks.throttle( gr.sizeof_float*96, 2000, True, 0 if "time" == "auto" else max( int(float(0.01) * 2000) if "time" == "time" else int(0.01), 1) )
        self.ritmo_grafico = blocks.throttle( gr.sizeof_float*96, 2000, True, 0 if "time" == "auto" else max( int(float(0.01) * 2000) if "time" == "time" else int(0.01), 1) )
        self._permanencia_range = qtgui.Range(1, 30, 0.5, 7, 50)
        self._permanencia_win = qtgui.RangeWidget(self._permanencia_range, self.set_permanencia, "Segundos encendida por linea", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._permanencia_win, 3, 0, 1, 3)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
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

            val = self.lista_de_pasos.pop()
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_paso,val))
              except AttributeError:
                self.set_paso(val)
            except AttributeError:
              pass
            time.sleep(1.0 / (10))
        _paso_thread = threading.Thread(target=_paso_probe)
        _paso_thread.daemon = True
        _paso_thread.start()
        # Create the options list
        self._mascara_options = [0, 1]
        # Create the labels list
        self._mascara_labels = ['G1 clase A (50 y 57)', 'G1 clase B (40 y 47)']
        # Create the combo box
        self._mascara_tool_bar = Qt.QToolBar(self)
        self._mascara_tool_bar.addWidget(Qt.QLabel("Mascara CISPR 11" + ": "))
        self._mascara_combo_box = Qt.QComboBox()
        self._mascara_tool_bar.addWidget(self._mascara_combo_box)
        for _label in self._mascara_labels: self._mascara_combo_box.addItem(_label)
        self._mascara_callback = lambda i: Qt.QMetaObject.invokeMethod(self._mascara_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._mascara_options.index(i)))
        self._mascara_callback(self.mascara)
        self._mascara_combo_box.currentIndexChanged.connect(
            lambda i: self.set_mascara(self._mascara_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._mascara_tool_bar, 2, 9, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(9, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.grafico_irradiado = qtgui.vector_sink_f(
            96,
            (f_primera / 1e6),
            (paso_lineas / 1e6),
            "Frecuencia de la linea",
            "Campo",
            "Campo en la camara, ultima calibracion irradiada (dBuV/m)",
            2, # Number of inputs
            None # parent
        )
        self.grafico_irradiado.set_update_time(0.10)
        self.grafico_irradiado.set_y_axis(20, 80)
        self.grafico_irradiado.enable_autoscale(False)
        self.grafico_irradiado.enable_grid(True)
        self.grafico_irradiado.set_x_axis_units("MHz")
        self.grafico_irradiado.set_y_axis_units("dBuV/m")
        self.grafico_irradiado.set_ref_level(0)


        labels = ["Mascara de CISPR 11", "Medido (mayor de las alturas)", '', '', '',
            '', '', '', '', '']
        widths = [3, 3, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["red", "blue", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(2):
            if len(labels[i]) == 0:
                self.grafico_irradiado.set_line_label(i, "Data {0}".format(i))
            else:
                self.grafico_irradiado.set_line_label(i, labels[i])
            self.grafico_irradiado.set_line_width(i, widths[i])
            self.grafico_irradiado.set_line_color(i, colors[i])
            self.grafico_irradiado.set_line_alpha(i, alphas[i])

        self._grafico_irradiado_win = sip.wrapinstance(self.grafico_irradiado.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._grafico_irradiado_win, 12, 0, 2, 12)
        for r in range(12, 14):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.grafico = qtgui.vector_sink_f(
            96,
            (f_primera / 1e6),
            (paso_lineas / 1e6),
            "Frecuencia de la linea",
            "Nivel",
            "Nivel por cable de cada linea (dBm)",
            4, # Number of inputs
            None # parent
        )
        self.grafico.set_update_time(0.10)
        self.grafico.set_y_axis((-60), (-10))
        self.grafico.enable_autoscale(False)
        self.grafico.enable_grid(True)
        self.grafico.set_x_axis_units("MHz")
        self.grafico.set_y_axis_units("dBm")
        self.grafico.set_ref_level(0)


        labels = ["Objetivo", "Lo que sale (estimado)", "Linea que sale ahora", "Respuesta de la placa, sin compensar", '',
            '', '', '', '', '']
        widths = [3, 2, 4, 2, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "green", "red", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(4):
            if len(labels[i]) == 0:
                self.grafico.set_line_label(i, "Data {0}".format(i))
            else:
                self.grafico.set_line_label(i, labels[i])
            self.grafico.set_line_width(i, widths[i])
            self.grafico.set_line_color(i, colors[i])
            self.grafico.set_line_alpha(i, alphas[i])

        self._grafico_win = sip.wrapinstance(self.grafico.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._grafico_win, 10, 0, 2, 12)
        for r in range(10, 12):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._ganancia_range = qtgui.Range(0, 55, 1, 31, 50)
        self._ganancia_win = qtgui.RangeWidget(self._ganancia_range, self.set_ganancia, "Ganancia de TX (dB)", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._ganancia_win, 2, 0, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._fijo_options = [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95]
        # Create the labels list
        self._fijo_labels = ['Barrido completo', 'Fija en 50 MHz', 'Fija en 60 MHz', 'Fija en 70 MHz', 'Fija en 80 MHz', 'Fija en 90 MHz', 'Fija en 100 MHz', 'Fija en 110 MHz', 'Fija en 120 MHz', 'Fija en 130 MHz', 'Fija en 140 MHz', 'Fija en 150 MHz', 'Fija en 160 MHz', 'Fija en 170 MHz', 'Fija en 180 MHz', 'Fija en 190 MHz', 'Fija en 200 MHz', 'Fija en 210 MHz', 'Fija en 220 MHz', 'Fija en 230 MHz', 'Fija en 240 MHz', 'Fija en 250 MHz', 'Fija en 260 MHz', 'Fija en 270 MHz', 'Fija en 280 MHz', 'Fija en 290 MHz', 'Fija en 300 MHz', 'Fija en 310 MHz', 'Fija en 320 MHz', 'Fija en 330 MHz', 'Fija en 340 MHz', 'Fija en 350 MHz', 'Fija en 360 MHz', 'Fija en 370 MHz', 'Fija en 380 MHz', 'Fija en 390 MHz', 'Fija en 400 MHz', 'Fija en 410 MHz', 'Fija en 420 MHz', 'Fija en 430 MHz', 'Fija en 440 MHz', 'Fija en 450 MHz', 'Fija en 460 MHz', 'Fija en 470 MHz', 'Fija en 480 MHz', 'Fija en 490 MHz', 'Fija en 500 MHz', 'Fija en 510 MHz', 'Fija en 520 MHz', 'Fija en 530 MHz', 'Fija en 540 MHz', 'Fija en 550 MHz', 'Fija en 560 MHz', 'Fija en 570 MHz', 'Fija en 580 MHz', 'Fija en 590 MHz', 'Fija en 600 MHz', 'Fija en 610 MHz', 'Fija en 620 MHz', 'Fija en 630 MHz', 'Fija en 640 MHz', 'Fija en 650 MHz', 'Fija en 660 MHz', 'Fija en 670 MHz', 'Fija en 680 MHz', 'Fija en 690 MHz', 'Fija en 700 MHz', 'Fija en 710 MHz', 'Fija en 720 MHz', 'Fija en 730 MHz', 'Fija en 740 MHz', 'Fija en 750 MHz', 'Fija en 760 MHz', 'Fija en 770 MHz', 'Fija en 780 MHz', 'Fija en 790 MHz', 'Fija en 800 MHz', 'Fija en 810 MHz', 'Fija en 820 MHz', 'Fija en 830 MHz', 'Fija en 840 MHz', 'Fija en 850 MHz', 'Fija en 860 MHz', 'Fija en 870 MHz', 'Fija en 880 MHz', 'Fija en 890 MHz', 'Fija en 900 MHz', 'Fija en 910 MHz', 'Fija en 920 MHz', 'Fija en 930 MHz', 'Fija en 940 MHz', 'Fija en 950 MHz', 'Fija en 960 MHz', 'Fija en 970 MHz', 'Fija en 980 MHz', 'Fija en 990 MHz', 'Fija en 1000 MHz']
        # Create the combo box
        self._fijo_tool_bar = Qt.QToolBar(self)
        self._fijo_tool_bar.addWidget(Qt.QLabel("Modo" + ": "))
        self._fijo_combo_box = Qt.QComboBox()
        self._fijo_tool_bar.addWidget(self._fijo_combo_box)
        for _label in self._fijo_labels: self._fijo_combo_box.addItem(_label)
        self._fijo_callback = lambda i: Qt.QMetaObject.invokeMethod(self._fijo_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._fijo_options.index(i)))
        self._fijo_callback(self.fijo)
        self._fijo_combo_box.currentIndexChanged.connect(
            lambda i: self.set_fijo(self._fijo_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._fijo_tool_bar, 2, 6, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 9):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_tiempos_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>":
            self._et_tiempos_formatter = lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_tiempos_formatter = lambda x: str(x)

        self._et_tiempos_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Pasada completa: </span>"))
        self._et_tiempos_label = Qt.QLabel(str(self._et_tiempos_formatter(self.et_tiempos)))
        self._et_tiempos_tool_bar.addWidget(self._et_tiempos_label)
        self.top_grid_layout.addWidget(self._et_tiempos_tool_bar, 3, 6, 1, 6)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_salida_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('#d68910' if 'SIN PLACA' in str(x) else '#1e8449') + "'><b>" + str(x) + "</b></span>":
            self._et_salida_formatter = lambda x: "<span style='font-size:11pt; color:" + ('#d68910' if 'SIN PLACA' in str(x) else '#1e8449') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_salida_formatter = lambda x: str(x)

        self._et_salida_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Salida: </span>"))
        self._et_salida_label = Qt.QLabel(str(self._et_salida_formatter(self.et_salida)))
        self._et_salida_tool_bar.addWidget(self._et_salida_label)
        self.top_grid_layout.addWidget(self._et_salida_tool_bar, 9, 8, 1, 4)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_portadora_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>":
            self._et_portadora_formatter = lambda x: "<span style='font-size:15pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_portadora_formatter = lambda x: str(x)

        self._et_portadora_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Portadora: </span>"))
        self._et_portadora_label = Qt.QLabel(str(self._et_portadora_formatter(self.et_portadora)))
        self._et_portadora_tool_bar.addWidget(self._et_portadora_label)
        self.top_grid_layout.addWidget(self._et_portadora_tool_bar, 0, 8, 1, 4)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_obj_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('#c0392b' if str(x).startswith('NO') else 'black') + "'><b>" + str(x) + "</b></span>":
            self._et_obj_formatter = lambda x: "<span style='font-size:11pt; color:" + ('#c0392b' if str(x).startswith('NO') else 'black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_obj_formatter = lambda x: str(x)

        self._et_obj_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Objetivo: </span>"))
        self._et_obj_label = Qt.QLabel(str(self._et_obj_formatter(self.et_obj)))
        self._et_obj_tool_bar.addWidget(self._et_obj_label)
        self.top_grid_layout.addWidget(self._et_obj_tool_bar, 9, 0, 1, 8)
        for r in range(9, 10):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_nivel_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>":
            self._et_nivel_formatter = lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_nivel_formatter = lambda x: str(x)

        self._et_nivel_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Esta linea: </span>"))
        self._et_nivel_label = Qt.QLabel(str(self._et_nivel_formatter(self.et_nivel)))
        self._et_nivel_tool_bar.addWidget(self._et_nivel_label)
        self.top_grid_layout.addWidget(self._et_nivel_tool_bar, 4, 0, 1, 6)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_margen_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('#c0392b' if x > 0 else '#1e8449') + "'><b>" + str(x) + "</b></span>":
            self._et_margen_formatter = lambda x: "<span style='font-size:11pt; color:" + ('#c0392b' if x > 0 else '#1e8449') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_margen_formatter = lambda x: str(x)

        self._et_margen_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Lineas sin margen: </span>"))
        self._et_margen_label = Qt.QLabel(str(self._et_margen_formatter(self.et_margen)))
        self._et_margen_tool_bar.addWidget(self._et_margen_label)
        self.top_grid_layout.addWidget(self._et_margen_tool_bar, 5, 4, 1, 4)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_linea_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>":
            self._et_linea_formatter = lambda x: "<span style='font-size:15pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_linea_formatter = lambda x: str(x)

        self._et_linea_tool_bar.addWidget(Qt.QLabel("<span style='font-size:15pt'>Linea: </span>"))
        self._et_linea_label = Qt.QLabel(str(self._et_linea_formatter(self.et_linea)))
        self._et_linea_tool_bar.addWidget(self._et_linea_label)
        self.top_grid_layout.addWidget(self._et_linea_tool_bar, 0, 4, 1, 4)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_irr_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>":
            self._et_irr_formatter = lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_irr_formatter = lambda x: str(x)

        self._et_irr_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Ultima irradiada: </span>"))
        self._et_irr_label = Qt.QLabel(str(self._et_irr_formatter(self.et_irr)))
        self._et_irr_tool_bar.addWidget(self._et_irr_label)
        self.top_grid_layout.addWidget(self._et_irr_tool_bar, 8, 6, 1, 6)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_gmin_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>":
            self._et_gmin_formatter = lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_gmin_formatter = lambda x: str(x)

        self._et_gmin_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Ganancia minima: </span>"))
        self._et_gmin_label = Qt.QLabel(str(self._et_gmin_formatter(self.et_gmin)))
        self._et_gmin_tool_bar.addWidget(self._et_gmin_label)
        self.top_grid_layout.addWidget(self._et_gmin_tool_bar, 5, 8, 1, 4)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_etapa_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:15pt; color:" + ('#c0392b' if 'PAUSA' in str(x) else ('#d68910' if 'CORTE' in str(x) else ('#2e86c1' if 'LINEA' in str(x) else ('#1e8449' if 'EMITIENDO' in str(x) else 'gray')))) + "'><b>" + str(x) + "</b></span>":
            self._et_etapa_formatter = lambda x: "<span style='font-size:15pt; color:" + ('#c0392b' if 'PAUSA' in str(x) else ('#d68910' if 'CORTE' in str(x) else ('#2e86c1' if 'LINEA' in str(x) else ('#1e8449' if 'EMITIENDO' in str(x) else 'gray')))) + "'><b>" + str(x) + "</b></span>"
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

        if lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>":
            self._et_espurias_formatter = lambda x: "<span style='font-size:11pt; color:" + ('black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_espurias_formatter = lambda x: str(x)

        self._et_espurias_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Sus espurias (MHz): </span>"))
        self._et_espurias_label = Qt.QLabel(str(self._et_espurias_formatter(self.et_espurias)))
        self._et_espurias_tool_bar.addWidget(self._et_espurias_label)
        self.top_grid_layout.addWidget(self._et_espurias_tool_bar, 4, 6, 1, 6)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(6, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_cargadas_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('#c0392b' if 'NO coincide' in str(x) else 'black') + "'><b>" + str(x) + "</b></span>":
            self._et_cargadas_formatter = lambda x: "<span style='font-size:11pt; color:" + ('#c0392b' if 'NO coincide' in str(x) else 'black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_cargadas_formatter = lambda x: str(x)

        self._et_cargadas_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Conducida: </span>"))
        self._et_cargadas_label = Qt.QLabel(str(self._et_cargadas_formatter(self.et_cargadas)))
        self._et_cargadas_tool_bar.addWidget(self._et_cargadas_label)
        self.top_grid_layout.addWidget(self._et_cargadas_tool_bar, 5, 0, 1, 4)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._et_cal_tool_bar = Qt.QToolBar(self)

        if lambda x: "<span style='font-size:11pt; color:" + ('#c0392b' if str(x).startswith('NO') else 'black') + "'><b>" + str(x) + "</b></span>":
            self._et_cal_formatter = lambda x: "<span style='font-size:11pt; color:" + ('#c0392b' if str(x).startswith('NO') else 'black') + "'><b>" + str(x) + "</b></span>"
        else:
            self._et_cal_formatter = lambda x: str(x)

        self._et_cal_tool_bar.addWidget(Qt.QLabel("<span style='font-size:11pt'>Calibracion conducida: </span>"))
        self._et_cal_label = Qt.QLabel(str(self._et_cal_formatter(self.et_cal)))
        self._et_cal_tool_bar.addWidget(self._et_cal_label)
        self.top_grid_layout.addWidget(self._et_cal_tool_bar, 8, 0, 1, 6)
        for r in range(8, 9):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.datos_resp = blocks.vector_source_f(nivel_respuesta, True, 96, [])
        self.datos_obj = blocks.vector_source_f(objetivo, True, 96, [])
        self.datos_mascara = blocks.vector_source_f(limite_lineas, True, 96, [])
        self.datos_irr = blocks.vector_source_f(curva_irradiada, True, 96, [])
        self.datos_est = blocks.vector_source_f(nivel_estimado, True, 96, [])
        self.datos_actual = blocks.vector_source_f(curva_actual, True, 96, [])
        self._corte_range = qtgui.Range(0.2, 3, 0.1, 0.5, 50)
        self._corte_win = qtgui.RangeWidget(self._corte_range, self.set_corte, "Corte en cada salto (s)", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._corte_win, 3, 3, 1, 3)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        _congelar_check_box = Qt.QCheckBox("CONGELAR en la linea actual (sigue emitiendo)")
        self._congelar_choices = {True: 1, False: 0}
        self._congelar_choices_inv = dict((v,k) for k,v in self._congelar_choices.items())
        self._congelar_callback = lambda i: Qt.QMetaObject.invokeMethod(_congelar_check_box, "setChecked", Qt.Q_ARG("bool", self._congelar_choices_inv[i]))
        self._congelar_callback(self.congelar)
        _congelar_check_box.stateChanged.connect(lambda i: self.set_congelar(self._congelar_choices[bool(i)]))
        self.top_grid_layout.addWidget(_congelar_check_box, 1, 4, 1, 4)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_referencia_push_button = Qt.QPushButton('3. Guardar perfil de referencia (captura .csv)')
        _boton_referencia_push_button = Qt.QPushButton('3. Guardar perfil de referencia (captura .csv)')
        self._boton_referencia_choices = {'Pressed': 1, 'Released': 0}
        _boton_referencia_push_button.pressed.connect(lambda: self.set_boton_referencia(self._boton_referencia_choices['Pressed']))
        _boton_referencia_push_button.released.connect(lambda: self.set_boton_referencia(self._boton_referencia_choices['Released']))
        self.top_grid_layout.addWidget(_boton_referencia_push_button, 7, 8, 1, 4)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_irradiada_push_button = Qt.QPushButton('2. Calibracion irradiada (trazas .DAT del receptor)')
        _boton_irradiada_push_button = Qt.QPushButton('2. Calibracion irradiada (trazas .DAT del receptor)')
        self._boton_irradiada_choices = {'Pressed': 1, 'Released': 0}
        _boton_irradiada_push_button.pressed.connect(lambda: self.set_boton_irradiada(self._boton_irradiada_choices['Pressed']))
        _boton_irradiada_push_button.released.connect(lambda: self.set_boton_irradiada(self._boton_irradiada_choices['Released']))
        self.top_grid_layout.addWidget(_boton_irradiada_push_button, 7, 4, 1, 4)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_importar_obj_push_button = Qt.QPushButton('Importar objetivo o perfil de referencia')
        _boton_importar_obj_push_button = Qt.QPushButton('Importar objetivo o perfil de referencia')
        self._boton_importar_obj_choices = {'Pressed': 1, 'Released': 0}
        _boton_importar_obj_push_button.pressed.connect(lambda: self.set_boton_importar_obj(self._boton_importar_obj_choices['Pressed']))
        _boton_importar_obj_push_button.released.connect(lambda: self.set_boton_importar_obj(self._boton_importar_obj_choices['Released']))
        self.top_grid_layout.addWidget(_boton_importar_obj_push_button, 7, 0, 1, 4)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_importar_cal_push_button = Qt.QPushButton('Importar calibracion previa')
        _boton_importar_cal_push_button = Qt.QPushButton('Importar calibracion previa')
        self._boton_importar_cal_choices = {'Pressed': 1, 'Released': 0}
        _boton_importar_cal_push_button.pressed.connect(lambda: self.set_boton_importar_cal(self._boton_importar_cal_choices['Pressed']))
        _boton_importar_cal_push_button.released.connect(lambda: self.set_boton_importar_cal(self._boton_importar_cal_choices['Released']))
        self.top_grid_layout.addWidget(_boton_importar_cal_push_button, 6, 8, 1, 4)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(8, 12):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_guardar_cal_push_button = Qt.QPushButton('Guardar calibracion')
        _boton_guardar_cal_push_button = Qt.QPushButton('Guardar calibracion')
        self._boton_guardar_cal_choices = {'Pressed': 1, 'Released': 0}
        _boton_guardar_cal_push_button.pressed.connect(lambda: self.set_boton_guardar_cal(self._boton_guardar_cal_choices['Pressed']))
        _boton_guardar_cal_push_button.released.connect(lambda: self.set_boton_guardar_cal(self._boton_guardar_cal_choices['Released']))
        self.top_grid_layout.addWidget(_boton_guardar_cal_push_button, 6, 4, 1, 4)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(4, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        _boton_conducida_push_button = Qt.QPushButton('1. Calibracion conducida (captura .csv de la tinySA)')
        _boton_conducida_push_button = Qt.QPushButton('1. Calibracion conducida (captura .csv de la tinySA)')
        self._boton_conducida_choices = {'Pressed': 1, 'Released': 0}
        _boton_conducida_push_button.pressed.connect(lambda: self.set_boton_conducida(self._boton_conducida_choices['Pressed']))
        _boton_conducida_push_button.released.connect(lambda: self.set_boton_conducida(self._boton_conducida_choices['Released']))
        self.top_grid_layout.addWidget(_boton_conducida_push_button, 6, 0, 1, 4)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 4):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.datos_actual, 0), (self.grafico, 2))
        self.connect((self.datos_est, 0), (self.grafico, 1))
        self.connect((self.datos_irr, 0), (self.grafico_irradiado, 1))
        self.connect((self.datos_mascara, 0), (self.ritmo_grafico_2, 0))
        self.connect((self.datos_obj, 0), (self.ritmo_grafico, 0))
        self.connect((self.datos_resp, 0), (self.grafico, 3))
        self.connect((self.ritmo_grafico, 0), (self.grafico, 0))
        self.connect((self.ritmo_grafico_2, 0), (self.grafico_irradiado, 0))
        self.connect((self.ritmo_simulacion, 0), (self.salida_nula, 0))
        self.connect((self.tono, 0), (self.ritmo_simulacion, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "exp27_a9_peine_10MHz_sin_placa")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_silencio(self):
        return self.silencio

    def set_silencio(self, silencio):
        self.silencio = silencio
        self._silencio_callback(self.silencio)
        self.set_apagado(int(round(10 * (self.corte + (self.permanencia if self.silencio == 1 else 0)))))

    def get_permanencia(self):
        return self.permanencia

    def set_permanencia(self, permanencia):
        self.permanencia = permanencia
        self.set_encendido(int(round(10 * self.permanencia)))
        self.set_apagado(int(round(10 * (self.corte + (self.permanencia if self.silencio == 1 else 0)))))

    def get_corte(self):
        return self.corte

    def set_corte(self, corte):
        self.corte = corte
        self.set_apagado(int(round(10 * (self.corte + (self.permanencia if self.silencio == 1 else 0)))))

    def get_paso(self):
        return self.paso

    def set_paso(self, paso):
        self.paso = paso
        self.set_decima(max(self.paso, 0))
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0 and (self.fijo >= 0 or self.congelar == 1 or self.en_corte == 0)) else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('LINEA FIJA, emision continua' if self.fijo >= 0 else ('LINEA CONGELADA, emision continua' if self.congelar == 1 else ('CORTE (salto de linea)' if self.en_corte == 1 else 'EMITIENDO')))))

    def get_encendido(self):
        return self.encendido

    def set_encendido(self, encendido):
        self.encendido = encendido
        self.set_por_linea(self.encendido + self.apagado)
        self.set_en_corte(0 if self.antes <= self.dentro < self.antes + self.encendido else 1)
        self.set_et_tiempos('%d min %02d s (%.1f s encendida y %.1f s apagada por linea)' % (self.n_lineas * self.por_linea // 600, (self.n_lineas * self.por_linea // 10) % 60, self.encendido / 10.0, self.apagado / 10.0))

    def get_apagado(self):
        return self.apagado

    def set_apagado(self, apagado):
        self.apagado = apagado
        self.set_antes(self.apagado // 2)
        self.set_por_linea(self.encendido + self.apagado)
        self.set_et_tiempos('%d min %02d s (%.1f s encendida y %.1f s apagada por linea)' % (self.n_lineas * self.por_linea // 600, (self.n_lineas * self.por_linea // 10) % 60, self.encendido / 10.0, self.apagado / 10.0))

    def get_por_linea(self):
        return self.por_linea

    def set_por_linea(self, por_linea):
        self.por_linea = por_linea
        self.set_ciclo(self.decima // self.por_linea)
        self.set_dentro(self.decima % self.por_linea)
        self.set_et_tiempos('%d min %02d s (%.1f s encendida y %.1f s apagada por linea)' % (self.n_lineas * self.por_linea // 600, (self.n_lineas * self.por_linea // 10) % 60, self.encendido / 10.0, self.apagado / 10.0))

    def get_decima(self):
        return self.decima

    def set_decima(self, decima):
        self.decima = decima
        self.set_ciclo(self.decima // self.por_linea)
        self.set_dentro(self.decima % self.por_linea)

    def get_n_lineas(self):
        return self.n_lineas

    def set_n_lineas(self, n_lineas):
        self.n_lineas = n_lineas
        self.set_objetivo([-35.0] * self.n_lineas)
        self.set_medido_irradiado([0.0] * self.n_lineas)
        self.set_posicion(self.ciclo % self.n_lineas)
        self.set_pasada(self.ciclo // self.n_lineas + 1)
        self.set_medidos([0.0] * self.n_lineas)
        self.set_pedido([((self.objetivo[k] - (self.medidos[k] + self.ganancia - self.ganancia_de_lectura)) if self.medidos[k] != 0 else 0.0) for k in range(self.n_lineas)])
        self.set_ganancia_minima(int(math.ceil(self.ganancia_de_lectura + max([self.objetivo[k] - self.medidos[k] for k in range(self.n_lineas) if self.medidos[k] != 0]) - 20 * math.log10(self.amp_max / self.amp_base))) if self.cargadas > 0 else 0)
        self.set_nivel_estimado([((self.medidos[k] + self.ganancia - self.ganancia_de_lectura) + 20 * math.log10(self.amp_tabla[k] / self.amp_base)) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])
        self.set_limite_lineas([((50.0 if self.f_primera / 1e6 + 10 * k <= 230 else 57.0) if self.mascara == 0 else (40.0 if self.f_primera / 1e6 + 10 * k <= 230 else 47.0)) for k in range(self.n_lineas)])
        self.set_et_linea(('%.0f MHz (fija)' % (self.linea / 1e6)) if self.fijo >= 0 else '%.0f MHz (paso %d de %d, pasada %d)' % (self.linea / 1e6, self.posicion + 1, self.n_lineas, self.pasada))
        self.set_et_tiempos('%d min %02d s (%.1f s encendida y %.1f s apagada por linea)' % (self.n_lineas * self.por_linea // 600, (self.n_lineas * self.por_linea // 10) % 60, self.encendido / 10.0, self.apagado / 10.0))
        self.set_et_cargadas(('%d/%d' % (self.cargadas, self.n_lineas)) + ((', es de %g MHz: NO coincide' % self.separacion_cal) if (self.cargadas > 0 and self.separacion_cal != 0 and self.separacion_cal != self.separacion) else ((', de %g MHz' % self.separacion_cal) if self.separacion_cal != 0 else '')))
        self.set_curva_actual([(self.objetivo[k] if (k == self.indice and self.emite == 1) else -100) for k in range(self.n_lineas)])
        self.set_nivel_respuesta([(self.medidos[k] + self.ganancia - self.ganancia_de_lectura) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])

    def get_ciclo(self):
        return self.ciclo

    def set_ciclo(self, ciclo):
        self.ciclo = ciclo
        self.set_posicion(self.ciclo % self.n_lineas)
        self.set_pasada(self.ciclo // self.n_lineas + 1)

    def get_posicion(self):
        return self.posicion

    def set_posicion(self, posicion):
        self.posicion = posicion
        self.set_indice(self.fijo if self.fijo >= 0 else self.posicion)
        self.set_et_linea(('%.0f MHz (fija)' % (self.linea / 1e6)) if self.fijo >= 0 else '%.0f MHz (paso %d de %d, pasada %d)' % (self.linea / 1e6, self.posicion + 1, self.n_lineas, self.pasada))

    def get_objetivo(self):
        return self.objetivo

    def set_objetivo(self, objetivo):
        self.objetivo = objetivo
        self.set_pedido([((self.objetivo[k] - (self.medidos[k] + self.ganancia - self.ganancia_de_lectura)) if self.medidos[k] != 0 else 0.0) for k in range(self.n_lineas)])
        self.set_ganancia_minima(int(math.ceil(self.ganancia_de_lectura + max([self.objetivo[k] - self.medidos[k] for k in range(self.n_lineas) if self.medidos[k] != 0]) - 20 * math.log10(self.amp_max / self.amp_base))) if self.cargadas > 0 else 0)
        self.set_et_nivel('amplitud %.3f, sale unos %.1f dBm (objetivo %.1f dBm)' % (self.amp_tabla[self.indice], self.nivel_estimado[self.indice], self.objetivo[self.indice]))
        self.set_curva_actual([(self.objetivo[k] if (k == self.indice and self.emite == 1) else -100) for k in range(self.n_lineas)])
        self.datos_obj.set_data(self.objetivo, [])

    def get_medidos(self):
        return self.medidos

    def set_medidos(self, medidos):
        self.medidos = medidos
        self.set_pedido([((self.objetivo[k] - (self.medidos[k] + self.ganancia - self.ganancia_de_lectura)) if self.medidos[k] != 0 else 0.0) for k in range(self.n_lineas)])
        self.set_cargadas(sum(1 for leido in self.medidos if leido != 0))
        self.set_ganancia_minima(int(math.ceil(self.ganancia_de_lectura + max([self.objetivo[k] - self.medidos[k] for k in range(self.n_lineas) if self.medidos[k] != 0]) - 20 * math.log10(self.amp_max / self.amp_base))) if self.cargadas > 0 else 0)
        self.set_nivel_estimado([((self.medidos[k] + self.ganancia - self.ganancia_de_lectura) + 20 * math.log10(self.amp_tabla[k] / self.amp_base)) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])
        self.set_nivel_respuesta([(self.medidos[k] + self.ganancia - self.ganancia_de_lectura) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])

    def get_ganancia_de_lectura(self):
        return self.ganancia_de_lectura

    def set_ganancia_de_lectura(self, ganancia_de_lectura):
        self.ganancia_de_lectura = ganancia_de_lectura
        self.set_pedido([((self.objetivo[k] - (self.medidos[k] + self.ganancia - self.ganancia_de_lectura)) if self.medidos[k] != 0 else 0.0) for k in range(self.n_lineas)])
        self.set_ganancia_minima(int(math.ceil(self.ganancia_de_lectura + max([self.objetivo[k] - self.medidos[k] for k in range(self.n_lineas) if self.medidos[k] != 0]) - 20 * math.log10(self.amp_max / self.amp_base))) if self.cargadas > 0 else 0)
        self.set_nivel_estimado([((self.medidos[k] + self.ganancia - self.ganancia_de_lectura) + 20 * math.log10(self.amp_tabla[k] / self.amp_base)) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])
        self.set_nivel_respuesta([(self.medidos[k] + self.ganancia - self.ganancia_de_lectura) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])

    def get_ganancia(self):
        return self.ganancia

    def set_ganancia(self, ganancia):
        self.ganancia = ganancia
        self.set_pedido([((self.objetivo[k] - (self.medidos[k] + self.ganancia - self.ganancia_de_lectura)) if self.medidos[k] != 0 else 0.0) for k in range(self.n_lineas)])
        self.set_nivel_sin_calibrar(self.ganancia - 68)
        self.set_tx_gain(self.ganancia if self.pausa == 0 else 0)
        self.set_nivel_estimado([((self.medidos[k] + self.ganancia - self.ganancia_de_lectura) + 20 * math.log10(self.amp_tabla[k] / self.amp_base)) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])
        self.set_nivel_respuesta([(self.medidos[k] + self.ganancia - self.ganancia_de_lectura) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])

    def get_fijo(self):
        return self.fijo

    def set_fijo(self, fijo):
        self.fijo = fijo
        self._fijo_callback(self.fijo)
        self.set_indice(self.fijo if self.fijo >= 0 else self.posicion)
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0 and (self.fijo >= 0 or self.congelar == 1 or self.en_corte == 0)) else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('LINEA FIJA, emision continua' if self.fijo >= 0 else ('LINEA CONGELADA, emision continua' if self.congelar == 1 else ('CORTE (salto de linea)' if self.en_corte == 1 else 'EMITIENDO')))))
        self.set_et_linea(('%.0f MHz (fija)' % (self.linea / 1e6)) if self.fijo >= 0 else '%.0f MHz (paso %d de %d, pasada %d)' % (self.linea / 1e6, self.posicion + 1, self.n_lineas, self.pasada))

    def get_separacion(self):
        return self.separacion

    def set_separacion(self, separacion):
        self.separacion = separacion
        self._separacion_callback(self.separacion)
        self.set_f_tono(-self.separacion * 1e6)
        self.set_et_espurias('fuga %.2f, imagen %.2f, 3C+S %.2f, 5C-S %.2f' % (self.freq / 1e6, self.freq / 1e6 + self.separacion, 3 * self.freq / 1e6 + self.separacion, 5 * self.freq / 1e6 - self.separacion))
        self.set_et_cargadas(('%d/%d' % (self.cargadas, self.n_lineas)) + ((', es de %g MHz: NO coincide' % self.separacion_cal) if (self.cargadas > 0 and self.separacion_cal != 0 and self.separacion_cal != self.separacion) else ((', de %g MHz' % self.separacion_cal) if self.separacion_cal != 0 else '')))

    def get_prefijo(self):
        return self.prefijo

    def set_prefijo(self, prefijo):
        self.prefijo = prefijo
        self.set_archivo_cal(self.prefijo + 'calibracion_conducida.txt')
        self.set_archivo_obj(self.prefijo + 'objetivo.txt')
        self.set_archivo_irr(self.prefijo + 'ultima_irradiada.txt')

    def get_pedido(self):
        return self.pedido

    def set_pedido(self, pedido):
        self.pedido = pedido
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.pedido])
        self.set_sin_margen(sum(1 for db in self.pedido if self.amp_base * 10 ** (db / 20.0) > self.amp_max))

    def get_paso_lineas(self):
        return self.paso_lineas

    def set_paso_lineas(self, paso_lineas):
        self.paso_lineas = paso_lineas
        self.set_linea(self.f_primera + self.paso_lineas * self.indice)
        self.grafico.set_x_axis((self.f_primera / 1e6), (self.paso_lineas / 1e6))
        self.grafico_irradiado.set_x_axis((self.f_primera / 1e6), (self.paso_lineas / 1e6))

    def get_indice(self):
        return self.indice

    def set_indice(self, indice):
        self.indice = indice
        self.set_linea(self.f_primera + self.paso_lineas * self.indice)
        self.set_amp_tx(self.amp_tabla[self.indice] if self.emite == 1 else 0)
        self.set_et_nivel('amplitud %.3f, sale unos %.1f dBm (objetivo %.1f dBm)' % (self.amp_tabla[self.indice], self.nivel_estimado[self.indice], self.objetivo[self.indice]))
        self.set_curva_actual([(self.objetivo[k] if (k == self.indice and self.emite == 1) else -100) for k in range(self.n_lineas)])

    def get_f_primera(self):
        return self.f_primera

    def set_f_primera(self, f_primera):
        self.f_primera = f_primera
        self.set_linea(self.f_primera + self.paso_lineas * self.indice)
        self.set_limite_lineas([((50.0 if self.f_primera / 1e6 + 10 * k <= 230 else 57.0) if self.mascara == 0 else (40.0 if self.f_primera / 1e6 + 10 * k <= 230 else 47.0)) for k in range(self.n_lineas)])
        self.grafico.set_x_axis((self.f_primera / 1e6), (self.paso_lineas / 1e6))
        self.grafico_irradiado.set_x_axis((self.f_primera / 1e6), (self.paso_lineas / 1e6))

    def get_dentro(self):
        return self.dentro

    def set_dentro(self, dentro):
        self.dentro = dentro
        self.set_en_corte(0 if self.antes <= self.dentro < self.antes + self.encendido else 1)

    def get_antes(self):
        return self.antes

    def set_antes(self, antes):
        self.antes = antes
        self.set_en_corte(0 if self.antes <= self.dentro < self.antes + self.encendido else 1)

    def get_amp_max(self):
        return self.amp_max

    def set_amp_max(self, amp_max):
        self.amp_max = amp_max
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.pedido])
        self.set_sin_margen(sum(1 for db in self.pedido if self.amp_base * 10 ** (db / 20.0) > self.amp_max))
        self.set_ganancia_minima(int(math.ceil(self.ganancia_de_lectura + max([self.objetivo[k] - self.medidos[k] for k in range(self.n_lineas) if self.medidos[k] != 0]) - 20 * math.log10(self.amp_max / self.amp_base))) if self.cargadas > 0 else 0)

    def get_amp_base(self):
        return self.amp_base

    def set_amp_base(self, amp_base):
        self.amp_base = amp_base
        self.set_amp_tabla([min(self.amp_base * 10 ** (db / 20.0), self.amp_max) for db in self.pedido])
        self.set_sin_margen(sum(1 for db in self.pedido if self.amp_base * 10 ** (db / 20.0) > self.amp_max))
        self.set_ganancia_minima(int(math.ceil(self.ganancia_de_lectura + max([self.objetivo[k] - self.medidos[k] for k in range(self.n_lineas) if self.medidos[k] != 0]) - 20 * math.log10(self.amp_max / self.amp_base))) if self.cargadas > 0 else 0)
        self.set_nivel_estimado([((self.medidos[k] + self.ganancia - self.ganancia_de_lectura) + 20 * math.log10(self.amp_tabla[k] / self.amp_base)) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])

    def get_pausa(self):
        return self.pausa

    def set_pausa(self, pausa):
        self.pausa = pausa
        self._pausa_callback(self.pausa)
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0 and (self.fijo >= 0 or self.congelar == 1 or self.en_corte == 0)) else 0)
        self.set_tx_gain(self.ganancia if self.pausa == 0 else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('LINEA FIJA, emision continua' if self.fijo >= 0 else ('LINEA CONGELADA, emision continua' if self.congelar == 1 else ('CORTE (salto de linea)' if self.en_corte == 1 else 'EMITIENDO')))))

    def get_linea(self):
        return self.linea

    def set_linea(self, linea):
        self.linea = linea
        self.set_freq(self.linea - self.f_tono)
        self.set_et_linea(('%.0f MHz (fija)' % (self.linea / 1e6)) if self.fijo >= 0 else '%.0f MHz (paso %d de %d, pasada %d)' % (self.linea / 1e6, self.posicion + 1, self.n_lineas, self.pasada))

    def get_f_tono(self):
        return self.f_tono

    def set_f_tono(self, f_tono):
        self.f_tono = f_tono
        self.set_freq(self.linea - self.f_tono)
        self.tono.set_frequency(self.f_tono)

    def get_en_corte(self):
        return self.en_corte

    def set_en_corte(self, en_corte):
        self.en_corte = en_corte
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0 and (self.fijo >= 0 or self.congelar == 1 or self.en_corte == 0)) else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('LINEA FIJA, emision continua' if self.fijo >= 0 else ('LINEA CONGELADA, emision continua' if self.congelar == 1 else ('CORTE (salto de linea)' if self.en_corte == 1 else 'EMITIENDO')))))

    def get_congelar(self):
        return self.congelar

    def set_congelar(self, congelar):
        self.congelar = congelar
        self._congelar_callback(self.congelar)
        self.set_emite(1 if (self.pausa == 0 and self.paso >= 0 and (self.fijo >= 0 or self.congelar == 1 or self.en_corte == 0)) else 0)
        self.set_etapa('PAUSA (sin emitir)' if self.pausa == 1 else ('INICIACION' if self.paso < 0 else ('LINEA FIJA, emision continua' if self.fijo >= 0 else ('LINEA CONGELADA, emision continua' if self.congelar == 1 else ('CORTE (salto de linea)' if self.en_corte == 1 else 'EMITIENDO')))))

    def get_cargadas(self):
        return self.cargadas

    def set_cargadas(self, cargadas):
        self.cargadas = cargadas
        self.set_ganancia_minima(int(math.ceil(self.ganancia_de_lectura + max([self.objetivo[k] - self.medidos[k] for k in range(self.n_lineas) if self.medidos[k] != 0]) - 20 * math.log10(self.amp_max / self.amp_base))) if self.cargadas > 0 else 0)
        self.set_et_cargadas(('%d/%d' % (self.cargadas, self.n_lineas)) + ((', es de %g MHz: NO coincide' % self.separacion_cal) if (self.cargadas > 0 and self.separacion_cal != 0 and self.separacion_cal != self.separacion) else ((', de %g MHz' % self.separacion_cal) if self.separacion_cal != 0 else '')))
        self.set_et_gmin(('%d dB' % self.ganancia_minima) if self.cargadas > 0 else 'sin calibracion conducida')

    def get_archivo_cal(self):
        return self.archivo_cal

    def set_archivo_cal(self, archivo_cal):
        self.archivo_cal = archivo_cal
        self.set_estado_cal('hay una guardada, sin importar' if os.path.exists(self.archivo_cal) else 'todavia no hay ninguna guardada')

    def get_amp_tabla(self):
        return self.amp_tabla

    def set_amp_tabla(self, amp_tabla):
        self.amp_tabla = amp_tabla
        self.set_amp_tx(self.amp_tabla[self.indice] if self.emite == 1 else 0)
        self.set_nivel_estimado([((self.medidos[k] + self.ganancia - self.ganancia_de_lectura) + 20 * math.log10(self.amp_tabla[k] / self.amp_base)) if self.medidos[k] != 0 else -100 for k in range(self.n_lineas)])
        self.set_et_nivel('amplitud %.3f, sale unos %.1f dBm (objetivo %.1f dBm)' % (self.amp_tabla[self.indice], self.nivel_estimado[self.indice], self.objetivo[self.indice]))

    def get_texto_salida(self):
        return self.texto_salida

    def set_texto_salida(self, texto_salida):
        self.texto_salida = texto_salida
        self.set_et_salida(self.texto_salida + ', %.0f MSPS' % (self.samp_rate / 1e6))

    def get_sin_margen(self):
        return self.sin_margen

    def set_sin_margen(self, sin_margen):
        self.sin_margen = sin_margen
        self.set_et_margen(self.sin_margen)

    def get_separacion_cal(self):
        return self.separacion_cal

    def set_separacion_cal(self, separacion_cal):
        self.separacion_cal = separacion_cal
        self.set_et_cargadas(('%d/%d' % (self.cargadas, self.n_lineas)) + ((', es de %g MHz: NO coincide' % self.separacion_cal) if (self.cargadas > 0 and self.separacion_cal != 0 and self.separacion_cal != self.separacion) else ((', de %g MHz' % self.separacion_cal) if self.separacion_cal != 0 else '')))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_ancho_banda(0.9 * self.samp_rate)
        self.set_et_salida(self.texto_salida + ', %.0f MSPS' % (self.samp_rate / 1e6))
        self.tono.set_sampling_freq(self.samp_rate)

    def get_pasada(self):
        return self.pasada

    def set_pasada(self, pasada):
        self.pasada = pasada
        self.set_et_linea(('%.0f MHz (fija)' % (self.linea / 1e6)) if self.fijo >= 0 else '%.0f MHz (paso %d de %d, pasada %d)' % (self.linea / 1e6, self.posicion + 1, self.n_lineas, self.pasada))

    def get_nivel_estimado(self):
        return self.nivel_estimado

    def set_nivel_estimado(self, nivel_estimado):
        self.nivel_estimado = nivel_estimado
        self.set_et_nivel('amplitud %.3f, sale unos %.1f dBm (objetivo %.1f dBm)' % (self.amp_tabla[self.indice], self.nivel_estimado[self.indice], self.objetivo[self.indice]))
        self.datos_est.set_data(self.nivel_estimado, [])

    def get_medido_irradiado(self):
        return self.medido_irradiado

    def set_medido_irradiado(self, medido_irradiado):
        self.medido_irradiado = medido_irradiado
        self.set_curva_irradiada([(v if v != 0 else -100) for v in self.medido_irradiado])

    def get_mascara(self):
        return self.mascara

    def set_mascara(self, mascara):
        self.mascara = mascara
        self._mascara_callback(self.mascara)
        self.set_limite_lineas([((50.0 if self.f_primera / 1e6 + 10 * k <= 230 else 57.0) if self.mascara == 0 else (40.0 if self.f_primera / 1e6 + 10 * k <= 230 else 47.0)) for k in range(self.n_lineas)])

    def get_ganancia_minima(self):
        return self.ganancia_minima

    def set_ganancia_minima(self, ganancia_minima):
        self.ganancia_minima = ganancia_minima
        self.set_et_gmin(('%d dB' % self.ganancia_minima) if self.cargadas > 0 else 'sin calibracion conducida')

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_et_portadora('%.2f MHz' % (self.freq / 1e6))
        self.set_et_espurias('fuga %.2f, imagen %.2f, 3C+S %.2f, 5C-S %.2f' % (self.freq / 1e6, self.freq / 1e6 + self.separacion, 3 * self.freq / 1e6 + self.separacion, 5 * self.freq / 1e6 - self.separacion))

    def get_etapa(self):
        return self.etapa

    def set_etapa(self, etapa):
        self.etapa = etapa
        self.set_et_etapa(self.etapa)

    def get_estado_obj(self):
        return self.estado_obj

    def set_estado_obj(self, estado_obj):
        self.estado_obj = estado_obj
        self.set_et_obj(self.estado_obj)

    def get_estado_irr(self):
        return self.estado_irr

    def set_estado_irr(self, estado_irr):
        self.estado_irr = estado_irr
        self.set_et_irr(self.estado_irr)

    def get_estado_cal(self):
        return self.estado_cal

    def set_estado_cal(self, estado_cal):
        self.estado_cal = estado_cal
        self.set_et_cal(self.estado_cal)

    def get_emite(self):
        return self.emite

    def set_emite(self, emite):
        self.emite = emite
        self.set_amp_tx(self.amp_tabla[self.indice] if self.emite == 1 else 0)
        self.set_curva_actual([(self.objetivo[k] if (k == self.indice and self.emite == 1) else -100) for k in range(self.n_lineas)])

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain

    def get_nivel_sin_calibrar(self):
        return self.nivel_sin_calibrar

    def set_nivel_sin_calibrar(self, nivel_sin_calibrar):
        self.nivel_sin_calibrar = nivel_sin_calibrar

    def get_nivel_respuesta(self):
        return self.nivel_respuesta

    def set_nivel_respuesta(self, nivel_respuesta):
        self.nivel_respuesta = nivel_respuesta
        self.datos_resp.set_data(self.nivel_respuesta, [])

    def get_muestras_por_bloque(self):
        return self.muestras_por_bloque

    def set_muestras_por_bloque(self, muestras_por_bloque):
        self.muestras_por_bloque = muestras_por_bloque

    def get_lista_de_pasos(self):
        return self.lista_de_pasos

    def set_lista_de_pasos(self, lista_de_pasos):
        self.lista_de_pasos = lista_de_pasos

    def get_limite_lineas(self):
        return self.limite_lineas

    def set_limite_lineas(self, limite_lineas):
        self.limite_lineas = limite_lineas
        self.datos_mascara.set_data(self.limite_lineas, [])

    def get_et_tiempos(self):
        return self.et_tiempos

    def set_et_tiempos(self, et_tiempos):
        self.et_tiempos = et_tiempos
        Qt.QMetaObject.invokeMethod(self._et_tiempos_label, "setText", Qt.Q_ARG("QString", str(self._et_tiempos_formatter(self.et_tiempos))))

    def get_et_salida(self):
        return self.et_salida

    def set_et_salida(self, et_salida):
        self.et_salida = et_salida
        Qt.QMetaObject.invokeMethod(self._et_salida_label, "setText", Qt.Q_ARG("QString", str(self._et_salida_formatter(self.et_salida))))

    def get_et_portadora(self):
        return self.et_portadora

    def set_et_portadora(self, et_portadora):
        self.et_portadora = et_portadora
        Qt.QMetaObject.invokeMethod(self._et_portadora_label, "setText", Qt.Q_ARG("QString", str(self._et_portadora_formatter(self.et_portadora))))

    def get_et_obj(self):
        return self.et_obj

    def set_et_obj(self, et_obj):
        self.et_obj = et_obj
        Qt.QMetaObject.invokeMethod(self._et_obj_label, "setText", Qt.Q_ARG("QString", str(self._et_obj_formatter(self.et_obj))))

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

    def get_et_irr(self):
        return self.et_irr

    def set_et_irr(self, et_irr):
        self.et_irr = et_irr
        Qt.QMetaObject.invokeMethod(self._et_irr_label, "setText", Qt.Q_ARG("QString", str(self._et_irr_formatter(self.et_irr))))

    def get_et_gmin(self):
        return self.et_gmin

    def set_et_gmin(self, et_gmin):
        self.et_gmin = et_gmin
        Qt.QMetaObject.invokeMethod(self._et_gmin_label, "setText", Qt.Q_ARG("QString", str(self._et_gmin_formatter(self.et_gmin))))

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

    def get_et_cargadas(self):
        return self.et_cargadas

    def set_et_cargadas(self, et_cargadas):
        self.et_cargadas = et_cargadas
        Qt.QMetaObject.invokeMethod(self._et_cargadas_label, "setText", Qt.Q_ARG("QString", str(self._et_cargadas_formatter(self.et_cargadas))))

    def get_et_cal(self):
        return self.et_cal

    def set_et_cal(self, et_cal):
        self.et_cal = et_cal
        Qt.QMetaObject.invokeMethod(self._et_cal_label, "setText", Qt.Q_ARG("QString", str(self._et_cal_formatter(self.et_cal))))

    def get_curva_irradiada(self):
        return self.curva_irradiada

    def set_curva_irradiada(self, curva_irradiada):
        self.curva_irradiada = curva_irradiada
        self.datos_irr.set_data(self.curva_irradiada, [])

    def get_curva_actual(self):
        return self.curva_actual

    def set_curva_actual(self, curva_actual):
        self.curva_actual = curva_actual
        self.datos_actual.set_data(self.curva_actual, [])

    def get_boton_referencia(self):
        return self.boton_referencia

    def set_boton_referencia(self, boton_referencia):
        self.boton_referencia = boton_referencia

    def get_boton_irradiada(self):
        return self.boton_irradiada

    def set_boton_irradiada(self, boton_irradiada):
        self.boton_irradiada = boton_irradiada

    def get_boton_importar_obj(self):
        return self.boton_importar_obj

    def set_boton_importar_obj(self, boton_importar_obj):
        self.boton_importar_obj = boton_importar_obj

    def get_boton_importar_cal(self):
        return self.boton_importar_cal

    def set_boton_importar_cal(self, boton_importar_cal):
        self.boton_importar_cal = boton_importar_cal

    def get_boton_guardar_cal(self):
        return self.boton_guardar_cal

    def set_boton_guardar_cal(self, boton_guardar_cal):
        self.boton_guardar_cal = boton_guardar_cal

    def get_boton_conducida(self):
        return self.boton_conducida

    def set_boton_conducida(self, boton_conducida):
        self.boton_conducida = boton_conducida

    def get_bloques_usb(self):
        return self.bloques_usb

    def set_bloques_usb(self, bloques_usb):
        self.bloques_usb = bloques_usb

    def get_archivo_obj(self):
        return self.archivo_obj

    def set_archivo_obj(self, archivo_obj):
        self.archivo_obj = archivo_obj

    def get_archivo_irr(self):
        return self.archivo_irr

    def set_archivo_irr(self, archivo_irr):
        self.archivo_irr = archivo_irr

    def get_ancho_banda(self):
        return self.ancho_banda

    def set_ancho_banda(self, ancho_banda):
        self.ancho_banda = ancho_banda

    def get_amp_tx(self):
        return self.amp_tx

    def set_amp_tx(self, amp_tx):
        self.amp_tx = amp_tx
        self.tono.set_amplitude(self.amp_tx)




def main(top_block_cls=exp27_a9_peine_10MHz_sin_placa, options=None):

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
