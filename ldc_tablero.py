#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LDC — Tablero de datos y escaneo de pools para el Pulso semanal.

Solo librería estándar. Sin dependencias, sin API keys.
Todas las fuentes son públicas.

Uso:
    python3 ldc_tablero.py                  # markdown por stdout
    python3 ldc_tablero.py --json           # JSON por stdout
    python3 ldc_tablero.py --out DIR        # escribe DIR/tablero.md, DIR/tablero.json
                                            # y DIR/historico/AAAA-MM-DD.json; si existe
                                            # DIR/tablero.json previo, compara contra él

Regla de oro: si un dato no se puede obtener, se marca "n/d".
NUNCA se estima ni se inventa. Cada fuente que falla queda anotada.

Límite: este script describe régimen y mecánica. No emite dirección.
"""

import json
import math
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (compatible; LDC-tablero/2.0)"
TIMEOUT = 40
CTX = ssl.create_default_context()

ERRORES = []
NOTAS = []

# ─────────────────────────────────────────────────────────────
# PARÁMETROS DEL LP SYSTEM (calibrables)
# ─────────────────────────────────────────────────────────────

UMBRAL_DRIFT = 1.5        # por encima => tendencia direccional
UMBRAL_VOL_ALTA = 65.0    # RV30 anualizada en % por encima => alta volatilidad
POSICION_USD = 400.0      # tamaño de posición volátil del LP System
TVL_MINIMO = 250_000      # pools por debajo no se consideran
SIGMA_ESTABLES_PCT = 2.0  # sigma anual supuesta para par estable/estable
HORIZONTE_DIAS = 30       # horizonte de la ficha de candidato
RATIO_APTO = 2.0          # rotación real / mínima para "Apto"
RATIO_VIGILAR = 1.0       # rotación real / mínima para "Vigilar"

SPLIT_LP = {"Orca": 0.87, "Raydium": 0.84, "Aerodrome": 1.0}
# Aerodrome Slipstream: las comisiones van al LP salvo que la posición esté
# stakeada en gauge, en cuyo caso van a los votantes y el LP cobra AERO.

ESTABLES = {"USDC", "USDT", "USD1", "PYUSD", "USDS", "JUPUSD", "USDG", "USDE",
            "FDUSD", "DAI", "USDBC", "TUSD", "SUSD", "USDH", "CUSD", "AUSD",
            "USDY", "EURC", "USDP", "GHO", "LUSD"}
BTC_LIKE = {"BTC", "WBTC", "CBBTC", "ZBTC", "TBTC", "XBTC", "BTCB", "WBTC.E", "21BTC"}
USD_PARA_BTC = {"USDC", "USDT"}


def get(url, params=None):
    """GET JSON. Devuelve None y registra el error si falla."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        ERRORES.append(f"{url.split('?')[0]} -> {type(e).__name__}: {e}")
        return None


def fnum(x):
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def fmt(v, dec=2, suf="", pre=""):
    if v is None:
        return "n/d"
    try:
        return f"{pre}{v:,.{dec}f}{suf}".replace(",", "@").replace(".", ",").replace("@", ".")
    except Exception:
        return str(v)


def fmt_usd(v):
    if v is None:
        return "n/d"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if abs(v) >= div:
            return f"${v/div:.2f}{suf}".replace(".", ",")
    return f"${v:.0f}"


def pct_delta(actual, previo):
    if actual is None or previo is None or previo == 0:
        return None
    return (actual / previo - 1) * 100


def norm_sym(s):
    if not s:
        return ""
    s = s.upper().strip()
    if s in ("WSOL",):
        return "SOL"
    if s.startswith("$"):
        s = s[1:]
    return s


# ─────────────────────────────────────────────────────────────
# 1. OHLC DE BTC Y VOLATILIDAD REALIZADA
# ─────────────────────────────────────────────────────────────

def klines_btc(interval="1d", limit=400):
    """OHLC de Binance. Sin key. Fallback a api.binance.com."""
    for host in ("https://data-api.binance.vision", "https://api.binance.com"):
        d = get(f"{host}/api/v3/klines",
                {"symbol": "BTCUSDT", "interval": interval, "limit": limit})
        if d and isinstance(d, list) and len(d) > 10:
            velas = [{"t": int(k[0]), "o": float(k[1]), "h": float(k[2]),
                      "l": float(k[3]), "c": float(k[4]), "v": float(k[5])} for k in d]
            # La última vela es la del día en curso (incompleta): se descarta
            # para que la ventana cierre en el último día completo.
            ahora = int(datetime.now(timezone.utc).timestamp() * 1000)
            if velas and velas[-1]["t"] + 86_400_000 > ahora:
                velas = velas[:-1]
            return velas
    return None


