# Gráficos de Zt de las dos puntas para el informe del TP6
# Lee las mediciones de TP6_Zt_puntas.xlsx (corrida 1).
# Si existe TP6_Zt_puntas_corrida2.xlsx (mismo formato) la agrega como corrida 2.
import math
import os
from openpyxl import load_workbook
import matplotlib.pyplot as plt

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_1 = os.path.join(CARPETA, "TP6_Zt_puntas.xlsx")
ARCHIVO_2 = os.path.join(CARPETA, "TP6_Zt_puntas_corrida2.xlsx")
SALIDA = os.path.join(CARPETA, "Imagenes")

# Frecuencia hasta la que cada punta funciona bien (MHz)
LIMITE_CIRCULAR = 56
LIMITE_CUADRADA = 35.5


def leer_corrida(archivo):
    # Devuelve frecuencias y Zt (dBΩ) de cada punta, calculando Zt desde los datos crudos
    hoja = load_workbook(archivo, data_only=True)["Medición"]
    perdida = hoja["G4"].value or 0
    constante = 20 * math.log10(50)
    datos = {"circular": ([], []), "cuadrada": ([], [])}
    fila = 10
    while hoja["B" + str(fila)].value is not None:
        f = hoja["B" + str(fila)].value
        p_gen = hoja["C" + str(fila)].value
        p_circular = hoja["D" + str(fila)].value
        p_cuadrada = hoja["I" + str(fila)].value
        if p_circular is not None:
            datos["circular"][0].append(f)
            datos["circular"][1].append(p_circular - p_gen + constante + perdida)
        if p_cuadrada is not None:
            datos["cuadrada"][0].append(f)
            datos["cuadrada"][1].append(p_cuadrada - p_gen + constante + perdida)
        fila += 1
    return datos


def recortar(curva, limite):
    # Deja solo los puntos hasta la frecuencia límite
    frecuencias = []
    valores = []
    for f, z in zip(curva[0], curva[1]):
        if f <= limite:
            frecuencias.append(f)
            valores.append(z)
    return frecuencias, valores


def graficar(punta, titulo, limite, corrida1, corrida2, archivo, solo_rango_util=False):
    curva1 = corrida1[punta]
    if solo_rango_util:
        curva1 = recortar(curva1, limite)
    plt.figure(figsize=(6.3, 3.6))
    plt.semilogx(curva1[0], curva1[1], color="black", linestyle="-",
                 marker="o", markersize=3.5, linewidth=1.2, label="Corrida 1")
    if corrida2 is not None:
        curva2 = corrida2[punta]
        if solo_rango_util:
            curva2 = recortar(curva2, limite)
        plt.semilogx(curva2[0], curva2[1], color="black", linestyle="--",
                     marker="s", markersize=3.5, markerfacecolor="white", linewidth=1.2,
                     label="Corrida 2")
    if solo_rango_util:
        plt.xlim(0.01, 100)
    else:
        plt.axvline(limite, color="black", linestyle=":", linewidth=1)
        plt.text(limite * 0.92, plt.ylim()[0] + 1, "fin del rango útil", rotation=90,
                 ha="right", va="bottom", fontsize=8)
        plt.xlim(0.01, 200)
    plt.xticks([0.01, 0.1, 1, 10, 100], ["0,01", "0,1", "1", "10", "100"])
    plt.xlabel("Frecuencia (MHz)")
    plt.ylabel("Zt (dBΩ)")
    plt.title(titulo, fontsize=10)
    plt.grid(True, which="major", color="0.75", linewidth=0.6)
    plt.grid(True, which="minor", color="0.9", linewidth=0.4)
    if solo_rango_util:
        plt.legend(fontsize=8, loc="upper center")
    else:
        plt.legend(fontsize=8, loc="lower center")
    plt.tight_layout()
    plt.savefig(archivo)
    plt.close()


def resumen(punta, datos, desde, hasta):
    # Promedio, mínimo y máximo de Zt entre dos frecuencias (para escribir el informe)
    valores = [z for f, z in zip(datos[punta][0], datos[punta][1]) if desde <= f <= hasta]
    promedio = sum(valores) / len(valores)
    print(punta, desde, "a", hasta, "MHz: promedio", round(promedio, 1),
          "mín", round(min(valores), 1), "máx", round(max(valores), 1))


corrida1 = leer_corrida(ARCHIVO_1)
corrida2 = None
if os.path.exists(ARCHIVO_2):
    corrida2 = leer_corrida(ARCHIVO_2)

graficar("circular", "Punta circular", LIMITE_CIRCULAR, corrida1, corrida2,
         os.path.join(SALIDA, "zt_punta_circular.pdf"))
graficar("circular", "Punta circular, rango útil", LIMITE_CIRCULAR, corrida1, corrida2,
         os.path.join(SALIDA, "zt_punta_circular_rango_util.pdf"), solo_rango_util=True)
graficar("cuadrada", "Punta cuadrada con apertura", LIMITE_CUADRADA, corrida1, corrida2,
         os.path.join(SALIDA, "zt_punta_cuadrada.pdf"))

resumen("circular", corrida1, 0.04, 20)
resumen("cuadrada", corrida1, 0.25, 8)
print("Listo")
