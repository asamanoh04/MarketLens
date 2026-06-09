# MarketLens — Contexto para Claude Code

## ¿Qué es este proyecto?
Pipeline completo de análisis de mercados financieros que cubre
cripto, forex, acciones e índices. Incluye ingesta de APIs,
limpieza de datos, EDA, minería de datos, ML predictivo y
dashboard interactivo.

## Stack tecnológico
- Lenguaje: Python 3
- Entorno: WSL2 Ubuntu 20.04 + VSCode
- Control de versiones: Git + GitHub (asamanoh04/MarketLens)

## Activos monitoreados
- Cripto: BTC, ETH, SOL
- Forex: EUR/USD, USD/MXN, JPY/MXN
- Índices: S&P500, NASDAQ
- Acciones: AAPL, TSLA (expandible)

## Estructura del proyecto
- `data/` — datos crudos y procesados
- `src/` — código fuente principal
- `notebooks/` — análisis exploratorio
- `dashboard/` — visualización interactiva
- `models/` — modelos entrenados de ML
- `tests/` — pruebas unitarias

## Fases del proyecto
1. Ingesta de datos via APIs
2. Pipeline de limpieza y transformación
3. EDA y minería de datos
4. Modelo de ML predictivo
5. Dashboard interactivo con Plotly/Dash

## Perfil del desarrollador
- 4 años de experiencia en Java, Python, SQL, Bash, Git
- Reconectando con la práctica después de usar IA
- Conoce conceptos de ML pero poca experiencia práctica
- Prefiere explicaciones con analogías simples

## Reglas de trabajo
- Explicar cada decisión importante antes de implementarla
- Commits frecuentes con mensajes descriptivos en español
- Un archivo, una responsabilidad
- Código limpio con comentarios en español
- Antes de crear algo nuevo, revisar si ya existe

## Cómo agregar un activo nuevo
Solo agregarlo en `config/assets.yaml` con su símbolo y tipo.
El sistema lo detecta automáticamente.

## Contexto adicional
- Sin API de Anthropic por ahora, usar librerías gratuitas para NLP
- Priorizar que el código sea legible sobre que sea óptimo
- Este proyecto es para aprender, no para producción

## Estrategias de Trading Personales
Estoy tomando un curso de bolsa y day trading. Conforme aprenda
nuevas estrategias las voy a documentar aquí para que el sistema
las use como base para sus recomendaciones.

### Cómo agregar una estrategia nueva
Agregarla en `config/strategies.yaml` con:
- Nombre de la estrategia
- Condiciones de entrada (cuándo comprar)
- Condiciones de salida (cuándo vender)
- Activos donde aplica
- Timeframe (1min, 5min, 1hr, 1día)

### Objetivo
Que el dashboard muestre alertas y recomendaciones basadas
en MIS estrategias aprendidas, no en estrategias genéricas.

## Estado actual del proyecto
- Fase 1 en progreso — ingesta de datos funcionando
- 10 activos descargados en data/raw/ (se abandonó Yahoo Finance por bloqueos)
- Cripto (BTC/ETH/SOL): Binance, historial OHLCV completo desde 2017
- Forex (EURUSD/MXN/JPYMXN): Alpha Vantage full, historial largo (~años)
- Acciones/índices (AAPL/TSLA/SPY/QQQ): Alpha Vantage compact (~100 días)
- Pendiente: bajar historial largo de acciones/índices manualmente como CSV
- Siguiente paso: limpieza y transformación de datos (Fase 2)

## Notas técnicas
- Fuentes de datos: Binance (cripto, sin API key) + Alpha Vantage (lo demás)
- Alpha Vantage gratis: 25 llamadas/día, 1 req/seg. API key en .env como
  ALPHA_VANTAGE_KEY
- outputsize="full" es premium en acciones/índices (TIME_SERIES_DAILY) → usar
  "compact" (~100 días). Pero en forex (FX_DAILY) "full" SÍ es gratis y da
  historial largo, así que ahí sí se usa "full"
- Índices: Alpha Vantage no acepta notación Yahoo (^GSPC/^IXIC); se usan ETFs
  proxy: S&P 500 → SPY, NASDAQ → QQQ
- Forex: en notación Yahoo, símbolo de una sola moneda (MXN=X) tiene base USD
- time.sleep(5) entre descargas para respetar el límite de Alpha Vantage
- Columnas NO homogéneas entre fuentes: Binance da open/high/low/close/volume;
  Alpha Vantage da "1. open", "2. high", etc. Normalizarlas es el 1er paso de Fase 2
- Python 3.9 en venv. yfinance ya no se usa (reemplazado por Binance + Alpha Vantage)

## Curso en progreso
- Curso Capitaria de análisis técnico (5 videos)
- Notas en estrategias/capitaria/notas.md
- Estrategias se agregarán a config/strategies.yaml al terminar el curso