def vol_close_to_close(velas, n):
    """Volatilidad realizada anualizada, estimador close-to-close."""
    if not velas or len(velas) < n + 1:
        return None
    cs = [v["c"] for v in velas[-(n + 1):]]
    rets = [math.log(cs[i] / cs[i - 1]) for i in range(1, len(cs))]
    m = sum(rets) / len(rets)
    var = sum((r - m) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(365) * 100


def vol_parkinson(velas, n):
    """Volatilidad realizada anualizada, estimador Parkinson (rango alto-bajo).

    Para un LP es mejor estimador que close-to-close: el ingreso por comisiones
    depende del recorrido del precio dentro de la vela, no de dónde cierra.
    """
    if not velas or len(velas) < n:
        return None
    sel = velas[-n:]
    s = sum(math.log(v["h"] / v["l"]) ** 2 for v in sel if v["l"] > 0)
    return math.sqrt(s / (4 * math.log(2) * len(sel))) * math.sqrt(365) * 100


def drift_ratio(velas, n=30):
    """|retorno acumulado| / (sigma * sqrt(t)). Alto = tendencia direccional."""
    if not velas or len(velas) < n + 1:
        return None
    cs = [v["c"] for v in velas[-(n + 1):]]
    ret = abs(math.log(cs[-1] / cs[0]))
    rets = [math.log(cs[i] / cs[i - 1]) for i in range(1, len(cs))]
    m = sum(rets) / len(rets)
    var = sum((r - m) ** 2 for r in rets) / (len(rets) - 1)
    sd = math.sqrt(var)
    return ret / (sd * math.sqrt(n)) if sd > 0 else None


# ─────────────────────────────────────────────────────────────
# 2. VOLATILIDAD IMPLÍCITA (DVOL de Deribit)
# ─────────────────────────────────────────────────────────────

def dvol_btc():
    ahora = int(datetime.now(timezone.utc).timestamp() * 1000)
    hace = ahora - 10 * 24 * 3600 * 1000
    d = get("https://www.deribit.com/api/v2/public/get_volatility_index_data",
            {"currency": "BTC", "start_timestamp": hace,
             "end_timestamp": ahora, "resolution": "43200"})
    try:
        velas = d["result"]["data"]
        return {"actual": float(velas[-1][4]),
                "hace_7d": float(velas[-15][4]) if len(velas) >= 15 else None}
    except Exception:
        return {"actual": None, "hace_7d": None}


# ─────────────────────────────────────────────────────────────
# 3. DERIVADOS: FUNDING Y OPEN INTEREST
# ─────────────────────────────────────────────────────────────

def funding_oi_btc():
    """Binance USDT-M como primera fuente; Deribit BTC-PERPETUAL como respaldo.

    Binance futures está geobloqueado (451) desde algunas regiones. Si cae,
    se usa Deribit y se declara: no es el mismo contrato ni el mismo mercado.
    """
    out = {"fuente": None, "funding_actual_pct": None,
           "funding_medio_7d_pct": None, "oi": None, "oi_unidad": None}
    pi = get("https://fapi.binance.com/fapi/v1/premiumIndex", {"symbol": "BTCUSDT"})
    if pi and "lastFundingRate" in pi:
        out["fuente"] = "Binance USDT-M BTCUSDT"
        out["funding_actual_pct"] = float(pi["lastFundingRate"]) * 100
        hist = get("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": "BTCUSDT", "limit": 21})  # 3/día * 7d
        if hist and isinstance(hist, list) and hist:
            rates = [float(h["fundingRate"]) for h in hist]
            out["funding_medio_7d_pct"] = sum(rates) / len(rates) * 100
        oi = get("https://fapi.binance.com/fapi/v1/openInterest", {"symbol": "BTCUSDT"})
        if oi and "openInterest" in oi:
            out["oi"] = float(oi["openInterest"])
            out["oi_unidad"] = "BTC"
        return out

    t = get("https://www.deribit.com/api/v2/public/ticker", {"instrument_name": "BTC-PERPETUAL"})
    try:
        r = t["result"]
        out["fuente"] = "Deribit BTC-PERPETUAL (respaldo: Binance no accesible)"
        out["funding_actual_pct"] = float(r["funding_8h"]) * 100
        out["oi"] = float(r["open_interest"])
        out["oi_unidad"] = "USD"
        ahora = int(datetime.now(timezone.utc).timestamp() * 1000)
        f7 = get("https://www.deribit.com/api/v2/public/get_funding_rate_value",
                 {"instrument_name": "BTC-PERPETUAL",
                  "start_timestamp": ahora - 7 * 86_400_000, "end_timestamp": ahora})
        if f7 and "result" in f7 and f7["result"] is not None:
            # acumulado 7d -> media por periodo de 8h
            out["funding_medio_7d_pct"] = float(f7["result"]) / 21 * 100
    except Exception:
        pass
    return out


# ─────────────────────────────────────────────────────────────
# 4. DEFILLAMA: TVL, STABLECOINS
# ─────────────────────────────────────────────────────────────

PROTOCOLOS = ["orca", "raydium", "aerodrome-slipstream"]


def tvl_protocolos():
    out = {}
    for slug in PROTOCOLOS:
        d = get(f"https://api.llama.fi/protocol/{slug}")
        if not d:
            out[slug] = {"tvl": None, "tvl_7d": None}
            continue
        serie = d.get("tvl") or []
        actual = serie[-1]["totalLiquidityUSD"] if serie else None
        previo = serie[-8]["totalLiquidityUSD"] if len(serie) >= 8 else None
        out[slug] = {"tvl": actual, "tvl_7d": previo}
    return out


def stablecoins_por_cadena():
    d = get("https://stablecoins.llama.fi/stablecoinchains")
    if not d:
        return {}
    out = {}
    for c in d:
        nombre = c.get("name") or c.get("gecko_id")
        if nombre in ("Solana", "Base", "Ethereum"):
            tc = c.get("totalCirculatingUSD") or {}
            out[nombre] = sum(v for v in tc.values() if isinstance(v, (int, float)))
    return out


def stablecoins_peg():
    """Precio de las stablecoins principales. Señal temprana de depeg."""
    d = get("https://stablecoins.llama.fi/stablecoinprices")
    if not d or not isinstance(d, list):
        return {}
    ultimo = d[-1].get("prices", {}) if d else {}
    return {k: v for k, v in ultimo.items() if k in ("usd-coin", "tether", "dai", "usds")}


# ─────────────────────────────────────────────────────────────
# 5. RÉGIMEN, ANCHURA, BREAK-EVEN
# ─────────────────────────────────────────────────────────────

