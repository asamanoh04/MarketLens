# Trades de expertos — Grupo WhatsApp Capitaria

## ¿Qué es esta carpeta?

Aquí se registran, a mano, las señales de trading que los expertos publican
en el grupo de WhatsApp de Capitaria. Cada señal se anota cuando llega y se
actualiza cuando el trade se resuelve (toca stop loss, toca take profit o
se cierra manualmente).

El archivo principal es [trades.yaml](trades.yaml).

## ¿Por qué son para validación y no para entrenamiento?

Un modelo de ML necesita miles de ejemplos para aprender patrones. Aquí van
a haber decenas, quizá algunos cientos con el tiempo. Entrenar con tan pocos
datos no produce un modelo, produce memorización: el modelo se aprende de
memoria esos casos y falla en todo lo demás.

Lo que sí valen estos trades es como **vara de medir**. Son operaciones
reales, hechas por humanos con experiencia, con resultado conocido. Sirven
para tres cosas:

1. **Votante adicional en la Capa 2.** La señal del experto entra al sistema
   de votación como una opinión más junto a la de los modelos.
2. **Fuente de ideas para features.** El campo `razon` dice qué miró el
   experto ("rompió resistencia con volumen", "RSI en sobreventa"). Eso es
   una lista de indicadores que vale la pena programar.
3. **Conjunto de prueba real.** Se puede preguntar: en esa fecha, con ese
   activo, ¿nuestros modelos habrían dado la misma señal? Si sí, buena
   señal. Si no, hay algo que el sistema no está viendo.

Es como aprender a cocinar: no aprendes viendo tres platos, pero sí puedes
usar esos tres platos para saber si lo que tú cocinaste quedó parecido.

## Cómo registrar un trade nuevo

1. Abrir [trades.yaml](trades.yaml).
2. Copiar el bloque completo del último trade (desde `- id:` hasta `notas:`).
3. Pegarlo al final de la lista.
4. Llenar los campos:

| Campo | Qué va |
|---|---|
| `id` | El siguiente número consecutivo |
| `fecha_senal` | Fecha en que llegó el mensaje, formato `AAAA-MM-DD` |
| `activo` | Símbolo tal como se usa en el proyecto: `EURUSD`, `BTC`, `SPY`… |
| `direccion` | `long` si es compra, `short` si es venta |
| `precio_entrada` | Precio al que el experto dice entrar |
| `stop_loss` | Precio donde se corta la pérdida |
| `take_profit` | Precio objetivo de ganancia |
| `ratio_riesgo_beneficio` | Se calcula, ver más abajo |
| `razon` | La justificación técnica, en tus palabras si el mensaje es largo |
| `mensaje_original` | El texto copy-paste del WhatsApp, tal cual llegó |
| `estado` | `abierto` al registrarlo (o `no_ejecutado` si decidiste no tomarlo) |
| `resultado` | `pendiente` al registrarlo |
| `fecha_cierre` | `null` al registrarlo |
| `notas` | `""` o cualquier observación tuya |

Al registrarlo el trade queda `estado: abierto` y `resultado: pendiente`.
No hay que tocar nada más hasta que se resuelva.

## Cómo cerrar un trade

Cuando el trade se resuelve, editar el bloque de ese `id` y cambiar tres
campos:

- `estado:` pasa de `abierto` a `cerrado`
- `resultado:` pasa de `pendiente` a `ganado`, `perdido` o `breakeven`
- `fecha_cierre:` pasa de `null` a la fecha real, formato `AAAA-MM-DD`

Ejemplo, antes:

```yaml
    estado: abierto
    resultado: pendiente
    fecha_cierre: null
    notas: ""
```

Después:

```yaml
    estado: cerrado
    resultado: ganado
    fecha_cierre: 2026-06-23
    notas: "Tocó take profit al tercer día"
```

Si el experto avisó la señal pero nunca se ejecutó (llegó tarde, el precio
se fue sin ti), el trade se marca `estado: no_ejecutado` y `resultado`
queda como lo que hubiera pasado, o `pendiente` si no se puede saber.
Igual sirve para validación: la señal existió aunque no se haya tomado.

## Cómo se calcula el ratio riesgo/beneficio

El ratio compara cuánto puedes ganar contra cuánto puedes perder. Para un
**long** (compra):

```
ratio = (take_profit - precio_entrada) / (precio_entrada - stop_loss)
```

Con los números del ejemplo:

```
(1.0910 - 1.0850) / (1.0850 - 1.0820) = 0.0060 / 0.0030 = 2
```

Se escribe como `"1:2"` — arriesgas 1 para ganar 2.

Para un **short** (venta) los papeles se invierten: la ganancia está abajo
y el stop arriba, así que la fórmula es

```
ratio = (precio_entrada - take_profit) / (stop_loss - precio_entrada)
```

Se guarda siempre como texto `"1:N"` para que se lea fácil. Si el número no
es redondo, se redondea a un decimal: `"1:1.5"`.

## Meta del sistema

Win rate mayor a 50% con ratio riesgo/beneficio 1:2. Con esa combinación,
ganar la mitad de las veces ya deja el sistema en positivo.
