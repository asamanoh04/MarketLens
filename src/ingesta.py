# src/ingesta.py
# Módulo para descargar datos de mercados financieros

import yfinance as yf
import yaml
import pandas as pd
from pathlib import Path
import time

# Rutas del proyecto
RAIZ = Path(__file__).parent.parent
CONFIG = RAIZ / "config" / "assets.yaml"
DATOS_CRUDOS = RAIZ / "data" / "raw"


def cargar_activos():
    """Lee el archivo de configuración y regresa todos los activos activos."""
    with open(CONFIG) as f:
        config = yaml.safe_load(f)

    activos = []
    for categoria, lista in config.items():
        for activo in lista:
            if activo.get("activo", True):
                activos.append(activo)
    return activos


def descargar_activo(simbolo, nombre, periodo="1y", intervalo="1d"):
    """Descarga datos históricos de un activo y los guarda en data/raw."""
    print(f"Descargando {nombre} ({simbolo})...")

    df = yf.download(simbolo, period=periodo, interval=intervalo, progress=False)

    if df.empty:
        print(f"  ADVERTENCIA: No se encontraron datos para {simbolo}")
        return None

    archivo = DATOS_CRUDOS / f"{simbolo.replace('=X', '').replace('^', '')}.csv"
    df.to_csv(archivo)
    print(f"  OK: {archivo.name} — {len(df)} registros")
    return df


def descargar_todos():
    """Descarga todos los activos definidos en assets.yaml."""
    activos = cargar_activos()
    print(f"\nDescargando {len(activos)} activos...\n")

    resultados = {}
    for activo in activos:
        # Lee el periodo definido en assets.yaml; si falta, usa "1y" por defecto
        df = descargar_activo(
            activo["simbolo"],
            activo["nombre"],
            periodo=activo.get("periodo", "1y"),
        )
        if df is not None:
            resultados[activo["simbolo"]] = df
        time.sleep(8)

    print(f"\nDescarga completa — {len(resultados)} activos descargados")
    return resultados


if __name__ == "__main__":
    descargar_todos()