def clasificar_regimen(rv30, drift):
    if rv30 is None or drift is None:
        return "n/d", "Faltan datos para clasificar el régimen."
    if drift > UMBRAL_DRIFT:
        return ("TENDENCIA DIRECCIONAL",
                f"El desplazamiento acumulado a 30 días es {drift:.2f} veces lo esperable "
                f"por volatilidad (umbral {UMBRAL_DRIFT}). Régimen desfavorable para LP: "
                f"la posición se convierte al activo que pierde y sale de rango con frecuencia.")
    if rv30 > UMBRAL_VOL_ALTA:
        return ("ALTA VOLATILIDAD SIN DIRECCIÓN",
                f"Volatilidad realizada a 30 días del {rv30:.1f}% anualizado, por encima del "
                f"umbral del {UMBRAL_VOL_ALTA}%, sin desplazamiento neto significativo "
                f"(drift {drift:.2f}). El peor régimen para LP: la pérdida contra arbitraje "
                f"escala con la varianza y los reposicionamientos se multiplican.")
    return ("RANGO CON VOLUMEN",
            f"Volatilidad realizada a 30 días del {rv30:.1f}% anualizado y desplazamiento "
            f"acumulado de {drift:.2f} desviaciones. Régimen estructuralmente favorable "
            f"para proveer liquidez concentrada.")


def semianchura(sigma_pct, dias):
    """b = sigma * sqrt(tau) (log). Devuelve (b, semianchura %, amplificación)."""
    if sigma_pct is None:
        return None, None, None
    sigma_d = (sigma_pct / 100) / math.sqrt(365)
    b = sigma_d * math.sqrt(dias)
    r = math.exp(2 * b)
    amp = 1 / (1 - r ** -0.5) if r > 1 else None
    return b, (math.exp(b) - 1) * 100, amp


def anchura_sugerida(rv30_pct):
    if rv30_pct is None:
        return []
    filas = []
    for dias in (7, 14, 30, 60, 90):
        _, sa, amp = semianchura(rv30_pct, dias)
        filas.append({"dias": dias, "semianchura_pct": sa, "amplificacion": amp})
    return filas


def lvr_anual(sigma_pct):
    """LVR anual sobre el valor de la posición = sigma^2 / 8 (Milionis et al.)."""
    if sigma_pct is None:
        return None
    return (sigma_pct / 100) ** 2 / 8


def break_even(rv_pct, fee_frac, split_lp=1.0):
    """Rotación anual mínima (volumen/TVL) para cubrir el LVR.

    LVR anual = sigma^2 / 8.   Ingreso = gamma_efectiva * (volumen/TVL).
    fee_frac en fracción (0.0004 = 4 bp).
    """
    if rv_pct is None or fee_frac is None:
        return None
    gamma = fee_frac * split_lp
    if gamma <= 0:
        return None
    return lvr_anual(rv_pct) / gamma


# ─────────────────────────────────────────────────────────────
# 6. ESCANEO DE POOLS: ORCA, RAYDIUM, AERODROME
# ─────────────────────────────────────────────────────────────

def _pool(plataforma, cadena, pid, a, b, fee, tvl, v24, v7, v30, fee_apr_api_7=None,
          fee_apr_api_30=None, reward_apr=None, extra=None):
    return {"plataforma": plataforma, "cadena": cadena, "id": pid,
            "par": f"{norm_sym(a)}/{norm_sym(b)}", "a": norm_sym(a), "b": norm_sym(b),
            "fee": fee, "tvl": tvl, "vol24": v24, "vol7": v7, "vol30": v30,
            "fee_apr_api_7": fee_apr_api_7, "fee_apr_api_30": fee_apr_api_30,
            "reward_apr": reward_apr, "extra": extra or {}}


def pools_raydium():
    """API v3 de Raydium, paginada. feeRate viene en fracción."""
    res = []
    for page in range(1, 15):
        d = get("https://api-v3.raydium.io/pools/info/list",
                {"poolType": "all", "poolSortField": "volume7d", "sortType": "desc",
                 "pageSize": 100, "page": page})
        try:
            data = d["data"]["data"]
        except Exception:
            break
        for p in data:
            tvl = fnum(p.get("tvl"))
            if tvl is None or tvl < TVL_MINIMO:
                continue
            wk, mo, dy = p.get("week") or {}, p.get("month") or {}, p.get("day") or {}
            fee_apr_w, apr_w = fnum(wk.get("feeApr")), fnum(wk.get("apr"))
            reward = (apr_w - fee_apr_w) if (apr_w is not None and fee_apr_w is not None) else None
            res.append(_pool("Raydium", "Solana", p.get("id"),
                             (p.get("mintA") or {}).get("symbol"), (p.get("mintB") or {}).get("symbol"),
                             fnum(p.get("feeRate")), tvl, fnum(dy.get("volume")),
                             fnum(wk.get("volume")), fnum(mo.get("volume")),
                             fee_apr_w, fnum(mo.get("feeApr")), reward,
                             {"tipo": p.get("type")}))
        if not d["data"].get("hasNextPage"):
            break
        # más allá de la página en la que el TVL ya no llega al mínimo, no merece seguir
        if data and all((fnum(p.get("tvl")) or 0) < TVL_MINIMO for p in data):
            break
    return res


def _orca_fee(v):
    v = fnum(v)
    if v is None:
        return None
    return v / 1_000_000 if v > 1 else v   # 400 -> 0.0004; ya en fracción si <= 1


def pools_orca():
    """API v2 de Orca (Whirlpools). Paginación por cursor si la expone."""
    res = []
    params = {"sort": "volume:desc", "size": 200}
    seen = set()
    for _ in range(20):
        d = get("https://api.orca.so/v2/solana/pools", params)
        try:
            data = d["data"]
        except Exception:
            break
        for p in data:
            addr = p.get("address")
            if addr in seen:
                continue
            seen.add(addr)
            tvl = fnum(p.get("tvlUsdc"))
            if tvl is None or tvl < TVL_MINIMO:
                continue
            st = p.get("stats") or {}
            s24, s7, s30 = st.get("24h") or {}, st.get("7d") or {}, st.get("30d") or {}
            res.append(_pool("Orca", "Solana", addr,
                             (p.get("tokenA") or {}).get("symbol"), (p.get("tokenB") or {}).get("symbol"),
                             _orca_fee(p.get("feeRate")), tvl,
                             fnum(s24.get("volume")), fnum(s7.get("volume")), fnum(s30.get("volume")),
                             None, None, None,
                             {"fees7": fnum(s7.get("fees")), "fees30": fnum(s30.get("fees")),
                              "yield7": fnum(s7.get("yieldOverTvl")), "yield30": fnum(s30.get("yieldOverTvl"))}))
        nxt = ((d.get("meta") or {}).get("cursor") or {}).get("next")
        if not nxt:
            break
        # La respuesta expone meta.cursor.next, pero el parámetro que la API acepta
        # para avanzar se llama "after": con "cursor" devuelve siempre la primera página.
        params = {"sort": "volume:desc", "size": 200, "after": nxt}
        if data and all((fnum(p.get("tvlUsdc")) or 0) < TVL_MINIMO for p in data):
            break
    return res


