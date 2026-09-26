# TABLERO LDC — generado 2026-09-26T15:09:02+00:00 — última vela diaria cerrada: 2026-09-25

Comparado contra la ejecución del 2026-09-19T14:43:31+00:00.

## Mercado

| Métrica | Valor | Hace 7d | Δ |
|---|---|---|---|
| BTC | $84.100 | $80.884 | 3,98% |

## Volatilidad y régimen

| Métrica | Valor | Ejecución previa |
|---|---|---|
| Vol. realizada 7d (close-to-close) | 52,3% | |
| **Vol. realizada 30d (close-to-close)** | **43,0%** | 47,1% |
| Vol. realizada 30d (Parkinson) | 40,3% | 44,1% |
| Vol. realizada 90d | 39,0% | |
| Vol. implícita (DVOL) | 34,7% | 36,3% (hace 7d, Deribit) |
| Spread IV − RV30 | -8,3 pp | |
| Drift ratio 30d | 0,51 | 1,14 |

**RÉGIMEN: RANGO CON VOLUMEN** (previo: RANGO CON VOLUMEN)

Volatilidad realizada a 30 días del 43.0% anualizado y desplazamiento acumulado de 0.51 desviaciones. Régimen estructuralmente favorable para proveer liquidez concentrada.

*Parkinson usa el rango alto-bajo y es mejor estimador para un LP: el ingreso por comisiones depende del recorrido del precio dentro de la vela, no de dónde cierra.*

## Anchura de rango sugerida

Derivada de `b = σ·√τ` con σ = RV30 close-to-close. Semianchura para permanecer en rango el horizonte objetivo.

| Horizonte | Semianchura | Amplificación de comisiones **y** de LVR |
|---|---|---|
| 7 días | ±6,13% | 17,3x |
| 14 días | ±8,78% | 12,4x |
| 30 días | ±13,12% | 8,6x |
| 60 días | ±19,04% | 6,3x |
| 90 días | ±23,80% | 5,2x |

*Concentrar amplifica comisiones y pérdida por el mismo factor. La anchura no decide rentabilidad: decide tiempo en rango, coste de reposicionar y número de hechos imponibles.*

## Break-even: rotación anual mínima (volumen/TVL)

| Par y tier | Rotación mínima |
|---|---|
| BTC/USDC 5bp en Orca (87% al LP) | 53,1x |
| BTC/USDC 30bp en Orca (87% al LP) | 8,9x |
| BTC/USDC 25bp en Raydium (84% al LP) | 11,0x |
| Estables 1bp (σ supuesta 2.0%) | 0,57x |

## Derivados

Fuente: Deribit BTC-PERPETUAL (respaldo: Binance no accesible)

| Métrica | Valor |
|---|---|
| Funding actual (por periodo de 8h) | -0,0000% |
| Funding medio 7d (por periodo de 8h) | 0,0077% |
| Open interest | 883.546.980 USD |

## TVL de las plataformas

| Protocolo | TVL | Hace 7d | Δ |
|---|---|---|---|
| orca | $296,99M | $274,67M | 8,1% |
| raydium | $1,36B | $1,25B | 8,7% |
| aerodrome-slipstream | $230,49M | $217,27M | 6,1% |

## Stablecoins

| Cadena | Supply |
|---|---|
| Ethereum | $147,12B |
| Solana | $17,63B |
| Base | $5,11B |

| Stablecoin | Precio |
|---|---|
| usds | $0,9997 |
| tether | $0,9998 |
| usd-coin | $0,9999 |
| dai | $0,9999 |

# CANDIDATOS — dónde se puede actuar

**Estas cifras cubren solo el componente de market making (FEE − LVR). No incluyen la exposición al precio, que es dirección, no se estima, y domina la varianza del resultado.**

Alcance vigente: pares estables y BTC/USDC en Orca, Raydium y Aerodrome. TVL mínimo $250,00k. Posición de referencia $400. Fee APR calculado como rotación anual × fee × reparto al LP (Orca 87%, Raydium 84%, Aerodrome 100% si no está en gauge); σ de estables supuesta 2.0%. Rotación mínima = (σ²/8)/γ_efectiva, rango completo. El neto de cada ficha resta el LVR de la posición concentrada (amplificación × σ²/8) al fee APR medio del pool, sin amplificar este último: el fee APR del pool ya incorpora la concentración media de sus LPs.

