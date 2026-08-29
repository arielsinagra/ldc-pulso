# TABLERO LDC — generado 2026-08-29T16:29:01+00:00 — última vela diaria cerrada: 2026-08-28

Sin ejecución previa: las columnas de comparación semanal de pools salen vacías.

## Mercado

| Métrica | Valor | Hace 7d | Δ |
|---|---|---|---|
| BTC | $77.846 | $78.338 | -0,63% |

## Volatilidad y régimen

| Métrica | Valor | Ejecución previa |
|---|---|---|
| Vol. realizada 7d (close-to-close) | 33,3% | |
| **Vol. realizada 30d (close-to-close)** | **43,9%** | n/d |
| Vol. realizada 30d (Parkinson) | 40,6% | n/d |
| Vol. realizada 90d | 41,0% | |
| Vol. implícita (DVOL) | 37,5% | 42,3% (hace 7d, Deribit) |
| Spread IV − RV30 | -6,4 pp | |
| Drift ratio 30d | 1,56 | n/d |

**RÉGIMEN: TENDENCIA DIRECCIONAL**

El desplazamiento acumulado a 30 días es 1.56 veces lo esperable por volatilidad (umbral 1.5). Régimen desfavorable para LP: la posición se convierte al activo que pierde y sale de rango con frecuencia.

*Parkinson usa el rango alto-bajo y es mejor estimador para un LP: el ingreso por comisiones depende del recorrido del precio dentro de la vela, no de dónde cierra.*

## Anchura de rango sugerida

Derivada de `b = σ·√τ` con σ = RV30 close-to-close. Semianchura para permanecer en rango el horizonte objetivo.

| Horizonte | Semianchura | Amplificación de comisiones **y** de LVR |
|---|---|---|
| 7 días | ±6,27% | 17,0x |
| 14 días | ±8,98% | 12,1x |
| 30 días | ±13,41% | 8,5x |
| 60 días | ±19,49% | 6,1x |
| 90 días | ±24,36% | 5,1x |

*Concentrar amplifica comisiones y pérdida por el mismo factor. La anchura no decide rentabilidad: decide tiempo en rango, coste de reposicionar y número de hechos imponibles.*

## Break-even: rotación anual mínima (volumen/TVL)

| Par y tier | Rotación mínima |
|---|---|
| BTC/USDC 5bp en Orca (87% al LP) | 55,4x |
| BTC/USDC 30bp en Orca (87% al LP) | 9,2x |
| BTC/USDC 25bp en Raydium (84% al LP) | 11,5x |
| Estables 1bp (σ supuesta 2.0%) | 0,57x |

## Derivados

Fuente: Binance USDT-M BTCUSDT

| Métrica | Valor |
|---|---|
| Funding actual (por periodo de 8h) | 0,0100% |
| Funding medio 7d (por periodo de 8h) | 0,0086% |
| Open interest | 107.611 BTC |

## TVL de las plataformas

| Protocolo | TVL | Hace 7d | Δ |
|---|---|---|---|
| orca | $260,77M | $256,92M | 1,5% |
| raydium | $1,12B | $1,06B | 6,1% |
| aerodrome-slipstream | $186,79M | $131,68M | 41,8% |

## Stablecoins

| Cadena | Supply |
|---|---|
| Ethereum | $148,25B |
| Solana | $15,99B |
| Base | $5,01B |

| Stablecoin | Precio |
|---|---|
| usd-coin | $1,0000 |
| tether | $1,0000 |
| usds | $1,0000 |
| dai | $1,0000 |

# CANDIDATOS — dónde se puede actuar

**Estas cifras cubren solo el componente de market making (FEE − LVR). No incluyen la exposición al precio, que es dirección, no se estima, y domina la varianza del resultado.**

**Régimen vigente: TENDENCIA DIRECCIONAL.** El cálculo de abajo es correcto y el terreno es malo: los veredictos describen el pool, no el momento.