def _fee_de_poolmeta(meta):
    if not meta:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", str(meta))
    if m:
        return float(m.group(1)) / 100
    m = re.search(r"(\d+)\s*bps?", str(meta).lower())
    if m:
        return float(m.group(1)) / 10_000
    return None


def pools_aerodrome(llama_pools):
    """Aerodrome (Base) desde yields.llama.fi/pools, que no tiene API pública propia.

    apyBase = fee APR según DefiLlama; volumeUsd7d/tvlUsd = rotación 7d.
    No hay ventana de 30 días de volumen: se declara.
    """
    res = []
    if not llama_pools:
        return res
    for p in llama_pools:
        if not str(p.get("project", "")).startswith("aerodrome"):
            continue
        if p.get("chain") != "Base":
            continue
        tvl = fnum(p.get("tvlUsd"))
        if tvl is None or tvl < TVL_MINIMO:
            continue
        sym = (p.get("symbol") or "").split("-")
        a, b = (sym + ["", ""])[:2]
        res.append(_pool("Aerodrome", "Base", p.get("pool"), a, b,
                         _fee_de_poolmeta(p.get("poolMeta")), tvl,
                         fnum(p.get("volumeUsd1d")), fnum(p.get("volumeUsd7d")), None,
                         fnum(p.get("apyBase7d")), fnum(p.get("apyMean30d")), fnum(p.get("apyReward")),
                         {"apyBase": fnum(p.get("apyBase")), "poolMeta": p.get("poolMeta"),
                          "project": p.get("project")}))
    return res


def llama_pools_completo():
    d = get("https://yields.llama.fi/pools")
    if not d or "data" not in d:
        return None
    return d["data"]


def en_alcance(p):
    a, b = p["a"], p["b"]
    if a in ESTABLES and b in ESTABLES:
        return "estable"
    if (a in BTC_LIKE and b in USD_PARA_BTC) or (b in BTC_LIKE and a in USD_PARA_BTC):
        return "btc"
    return None


def enriquecer(p, rv30_pct, prev_por_id):
    """Cinco métricas del Bloque 3 + break-even + ficha."""
    tvl, v7, v30, v24 = p["tvl"], p["vol7"], p["vol30"], p["vol24"]
    split = SPLIT_LP.get(p["plataforma"], 1.0)
    fee = p["fee"]
    tipo = en_alcance(p)
    p["alcance"] = tipo
    sigma = SIGMA_ESTABLES_PCT if tipo == "estable" else rv30_pct

    # Rotación anualizada (volumen/TVL)
    p["rot7_anual"] = v7 / tvl * 365 / 7 if (v7 and tvl) else None
    p["rot30_anual"] = v30 / tvl * 365 / 30 if (v30 and tvl) else None

    # Fee APR del LP, calculado desde volumen (comparable entre plataformas)
    p["fee_apr_7"] = p["rot7_anual"] * fee * split * 100 if (p["rot7_anual"] is not None and fee) else None
    p["fee_apr_30"] = p["rot30_anual"] * fee * split * 100 if (p["rot30_anual"] is not None and fee) else None
    # Aerodrome no da fee ni vol30: se usa el apyBase de DefiLlama como fee APR
    if p["plataforma"] == "Aerodrome":
        if p["fee_apr_7"] is None:
            p["fee_apr_7"] = p["fee_apr_api_7"]
        if p["fee_apr_30"] is None:
            p["fee_apr_30"] = p["fee_apr_api_30"]

    # Tendencia de volumen: 24h*7 vs 7d, y 7d vs 30d*7/30
    p["tend_24h_vs_7d"] = (v24 * 7 / v7) if (v24 and v7) else None
    p["tend_7d_vs_30d"] = (v7 / (v30 * 7 / 30)) if (v7 and v30) else None

    # Estabilidad del fee APR: 7d / 30d
    p["estab_apr"] = (p["fee_apr_7"] / p["fee_apr_30"]) if (p["fee_apr_7"] and p["fee_apr_30"]) else None

    # Dilución de cuota: crecimiento TVL - crecimiento volumen 7d (contra ejecución previa)
    prev = prev_por_id.get(p["id"])
    p["dilucion_pp"] = None
    p["rot7_prev"] = None
    if prev:
        p["rot7_prev"] = prev.get("rot7_anual")
        if prev.get("tvl") and prev.get("vol7") and tvl and v7:
            p["dilucion_pp"] = ((tvl / prev["tvl"] - 1) - (v7 / prev["vol7"] - 1)) * 100

    # Profundidad frente a la posición
    p["cuota_pct"] = POSICION_USD / (tvl + POSICION_USD) * 100 if tvl else None

    # Break-even y ratio
    p["rot_min"] = break_even(sigma, fee, split) if fee else None
    p["ratio_be"] = (p["rot7_anual"] / p["rot_min"]) if (p["rot7_anual"] and p["rot_min"]) else None

    # Ficha: anchura para el horizonte, amplificación, neto de market making
    _, sa, amp = semianchura(sigma, HORIZONTE_DIAS)
    p["semianchura_pct"] = sa
    p["amplificacion"] = amp
    p["horizonte_dias"] = HORIZONTE_DIAS
    # Neto de market making = fee APR medio del pool − LVR de la posición concentrada.
    # El fee APR del pool (fees/TVL) ya recoge la concentración media de sus LPs, así que
    # NO se multiplica por la amplificación: hacerlo contaría dos veces. El LVR sí escala
    # con la densidad de la posición propia: amp × σ²/8. Supuesto declarado: la posición
    # está tan concentrada como el LP medio del pool; si está más, sube fee y LVR a la vez.
    lvr = lvr_anual(sigma)
    p["lvr_full_range_pct"] = lvr * 100 if lvr is not None else None
    p["lvr_posicion_pct"] = lvr * amp * 100 if (lvr is not None and amp) else None
    if p["fee_apr_7"] is not None and p["lvr_posicion_pct"] is not None:
        neto = p["fee_apr_7"] - p["lvr_posicion_pct"]
        p["neto_mm_anual_pct"] = neto
        p["neto_mm_anual_usd"] = neto / 100 * POSICION_USD
    else:
        p["neto_mm_anual_pct"] = None
        p["neto_mm_anual_usd"] = None
    # Cadencia: revisar cada ~horizonte/6 días; alerta al 70% de la semianchura
    p["revision_dias"] = max(1, round(HORIZONTE_DIAS / 6))
    p["alerta_borde_pct"] = sa * 0.7 if sa else None

    # Veredicto (solo componente de market making; el régimen condiciona aparte)
    r = p["ratio_be"]
    neto = p["neto_mm_anual_pct"]
    estable = p["estab_apr"] is None or 0.5 <= p["estab_apr"] <= 2.0
    if r is None:
        p["veredicto"], p["motivo"] = "Descartado", "sin rotación o sin fee: no comparable"
    elif r < RATIO_VIGILAR:
        p["veredicto"], p["motivo"] = "Descartado", f"rotación {r:.1f}x la mínima: no cubre ni el LVR de rango completo"
    elif neto is not None and neto <= 0:
        p["veredicto"], p["motivo"] = "Vigilar", f"rotación {r:.1f}x la mínima pero el LVR de la posición concentrada ({p['lvr_posicion_pct']:.1f}%) supera el fee APR"
    elif r >= RATIO_APTO and estable:
        p["veredicto"], p["motivo"] = "Apto", f"rotación {r:.1f}x la mínima, neto positivo y APR estable"
    elif r >= RATIO_APTO:
        p["veredicto"], p["motivo"] = "Vigilar", f"rotación {r:.1f}x la mínima pero APR errático (7d/30d = {p['estab_apr']:.2f})"
    else:
        p["veredicto"], p["motivo"] = "Vigilar", f"rotación {r:.1f}x la mínima: cubre LVR sin margen"
    return p