Hueco conocido: el tamaño medio de swap, que distinguiría flujo de ruido de arbitraje, requiere número de transacciones y ninguna de estas fuentes lo expone. Rotación y estabilidad del APR son proxies imperfectos.

| Par | Plataforma | TVL | Fee | Rot. 7d anual | Rot. mínima | Ratio | Fee APR 7d | Fee APR 30d | Estab. 7d/30d | Dilución 7d | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURC/USDC | Aerodrome | $433,85k | 0,007% | 3.517x* | 0,7x | 4.923,3x | 24,62% | n/d | n/d | n/d | **Apto** |
| USDC/EURC | Orca | $489,41k | 0,010% | 1.290x | 0,6x | 2.244,2x | 11,22% | 9,00% | 1,25 | -62,7 pp | **Apto** |
| USDG/USDE | Orca | $2,51M | 0,010% | 841x | 0,6x | 1.463,6x | 7,32% | 4,43% | 1,65 | -104,8 pp | **Apto** |
| EURC/USDC | Aerodrome | $1,78M | 0,007% | 633x* | 0,7x | 924,7x | 4,62% | n/d | n/d | n/d | **Apto** |
| USDC/USDT | Orca | $718,89k | 0,010% | 470x | 0,6x | 817,9x | 4,09% | 3,18% | 1,29 | -67,9 pp | **Apto** |
| PYUSD/USDT | Raydium | $351,24k | 0,010% | 479x | 0,6x | 804,6x | 4,02% | 3,19% | 1,26 | -38,7 pp | **Apto** |
| TUSD/USDT | Raydium | $351,51k | 0,010% | 427x | 0,6x | 717,6x | 3,59% | 2,46% | 1,46 | -21,8 pp | **Apto** |
| USDC/USDT | Raydium | $1,60M | 0,010% | 385x | 0,6x | 646,1x | 3,23% | 2,40% | 1,34 | -5,5 pp | **Apto** |
| USDC/USDT | Aerodrome | $1,54M | 0,001% | 2.396x* | 5,6x | 431,2x | 2,16% | n/d | n/d | n/d | **Apto** |
| USDC/CBBTC | Aerodrome | $5,10M | 0,012% | 3.321x* | 190,9x | 17,4x | 40,19% | n/d | n/d | n/d | **Apto** |
| USDC/CBBTC | Aerodrome | $308,84k | 0,150% | 195x* | 15,4x | 12,7x | 29,24% | n/d | n/d | n/d | **Apto** |
| USDC/CBBTC | Aerodrome | $5,54M | 0,040% | 729x* | 57,7x | 12,6x | 29,16% | n/d | n/d | n/d | **Apto** |
| CBBTC/USDC | Orca | $5,62M | 0,040% | 828x | 66,4x | 12,5x | 28,80% | 32,12% | 0,90 | -17,8 pp | **Apto** |
| PYUSD/USDE | Orca | $2,16M | 0,010% | 910x | 0,6x | 1.584,1x | 7,92% | 3,34% | 2,37 | -273,8 pp | **Vigilar** |
| USDY/USDC | Orca | $1,73M | 0,160% | 9x | 0,0x | 253,1x | 1,27% | 0,57% | 2,21 | -236,9 pp | **Vigilar** |

\* Rotación implícita: DefiLlama no publica volumen 7d para ese pool; se obtiene invirtiendo su `apyBase7d` (fee APR = rotación × fee × reparto). Misma ventana, sin estimación. Sin volumen 30d, la estabilidad 7d/30d de esos pools queda n/d.

### EURC/USDC — Aerodrome (Base), fee 0,007%