Alcance vigente: pares estables y BTC/USDC en Orca, Raydium y Aerodrome. TVL mínimo $250,00k. Posición de referencia $400. Fee APR calculado como rotación anual × fee × reparto al LP (Orca 87%, Raydium 84%, Aerodrome 100% si no está en gauge); σ de estables supuesta 2.0%. Rotación mínima = (σ²/8)/γ_efectiva, rango completo. El neto de cada ficha resta el LVR de la posición concentrada (amplificación × σ²/8) al fee APR medio del pool, sin amplificar este último: el fee APR del pool ya incorpora la concentración media de sus LPs.

Hueco conocido: el tamaño medio de swap, que distinguiría flujo de ruido de arbitraje, requiere número de transacciones y ninguna de estas fuentes lo expone. Rotación y estabilidad del APR son proxies imperfectos.

| Par | Plataforma | TVL | Fee | Rot. 7d anual | Rot. mínima | Ratio | Fee APR 7d | Fee APR 30d | Estab. 7d/30d | Dilución 7d | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| USDC/EURC | Orca | $373,31k | 0,010% | 1.171x | 1x | 2.038,2x | 10,19% | 10,00% | 1,02 | n/d | **Apto** |
| USDC/USDT | Orca | $1,16M | 0,010% | 356x | 1x | 620,2x | 3,10% | 2,83% | 1,10 | n/d | **Apto** |
| PYUSD/USDT | Raydium | $350,44k | 0,010% | 296x | 1x | 498,1x | 2,49% | 1,71% | 1,46 | n/d | **Apto** |
| USDG/USDE | Orca | $2,50M | 0,010% | 206x | 1x | 358,6x | 1,79% | 2,59% | 0,69 | n/d | **Apto** |
| TUSD/USDT | Raydium | $350,87k | 0,010% | 199x | 1x | 333,9x | 1,67% | 1,28% | 1,31 | n/d | **Apto** |
| USDS/USDC | Raydium | $1,43M | 0,010% | 162x | 1x | 271,5x | 1,36% | 0,72% | 1,90 | n/d | **Apto** |
| USDC/USDT | Raydium | $3,70M | 0,010% | 131x | 1x | 220,3x | 1,10% | 1,36% | 0,81 | n/d | **Apto** |
| USDY/USDC | Orca | $2,92M | 0,160% | 7x | 0x | 191,5x | 0,96% | 0,56% | 1,71 | n/d | **Apto** |
| USD1/USDC | Raydium | $9,90M | 0,010% | 112x | 1x | 188,4x | 0,94% | 0,60% | 1,57 | n/d | **Apto** |
| JUPUSD/USDC | Raydium | $3,89M | 0,010% | 109x | 1x | 182,4x | 0,91% | 0,68% | 1,33 | n/d | **Apto** |
| CBBTC/USDC | Orca | $5,98M | 0,040% | 1.065x | 69x | 15,4x | 37,07% | 24,80% | 1,50 | n/d | **Apto** |
| JUPUSD/USDC | Orca | $3,85M | 0,010% | 93x | 1x | 161,3x | 0,81% | 0,56% | 1,43 | n/d | **Vigilar** |
| PYUSD/USDE | Orca | $2,15M | 0,010% | 86x | 1x | 149,3x | 0,75% | 1,42% | 0,53 | n/d | **Vigilar** |
| USDG/USDC | Orca | $25,70M | 0,010% | 47x | 1x | 81,2x | 0,41% | 0,26% | 1,59 | n/d | **Vigilar** |
| PYUSD/USDC | Orca | $18,46M | 0,010% | 10x | 1x | 18,2x | 0,09% | 0,20% | 0,45 | n/d | **Vigilar** |

### USDC/EURC — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 10,19% · 30d 10,00%
- Rotación real vs mínima: 1.171x vs 1x anual → ratio 2.038,2x
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 9,3% → $37 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 0,25 · 7d/30d 1,02 · cuota de la posición 0,1070% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 2038.2x la mínima, neto positivo y APR estable