def escanear_pools(rv30_pct, prev_por_id):
    llama = llama_pools_completo()
    todos = pools_raydium() + pools_orca() + pools_aerodrome(llama)
    if llama is None:
        NOTAS.append("Aerodrome sin datos: yields.llama.fi/pools no accesible.")
    for p in todos:
        enriquecer(p, rv30_pct, prev_por_id)
    dentro = [p for p in todos if p["alcance"]]
    fuera = [p for p in todos if not p["alcance"]]
    orden = {"Apto": 0, "Vigilar": 1, "Descartado": 2}
    dentro.sort(key=lambda p: (orden[p["veredicto"]], -(p["ratio_be"] or 0)))
    fuera = [p for p in fuera if p["fee_apr_7"] is not None]
    fuera.sort(key=lambda p: -(p["fee_apr_7"] or 0))
    radar = fuera[:8]
    return todos, dentro, radar


def cambios_vs_previo(dentro, prev_dentro):
    """Qué entra, qué sale, qué cambia de veredicto."""
    prev = {p["id"]: p for p in prev_dentro}
    act = {p["id"]: p for p in dentro}
    out = {"entran": [], "salen": [], "cambian": []}
    for pid, p in act.items():
        if pid not in prev:
            if p["veredicto"] != "Descartado":
                out["entran"].append(f"{p['par']} {p['plataforma']} -> {p['veredicto']}")
        elif prev[pid].get("veredicto") != p["veredicto"]:
            out["cambian"].append(f"{p['par']} {p['plataforma']}: {prev[pid].get('veredicto')} -> {p['veredicto']}")
    for pid, p in prev.items():
        if pid not in act and p.get("veredicto") != "Descartado":
            out["salen"].append(f"{p['par']} {p['plataforma']} (era {p.get('veredicto')})")
    return out


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def cargar_previo(out_dir):
    if not out_dir:
        return None
    ruta = os.path.join(out_dir, "tablero.json")
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        NOTAS.append(f"No se pudo leer el tablero previo: {e}")
        return None


