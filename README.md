# ldc-pulso

Datos del Pulso LDC (Laboratorio DeFi Crypto) y control de posiciones del LP System.
Dos módulos, dos cadencias, un solo repositorio:

| Módulo | Script | Cuándo corre | Salidas |
|---|---|---|---|
| Tablero de mercado | `ldc_tablero.py` | sábados 06:15 UTC (Actions) | `tablero.md`, `tablero.json`, `historico/AAAA-MM-DD.json` |
| Posiciones LP | `lp_posiciones.py` | diario 05:40 UTC (Actions) y tras el tablero | `posiciones.md`, `posiciones.json`, `dashboard.html` |

La tarea programada de Claude lee el repo los sábados (clonándolo) y redacta el pulso.
Solo librería estándar de Python. Sin claves, sin firma, sin nada que pueda mover fondos.

## Tablero

Precios, volatilidad realizada e implícita de BTC, régimen, anchura de rango y
break-even de un LP concentrado, TVL, derivados, stablecoins y escaneo de pools en
Orca, Raydium y Aerodrome. Solo datos públicos. No emite dirección.

Uso manual: `python3 ldc_tablero.py` (markdown por pantalla) o `python3 ldc_tablero.py --out .`.

## Posiciones LP

Lee **on-chain, por dirección pública**, las posiciones de liquidez concentrada
abiertas en Orca Whirlpools y Raydium CLMM (Solana) y Aerodrome Slipstream (Base,
incluidas las stakeadas en gauge), y calcula el protocolo de control del LP System:

- dentro / fuera de rango y distancia a cada borde, en % y en ATR diarios
  (ATR14 de BTC para pares BTC; σ diaria para estables)
- **stop**: cierre H4 de BTC fuera del rango (la regla del sistema: no por movimiento intrarrango)
- fees pendientes en tokens y USD, con el origen declarado (solo contabilizadas o
  también devengadas desde el último checkpoint)
- valor a precios actuales, composición
- con datos del tracker (`posiciones_manuales`): días abierta, IL frente a HODL,
  exposición al precio, earn (cobros + pendientes) y ratio earn/IL contra los
  umbrales del sistema (2,0 entrar / 2,5 reposicionar)
- veredicto vigente del pool en el tablero

Situaciones: `EN RANGO` · `ALERTA DE BORDE` (a menos de 1 ATR) · `FUERA DE RANGO` · `STOP`.

Configuración en `posiciones.config.json`: wallets (públicas), tokenIds extra de
Slipstream, pools de Aerodrome donde buscar posiciones stakeadas, datos manuales del
tracker, parámetros y direcciones de contratos. Con las listas vacías el módulo
escribe salidas vacías y no falla.

`dashboard.html` es autocontenido (datos incrustados): se abre en el navegador desde
el clon local tras `git pull`. No necesita servidor ni red.

Uso manual: `python3 lp_posiciones.py --out .` · pruebas sin red:
`python3 -m unittest tests/test_lp_posiciones.py`.

### Lo que el lector NO hace

- No estima: lo que no puede leer sale como `n/d`.
- No firma ni prepara transacciones. No hay claves en ningún sitio.
- En Solana, las fees devengadas desde el último checkpoint solo se calculan cuando el
  tick array tiene el tamaño fijo clásico; con tick arrays dinámicos de Orca se
  muestran solo las contabilizadas (`fee_owed`) y se declara.
- Los precios de tokens USD se suponen 1,00 (el peg se vigila en el tablero); BTC de
  Binance; EUR/USD del BCE vía Frankfurter. Tokens sin fuente: valor `n/d`.

## Automatización

GitHub Actions (`.github/workflows/tablero.yml` y `posiciones.yml`) ejecuta ambos
scripts y publica con el token del propio repo. También se pueden lanzar a mano
desde la pestaña Actions (`workflow_dispatch`).

El agente launchd del iMac (`com.arielsinagra.ldc-pulso.plist`, `publicar.sh`) queda
como respaldo manual. Registro en `~/Library/Logs/ldc-pulso.log`.

## Confidencialidad

Mientras contenga direcciones de wallet o posiciones, este repositorio debe ser
privado. El tablero de mercado no tiene nada privado; las posiciones sí.
