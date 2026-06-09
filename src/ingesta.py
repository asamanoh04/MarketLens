# src/ingesta.py
# Módulo para descargar datos de mercados financieros

import yaml
import pandas as pd
from pathlib import Path
import time
import os
from dotenv import load_dotenv
from binance.client import Client
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.foreignexchange import ForeignExchange

load_dotenv()


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
                activo["categoria"] = categoria  # ← esta línea faltaba
                activos.append(activo)
    return activos


def descargar_cripto(activo):
    nombre = activo["nombre"]
    simbolo = activo["simbolo"]
    binance_simbolo = activo["binance_simbolo"]

    print(f"Descargando {nombre} ({simbolo})...")

    # Binance entrega OHLCV diario público desde 2017 sin API key ni límite.
    cliente = Client()
    velas = cliente.get_historical_klines(
        binance_simbolo,
        Client.KLINE_INTERVAL_1DAY,
        "1 Jan 2017"
    )

    if not velas:
        print(f"  ADVERTENCIA: No se encontraron datos para {simbolo}")
        return None

    # Cada vela es: [open_time, open, high, low, close, volume, close_time, ...]
    columnas = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_base", "taker_quote", "ignorar"
    ]
    df = pd.DataFrame(velas, columns=columnas)
    df["fecha"] = pd.to_datetime(df["open_time"], unit="ms")

    # Nos quedamos solo con OHLCV y lo pasamos a número.
    df = df[["fecha", "open", "high", "low", "close", "volume"]].set_index("fecha")
    df = df.astype(float)

    archivo = DATOS_CRUDOS / f"{simbolo.replace('-USD', '')}.csv"
    df.to_csv(archivo)
    print(f"  OK: {archivo.name} — {len(df)} registros")
    return df

def descargar_tradicional(activo):
    nombre = activo["nombre"]
    simbolo = activo["simbolo"]
    categoria = activo["categoria"]
    periodo = activo["periodo"]

    print(f"Descargando {nombre} ({simbolo})...")

    api_key = os.getenv("ALPHA_VANTAGE_KEY")

    if categoria == "acciones" or categoria == "indices":
        # En acciones/índices outputsize="full" es premium; con la llave gratis
        # solo "compact" (~100 días). El historial largo se baja manual como CSV.
        ts = TimeSeries(key=api_key, output_format="pandas")
        df, _ = ts.get_daily(symbol=simbolo, outputsize="compact")

    elif categoria == "forex":
        # En forex (FX_DAILY) "full" SÍ es gratis: hasta ~20 años de historial.
        fx = ForeignExchange(key=api_key, output_format="pandas")
        simbolo_limpio = simbolo.replace("=X", "")
        # Yahoo: si el símbolo trae una sola moneda (ej. MXN=X), la base es USD.
        if len(simbolo_limpio) == 3:
            from_currency = "USD"
            to_currency = simbolo_limpio
        else:
            from_currency = simbolo_limpio[:3]
            to_currency = simbolo_limpio[3:]
        df, _ = fx.get_currency_exchange_daily(
            from_symbol=from_currency,
            to_symbol=to_currency,
            outputsize="full"
        )

    if df is None or df.empty:
        print(f"  ADVERTENCIA: No se encontraron datos para {simbolo}")
        return None

    archivo = DATOS_CRUDOS / f"{simbolo.replace('=X', '').replace('^', '')}.csv"
    df.to_csv(archivo)
    print(f"  OK: {archivo.name} — {len(df)} registros")
    return df


def descargar_todos():
    activos = cargar_activos()
    print(f"\nDescargando {len(activos)} activos...\n")

    resultados = {}
    for activo in activos:
        try:
            if activo["categoria"] == "criptomonedas":
                df = descargar_cripto(activo)
            else:
                df = descargar_tradicional(activo)

            if df is not None:
                resultados[activo["simbolo"]] = df
        except Exception as e:
            print(f"  ERROR descargando {activo['simbolo']}: {e}")
        time.sleep(5)

    print(f"\nDescarga completa — {len(resultados)} activos descargados")
    return resultados


if __name__ == "__main__":
    descargar_todos()