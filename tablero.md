# TABLERO LDC — generado 2026-09-19T14:43:31+00:00 — última vela diaria cerrada: 2026-09-18

Comparado contra la ejecución del 2026-08-29T17:13:44+00:00.

## Mercado

| Métrica | Valor | Hace 7d | Δ |
|---|---|---|---|
| BTC | $80.884 | $77.226 | 4,74% |

## Volatilidad y régimen

| Métrica | Valor | Ejecución previa |
|---|---|---|
| Vol. realizada 7d (close-to-close) | 51,8% | |
| **Vol. realizada 30d (close-to-close)** | **47,1%** | 43,9% |
| Vol. realizada 30d (Parkinson) | 44,1% | 40,6% |
| Vol. realizada 90d | 37,9% | |
| Vol. implícita (DVOL) | 34,8% | 37,0% (hace 7d, Deribit) |
| Spread IV − RV30 | -12,2 pp | |
| Drift ratio 30d | 1,14 | 1,56 |

**RÉGIMEN: RANGO CON VOLUMEN** (previo: TENDENCIA DIRECCIONAL)

Volatilidad realizada a 30 días del 47.1% anualizado y desplazamiento acumulado de 1.14 desviaciones. Régimen estructuralmente favorable para proveer liquidez concentrada.

*Parkinson usa el rango alto-bajo y es mejor estimador para un LP: el ingreso por comisiones depende del recorrido del precio dentro de la vela, no de dónde cierra.*

## Anchura de rango sugerida

Derivada de `b = σ·√τ` con σ = RV30 close-to-close. Semianchura para permanecer en rango el horizonte objetivo.

| Horizonte | Semianchura | Amplificación de comisiones **y** de LVR |
|---|---|---|
| 7 días | ±6,73% | 15,9x |
| 14 días | ±9,65% | 11,4x |
| 30 días | ±14,44% | 7,9x |
| 60 días | ±21,02% | 5,8x |
| 90 días | ±26,32% | 4,8x |

*Concentrar amplifica comisiones y pérdida por el mismo factor. La anchura no decide rentabilidad: decide tiempo en rango, coste de reposicionar y número de hechos imponibles.*

## Break-even: rotación anual mínima (volumen/TVL)

| Par y tier | Rotación mínima |
|---|---|
| BTC/USDC 5bp en Orca (87% al LP) | 63,6x |
| BTC/USDC 30bp en Orca (87% al LP) | 10,6x |
| BTC/USDC 25bp en Raydium (84% al LP) | 13,2x |
| Estables 1bp (σ supuesta 2.0%) | 0,57x |

## Derivados

Fuente: Binance USDT-M BTCUSDT

| Métrica | Valor |
|---|---|
| Funding actual (por periodo de 8h) | 0,0100% |
| Funding medio 7d (por periodo de 8h) | 0,0063% |
| Open interest | 108.165 BTC |

## TVL de las plataformas

| Protocolo | TVL | Hace 7d | Δ |
|---|---|---|---|
| orca | $275,91M | $258,89M | 6,6% |
| raydium | $1,26B | $1,14B | 10,4% |
| aerodrome-slipstream | $218,48M | $203,95M | 7,1% |

## Stablecoins

| Cadena | Supply |
|---|---|
| Ethereum | $147,24B |
| Solana | $16,59B |
| Base | $5,09B |

| Stablecoin | Precio |
|---|---|
| usd-coin | $0,9997 |
| tether | $0,9996 |
| usds | $0,9999 |
| dai | $0,9998 |

# CANDIDATOS — dónde se puede actuar

**Estas cifras cubren solo el componente de market making (FEE − LVR). No incluyen la exposición al precio, que es dirección, no se estima, y domina la varianza del resultado.**

Alcance vigente: pares estables y BTC/USDC en Orca, Raydium y Aerodrome. TVL mínimo $250,00k. Posición de referencia $400. Fee APR calculado como rotación anual × fee × reparto al LP (Orca 87%, Raydium 84%, Aerodrome 100% si no está en gauge); σ de estables supuesta 2.0%. Rotación mínima = (σ²/8)/γ_efectiva, rango completo. El neto de cada ficha resta el LVR de la posición concentrada (amplificación × σ²/8) al fee APR medio del pool, sin amplificar este último: el fee APR del pool ya incorpora la concentración media de sus LPs.