- Fee APR real (LP): 7d 24,62% · 30d n/d · reward APR aparte 75,62%
- Rotación real vs mínima: 3.517x (implícita, de apyBase7d) vs 0,7x anual → ratio 4.923,3x (previa 2.841x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 23,7% → $95 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d n/d · 7d/30d n/d · cuota de la posición 0,0921% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 4923.3x la mínima, neto positivo y APR estable

### USDC/EURC — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 11,22% · 30d 9,00%
- Rotación real vs mínima: 1.290x vs 0,6x anual → ratio 2.244,2x (previa 809x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 10,3% → $41 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 0,39 · 7d/30d 1,25 · cuota de la posición 0,0817% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 2244.2x la mínima, neto positivo y APR estable

### USDG/USDE — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 7,32% · 30d 4,43%
- Rotación real vs mínima: 841x vs 0,6x anual → ratio 1.463,6x (previa 411x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 6,4% → $26 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 1,61 · 7d/30d 1,65 · cuota de la posición 0,0159% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 1463.6x la mínima, neto positivo y APR estable

### EURC/USDC — Aerodrome (Base), fee 0,007%

- Fee APR real (LP): 7d 4,62% · 30d n/d · reward APR aparte 3,19%
- Rotación real vs mínima: 633x (implícita, de apyBase7d) vs 0,7x anual → ratio 924,7x (previa 690x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 3,7% → $15 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d n/d · 7d/30d n/d · cuota de la posición 0,0225% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 924.7x la mínima, neto positivo y APR estable

### USDC/USDT — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 4,09% · 30d 3,18%
- Rotación real vs mínima: 470x vs 0,6x anual → ratio 817,9x (previa 277x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 3,2% → $13 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 0,26 · 7d/30d 1,29 · cuota de la posición 0,0556% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 817.9x la mínima, neto positivo y APR estable

### Cambios respecto a la ejecución previa

- Entran: USDC/USDT Orca -> Apto
- Entran: PYUSD/USDT Raydium -> Apto
- Entran: TUSD/USDT Raydium -> Apto
- Entran: USDC/USDT Raydium -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: CBBTC/USDC Orca -> Apto
- Entran: PYUSD/USDE Orca -> Vigilar
- Entran: USDY/USDC Orca -> Vigilar
- Entran: PYUSD/USDG Orca -> Vigilar
- Entran: JUPUSD/USDC Orca -> Vigilar
- Entran: JUPUSD/USDC Raydium -> Vigilar
- Entran: USDG/USDC Orca -> Vigilar
- Entran: USD1/USDC Raydium -> Vigilar
- Entran: PYUSD/USDC Orca -> Vigilar
- Entran: WBTC/USDC Raydium -> Vigilar
- Entran: TBTC/USDC Aerodrome -> Vigilar
- Entran: USDC/CBBTC Aerodrome -> Vigilar

## Radar — fuera del alcance actual

Sin ficha ni veredicto. Para decidir si merece ampliar el alcance, no para actuar.

| Par | Plataforma | TVL | Fee | Rot. 7d anual | Fee APR 7d (LP) | Fee APR 30d | Por qué destaca |
|---|---|---|---|---|---|---|---|
| NVDAX/SI | Raydium | $496,86k | 1,250% | 3.262x | 3.424,7% | 799,1% | fee APR alto |
| WETH/USDC | Aerodrome | $257,85k | 2,000% | 1.387x* | 2.773,3% | n/d | fee APR alto |
| SOL/SHARTCOIN | Raydium | $340,07k | 2,500% | 1.089x | 2.287,1% | 533,7% | fee APR alto |
| GLDX/GP | Raydium | $254,17k | 1,250% | 2.077x | 2.181,3% | 988,4% | fee APR alto |
| GMEX/USDC | Orca | $310,83k | 0,650% | 2.423x | 1.370,5% | 482,2% | fee APR alto |
| ZEC/MASK | Raydium | $507,20k | 1,250% | 1.028x | 1.079,2% | 251,8% | fee APR alto |
| TRUST/USDC | Aerodrome | $290,18k | 0,040% | 26.729x* | 1.069,2% | n/d | fee APR alto |
| 🎒/BP | Raydium | $303,23k | 1,250% | 857x | 899,8% | 748,6% | fee APR alto |

\* Rotación implícita, invertida de `apyBase7d` de DefiLlama. Con fees muy bajos la inversión amplifica cualquier error de esa medida: cifra orientativa, sin veredicto.

## Fuentes que fallaron

- https://fapi.binance.com/fapi/v1/premiumIndex -> HTTPError: HTTP Error 451: 

*Los datos afectados figuran como n/d. No se han estimado.*

## Fuentes

- OHLC BTC: https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=400
- DVOL: https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&resolution=43200
- Derivados: https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT (respaldo https://www.deribit.com/api/v2/public/ticker?instrument_name=BTC-PERPETUAL)
- TVL: https://api.llama.fi/protocol/orca · /raydium · /aerodrome-slipstream
- Pools Raydium: https://api-v3.raydium.io/pools/info/list?poolType=all&poolSortField=volume7d&sortType=desc&pageSize=100&page=1
- Pools Orca: https://api.orca.so/v2/solana/pools?sort=volume:desc
- Pools Aerodrome: https://yields.llama.fi/pools (project aerodrome-*)
- Stablecoins: https://stablecoins.llama.fi/stablecoinchains · https://stablecoins.llama.fi/stablecoinprices