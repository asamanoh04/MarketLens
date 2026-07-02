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
# Acciones/índices: el historial largo no hay fuente gratis automática,
# se baja a mano de Stooq (el navegador resuelve su muro anti-bot) y los
# CSV originales viven aquí. Ver data/raw/manual/README.md.
DATOS_MANUALES = DATOS_CRUDOS / "manual"


def guardar_merge(df_nuevo, archivo):
    """Pega df_nuevo sobre lo que ya exista en 'archivo' y guarda de viejo a nuevo.

    Es la pieza que permite actualizar de a poco: si ya hay historial en disco,
    lo lee, le agrega las filas nuevas y quita fechas duplicadas quedándose con
    el dato más reciente (por si la fuente corrige un precio). Así una fuente
    que solo entrega los últimos ~100 días nunca borra la historia profunda.
    """
    if archivo.exists():
        # La fecha siempre es la primera columna, sin importar cómo se llame
        # (fecha / date / Date). La leemos como índice de tipo fecha.
        df_viejo = pd.read_csv(archivo, index_col=0, parse_dates=[0])
        # Igualamos el nombre del índice para que concat no invente columnas.
        df_viejo.index.name = df_nuevo.index.name
        df = pd.concat([df_viejo, df_nuevo])
        # Ante una fecha repetida nos quedamos con la última = la recién bajada.
        df = df[~df.index.duplicated(keep="last")]
    else:
        df = df_nuevo

    df = df.sort_index()
    df.to_csv(archivo)
    return df


def _normalizar_ohlcv_av(df):
    """Renombra las columnas de Alpha Vantage (ej. '1. open') a Open/High/Low/
    Close/Volume y llama 'Date' al índice, para que empaten con la base de Stooq
    al hacer el merge de acciones/índices."""
    mapa = {col: col.split(". ")[-1].capitalize() for col in df.columns}
    df = df.rename(columns=mapa)
    df.index.name = "Date"
    return df


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
    # Binance re-baja todo el historial cada vez; el merge lo deja idempotente
    # (las fechas repetidas se colapsan) y suma los días nuevos al final.
    df = guardar_merge(df, archivo)
    print(f"  OK: {archivo.name} — {len(df)} registros")
    return df

def descargar_tradicional(activo):
    """Forex vía Alpha Vantage (FX_DAILY 'full', gratis: ~20 años)."""
    nombre = activo["nombre"]
    simbolo = activo["simbolo"]

    print(f"Descargando {nombre} ({simbolo})...")

    api_key = os.getenv("ALPHA_VANTAGE_KEY")
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

    # Alpha Vantage entrega de más reciente a más antiguo; guardar_merge ordena.
    archivo = DATOS_CRUDOS / f"{simbolo.replace('=X', '')}.csv"
    df = guardar_merge(df, archivo)
    print(f"  OK: {archivo.name} — {len(df)} registros")
    return df


def actualizar_accion_indice(activo):
    """Acciones e índices con historial profundo (Stooq) + días nuevos (AV).

    Stooq da el historial largo pero se baja a mano una sola vez; queda como
    base. De ahí en adelante Alpha Vantage 'compact' (últimos ~100 días, gratis
    para estos símbolos) trae lo nuevo y guardar_merge lo pega sobre la base.
    Así se mantiene al día solo (sin volver a Stooq) conservando la historia.
    """
    nombre = activo["nombre"]
    simbolo = activo["simbolo"]

    print(f"Actualizando {nombre} ({simbolo})...")

    archivo = DATOS_CRUDOS / f"{simbolo.replace('^', '')}.csv"

    # 1. Semilla: si aún no hay CSV de trabajo, partimos del histórico de Stooq.
    if not archivo.exists():
        origen = DATOS_MANUALES / activo.get("archivo_manual", "")
        if origen.exists():
            # Stooq entrega columnas: Date, Open, High, Low, Close, Volume.
            base = pd.read_csv(origen, parse_dates=["Date"], index_col="Date")
            guardar_merge(base, archivo)
            print(f"  semilla Stooq: {len(base)} registros históricos")
        else:
            print(f"  ADVERTENCIA: sin base Stooq ({activo.get('archivo_manual')}) — "
                  f"solo se tendrán ~100 días de Alpha Vantage")

    # 2. Actualización: últimos ~100 días de Alpha Vantage y merge sobre la base.
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    ts = TimeSeries(key=api_key, output_format="pandas")
    df, _ = ts.get_daily(symbol=simbolo, outputsize="compact")

    if df is None or df.empty:
        print(f"  ADVERTENCIA: Alpha Vantage no devolvió datos para {simbolo}")
        # Si al menos existe la base de Stooq, no es un fallo total.
        return pd.read_csv(archivo, index_col=0, parse_dates=[0]) if archivo.exists() else None

    df = _normalizar_ohlcv_av(df)
    df = guardar_merge(df, archivo)
    print(f"  OK: {archivo.name} — {len(df)} registros")
    return df


def descargar_todos():
    activos = cargar_activos()
    print(f"\nDescargando {len(activos)} activos...\n")

    resultados = {}
    for activo in activos:
        try:
            categoria = activo["categoria"]
            if categoria == "criptomonedas":
                df = descargar_cripto(activo)
            elif categoria == "forex":
                df = descargar_tradicional(activo)
            elif categoria in ("acciones", "indices"):
                df = actualizar_accion_indice(activo)
            else:
                print(f"  ADVERTENCIA: categoría desconocida '{categoria}' para {activo['simbolo']}")
                df = None

            if df is not None:
                resultados[activo["simbolo"]] = df
        except Exception as e:
            print(f"  ERROR descargando {activo['simbolo']}: {e}")

        # Todas las fuentes pegan a una API (Binance o Alpha Vantage); la pausa
        # respeta el límite de requests de Alpha Vantage (forex + acciones/índices).
        time.sleep(5)

    print(f"\nDescarga completa — {len(resultados)} activos descargados")
    return resultados


if __name__ == "__main__":
    descargar_todos()