Hueco conocido: el tamaño medio de swap, que distinguiría flujo de ruido de arbitraje, requiere número de transacciones y ninguna de estas fuentes lo expone. Rotación y estabilidad del APR son proxies imperfectos.

| Par | Plataforma | TVL | Fee | Rot. 7d anual | Rot. mínima | Ratio | Fee APR 7d | Fee APR 30d | Estab. 7d/30d | Dilución 7d | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURC/USDC | Aerodrome | $565,74k | 0,007% | 2.841x* | 0,7x | 3.976,8x | 19,88% | n/d | n/d | n/d | **Apto** |
| USDC/EURC | Orca | $464,18k | 0,010% | 809x | 0,6x | 1.407,0x | 7,04% | 8,60% | 0,82 | 38,3 pp | **Apto** |
| EURC/USDC | Aerodrome | $1,54M | 0,007% | 690x | 0,7x | 966,6x | 4,83% | n/d | n/d | n/d | **Apto** |
| USDC/USDT | Aerodrome | $821,39k | 0,001% | 4.490x | 5,6x | 808,2x | 4,04% | n/d | n/d | n/d | **Apto** |
| USDG/USDE | Orca | $2,50M | 0,010% | 411x | 0,6x | 715,8x | 3,58% | 2,62% | 1,37 | -98,1 pp | **Apto** |
| USDC/USDT | Raydium | $1,57M | 0,010% | 365x | 0,6x | 613,0x | 3,07% | 2,44% | 1,25 | -76,0 pp | **Apto** |
| TUSD/USDT | Raydium | $351,41k | 0,010% | 351x | 0,6x | 589,3x | 2,95% | 2,05% | 1,44 | -77,5 pp | **Apto** |
| PYUSD/USDT | Raydium | $351,11k | 0,010% | 345x | 0,6x | 580,1x | 2,90% | 2,74% | 1,06 | -16,9 pp | **Apto** |
| USDC/USDT | Orca | $738,71k | 0,010% | 277x | 0,6x | 481,8x | 2,41% | 3,31% | 0,73 | 14,2 pp | **Apto** |
| PYUSD/USDE | Orca | $2,15M | 0,010% | 244x | 0,6x | 424,8x | 2,12% | 1,35% | 1,57 | -178,5 pp | **Apto** |
| USDC/CBBTC | Aerodrome | $484,38k | 0,150% | 526x* | 18,4x | 28,5x | 78,84% | n/d | n/d | n/d | **Apto** |
| USDC/CBBTC | Aerodrome | $4,26M | 0,016% | 3.249x* | 169,8x | 19,1x | 52,95% | n/d | n/d | n/d | **Apto** |
| USDC/CBBTC | Aerodrome | $5,85M | 0,042% | 717x | 65,3x | 11,0x | 30,41% | n/d | n/d | n/d | **Apto** |
| CBBTC/USDC | Orca | $6,20M | 0,040% | 692x | 79,5x | 8,7x | 24,07% | 30,62% | 0,79 | 36,3 pp | **Apto** |
| USDS/USDC | Raydium | $1,26M | 0,010% | 63x | 0,6x | 106,1x | 0,53% | 0,72% | 0,74 | 53,4 pp | **Vigilar** |

\* Rotación implícita: DefiLlama no publica volumen 7d para ese pool; se obtiene invirtiendo su `apyBase7d` (fee APR = rotación × fee × reparto). Misma ventana, sin estimación. Sin volumen 30d, la estabilidad 7d/30d de esos pools queda n/d.

### EURC/USDC — Aerodrome (Base), fee 0,007%