### USDC/USDT — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 3,10% · 30d 2,83%
- Rotación real vs mínima: 356x vs 1x anual → ratio 620,2x
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 2,2% → $9 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 1,21 · 7d/30d 1,10 · cuota de la posición 0,0345% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 620.2x la mínima, neto positivo y APR estable

### PYUSD/USDT — Raydium (Solana), fee 0,010%

- Fee APR real (LP): 7d 2,49% · 30d 1,71%
- Rotación real vs mínima: 296x vs 1x anual → ratio 498,1x
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 1,6% → $6 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 2,42 · 7d/30d 1,46 · cuota de la posición 0,1140% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 498.1x la mínima, neto positivo y APR estable

### USDG/USDE — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 1,79% · 30d 2,59%
- Rotación real vs mínima: 206x vs 1x anual → ratio 358,6x
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 0,9% → $4 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 2,17 · 7d/30d 0,69 · cuota de la posición 0,0160% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 358.6x la mínima, neto positivo y APR estable

### TUSD/USDT — Raydium (Solana), fee 0,010%

- Fee APR real (LP): 7d 1,67% · 30d 1,28%
- Rotación real vs mínima: 199x vs 1x anual → ratio 333,9x
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 0,8% → $3 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 1,23 · 7d/30d 1,31 · cuota de la posición 0,1139% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 333.9x la mínima, neto positivo y APR estable

### Cambios respecto a la ejecución previa

Sin ejecución previa para comparar.

## Radar — fuera del alcance actual

Sin ficha ni veredicto. Para decidir si merece ampliar el alcance, no para actuar.

| Par | Plataforma | TVL | Fee | Rot. 7d anual | Fee APR 7d (LP) | Fee APR 30d | Por qué destaca |
|---|---|---|---|---|---|---|---|
| SOL/CYBERLEEK | Raydium | $507,78k | 0,250% | 9.555x | 2.006,5% | 612,8% | fee APR alto |
| USDC/LMTS | Aerodrome | $268,42k | 0,050% | n/d | 1.336,4% | 24,3% | fee APR alto |
| TRUST/USDC | Aerodrome | $257,17k | 0,020% | n/d | 1.076,4% | 9,4% | fee APR alto |
| WETH/AERO | Aerodrome | $1,33M | 0,300% | n/d | 622,8% | 11,5% | fee APR alto |
| ALIGN/USDC | Aerodrome | $262,95k | 1,000% | n/d | 504,9% | 7.472,1% | fee APR alto |
| USDC/HEEBOO | Raydium | $301,16k | 0,900% | 498x | 376,5% | 87,9% | fee APR alto |
| SOL/USDC | Aerodrome | $410,37k | 0,035% | n/d | 345,0% | 1.553,0% | fee APR alto |
| SOL/PUMP | Raydium | $1,23M | 0,100% | 4.020x | 337,7% | 198,8% | fee APR alto |

## Fuentes que fallaron

Ninguna.

## Fuentes

- OHLC BTC: https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=400
- DVOL: https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&resolution=43200
- Derivados: https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT (respaldo https://www.deribit.com/api/v2/public/ticker?instrument_name=BTC-PERPETUAL)
- TVL: https://api.llama.fi/protocol/orca · /raydium · /aerodrome-slipstream
- Pools Raydium: https://api-v3.raydium.io/pools/info/list?poolType=all&poolSortField=volume7d&sortType=desc&pageSize=100&page=1
- Pools Orca: https://api.orca.so/v2/solana/pools?sort=volume:desc
- Pools Aerodrome: https://yields.llama.fi/pools (project aerodrome-*)
- Stablecoins: https://stablecoins.llama.fi/stablecoinchains · https://stablecoins.llama.fi/stablecoinprices