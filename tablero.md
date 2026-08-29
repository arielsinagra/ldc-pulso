# TABLERO LDC — generado 2026-08-29T17:05:35+00:00 — última vela diaria cerrada: 2026-08-28

Comparado contra la ejecución del 2026-08-29T16:30:55+00:00.

## Mercado

| Métrica | Valor | Hace 7d | Δ |
|---|---|---|---|
| BTC | $77.846 | $78.338 | -0,63% |

## Volatilidad y régimen

| Métrica | Valor | Ejecución previa |
|---|---|---|
| Vol. realizada 7d (close-to-close) | 33,3% | |
| **Vol. realizada 30d (close-to-close)** | **43,9%** | 43,9% |
| Vol. realizada 30d (Parkinson) | 40,6% | 40,6% |
| Vol. realizada 90d | 41,0% | |
| Vol. implícita (DVOL) | 37,5% | 42,3% (hace 7d, Deribit) |
| Spread IV − RV30 | -6,4 pp | |
| Drift ratio 30d | 1,56 | 1,56 |

**RÉGIMEN: TENDENCIA DIRECCIONAL** (previo: TENDENCIA DIRECCIONAL)

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
| Open interest | 107.758 BTC |

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
| usds | $1,0000 |
| dai | $1,0001 |
| usd-coin | $1,0000 |
| tether | $1,0000 |

# CANDIDATOS — dónde se puede actuar

**Estas cifras cubren solo el componente de market making (FEE − LVR). No incluyen la exposición al precio, que es dirección, no se estima, y domina la varianza del resultado.**

**Régimen vigente: TENDENCIA DIRECCIONAL.** El cálculo de abajo es correcto y el terreno es malo: los veredictos describen el pool, no el momento.

Alcance vigente: pares estables y BTC/USDC en Orca, Raydium y Aerodrome. TVL mínimo $250,00k. Posición de referencia $400. Fee APR calculado como rotación anual × fee × reparto al LP (Orca 87%, Raydium 84%, Aerodrome 100% si no está en gauge); σ de estables supuesta 2.0%. Rotación mínima = (σ²/8)/γ_efectiva, rango completo. El neto de cada ficha resta el LVR de la posición concentrada (amplificación × σ²/8) al fee APR medio del pool, sin amplificar este último: el fee APR del pool ya incorpora la concentración media de sus LPs.

Hueco conocido: el tamaño medio de swap, que distinguiría flujo de ruido de arbitraje, requiere número de transacciones y ninguna de estas fuentes lo expone. Rotación y estabilidad del APR son proxies imperfectos.

| Par | Plataforma | TVL | Fee | Rot. 7d anual | Rot. mínima | Ratio | Fee APR 7d | Fee APR 30d | Estab. 7d/30d | Dilución 7d | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURC/USDC | Aerodrome | $775,11k | 0,007% | 2.814x* | 0,7x | 3.940,2x | 19,70% | n/d | n/d | n/d | **Apto** |
| USDC/EURC | Orca | $373,25k | 0,010% | 1.168x | 0,6x | 2.032,6x | 10,16% | 9,97% | 1,02 | 0,3 pp | **Apto** |
| EURC/USDC | Aerodrome | $1,92M | 0,007% | 938x* | 0,7x | 1.313,2x | 6,57% | n/d | n/d | n/d | **Apto** |
| USDC/USDT | Orca | $1,16M | 0,010% | 356x | 0,6x | 620,0x | 3,10% | 2,83% | 1,10 | 0,0 pp | **Apto** |
| PYUSD/USDT | Raydium | $350,44k | 0,010% | 296x | 0,6x | 496,6x | 2,48% | 1,71% | 1,46 | 0,2 pp | **Apto** |
| USDG/USDE | Orca | $2,50M | 0,010% | 208x | 0,6x | 361,7x | 1,81% | 2,60% | 0,70 | -0,8 pp | **Apto** |
| USDC/USDT | Aerodrome | $1,15M | 0,001% | 2.007x* | 5,6x | 361,3x | 1,81% | n/d | n/d | n/d | **Apto** |
| TUSD/USDT | Raydium | $350,87k | 0,010% | 198x | 0,6x | 332,5x | 1,66% | 1,28% | 1,30 | 0,3 pp | **Apto** |
| USDS/USDC | Raydium | $1,43M | 0,010% | 160x | 0,6x | 269,4x | 1,35% | 0,72% | 1,88 | 0,6 pp | **Apto** |
| USDC/USDT | Raydium | $3,70M | 0,010% | 131x | 0,6x | 219,5x | 1,10% | 1,36% | 0,81 | 0,3 pp | **Apto** |
| USDY/USDC | Orca | $2,92M | 0,160% | 7x | 0,0x | 191,5x | 0,96% | 0,56% | 1,71 | 0,0 pp | **Apto** |
| USD1/USDC | Raydium | $9,90M | 0,010% | 112x | 0,6x | 187,4x | 0,94% | 0,60% | 1,56 | 0,4 pp | **Apto** |
| JUPUSD/USDC | Raydium | $3,89M | 0,010% | 110x | 0,6x | 184,3x | 0,92% | 0,69% | 1,34 | -1,1 pp | **Apto** |
| USDC/CBBTC | Aerodrome | $4,17M | 0,012% | 5.584x* | 207,8x | 26,9x | 64,77% | n/d | n/d | n/d | **Apto** |
| USDC/CBBTC | Aerodrome | $5,81M | 0,024% | 2.089x* | 102,1x | 20,5x | 49,30% | n/d | n/d | n/d | **Apto** |