- Fee APR real (LP): 7d 19,88% · 30d n/d · reward APR aparte 25,93%
- Rotación real vs mínima: 2.841x (implícita, de apyBase7d) vs 0,7x anual → ratio 3.976,8x (previa 2.814x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 19,0% → $76 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d n/d · 7d/30d n/d · cuota de la posición 0,0707% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 3976.8x la mínima, neto positivo y APR estable

### USDC/EURC — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 7,04% · 30d 8,60%
- Rotación real vs mínima: 809x vs 0,6x anual → ratio 1.407,0x (previa 1.168x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 6,2% → $25 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 1,02 · 7d/30d 0,82 · cuota de la posición 0,0861% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 1407.0x la mínima, neto positivo y APR estable

### EURC/USDC — Aerodrome (Base), fee 0,007%

- Fee APR real (LP): 7d 4,83% · 30d n/d · reward APR aparte 2,60%
- Rotación real vs mínima: 690x vs 0,7x anual → ratio 966,6x (previa 938x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 4,0% → $16 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 0,97 · 7d/30d n/d · cuota de la posición 0,0261% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 966.6x la mínima, neto positivo y APR estable

### USDC/USDT — Aerodrome (Base), fee 0,001%

- Fee APR real (LP): 7d 4,04% · 30d n/d · reward APR aparte 4,35%
- Rotación real vs mínima: 4.490x vs 5,6x anual → ratio 808,2x (previa 2.007x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 3,2% → $13 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 1,03 · 7d/30d n/d · cuota de la posición 0,0487% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 808.2x la mínima, neto positivo y APR estable

### USDG/USDE — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 3,58% · 30d 2,62%
- Rotación real vs mínima: 411x vs 0,6x anual → ratio 715,8x (previa 208x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 2,7% → $11 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 1,46 · 7d/30d 1,37 · cuota de la posición 0,0160% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 715.8x la mínima, neto positivo y APR estable

### Cambios respecto a la ejecución previa

- Entran: USDC/USDT Aerodrome -> Apto
- Entran: USDG/USDE Orca -> Apto
- Entran: USDC/USDT Raydium -> Apto
- Entran: TUSD/USDT Raydium -> Apto
- Entran: PYUSD/USDE Orca -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: CBBTC/USDC Orca -> Apto
- Entran: USDS/USDC Raydium -> Vigilar
- Entran: USD1/USDC Raydium -> Vigilar
- Entran: USDG/USDC Orca -> Vigilar
- Entran: USDY/USDC Orca -> Vigilar
- Entran: PYUSD/USDC Orca -> Vigilar
- Entran: JUPUSD/USDC Raydium -> Vigilar
- Entran: JUPUSD/USDC Orca -> Vigilar
- Entran: TBTC/USDC Aerodrome -> Vigilar
- Entran: USDC/CBBTC Aerodrome -> Vigilar
- Entran: WBTC/USDC Raydium -> Vigilar

## Radar — fuera del alcance actual

Sin ficha ni veredicto. Para decidir si merece ampliar el alcance, no para actuar.

| Par | Plataforma | TVL | Fee | Rot. 7d anual | Fee APR 7d (LP) | Fee APR 30d | Por qué destaca |
|---|---|---|---|---|---|---|---|
| WETH/USDC | Aerodrome | $256,09k | 2,000% | 1.312x* | 2.623,5% | n/d | fee APR alto |
| ALLINU/DKNG | Raydium | $435,67k | 1,250% | 1.822x | 1.913,0% | 734,3% | fee APR alto |
| PURR/HYPE | Raydium | $263,97k | 1,000% | 1.350x | 1.134,0% | 1.451,2% | fee APR alto |
| TRUST/USDC | Aerodrome | $283,25k | 0,085% | 12.657x* | 1.075,8% | n/d | fee APR alto |
| WBTC/BTC | Raydium | $332,87k | 1,000% | 992x | 833,4% | 821,2% | fee APR alto |
| NEAR/NEARKAT | Raydium | $439,42k | 1,250% | 775x | 813,7% | 451,6% | fee APR alto |
| USDC/ZCAT | Raydium | $276,62k | 0,400% | 2.388x | 802,5% | 318,0% | fee APR alto |
| HEV/LIT | Raydium | $272,93k | 1,000% | 932x | 783,0% | 234,6% | fee APR alto |

\* Rotación implícita, invertida de `apyBase7d` de DefiLlama. Con fees muy bajos la inversión amplifica cualquier error de esa medida: cifra orientativa, sin veredicto.

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