def recolectar(previo=None):
    velas_d = klines_btc("1d", 400)
    precio = velas_d[-1]["c"] if velas_d else None
    precio_7d = velas_d[-8]["c"] if velas_d and len(velas_d) >= 8 else None
    fecha_cierre = (datetime.fromtimestamp(velas_d[-1]["t"] / 1000, timezone.utc).date().isoformat()
                    if velas_d else None)

    rv7_cc = vol_close_to_close(velas_d, 7)
    rv30_cc = vol_close_to_close(velas_d, 30)
    rv90_cc = vol_close_to_close(velas_d, 90)
    rv30_pk = vol_parkinson(velas_d, 30)
    drift = drift_ratio(velas_d, 30)

    iv = dvol_btc()
    spread_iv_rv = (iv["actual"] - rv30_cc) if (iv["actual"] and rv30_cc) else None

    regimen, justificacion = clasificar_regimen(rv30_cc, drift)

    prev_por_id = {}
    prev_dentro = []
    prev_vol = {}
    prev_regimen = None
    if previo:
        prev_por_id = {p["id"]: p for p in previo.get("pools_todos", []) if p.get("id")}
        prev_dentro = previo.get("candidatos", [])
        prev_vol = previo.get("volatilidad", {})
        prev_regimen = (previo.get("regimen") or {}).get("estado")

    todos, dentro, radar = escanear_pools(rv30_cc, prev_por_id)

    return {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ultima_vela_cerrada": fecha_cierre,
        "previo_generado_utc": previo.get("generado_utc") if previo else None,
        "btc": {"precio": precio, "precio_7d": precio_7d, "var_7d_pct": pct_delta(precio, precio_7d)},
        "volatilidad": {
            "rv7_cc": rv7_cc, "rv30_cc": rv30_cc, "rv90_cc": rv90_cc,
            "rv30_parkinson": rv30_pk,
            "iv_dvol": iv["actual"], "iv_dvol_7d": iv["hace_7d"],
            "spread_iv_rv": spread_iv_rv,
            "drift_ratio_30d": drift,
        },
        "volatilidad_previa": {k: prev_vol.get(k) for k in ("rv30_cc", "rv30_parkinson", "drift_ratio_30d", "iv_dvol")},
        "regimen": {"estado": regimen, "justificacion": justificacion, "previo": prev_regimen,
                    "umbral_drift": UMBRAL_DRIFT, "umbral_vol_alta": UMBRAL_VOL_ALTA},
        "anchura_sugerida": anchura_sugerida(rv30_cc),
        "break_even": {
            "btc_5bp_orca": break_even(rv30_cc, 0.0005, 0.87),
            "btc_30bp_orca": break_even(rv30_cc, 0.0030, 0.87),
            "btc_25bp_raydium": break_even(rv30_cc, 0.0025, 0.84),
            "estables_1bp": break_even(SIGMA_ESTABLES_PCT, 0.0001, 0.87),
        },
        "derivados": funding_oi_btc(),
        "tvl": tvl_protocolos(),
        "stablecoins_cadena": stablecoins_por_cadena(),
        "stablecoins_peg": stablecoins_peg(),
        "candidatos": dentro[:5],
        "candidatos_todos": dentro,
        "radar": radar,
        "cambios": cambios_vs_previo(dentro, prev_dentro),
        "pools_todos": todos,
        "parametros": {"posicion_usd": POSICION_USD, "tvl_minimo": TVL_MINIMO,
                       "sigma_estables_pct": SIGMA_ESTABLES_PCT, "horizonte_dias": HORIZONTE_DIAS,
                       "ratio_apto": RATIO_APTO, "ratio_vigilar": RATIO_VIGILAR, "split_lp": SPLIT_LP},
        "notas": NOTAS,
        "errores": ERRORES,
    }


def _fila_pool(p):
    return (f"| {p['par']} | {p['plataforma']} | {fmt_usd(p['tvl'])} | {fmt((p['fee'] or 0)*100,3,'%') if p['fee'] else 'n/d'} | "
            f"{fmt(p['rot7_anual'],0,'x')} | {fmt(p['rot_min'],0,'x')} | {fmt(p['ratio_be'],1,'x')} | "
            f"{fmt(p['fee_apr_7'],2,'%')} | {fmt(p['fee_apr_30'],2,'%')} | {fmt(p['estab_apr'],2)} | "
            f"{fmt(p['dilucion_pp'],1,' pp')} | **{p['veredicto']}** |")