\* Rotación implícita: DefiLlama no publica volumen 7d para ese pool; se obtiene invirtiendo su `apyBase7d` (fee APR = rotación × fee × reparto). Misma ventana, sin estimación. Sin volumen 30d, la estabilidad 7d/30d de esos pools queda n/d.

### EURC/USDC — Aerodrome (Base), fee 0,007%

- Fee APR real (LP): 7d 19,70% · 30d n/d · reward APR aparte 7,55%
- Rotación real vs mínima: 2.814x (implícita, de apyBase7d) vs 0,7x anual → ratio 3.940,2x
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 18,8% → $75 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d n/d · 7d/30d n/d · cuota de la posición 0,0516% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 3940.2x la mínima, neto positivo y APR estable

### USDC/EURC — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 10,16% · 30d 9,97%
- Rotación real vs mínima: 1.168x vs 0,6x anual → ratio 2.032,6x (previa 1.171x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 9,3% → $37 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 0,24 · 7d/30d 1,02 · cuota de la posición 0,1071% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 2032.6x la mínima, neto positivo y APR estable

### EURC/USDC — Aerodrome (Base), fee 0,007%

- Fee APR real (LP): 7d 6,57% · 30d n/d · reward APR aparte 2,17%
- Rotación real vs mínima: 938x (implícita, de apyBase7d) vs 0,7x anual → ratio 1.313,2x
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 5,7% → $23 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d n/d · 7d/30d n/d · cuota de la posición 0,0208% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 1313.2x la mínima, neto positivo y APR estable

### USDC/USDT — Orca (Solana), fee 0,010%

- Fee APR real (LP): 7d 3,10% · 30d 2,83%
- Rotación real vs mínima: 356x vs 0,6x anual → ratio 620,0x (previa 356x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 2,2% → $9 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 0,78 · 7d/30d 1,10 · cuota de la posición 0,0345% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 620.0x la mínima, neto positivo y APR estable

### PYUSD/USDT — Raydium (Solana), fee 0,010%

- Fee APR real (LP): 7d 2,48% · 30d 1,71%
- Rotación real vs mínima: 296x vs 0,6x anual → ratio 496,6x (previa 296x)
- Anchura sugerida a 30 días: ±0,58% · amplificación 174,9x
- LVR anual: rango completo 0,01% · posición a ±0,58% 0,87%
- Neto estimado de market making, anualizado: 1,6% → $6 sobre $400 (fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)
- Tendencia de volumen: 24h/7d 2,41 · 7d/30d 1,46 · cuota de la posición 0,1140% del pool
- Cadencia: revisar cada 5 días; alerta al alejarse ±0,40% del centro (70% de la semianchura)
- **Apto** — rotación 496.6x la mínima, neto positivo y APR estable

### Cambios respecto a la ejecución previa

- Entran: EURC/USDC Aerodrome -> Apto
- Entran: EURC/USDC Aerodrome -> Apto
- Entran: USDC/USDT Aerodrome -> Apto
- Entran: USDS/USDC Raydium -> Apto
- Entran: USDC/USDT Raydium -> Apto
- Entran: USDY/USDC Orca -> Apto
- Entran: USD1/USDC Raydium -> Apto
- Entran: JUPUSD/USDC Raydium -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: CBBTC/USDC Orca -> Apto
- Entran: USDC/CBBTC Aerodrome -> Apto
- Entran: JUPUSD/USDC Orca -> Vigilar
- Entran: PYUSD/USDE Orca -> Vigilar
- Entran: USDG/USDC Orca -> Vigilar
- Entran: PYUSD/USDC Orca -> Vigilar
- Entran: TBTC/USDC Aerodrome -> Vigilar
- Entran: USDC/CBBTC Aerodrome -> Vigilar

## Radar — fuera del alcance actual

Sin ficha ni veredicto. Para decidir si merece ampliar el alcance, no para actuar.

| Par | Plataforma | TVL | Fee | Rot. 7d anual | Fee APR 7d (LP) | Fee APR 30d | Por qué destaca |
|---|---|---|---|---|---|---|---|
| SOL/CYBERLEEK | Raydium | $512,30k | 0,250% | 9.440x | 1.982,4% | 607,5% | fee APR alto |
| USDC/LMTS | Aerodrome | $268,42k | 0,050% | 26.727x | 1.336,4% | n/d | fee APR alto |
| TRUST/USDC | Aerodrome | $257,17k | 0,020% | 53.818x | 1.076,4% | n/d | fee APR alto |
| WETH/AERO | Aerodrome | $1,33M | 0,300% | 2.076x | 622,8% | n/d | fee APR alto |
| ALIGN/USDC | Aerodrome | $262,95k | 1,000% | 505x | 504,9% | n/d | fee APR alto |
| USDC/HEEBOO | Raydium | $301,04k | 0,900% | 502x | 379,2% | 88,5% | fee APR alto |
| SOL/USDC | Aerodrome | $410,37k | 0,035% | 9.856x | 345,0% | n/d | fee APR alto |
| SOL/PUMP | Raydium | $1,23M | 0,100% | 3.998x | 335,8% | 199,2% | fee APR alto |

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