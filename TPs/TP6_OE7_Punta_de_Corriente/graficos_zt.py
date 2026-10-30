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


def graficar(punta, titulo, limite, corrida1, corrida2, archivo):
    # Una punta en todo el rango medido, con una línea punteada donde termina el rango útil
    plt.figure(figsize=(6.3, 3.6))
    plt.semilogx(corrida1[punta][0], corrida1[punta][1], color="black", linestyle="-",
                 marker="o", markersize=3.5, linewidth=1.2, label="Corrida 1")
    if corrida2 is not None:
        plt.semilogx(corrida2[punta][0], corrida2[punta][1], color="black", linestyle="--",
                     marker="s", markersize=3.5, markerfacecolor="white", linewidth=1.2,
                     label="Corrida 2")
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
    plt.legend(fontsize=8, loc="lower center")
    plt.tight_layout()
    plt.savefig(archivo)
    plt.close()


def graficar_rango_util(corrida1, corrida2, archivo):
    # Las dos puntas juntas, cada una solo hasta su límite, con líneas sin puntos
    plt.figure(figsize=(6.3, 3.6))
    curvas = [("circular", LIMITE_CIRCULAR, "Punta circular", "-", ":"),
              ("cuadrada", LIMITE_CUADRADA, "Punta cuadrada", "--", "-.")]
    for punta, limite, nombre, linea1, linea2 in curvas:
        curva1 = recortar(corrida1[punta], limite)
        if corrida2 is None:
            plt.semilogx(curva1[0], curva1[1], color="black", linestyle=linea1,
                         linewidth=1.4, label=nombre)
        else:
            curva2 = recortar(corrida2[punta], limite)
            plt.semilogx(curva1[0], curva1[1], color="black", linestyle=linea1,
                         linewidth=1.4, label=nombre + ", corrida 1")
            plt.semilogx(curva2[0], curva2[1], color="black", linestyle=linea2,
                         linewidth=1.4, label=nombre + ", corrida 2")
    plt.xlim(0.01, 100)
    plt.xticks([0.01, 0.1, 1, 10, 100], ["0,01", "0,1", "1", "10", "100"])
    plt.xlabel("Frecuencia (MHz)")
    plt.ylabel("Zt (dBΩ)")
    plt.title("Rango útil de las dos puntas", fontsize=10)
    plt.grid(True, which="major", color="0.75", linewidth=0.6)
    plt.grid(True, which="minor", color="0.9", linewidth=0.4)
    plt.legend(fontsize=8, loc="lower right")
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
    # Si la planilla de la corrida 2 todavía no tiene datos, no se dibuja
    if len(corrida2["circular"][0]) == 0 or len(corrida2["cuadrada"][0]) == 0:
        print("La corrida 2 todavía no tiene datos de las dos puntas, se grafica solo la corrida 1")
        corrida2 = None

graficar("circular", "Punta circular", LIMITE_CIRCULAR, corrida1, corrida2,
         os.path.join(SALIDA, "zt_punta_circular.pdf"))
graficar("cuadrada", "Punta cuadrada con apertura", LIMITE_CUADRADA, corrida1, corrida2,
         os.path.join(SALIDA, "zt_punta_cuadrada.pdf"))
graficar_rango_util(corrida1, corrida2, os.path.join(SALIDA, "zt_rango_util.pdf"))

resumen("circular", corrida1, 0.04, 20)
resumen("cuadrada", corrida1, 0.25, 8)
print("Listo")
