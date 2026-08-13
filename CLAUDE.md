# MarketLens — Contexto para Claude Code

## ¿Qué es este proyecto?
Pipeline completo de análisis de mercados financieros que cubre
cripto, forex, acciones e índices. Incluye ingesta de APIs,
limpieza de datos, EDA, minería de datos, ML predictivo y
dashboard interactivo.

## Arquitectura de inteligencia — Visión completa
MarketLens no es solo un predictor de precios. Es un sistema de análisis
de mercados financieros con tres capas de inteligencia que trabajan juntas:

**Capa 1 — Modelos de ML con features de análisis técnico**
Múltiples modelos entrenados con features derivados de análisis técnico:
soportes, resistencias, patrones de velas, indicadores cuantitativos.
Cada modelo ve el mercado desde una perspectiva estadística diferente.
Ningún modelo individual toma decisiones solo.

**Capa 2 — Sistema de votación con metamodelo**
Los modelos individuales votan. Un metamodelo aprende cuándo cada modelo
individual es más confiable según las condiciones del mercado. Por ejemplo:
modelo A es mejor en mercados trending, modelo B en mercados laterales.
El metamodelo decide a quién escuchar según el contexto actual.

**Capa 3 — Análisis independiente de Claude**
Claude analiza el mercado sin conocer las predicciones de los modelos
para evitar sesgos. Recibe datos crudos, noticias y contexto macro y da
su propia lectura. Solo al final se comparan ambas señales. Si Claude y
los modelos coinciden, la señal es fuerte. Si divergen, es señal de cautela.

**Capa transversal — Backtesting continuo**
Todo se valida contra datos históricos antes de usarse en tiempo real.
Las estrategias del curso se prueban estadísticamente. Los modelos se
evalúan en períodos que no vieron durante el entrenamiento.

**Principio de diseño:**
El sistema nunca dice "compra" o "vende" con certeza. Dice "bajo estas
condiciones históricas, esta configuración de señales ha resultado en X
con Y% de confianza". La decisión final siempre es humana.

## Stack tecnológico
- Lenguaje: Python 3.9 en venv
- Entorno: WSL2 Ubuntu 20.04 + VSCode
- Control de versiones: Git + GitHub (asamanoh04/MarketLens)

## Activos monitoreados
- Cripto: BTC, ETH, SOL
- Forex: EUR/USD, USD/MXN, USD/JPY
- Índices: SPY (S&P500), QQQ (NASDAQ)
- Acciones: AAPL, TSLA (expandible via config/assets.yaml)

## Estructura del proyecto
- `data/raw/` — datos crudos descargados de APIs, nunca modificar
- `data/processed/` — datos limpios y normalizados
- `src/` — código fuente principal
- `notebooks/` — análisis exploratorio (EDA)
- `dashboard/` — visualización interactiva con Plotly/Dash
- `models/` — modelos entrenados de ML
- `tests/` — pruebas unitarias
- `config/` — assets.yaml y strategies.yaml
- `estrategias/` — notas y PDFs de cursos de trading
- `docs/` — documentación de arquitectura y decisiones

## Fases del proyecto
1. Ingesta de datos via APIs ← COMPLETADA
2. Pipeline de limpieza y transformación ← EN CURSO
3. EDA y minería de datos
4. Feature engineering con estrategias del curso
5. Modelos de ML + sistema de votación + metamodelo
6. Backtesting de estrategias
7. Dashboard interactivo con Plotly/Dash

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
- Nunca modificar archivos en data/raw/

## Cómo agregar un activo nuevo
Solo agregarlo en `config/assets.yaml` con su símbolo y tipo.
El sistema lo detecta automáticamente.

## Estrategias de Trading Personales
Tomando curso Capitaria de análisis técnico (5 videos) y curso TJR.
Conforme se aprenden estrategias se documentan en:
- `estrategias/capitaria/notas.md`
- `estrategias/TJR/notas.md`

Las estrategias finales se agregan a `config/strategies.yaml` con:
- Nombre de la estrategia
- Condiciones de entrada (cuándo comprar)
- Condiciones de salida (cuándo vender)
- Activos donde aplica
- Timeframe (1min, 5min, 1hr, 1día)
- Fuente (de qué curso viene)

### Trades de expertos (WhatsApp Capitaria)
Registro en estrategias/capitaria/trades_whatsapp/trades.yaml.
Rol en la arquitectura: VALIDACIÓN, no entrenamiento (pocos datos).
Usos: (1) votante adicional en la Capa 2 de votación, (2) fuente de
ideas para features (la razón técnica de cada trade revela qué
indicadores programar), (3) conjunto de prueba real para medir si
nuestros modelos hubieran detectado los mismos trades.
Meta del sistema: win rate >50% con ratio riesgo/beneficio 1:2.

## Estado actual del proyecto
- Fase 1 COMPLETADA
- Cripto (BTC/ETH/SOL): Binance, OHLCV completo desde 2017
- Forex (EURUSD/USDMXN/USDJPY): Alpha Vantage full, historial largo
- Acciones/índices (AAPL/TSLA/SPY/QQQ): historial largo de Stooq (semilla
  manual, ya en data/raw/manual/) + días nuevos de Alpha Vantage compact
- Actualización incremental: correr `python src/ingesta.py` re-baja y hace
  merge por fecha (guardar_merge); se ejecuta manual cuando se quiera
- Siguiente paso: Fase 2 — limpieza y normalización de columnas

## Notas técnicas
- Fuentes: Binance (cripto, sin API key) + Alpha Vantage (lo demás)
- Alpha Vantage gratis: 25 llamadas/día. API key en .env como ALPHA_VANTAGE_KEY
- outputsize="full" gratis solo en forex. Acciones/índices usan Alpha Vantage
  "compact" (~100 días) SOLO para actualizar; el historial profundo viene de
  Stooq como semilla de una vez (ver data/raw/manual/README.md)
- guardar_merge() pega lo nuevo sobre lo que hay en disco, quita fechas
  duplicadas (gana el dato más reciente) y ordena de viejo a nuevo. Por eso
  re-correr ingesta.py es idempotente y nunca borra la historia profunda
- Presupuesto Alpha Vantage por corrida: 3 forex (full) + 4 acciones (compact)
  = 7 de 25 llamadas/día
- Índices: Alpha Vantage no acepta ^GSPC/^IXIC, se usan ETFs proxy SPY/QQQ
- Forex MXN=X significa USD/MXN y JPY=X significa USD/JPY (base USD para símbolos de una sola moneda)
- time.sleep(5) entre descargas para respetar límite de Alpha Vantage
- Columnas NO homogéneas entre fuentes, normalizar en Fase 2
- yfinance y pycoingecko eliminados, reemplazados por Binance + Alpha Vantage

## Contexto adicional
- Sin API de Anthropic por ahora
- Priorizar código legible sobre código óptimo
- Este proyecto es para aprender, no para producción