def markdown(d):
    L = []
    A = L.append
    A(f"# TABLERO LDC — generado {d['generado_utc']} — última vela diaria cerrada: {d['ultima_vela_cerrada'] or 'n/d'}")
    A("")
    if d["previo_generado_utc"]:
        A(f"Comparado contra la ejecución del {d['previo_generado_utc']}.")
    else:
        A("Sin ejecución previa: las columnas de comparación semanal de pools salen vacías.")
    A("")
    A("## Mercado")
    A("")
    A("| Métrica | Valor | Hace 7d | Δ |")
    A("|---|---|---|---|")
    b = d["btc"]
    A(f"| BTC | {fmt(b['precio'],0,pre='$')} | {fmt(b['precio_7d'],0,pre='$')} | {fmt(b['var_7d_pct'],2,suf='%')} |")
    A("")

    A("## Volatilidad y régimen")
    A("")
    v, vp = d["volatilidad"], d["volatilidad_previa"]
    A("| Métrica | Valor | Ejecución previa |")
    A("|---|---|---|")
    A(f"| Vol. realizada 7d (close-to-close) | {fmt(v['rv7_cc'],1,'%')} | |")
    A(f"| **Vol. realizada 30d (close-to-close)** | **{fmt(v['rv30_cc'],1,'%')}** | {fmt(vp.get('rv30_cc'),1,'%')} |")
    A(f"| Vol. realizada 30d (Parkinson) | {fmt(v['rv30_parkinson'],1,'%')} | {fmt(vp.get('rv30_parkinson'),1,'%')} |")
    A(f"| Vol. realizada 90d | {fmt(v['rv90_cc'],1,'%')} | |")
    A(f"| Vol. implícita (DVOL) | {fmt(v['iv_dvol'],1,'%')} | {fmt(v['iv_dvol_7d'],1,'%')} (hace 7d, Deribit) |")
    A(f"| Spread IV − RV30 | {fmt(v['spread_iv_rv'],1,' pp')} | |")
    A(f"| Drift ratio 30d | {fmt(v['drift_ratio_30d'],2)} | {fmt(vp.get('drift_ratio_30d'),2)} |")
    A("")
    r = d["regimen"]
    A(f"**RÉGIMEN: {r['estado']}**" + (f" (previo: {r['previo']})" if r["previo"] else ""))
    A("")
    A(r["justificacion"])
    A("")
    A("*Parkinson usa el rango alto-bajo y es mejor estimador para un LP: el ingreso por "
      "comisiones depende del recorrido del precio dentro de la vela, no de dónde cierra.*")
    A("")

    A("## Anchura de rango sugerida")
    A("")
    A("Derivada de `b = σ·√τ` con σ = RV30 close-to-close. Semianchura para permanecer en rango el horizonte objetivo.")
    A("")
    A("| Horizonte | Semianchura | Amplificación de comisiones **y** de LVR |")
    A("|---|---|---|")
    for f in d["anchura_sugerida"]:
        A(f"| {f['dias']} días | ±{fmt(f['semianchura_pct'],2,'%')} | {fmt(f['amplificacion'],1,'x')} |")
    A("")
    A("*Concentrar amplifica comisiones y pérdida por el mismo factor. La anchura no decide "
      "rentabilidad: decide tiempo en rango, coste de reposicionar y número de hechos imponibles.*")
    A("")

    A("## Break-even: rotación anual mínima (volumen/TVL)")
    A("")
    be = d["break_even"]
    A("| Par y tier | Rotación mínima |")
    A("|---|---|")
    A(f"| BTC/USDC 5bp en Orca (87% al LP) | {fmt(be['btc_5bp_orca'],1,'x')} |")
    A(f"| BTC/USDC 30bp en Orca (87% al LP) | {fmt(be['btc_30bp_orca'],1,'x')} |")
    A(f"| BTC/USDC 25bp en Raydium (84% al LP) | {fmt(be['btc_25bp_raydium'],1,'x')} |")
    A(f"| Estables 1bp (σ supuesta {SIGMA_ESTABLES_PCT}%) | {fmt(be['estables_1bp'],2,'x')} |")
    A("")

    A("## Derivados")
    A("")
    dv = d["derivados"]
    A(f"Fuente: {dv.get('fuente') or 'n/d'}")
    A("")
    A("| Métrica | Valor |")
    A("|---|---|")
    A(f"| Funding actual (por periodo de 8h) | {fmt(dv['funding_actual_pct'],4,'%')} |")
    A(f"| Funding medio 7d (por periodo de 8h) | {fmt(dv['funding_medio_7d_pct'],4,'%')} |")
    A(f"| Open interest | {fmt(dv['oi'],0,' '+(dv.get('oi_unidad') or ''))} |")
    A("")

    A("## TVL de las plataformas")
    A("")
    A("| Protocolo | TVL | Hace 7d | Δ |")
    A("|---|---|---|---|")
    for slug, t in d["tvl"].items():
        A(f"| {slug} | {fmt_usd(t['tvl'])} | {fmt_usd(t['tvl_7d'])} | {fmt(pct_delta(t['tvl'],t['tvl_7d']),1,'%')} |")
    A("")

    A("## Stablecoins")
    A("")
    A("| Cadena | Supply |")
    A("|---|---|")
    for c, val in d["stablecoins_cadena"].items():
        A(f"| {c} | {fmt_usd(val)} |")
    A("")
    peg = d["stablecoins_peg"]
    if peg:
        A("| Stablecoin | Precio |")
        A("|---|---|")
        for k, val in peg.items():
            A(f"| {k} | {fmt(val,4,pre='$')} |")
    A("")

    # ── BLOQUE 3 ──
    A("# CANDIDATOS — dónde se puede actuar")
    A("")
    A("**Estas cifras cubren solo el componente de market making (FEE − LVR). No incluyen la "
      "exposición al precio, que es dirección, no se estima, y domina la varianza del resultado.**")
    A("")
    if r["estado"] in ("TENDENCIA DIRECCIONAL", "ALTA VOLATILIDAD SIN DIRECCIÓN"):
        A(f"**Régimen vigente: {r['estado']}.** El cálculo de abajo es correcto y el terreno es malo: "
          "los veredictos describen el pool, no el momento.")
        A("")
    A(f"Alcance vigente: pares estables y BTC/USDC en Orca, Raydium y Aerodrome. TVL mínimo {fmt_usd(TVL_MINIMO)}. "
      f"Posición de referencia {fmt_usd(POSICION_USD)}. Fee APR calculado como rotación anual × fee × reparto al LP "
      f"(Orca 87%, Raydium 84%, Aerodrome 100% si no está en gauge); σ de estables supuesta {SIGMA_ESTABLES_PCT}%. "
      f"Rotación mínima = (σ²/8)/γ_efectiva, rango completo. El neto de cada ficha resta el LVR de la posición concentrada "
      f"(amplificación × σ²/8) al fee APR medio del pool, sin amplificar este último: el fee APR del pool ya incorpora "
      f"la concentración media de sus LPs.")
    A("")
    A("Hueco conocido: el tamaño medio de swap, que distinguiría flujo de ruido de arbitraje, requiere número de "
      "transacciones y ninguna de estas fuentes lo expone. Rotación y estabilidad del APR son proxies imperfectos.")
    A("")
    todos = d["candidatos_todos"]
    if not todos:
        A("**Esta semana no hay pool en alcance que pase el filtro de TVL.** Situación C del LP System: salida válida.")
    else:
        A("| Par | Plataforma | TVL | Fee | Rot. 7d anual | Rot. mínima | Ratio | Fee APR 7d | Fee APR 30d | Estab. 7d/30d | Dilución 7d | Veredicto |")
        A("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for p in todos[:15]:
            A(_fila_pool(p))
        A("")
        aptos = [p for p in todos if p["veredicto"] != "Descartado"]
        if not aptos:
            A("**Ningún pool en alcance cubre el break-even.** Situación C del LP System: salida válida, y es información.")
            A("")
        for p in d["candidatos"]:
            if p["veredicto"] == "Descartado":
                continue
            A(f"### {p['par']} — {p['plataforma']} ({p['cadena']}), fee {fmt((p['fee'] or 0)*100,3,'%') if p['fee'] else 'n/d'}")
            A("")
            A(f"- Fee APR real (LP): 7d {fmt(p['fee_apr_7'],2,'%')} · 30d {fmt(p['fee_apr_30'],2,'%')}"
              + (f" · reward APR aparte {fmt(p['reward_apr'],2,'%')}" if p.get("reward_apr") else ""))
            A(f"- Rotación real vs mínima: {fmt(p['rot7_anual'],0,'x')} vs {fmt(p['rot_min'],0,'x')} anual → ratio {fmt(p['ratio_be'],1,'x')}"
              + (f" (previa {fmt(p['rot7_prev'],0,'x')})" if p.get("rot7_prev") else ""))
            A(f"- Anchura sugerida a {p['horizonte_dias']} días: ±{fmt(p['semianchura_pct'],2,'%')} · amplificación {fmt(p['amplificacion'],1,'x')}")
            A(f"- LVR anual: rango completo {fmt(p['lvr_full_range_pct'],2,'%')} · posición a ±{fmt(p['semianchura_pct'],2,'%')} {fmt(p['lvr_posicion_pct'],2,'%')}")
            A(f"- Neto estimado de market making, anualizado: {fmt(p['neto_mm_anual_pct'],1,'%')} → {fmt(p['neto_mm_anual_usd'],0,pre='$')} sobre {fmt_usd(POSICION_USD)} "
              f"(fee APR medio del pool menos LVR de la posición; supone concentración igual a la media del pool)")
            A(f"- Tendencia de volumen: 24h/7d {fmt(p['tend_24h_vs_7d'],2)} · 7d/30d {fmt(p['tend_7d_vs_30d'],2)} · cuota de la posición {fmt(p['cuota_pct'],4,'%')} del pool")
            A(f"- Cadencia: revisar cada {p['revision_dias']} días; alerta al alejarse ±{fmt(p['alerta_borde_pct'],2,'%')} del centro (70% de la semianchura)")
            A(f"- **{p['veredicto']}** — {p['motivo']}")
            A("")
    c = d["cambios"]
    A("### Cambios respecto a la ejecución previa")
    A("")
    if not d["previo_generado_utc"]:
        A("Sin ejecución previa para comparar.")
    elif not (c["entran"] or c["salen"] or c["cambian"]):
        A("Sin cambios de veredicto en el universo en alcance.")
    else:
        for k, titulo in (("entran", "Entran"), ("salen", "Salen"), ("cambian", "Cambian")):
            for x in c[k]:
                A(f"- {titulo}: {x}")
    A("")

    A("## Radar — fuera del alcance actual")
    A("")
    A("Sin ficha ni veredicto. Para decidir si merece ampliar el alcance, no para actuar.")
    A("")
    if not d["radar"]:
        A("n/d")
    else:
        A("| Par | Plataforma | TVL | Fee | Rot. 7d anual | Fee APR 7d (LP) | Fee APR 30d | Por qué destaca |")
        A("|---|---|---|---|---|---|---|---|")
        for p in d["radar"]:
            por = "fee APR alto" if (p["fee_apr_7"] or 0) > 20 else "rotación alta"
            A(f"| {p['par']} | {p['plataforma']} | {fmt_usd(p['tvl'])} | {fmt((p['fee'] or 0)*100,3,'%') if p['fee'] else 'n/d'} | "
              f"{fmt(p['rot7_anual'],0,'x')} | {fmt(p['fee_apr_7'],1,'%')} | {fmt(p['fee_apr_30'],1,'%')} | {por} |")
    A("")

    if d["notas"]:
        A("## Notas")
        A("")
        for n in d["notas"]:
            A(f"- {n}")
        A("")
    A("## Fuentes que fallaron")
    A("")
    if d["errores"]:
        for e in d["errores"]:
            A(f"- {e}")
        A("")
        A("*Los datos afectados figuran como n/d. No se han estimado.*")
    else:
        A("Ninguna.")
    A("")
    A("## Fuentes")
    A("")
    A("- OHLC BTC: https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=400")
    A("- DVOL: https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&resolution=43200")
    A("- Derivados: https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT (respaldo https://www.deribit.com/api/v2/public/ticker?instrument_name=BTC-PERPETUAL)")
    A("- TVL: https://api.llama.fi/protocol/orca · /raydium · /aerodrome-slipstream")
    A("- Pools Raydium: https://api-v3.raydium.io/pools/info/list?poolType=all&poolSortField=volume7d&sortType=desc&pageSize=100&page=1")
    A("- Pools Orca: https://api.orca.so/v2/solana/pools?sort=volume:desc")
    A("- Pools Aerodrome: https://yields.llama.fi/pools (project aerodrome-*)")
    A("- Stablecoins: https://stablecoins.llama.fi/stablecoinchains · https://stablecoins.llama.fi/stablecoinprices")
    return "\n".join(L)


def main(argv):
    out_dir = None
    if "--out" in argv:
        out_dir = argv[argv.index("--out") + 1]
    previo = cargar_previo(out_dir)
    datos = recolectar(previo)
    if out_dir:
        os.makedirs(os.path.join(out_dir, "historico"), exist_ok=True)
        fecha = datos["ultima_vela_cerrada"] or datetime.now(timezone.utc).date().isoformat()
        with open(os.path.join(out_dir, "tablero.json"), "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=1, ensure_ascii=False)
        with open(os.path.join(out_dir, "historico", f"{fecha}.json"), "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=1, ensure_ascii=False)
        with open(os.path.join(out_dir, "tablero.md"), "w", encoding="utf-8") as f:
            f.write(markdown(datos))
        print(f"Escrito {out_dir}/tablero.md, tablero.json, historico/{fecha}.json")
        print(f"Errores de fuente: {len(ERRORES)}")
        for e in ERRORES:
            print("  -", e)
        return
    if "--json" in argv:
        print(json.dumps(datos, indent=2, ensure_ascii=False))
    else:
        print(markdown(datos))


if __name__ == "__main__":
    main(sys.argv[1:])
