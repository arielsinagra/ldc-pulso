#!/usr/bin/env python3
"""
LP System — lector de posiciones de liquidez concentrada por dirección pública.

Lee on-chain, sin claves ni firma, las posiciones abiertas en:
  - Orca Whirlpools (Solana)
  - Raydium CLMM (Solana)
  - Aerodrome Slipstream (Base), incluidas las stakeadas en gauge

y calcula el protocolo de control de posición abierta del LP System:
dentro/fuera de rango, distancia a cada borde en ATR diarios, cierre H4 fuera
de rango (stop), fees pendientes, IL frente a HODL y ratio earn/IL contra los
umbrales del sistema. Escribe posiciones.json, posiciones.md y dashboard.html.

Solo librería estándar. Regla: si un dato no se puede obtener, `n/d`; nunca se
estima. No emite dirección.

Uso:  python3 lp_posiciones.py --out .        (lee posiciones.config.json)
      python3 lp_posiciones.py --config otro.json --out .
"""

import hashlib
import json
import math
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone, date

VERSION = "1.0"
UA = "Mozilla/5.0 (compatible; LDC-posiciones/1.0)"
TIMEOUT = 40
CTX = ssl.create_default_context()

ERRORES = []
NOTAS = []

# ─────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────

def http_json(url, payload=None, params=None):
    """GET/POST JSON. None y error registrado si falla."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = None
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        ERRORES.append(f"{url.split('?')[0]} -> {type(e).__name__}: {e}")
        return None


def fmt(v, dec=2, suf="", pre=""):
    if v is None:
        return "n/d"
    try:
        return f"{pre}{v:,.{dec}f}{suf}"
    except Exception:
        return str(v)


def fmt_usd(v):
    return fmt(v, 2, pre="$")


def dias_desde(fecha_iso):
    try:
        f = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
        if f.tzinfo is None:
            f = f.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - f).total_seconds() / 86400
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# BASE58 Y PDA (Solana), sin dependencias
# ─────────────────────────────────────────────────────────────

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + _B58.index(ch)
    out = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + out


def b58encode(b):
    n = int.from_bytes(b, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = _B58[r] + s
    pad = len(b) - len(b.lstrip(b"\x00"))
    return "1" * pad + s


# Curva ed25519: una PDA es válida si NO está en la curva.
_P = 2 ** 255 - 19
_D = (-121665 * pow(121666, _P - 2, _P)) % _P


def _en_curva(b32):
    y = int.from_bytes(b32, "little") & ((1 << 255) - 1)
    if y >= _P:
        return False
    y2 = (y * y) % _P
    u = (y2 - 1) % _P
    v = (_D * y2 + 1) % _P
    # x² = u/v ; existe si (u/v) es residuo cuadrático
    x2 = (u * pow(v, _P - 2, _P)) % _P
    if x2 == 0:
        return True
    return pow(x2, (_P - 1) // 2, _P) == 1


def find_program_address(seeds, program_id_b):
    """Equivalente a Pubkey.find_program_address. Devuelve (bytes32, bump)."""
    for bump in range(255, -1, -1):
        h = hashlib.sha256()
        for s in seeds:
            h.update(s)
        h.update(bytes([bump]))
        h.update(program_id_b)
        h.update(b"ProgramDerivedAddress")
        cand = h.digest()
        if not _en_curva(cand):
            return cand, bump
    raise ValueError("sin bump válido")


def u128(b, o):
    return int.from_bytes(b[o:o + 16], "little")


def u64(b, o):
    return int.from_bytes(b[o:o + 8], "little")


def i32(b, o):
    return int.from_bytes(b[o:o + 4], "little", signed=True)


def u16(b, o):
    return int.from_bytes(b[o:o + 2], "little")


def pk(b, o):
    return b58encode(b[o:o + 32])


# ─────────────────────────────────────────────────────────────
# MATEMÁTICA DE LIQUIDEZ CONCENTRADA (común a los tres protocolos)
# ─────────────────────────────────────────────────────────────

def sqrt_precio_tick(tick):
    return math.sqrt(1.0001 ** tick)


def cantidades(liquidez, sqrt_p, sqrt_a, sqrt_b):
    """Cantidades (en unidades mínimas) de token0 y token1 para una posición.
    sqrt_* son raíces de precio (token1 por token0, sin decimales)."""
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    if sqrt_p <= sqrt_a:
        a0 = liquidez * (sqrt_b - sqrt_a) / (sqrt_a * sqrt_b)
        a1 = 0.0
    elif sqrt_p >= sqrt_b:
        a0 = 0.0
        a1 = liquidez * (sqrt_b - sqrt_a)
    else:
        a0 = liquidez * (sqrt_b - sqrt_p) / (sqrt_p * sqrt_b)
        a1 = liquidez * (sqrt_p - sqrt_a)
    return a0, a1


def fee_growth_inside(fgg, fgo_lower, fgo_upper, tick_lower, tick_upper, tick_cur, modulo):
    """Fórmula estándar Uniswap v3 (idéntica en Orca y Raydium, con Q64 en vez de Q128)."""
    below = fgo_lower if tick_cur >= tick_lower else (fgg - fgo_lower) % modulo
    above = fgo_upper if tick_cur < tick_upper else (fgg - fgo_upper) % modulo
    return (fgg - below - above) % modulo


# ─────────────────────────────────────────────────────────────
# SOLANA RPC
# ─────────────────────────────────────────────────────────────

class SolanaRPC:
    def __init__(self, url):
        self.url = url
        self._id = 0

    def call(self, method, params):
        self._id += 1
        r = http_json(self.url, {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        if r is None:
            return None
        if "error" in r:
            ERRORES.append(f"solana {method} -> {r['error']}")
            return None
        return r.get("result")

    def token_accounts(self, wallet, program):
        r = self.call("getTokenAccountsByOwner",
                      [wallet, {"programId": program}, {"encoding": "jsonParsed"}])
        out = []
        for a in (r or {}).get("value", []):
            try:
                info = a["account"]["data"]["parsed"]["info"]
                amt = info["tokenAmount"]
                if amt["decimals"] == 0 and amt["amount"] == "1":
                    out.append(info["mint"])
            except Exception:
                pass
        return out

    def cuentas(self, pubkeys):
        """getMultipleAccounts en lotes de 100. Devuelve dict pubkey -> (bytes, owner)."""
        out = {}
        for i in range(0, len(pubkeys), 100):
            lote = pubkeys[i:i + 100]
            r = self.call("getMultipleAccounts", [lote, {"encoding": "base64"}])
            for k, v in zip(lote, (r or {}).get("value", [])):
                if v:
                    import base64
                    out[k] = (base64.b64decode(v["data"][0]), v["owner"])
        return out

    def decimales_mint(self, mint):
        r = self.call("getAccountInfo", [mint, {"encoding": "jsonParsed"}])
        try:
            return int(r["value"]["data"]["parsed"]["info"]["decimals"])
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────
# ORCA WHIRLPOOLS
# Layouts verbatim de orca-so/whirlpools (position.rs, whirlpool.rs).
# Position: 8 disc + whirlpool 32 + position_mint 32 + liquidity u128 +
#   tick_lower i32 + tick_upper i32 + fg_checkpoint_a u128 + fee_owed_a u64 +
#   fg_checkpoint_b u128 + fee_owed_b u64 + 3×(u128+u64)   = 216 bytes
# ─────────────────────────────────────────────────────────────

ORCA_POSITION_LEN = 216
ORCA_TICKS_POR_ARRAY = 88
ORCA_TICK_LEN = 113
ORCA_TICKARRAY_LEN = 8 + 4 + ORCA_TICKS_POR_ARRAY * ORCA_TICK_LEN + 32


def orca_decodificar_posicion(b):
    return {
        "whirlpool": pk(b, 8),
        "mint": pk(b, 40),
        "liquidez": u128(b, 72),
        "tick_lower": i32(b, 88),
        "tick_upper": i32(b, 92),
        "fg_checkpoint_a": u128(b, 96),
        "fee_owed_a": u64(b, 112),
        "fg_checkpoint_b": u128(b, 120),
        "fee_owed_b": u64(b, 136),
    }


def orca_decodificar_whirlpool(b):
    return {
        "tick_spacing": u16(b, 41),
        "fee_rate": u16(b, 45),          # en centésimas de bp (1e-6)
        "liquidez": u128(b, 49),
        "sqrt_price_x64": u128(b, 65),
        "tick_current": i32(b, 81),
        "mint_a": pk(b, 101),
        "fg_global_a": u128(b, 165),
        "mint_b": pk(b, 181),
        "fg_global_b": u128(b, 245),
    }


def orca_tick_array_start(tick, spacing):
    n = ORCA_TICKS_POR_ARRAY * spacing
    return math.floor(tick / n) * n


def orca_decodificar_tick(b_array, tick, start, spacing):
    idx = (tick - start) // spacing
    o = 8 + 4 + idx * ORCA_TICK_LEN
    return {"fgo_a": u128(b_array, o + 1 + 16 + 16), "fgo_b": u128(b_array, o + 1 + 16 + 16 + 16)}


def leer_orca(rpc, wallet, mints_nft, cfg):
    prog = cfg["contratos"]["orca_whirlpool_program"]
    prog_b = b58decode(prog)
    pdas = {}
    for m in mints_nft:
        pda, _ = find_program_address([b"position", b58decode(m)], prog_b)
        pdas[b58encode(pda)] = m
    cuentas = rpc.cuentas(list(pdas.keys()))
    posiciones = []
    for pda, (data, owner) in cuentas.items():
        if owner != prog or len(data) != ORCA_POSITION_LEN:
            continue
        p = orca_decodificar_posicion(data)
        p["clave"] = pdas[pda]
        p["cuenta"] = pda
        posiciones.append(p)
    if not posiciones:
        return []
    pools = rpc.cuentas(list({p["whirlpool"] for p in posiciones}))
    out = []
    for p in posiciones:
        if p["whirlpool"] not in pools:
            ERRORES.append(f"orca: whirlpool {p['whirlpool']} no legible")
            continue
        w = orca_decodificar_whirlpool(pools[p["whirlpool"]][0])
        sqrt_p = w["sqrt_price_x64"] / 2 ** 64
        a0, a1 = cantidades(p["liquidez"], sqrt_p, sqrt_precio_tick(p["tick_lower"]), sqrt_precio_tick(p["tick_upper"]))
        fees_a, fees_b, fees_origen = p["fee_owed_a"], p["fee_owed_b"], "fee_owed (última actualización on-chain)"
        # Fees devengadas desde el último checkpoint: solo con tick arrays de tamaño fijo.
        try:
            st_l = orca_tick_array_start(p["tick_lower"], w["tick_spacing"])
            st_u = orca_tick_array_start(p["tick_upper"], w["tick_spacing"])
            pda_l, _ = find_program_address([b"tick_array", b58decode(p["whirlpool"]), str(st_l).encode()], prog_b)
            pda_u, _ = find_program_address([b"tick_array", b58decode(p["whirlpool"]), str(st_u).encode()], prog_b)
            ta = rpc.cuentas([b58encode(pda_l), b58encode(pda_u)])
            bl = ta.get(b58encode(pda_l), (None,))[0]
            bu = ta.get(b58encode(pda_u), (None,))[0]
            if bl and bu and len(bl) == ORCA_TICKARRAY_LEN and len(bu) == ORCA_TICKARRAY_LEN:
                tl = orca_decodificar_tick(bl, p["tick_lower"], st_l, w["tick_spacing"])
                tu = orca_decodificar_tick(bu, p["tick_upper"], st_u, w["tick_spacing"])
                M = 2 ** 128
                fgi_a = fee_growth_inside(w["fg_global_a"], tl["fgo_a"], tu["fgo_a"], p["tick_lower"], p["tick_upper"], w["tick_current"], M)
                fgi_b = fee_growth_inside(w["fg_global_b"], tl["fgo_b"], tu["fgo_b"], p["tick_lower"], p["tick_upper"], w["tick_current"], M)
                da = ((fgi_a - p["fg_checkpoint_a"]) % M) * p["liquidez"] // 2 ** 64
                db = ((fgi_b - p["fg_checkpoint_b"]) % M) * p["liquidez"] // 2 ** 64
                fees_a += da
                fees_b += db
                fees_origen = "fee_owed + devengado desde checkpoint (tick arrays)"
            else:
                NOTAS.append(f"orca {p['clave'][:8]}…: tick array de tamaño no fijo (dinámico); fees pendientes solo fee_owed")
        except Exception as e:
            NOTAS.append(f"orca {p['clave'][:8]}…: no se pudo calcular fee devengado ({type(e).__name__}); solo fee_owed")
        out.append({
            "plataforma": "Orca", "cadena": "Solana", "clave": p["clave"], "pool": p["whirlpool"],
            "mint0": w["mint_a"], "mint1": w["mint_b"], "fee_bps": w["fee_rate"] / 100.0,
            "tick_lower": p["tick_lower"], "tick_upper": p["tick_upper"], "tick_current": w["tick_current"],
            "sqrt_p": sqrt_p, "liquidez": p["liquidez"], "amt0_raw": a0, "amt1_raw": a1,
            "fees0_raw": fees_a, "fees1_raw": fees_b, "fees_origen": fees_origen, "stakeada": False,
        })
    return out


# ─────────────────────────────────────────────────────────────
# RAYDIUM CLMM
# Layouts verbatim de raydium-io/raydium-clmm (personal_position.rs, pool.rs, config.rs).
# PersonalPositionState: 8 + bump 1 + nft_mint 32 + pool_id 32 + tick_lower i32 +
#   tick_upper i32 + liquidity u128 + fgi0 u128 + fgi1 u128 + owed0 u64 + owed1 u64 + … = 281
# ─────────────────────────────────────────────────────────────

RAY_POSITION_LEN = 281


def ray_decodificar_posicion(b):
    return {
        "mint": pk(b, 9), "pool": pk(b, 41),
        "tick_lower": i32(b, 73), "tick_upper": i32(b, 77),
        "liquidez": u128(b, 81),
        "fgi0_last": u128(b, 97), "fgi1_last": u128(b, 113),
        "owed0": u64(b, 129), "owed1": u64(b, 137),
    }


def ray_decodificar_pool(b):
    return {
        "amm_config": pk(b, 9), "mint0": pk(b, 73), "mint1": pk(b, 105),
        "dec0": b[233], "dec1": b[234], "tick_spacing": u16(b, 235),
        "liquidez": u128(b, 237), "sqrt_price_x64": u128(b, 253), "tick_current": i32(b, 269),
        "fg_global_0": u128(b, 277), "fg_global_1": u128(b, 293),
    }


def ray_decodificar_config(b):
    # bump u8 @8, index u16 @9, owner 32 @11, protocol_fee_rate u32 @43, trade_fee_rate u32 @47
    return {"trade_fee_rate": int.from_bytes(b[47:51], "little")}  # 1e-6


RAY_TICKS_POR_ARRAY = 60
RAY_TICK_LEN = 168


def ray_tick_array_start(tick, spacing):
    n = RAY_TICKS_POR_ARRAY * spacing
    return math.floor(tick / n) * n


def ray_decodificar_tick(b_array, tick, start, spacing):
    idx = (tick - start) // spacing
    o = 8 + 32 + 4 + idx * RAY_TICK_LEN
    return {"fgo0": u128(b_array, o + 4 + 16 + 16), "fgo1": u128(b_array, o + 4 + 16 + 16 + 16)}


def leer_raydium(rpc, wallet, mints_nft, cfg):
    prog = cfg["contratos"]["raydium_clmm_program"]
    prog_b = b58decode(prog)
    pdas = {}
    for m in mints_nft:
        pda, _ = find_program_address([b"position", b58decode(m)], prog_b)
        pdas[b58encode(pda)] = m
    cuentas = rpc.cuentas(list(pdas.keys()))
    posiciones = []
    for pda, (data, owner) in cuentas.items():
        if owner != prog or len(data) < 145:
            continue
        p = ray_decodificar_posicion(data)
        p["clave"] = pdas[pda]
        posiciones.append(p)
    if not posiciones:
        return []
    pools = rpc.cuentas(list({p["pool"] for p in posiciones}))
    pools_dec = {k: ray_decodificar_pool(v[0]) for k, v in pools.items()}
    configs = rpc.cuentas(list({w["amm_config"] for w in pools_dec.values()}))
    out = []
    for p in posiciones:
        w = pools_dec.get(p["pool"])
        if not w:
            ERRORES.append(f"raydium: pool {p['pool']} no legible")
            continue
        fee_bps = None
        if w["amm_config"] in configs:
            fee_bps = ray_decodificar_config(configs[w["amm_config"]][0])["trade_fee_rate"] / 100.0
        sqrt_p = w["sqrt_price_x64"] / 2 ** 64
        a0, a1 = cantidades(p["liquidez"], sqrt_p, sqrt_precio_tick(p["tick_lower"]), sqrt_precio_tick(p["tick_upper"]))
        f0, f1, origen = p["owed0"], p["owed1"], "token_fees_owed (última actualización on-chain)"
        try:
            st_l = ray_tick_array_start(p["tick_lower"], w["tick_spacing"])
            st_u = ray_tick_array_start(p["tick_upper"], w["tick_spacing"])
            pool_b = b58decode(p["pool"])
            pda_l, _ = find_program_address([b"tick_array", pool_b, st_l.to_bytes(4, "big", signed=True)], prog_b)
            pda_u, _ = find_program_address([b"tick_array", pool_b, st_u.to_bytes(4, "big", signed=True)], prog_b)
            ta = rpc.cuentas([b58encode(pda_l), b58encode(pda_u)])
            bl = ta.get(b58encode(pda_l), (None,))[0]
            bu = ta.get(b58encode(pda_u), (None,))[0]
            if bl and bu:
                tl = ray_decodificar_tick(bl, p["tick_lower"], st_l, w["tick_spacing"])
                tu = ray_decodificar_tick(bu, p["tick_upper"], st_u, w["tick_spacing"])
                M = 2 ** 128
                fgi0 = fee_growth_inside(w["fg_global_0"], tl["fgo0"], tu["fgo0"], p["tick_lower"], p["tick_upper"], w["tick_current"], M)
                fgi1 = fee_growth_inside(w["fg_global_1"], tl["fgo1"], tu["fgo1"], p["tick_lower"], p["tick_upper"], w["tick_current"], M)
                f0 += ((fgi0 - p["fgi0_last"]) % M) * p["liquidez"] // 2 ** 64
                f1 += ((fgi1 - p["fgi1_last"]) % M) * p["liquidez"] // 2 ** 64
                origen = "owed + devengado desde checkpoint (tick arrays)"
        except Exception as e:
            NOTAS.append(f"raydium {p['clave'][:8]}…: no se pudo calcular fee devengado ({type(e).__name__}); solo owed")
        out.append({
            "plataforma": "Raydium", "cadena": "Solana", "clave": p["clave"], "pool": p["pool"],
            "mint0": w["mint0"], "mint1": w["mint1"], "fee_bps": fee_bps,
            "dec0": w["dec0"], "dec1": w["dec1"],
            "tick_lower": p["tick_lower"], "tick_upper": p["tick_upper"], "tick_current": w["tick_current"],
            "sqrt_p": sqrt_p, "liquidez": p["liquidez"], "amt0_raw": a0, "amt1_raw": a1,
            "fees0_raw": f0, "fees1_raw": f1, "fees_origen": origen, "stakeada": False,
        })
    return out


# ─────────────────────────────────────────────────────────────
# AERODROME SLIPSTREAM (Base) — JSON-RPC eth_call con ABI manual
# Firmas verbatim de aerodrome-finance/slipstream (INonfungiblePositionManager,
# ICLPoolState). ticks() lleva stakedLiquidityNet y rewardGrowthOutside: los
# feeGrowthOutside son las palabras 3 y 4, no 2 y 3 como en Uniswap.
# ─────────────────────────────────────────────────────────────

def keccak256(data):
    """keccak-256 (no sha3-256). Implementación mínima en Python puro."""
    RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
          0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
          0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
          0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
          0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
          0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
    ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
    M = (1 << 64) - 1

    def f(st):
        for rnd in range(24):
            C = [st[x][0] ^ st[x][1] ^ st[x][2] ^ st[x][3] ^ st[x][4] for x in range(5)]
            D = [C[(x - 1) % 5] ^ (((C[(x + 1) % 5] << 1) | (C[(x + 1) % 5] >> 63)) & M) for x in range(5)]
            st = [[st[x][y] ^ D[x] for y in range(5)] for x in range(5)]
            B = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    r = ROT[x][y]
                    B[y][(2 * x + 3 * y) % 5] = ((st[x][y] << r) | (st[x][y] >> (64 - r))) & M if r else st[x][y]
            st = [[B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
            st[0][0] ^= RC[rnd]
        return st

    rate = 136
    msg = bytearray(data) + b"\x01"
    while len(msg) % rate:
        msg += b"\x00"
    msg[-1] |= 0x80
    st = [[0] * 5 for _ in range(5)]
    for off in range(0, len(msg), rate):
        blk = msg[off:off + rate]
        for i in range(rate // 8):
            st[i % 5][i // 5] ^= int.from_bytes(blk[8 * i:8 * i + 8], "little")
        st = f(st)
    out = b""
    for y in range(5):
        for x in range(5):
            out += st[x][y].to_bytes(8, "little")
    return out[:32]


def selector(firma):
    return keccak256(firma.encode()).hex()[:8]


def enc_uint(n):
    return f"{n % (1 << 256):064x}"


def enc_int(n):
    return enc_uint(n % (1 << 256))


def enc_addr(a):
    return a.lower().replace("0x", "").rjust(64, "0")


def dec_words(hexdata):
    h = hexdata[2:] if hexdata.startswith("0x") else hexdata
    return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]


def dec_int(w, bits=256):
    return w - (1 << bits) if w >= (1 << (bits - 1)) else w


class EvmRPC:
    def __init__(self, url):
        self.url = url
        self._id = 0

    def call(self, to, data):
        self._id += 1
        r = http_json(self.url, {"jsonrpc": "2.0", "id": self._id, "method": "eth_call",
                                 "params": [{"to": to, "data": "0x" + data}, "latest"]})
        if r is None:
            return None
        if "error" in r:
            ERRORES.append(f"base eth_call {to[:10]}… {data[:8]} -> {r['error']}")
            return None
        res = r.get("result")
        return dec_words(res) if res and res != "0x" else None


SEL = {
    "balanceOf": selector("balanceOf(address)"),
    "tokenOfOwnerByIndex": selector("tokenOfOwnerByIndex(address,uint256)"),
    "positions": selector("positions(uint256)"),
    "ownerOf": selector("ownerOf(uint256)"),
    "getPool": selector("getPool(address,address,int24)"),
    "slot0": selector("slot0()"),
    "ticks": selector("ticks(int24)"),
    "fgg0": selector("feeGrowthGlobal0X128()"),
    "fgg1": selector("feeGrowthGlobal1X128()"),
    "fee": selector("fee()"),
    "gauge": selector("gauge()"),
    "stakedValues": selector("stakedValues(address)"),
    "decimals": selector("decimals()"),
    "symbol": selector("symbol()"),
}


def leer_aerodrome(rpc, wallet, cfg):
    npm = cfg["contratos"]["aerodrome_slipstream_nft_manager"]
    fab = cfg["contratos"]["aerodrome_slipstream_factory"]
    token_ids = []
    if wallet:
        bal = rpc.call(npm, SEL["balanceOf"] + enc_addr(wallet))
        n = bal[0] if bal else 0
        for i in range(n):
            t = rpc.call(npm, SEL["tokenOfOwnerByIndex"] + enc_addr(wallet) + enc_uint(i))
            if t:
                token_ids.append((t[0], False))
        # Stakeadas en gauge: el NFT lo custodia el gauge del pool. Se buscan en los pools listados.
        for pool in cfg.get("pools_aerodrome", []):
            g = rpc.call(pool, SEL["gauge"])
            if not g or g[0] == 0:
                continue
            gauge = "0x" + f"{g[0]:040x}"
            sv = rpc.call(gauge, SEL["stakedValues"] + enc_addr(wallet))
            if sv and len(sv) >= 2:
                cnt = sv[1]
                for k in range(cnt):
                    token_ids.append((sv[2 + k], True))
    for t in cfg.get("posiciones_base_extra", []):
        token_ids.append((int(t), None))
    out = []
    for tid, stakeada in token_ids:
        w = rpc.call(npm, SEL["positions"] + enc_uint(tid))
        if not w or len(w) < 12:
            ERRORES.append(f"aerodrome: positions({tid}) no legible")
            continue
        token0 = "0x" + f"{w[2]:040x}"
        token1 = "0x" + f"{w[3]:040x}"
        spacing = dec_int(w[4])
        tl, tu = dec_int(w[5]), dec_int(w[6])
        liq = w[7]
        fgi0_last, fgi1_last, owed0, owed1 = w[8], w[9], w[10], w[11]
        if liq == 0 and owed0 == 0 and owed1 == 0:
            continue  # NFT vacío (posición cerrada sin quemar)
        pool_w = rpc.call(fab, SEL["getPool"] + enc_addr(token0) + enc_addr(token1) + enc_int(spacing))
        if not pool_w or pool_w[0] == 0:
            ERRORES.append(f"aerodrome: getPool para tokenId {tid} sin resultado")
            continue
        pool = "0x" + f"{pool_w[0]:040x}"
        s0 = rpc.call(pool, SEL["slot0"])
        if not s0:
            continue
        sqrt_p = s0[0] / 2 ** 96
        tick_cur = dec_int(s0[1])
        fee_w = rpc.call(pool, SEL["fee"])
        fee_bps = fee_w[0] / 100.0 if fee_w else None
        if stakeada is None:
            own = rpc.call(npm, SEL["ownerOf"] + enc_uint(tid))
            stakeada = bool(own) and (wallet is None or f"{own[0]:040x}" != wallet.lower().replace("0x", ""))
        a0, a1 = cantidades(liq, sqrt_p, sqrt_precio_tick(tl), sqrt_precio_tick(tu))
        f0, f1, origen = owed0, owed1, "tokensOwed (última actualización on-chain)"
        try:
            g0 = rpc.call(pool, SEL["fgg0"])
            g1 = rpc.call(pool, SEL["fgg1"])
            tkl = rpc.call(pool, SEL["ticks"] + enc_int(tl))
            tku = rpc.call(pool, SEL["ticks"] + enc_int(tu))
            if g0 and g1 and tkl and tku and len(tkl) >= 5 and len(tku) >= 5:
                M = 2 ** 256
                fgi0 = fee_growth_inside(g0[0], tkl[3], tku[3], tl, tu, tick_cur, M)
                fgi1 = fee_growth_inside(g1[0], tkl[4], tku[4], tl, tu, tick_cur, M)
                f0 += ((fgi0 - fgi0_last) % M) * liq // 2 ** 128
                f1 += ((fgi1 - fgi1_last) % M) * liq // 2 ** 128
                origen = "tokensOwed + devengado desde checkpoint (ticks)"
        except Exception as e:
            NOTAS.append(f"aerodrome {tid}: no se pudo calcular fee devengado ({type(e).__name__})")
        if stakeada:
            NOTAS.append(f"aerodrome {tid}: stakeada en gauge; en Slipstream una posición en gauge cobra AERO y renuncia a las comisiones; las fees mostradas son las devengadas antes o fuera del gauge")
        out.append({
            "plataforma": "Aerodrome", "cadena": "Base", "clave": f"slipstream:{tid}", "pool": pool,
            "mint0": token0.lower(), "mint1": token1.lower(), "fee_bps": fee_bps,
            "tick_lower": tl, "tick_upper": tu, "tick_current": tick_cur,
            "sqrt_p": sqrt_p, "liquidez": liq, "amt0_raw": a0, "amt1_raw": a1,
            "fees0_raw": f0, "fees1_raw": f1, "fees_origen": origen, "stakeada": bool(stakeada),
        })
    return out


# ─────────────────────────────────────────────────────────────
# MERCADO: precio BTC, ATR diario, último cierre H4, EUR/USD
# ─────────────────────────────────────────────────────────────

def klines(interval, limit):
    for host in ("https://data-api.binance.vision", "https://api.binance.com"):
        d = http_json(f"{host}/api/v3/klines", params={"symbol": "BTCUSDT", "interval": interval, "limit": limit})
        if d and isinstance(d, list) and len(d) > 2:
            return [{"t": int(k[0]), "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]), "cierre": int(k[6])} for k in d]
    return None


def mercado(cfg):
    m = {"btc_precio": None, "btc_fuente": None, "atr_pct": None, "atr_dias": cfg["parametros"]["atr_dias"],
         "h4_cierre": None, "h4_hora_utc": None, "eurusd": None}
    n = cfg["parametros"]["atr_dias"]
    v = klines("1d", n + 3)
    if v:
        ahora = int(datetime.now(timezone.utc).timestamp() * 1000)
        cerradas = [k for k in v if k["cierre"] <= ahora]
        if len(cerradas) >= n + 1:
            trs = []
            for i in range(1, len(cerradas)):
                h, l, pc = cerradas[i]["h"], cerradas[i]["l"], cerradas[i - 1]["c"]
                trs.append(max(h - l, abs(h - pc), abs(l - pc)))
            atr = sum(trs[-n:]) / n
            m["atr_pct"] = atr / cerradas[-1]["c"] * 100
        m["btc_precio"] = v[-1]["c"]
        m["btc_fuente"] = "Binance BTCUSDT (última vela 1d, puede estar abierta)"
    h4 = klines("4h", 3)
    if h4:
        ahora = int(datetime.now(timezone.utc).timestamp() * 1000)
        cerradas = [k for k in h4 if k["cierre"] <= ahora]
        if cerradas:
            m["h4_cierre"] = cerradas[-1]["c"]
            m["h4_hora_utc"] = datetime.fromtimestamp(cerradas[-1]["cierre"] / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")
    fx = http_json("https://api.frankfurter.app/latest", params={"from": "EUR", "to": "USD"})
    try:
        m["eurusd"] = float(fx["rates"]["USD"])
    except Exception:
        pass
    return m


# ─────────────────────────────────────────────────────────────
# ENRIQUECIMIENTO: símbolos, orientación, métricas del protocolo
# ─────────────────────────────────────────────────────────────

BTC_LIKE = {"BTC", "WBTC", "CBBTC", "ZBTC", "TBTC", "XBTC", "BTCB", "21BTC"}
ESTABLES_USD = {"USDC", "USDT", "USD1", "PYUSD", "USDS", "JUPUSD", "USDG", "USDE", "USDBC", "DAI", "FDUSD", "USDY"}
ESTABLES_EUR = {"EURC", "EURS", "EURT", "EURE", "VEUR"}


def simbolo(cfg, cadena, direccion, rpc_sol=None, rpc_evm=None, dec_hint=None):
    tabla = cfg["tokens"]["solana" if cadena == "Solana" else "base"]
    key = direccion if cadena == "Solana" else direccion.lower()
    t = tabla.get(key)
    if t:
        return t["simbolo"], t["decimales"]
    dec = dec_hint
    sym = direccion[:4] + "…" + direccion[-4:]
    if cadena == "Solana" and rpc_sol is not None and dec is None:
        dec = rpc_sol.decimales_mint(direccion)
    if cadena == "Base" and rpc_evm is not None:
        d = rpc_evm.call(direccion, SEL["decimals"])
        if d:
            dec = d[0]
        s = rpc_evm.call(direccion, SEL["symbol"])
        if s and len(s) >= 3:
            try:
                ln = s[1]
                raw = ("".join(f"{w:064x}" for w in s[2:]))[:ln * 2]
                sym = bytes.fromhex(raw).decode("utf-8", "replace")
            except Exception:
                pass
    if dec is None:
        NOTAS.append(f"{cadena}: decimales de {direccion} no disponibles; cantidades en n/d")
    return sym, dec


def precio_usd(sym, m, cfg):
    s = sym.upper()
    if s in ESTABLES_USD:
        return cfg["parametros"]["precio_estables_usd"], "supuesto 1,00 (peg vigilado en el tablero)"
    if s in BTC_LIKE:
        return m["btc_precio"], m["btc_fuente"]
    if s in ESTABLES_EUR:
        return m["eurusd"], "EUR/USD Frankfurter (BCE)"
    return None, "sin fuente de precio"


def tipo_par(s0, s1):
    a, b = s0.upper(), s1.upper()
    if (a in BTC_LIKE and b in ESTABLES_USD) or (b in BTC_LIKE and a in ESTABLES_USD):
        return "btc"
    if (a in ESTABLES_EUR and b in ESTABLES_USD) or (b in ESTABLES_EUR and a in ESTABLES_USD):
        return "estable-fx"
    if a in ESTABLES_USD and b in ESTABLES_USD:
        return "estable-usd"
    return "otro"


def enriquecer(p, cfg, m, tablero, manuales, rpc_sol, rpc_evm):
    par = cfg["parametros"]
    s0, d0 = simbolo(cfg, p["cadena"], p["mint0"], rpc_sol, rpc_evm, p.get("dec0"))
    s1, d1 = simbolo(cfg, p["cadena"], p["mint1"], rpc_sol, rpc_evm, p.get("dec1"))
    p["token0"], p["token1"] = s0, s1
    p["tipo"] = tipo_par(s0, s1)
    ok = d0 is not None and d1 is not None
    # Precio del pool: token1 por token0, con decimales
    p_pool = (p["sqrt_p"] ** 2) * 10 ** (d0 - d1) if ok else None
    lo = (sqrt_precio_tick(p["tick_lower"]) ** 2) * 10 ** (d0 - d1) if ok else None
    hi = (sqrt_precio_tick(p["tick_upper"]) ** 2) * 10 ** (d0 - d1) if ok else None
    # Orientación: base = BTC si lo hay; si no EUR; si no token0
    base_es_1 = (s1.upper() in BTC_LIKE and s0.upper() not in BTC_LIKE) or \
                (s1.upper() in ESTABLES_EUR and s0.upper() in ESTABLES_USD)
    if base_es_1 and ok:
        p["base"], p["cot"] = s1, s0
        p["precio"], p["rango_inf"], p["rango_sup"] = 1 / p_pool, 1 / hi, 1 / lo
        p["base_amt"], p["cot_amt"] = p["amt1_raw"] / 10 ** d1, p["amt0_raw"] / 10 ** d0
        p["fees_base"], p["fees_cot"] = p["fees1_raw"] / 10 ** d1, p["fees0_raw"] / 10 ** d0
    elif ok:
        p["base"], p["cot"] = s0, s1
        p["precio"], p["rango_inf"], p["rango_sup"] = p_pool, lo, hi
        p["base_amt"], p["cot_amt"] = p["amt0_raw"] / 10 ** d0, p["amt1_raw"] / 10 ** d1
        p["fees_base"], p["fees_cot"] = p["fees0_raw"] / 10 ** d0, p["fees1_raw"] / 10 ** d1
    else:
        p.update({"base": s0, "cot": s1, "precio": None, "rango_inf": None, "rango_sup": None,
                  "base_amt": None, "cot_amt": None, "fees_base": None, "fees_cot": None})
    p["par"] = f"{p['base']}/{p['cot']}"
    p["en_rango"] = (p["tick_lower"] <= p["tick_current"] < p["tick_upper"])

    # Valor USD
    pb, fb = precio_usd(p["base"], m, cfg)
    pc, fc = precio_usd(p["cot"], m, cfg)
    p["precio_base_usd"], p["precio_cot_usd"] = pb, pc
    p["fuente_precios"] = f"{p['base']}: {fb} · {p['cot']}: {fc}"
    if ok and pb is not None and pc is not None:
        p["valor_usd"] = p["base_amt"] * pb + p["cot_amt"] * pc
        p["fees_usd"] = p["fees_base"] * pb + p["fees_cot"] * pc
    else:
        p["valor_usd"], p["fees_usd"] = None, None

    # Distancia a bordes y unidad de volatilidad diaria
    if p["tipo"] == "btc":
        p["vol_diaria_pct"], p["vol_unidad"] = m["atr_pct"], f"ATR{m['atr_dias']} diario BTC"
    elif p["tipo"] == "estable-usd":
        p["vol_diaria_pct"], p["vol_unidad"] = par["sigma_estables_anual_pct"] / math.sqrt(365), "σ diaria supuesta (2% anual)"
    elif p["tipo"] == "estable-fx":
        sfx = (tablero or {}).get("volatilidad", {}).get("sigma_fx_pct")
        p["vol_diaria_pct"], p["vol_unidad"] = (sfx / math.sqrt(252) if sfx else None), "σ diaria EUR/USD (tablero, BCE)"
    else:
        p["vol_diaria_pct"], p["vol_unidad"] = None, "sin referencia de volatilidad"
    if p["precio"]:
        p["dist_inf_pct"] = (p["precio"] - p["rango_inf"]) / p["precio"] * 100
        p["dist_sup_pct"] = (p["rango_sup"] - p["precio"]) / p["precio"] * 100
        p["semianchura_pct"] = (p["rango_sup"] - p["rango_inf"]) / (p["rango_sup"] + p["rango_inf"]) * 100
        if p["vol_diaria_pct"]:
            p["dist_inf_atr"] = p["dist_inf_pct"] / p["vol_diaria_pct"]
            p["dist_sup_atr"] = p["dist_sup_pct"] / p["vol_diaria_pct"]
        else:
            p["dist_inf_atr"] = p["dist_sup_atr"] = None
    else:
        p["dist_inf_pct"] = p["dist_sup_pct"] = p["semianchura_pct"] = p["dist_inf_atr"] = p["dist_sup_atr"] = None

    # Stop del LP System: solo por cierre H4 fuera de rango (pares BTC)
    p["h4_fuera"] = None
    if p["tipo"] == "btc" and m["h4_cierre"] and p["rango_inf"]:
        p["h4_fuera"] = not (p["rango_inf"] <= m["h4_cierre"] <= p["rango_sup"])
        p["h4_cierre"] = m["h4_cierre"]
        p["h4_hora_utc"] = m["h4_hora_utc"]

    # Datos manuales (tracker): entrada, cobros, stop
    man = manuales.get(p["clave"])
    p["manual"] = bool(man)
    p["dias_abierta"] = dias_desde(man["fecha_entrada"]) if man and man.get("fecha_entrada") else None
    p["il_usd"] = p["exposicion_usd"] = p["earn_usd"] = p["ratio_earn_il"] = None
    if man and ok and pb is not None and pc is not None and all(man.get(k) is not None for k in ("token_base_entrada", "token_cot_entrada", "precio_entrada")):
        # Convención del tracker: precio_entrada = base en unidades de cotización, y la
        # cotización es un token USD (los tres tipos de par del alcance lo cumplen).
        v_hold = man["token_base_entrada"] * pb + man["token_cot_entrada"] * pc
        v_entrada = man["token_base_entrada"] * man["precio_entrada"] + man["token_cot_entrada"]
        p["exposicion_usd"] = v_hold - v_entrada
        p["il_usd"] = p["valor_usd"] - v_hold
        p["earn_usd"] = (man.get("cobros_usd") or 0.0) + (p["fees_usd"] or 0.0)
        if p["il_usd"] < 0:
            p["ratio_earn_il"] = p["earn_usd"] / abs(p["il_usd"])
        p["capital_usd"] = man.get("capital_usd")
        p["stop_manual"] = man.get("stop")
        p["notas_manual"] = man.get("notas")

    # Cruce con el tablero (veredicto vigente del pool)
    p["tablero_veredicto"] = p["tablero_neto_pct"] = None
    if tablero:
        for c in tablero.get("candidatos_todos", []) + tablero.get("radar", []):
            mismo = (c.get("id") == p["pool"]) or \
                    (c.get("plataforma") == p["plataforma"] and {str(c.get("a", "")).upper(), str(c.get("b", "")).upper()} == {s0.upper(), s1.upper()})
            if mismo:
                p["tablero_veredicto"] = c.get("veredicto")
                p["tablero_neto_pct"] = c.get("neto_mm_anual_pct")
                p["tablero_motivo"] = c.get("motivo")
                break

    # Situación según el protocolo
    if p["h4_fuera"]:
        p["situacion"], p["situacion_motivo"] = "STOP", f"cierre H4 ({p['h4_hora_utc']} UTC) fuera de rango: la regla del sistema cierra la posición"
    elif not p["en_rango"]:
        p["situacion"], p["situacion_motivo"] = "FUERA DE RANGO", "precio actual fuera; sin cierre H4 fuera aún" if p["tipo"] == "btc" else "precio actual fuera del rango"
    elif p["dist_inf_atr"] is not None and min(p["dist_inf_atr"], p["dist_sup_atr"]) < par["alerta_borde_atr"]:
        lado = "inferior" if p["dist_inf_atr"] < p["dist_sup_atr"] else "superior"
        p["situacion"], p["situacion_motivo"] = "ALERTA DE BORDE", f"a menos de {par['alerta_borde_atr']:.0f} {p['vol_unidad']} del borde {lado}"
    else:
        p["situacion"], p["situacion_motivo"] = "EN RANGO", "sin alertas"
    if p["ratio_earn_il"] is not None and p["ratio_earn_il"] < par["umbral_earn_il_reposicionar"] and p["situacion"] == "EN RANGO":
        p["situacion_motivo"] = f"earn/IL {p['ratio_earn_il']:.2f} por debajo del umbral de reposicionamiento {par['umbral_earn_il_reposicionar']}"
    return p


# ─────────────────────────────────────────────────────────────
# RECOLECCIÓN
# ─────────────────────────────────────────────────────────────

def cargar_tablero(out_dir):
    try:
        with open(os.path.join(out_dir or ".", "tablero.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        NOTAS.append("tablero.json no disponible: sin cruce de veredictos ni σ FX")
        return None


def recolectar(cfg, out_dir):
    m = mercado(cfg)
    tablero = cargar_tablero(out_dir)
    manuales = {x["clave"]: x for x in cfg.get("posiciones_manuales", []) if x.get("clave")}
    rpc_sol = SolanaRPC(cfg["rpc"]["solana"])
    rpc_evm = EvmRPC(cfg["rpc"]["base"])
    crudas = []
    for w in cfg["wallets"].get("solana", []):
        mints = rpc_sol.token_accounts(w, cfg["contratos"]["spl_token_program"]) + \
                rpc_sol.token_accounts(w, cfg["contratos"]["spl_token_2022_program"])
        if mints:
            crudas += leer_orca(rpc_sol, w, mints, cfg)
            crudas += leer_raydium(rpc_sol, w, mints, cfg)
        else:
            NOTAS.append(f"solana {w[:6]}…: sin NFTs de posición en la wallet")
    wallets_base = cfg["wallets"].get("base", [])
    for w in wallets_base:
        crudas += leer_aerodrome(rpc_evm, w, cfg)
    if not wallets_base and cfg.get("posiciones_base_extra"):
        crudas += leer_aerodrome(rpc_evm, None, cfg)
    posiciones = [enriquecer(p, cfg, m, tablero, manuales, rpc_sol, rpc_evm) for p in crudas]
    vistas = {p["clave"] for p in posiciones}
    solo_manual = [x for k, x in manuales.items() if k not in vistas]
    for x in solo_manual:
        NOTAS.append(f"posición manual {x['clave'][:12]}… sin lectura on-chain: se lista como 'solo manual'")
    for p in posiciones:
        for k in ("sqrt_p", "amt0_raw", "amt1_raw", "fees0_raw", "fees1_raw", "liquidez", "dec0", "dec1"):
            p.pop(k, None)
    total = sum(p["valor_usd"] for p in posiciones if p["valor_usd"] is not None)
    fees = sum(p["fees_usd"] for p in posiciones if p["fees_usd"] is not None)
    return {
        "version_script": VERSION,
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mercado": m,
        "wallets": {k: [w[:6] + "…" + w[-4:] for w in v] for k, v in cfg["wallets"].items()},
        "parametros": cfg["parametros"],
        "resumen": {"n_posiciones": len(posiciones), "valor_usd": total if posiciones else None,
                    "fees_pendientes_usd": fees if posiciones else None,
                    "alertas": [p["par"] + " · " + p["situacion"] for p in posiciones if p["situacion"] != "EN RANGO"]},
        "posiciones": posiciones,
        "solo_manual": solo_manual,
        "tablero": {"ultima_vela": (tablero or {}).get("ultima_vela_cerrada"),
                    "regimen": ((tablero or {}).get("regimen") or {}).get("estado"),
                    "rv30": ((tablero or {}).get("volatilidad") or {}).get("rv30_cc"),
                    "drift": ((tablero or {}).get("volatilidad") or {}).get("drift_ratio_30d")},
        "notas": NOTAS, "errores": ERRORES,
    }


# ─────────────────────────────────────────────────────────────
# SALIDAS
# ─────────────────────────────────────────────────────────────

def markdown(d):
    L = []
    A = L.append
    m = d["mercado"]
    A(f"# Posiciones LP — {d['generado_utc']}")
    A("")
    A(f"Script v{d['version_script']} · BTC {fmt_usd(m['btc_precio'])} · ATR{m['atr_dias']} diario {fmt(m['atr_pct'], 2, '%')} · "
      f"último cierre H4 {fmt_usd(m['h4_cierre'])} ({m['h4_hora_utc'] or 'n/d'} UTC) · EUR/USD {fmt(m['eurusd'], 4)}")
    t = d["tablero"]
    A(f"Tablero: régimen {t['regimen'] or 'n/d'} · última vela {t['ultima_vela'] or 'n/d'} · RV30 {fmt(t['rv30'], 1, '%')} · drift {fmt(t['drift'], 2)}")
    A("")
    r = d["resumen"]
    if r["n_posiciones"] == 0:
        A("**Sin posiciones abiertas leídas on-chain.**" + (" Wallets configuradas: " + ", ".join(sum(d["wallets"].values(), [])) if any(d["wallets"].values()) else " No hay wallets en `posiciones.config.json`."))
    else:
        A(f"**{r['n_posiciones']} posiciones · valor {fmt_usd(r['valor_usd'])} · fees pendientes {fmt_usd(r['fees_pendientes_usd'])}**")
        if r["alertas"]:
            A("Alertas: " + " · ".join(r["alertas"]))
    A("")
    A("Estas cifras cubren la posición LP y sus comisiones. La exposición al precio del activo base es dirección y no se evalúa aquí más allá de su descomposición contable.")
    A("")
    if d["posiciones"]:
        A("| Par | Plataforma | Situación | Precio | Rango | Dist. inf | Dist. sup | Valor | Fees pend. | earn/IL | Tablero |")
        A("|---|---|---|---|---|---|---|---|---|---|---|")
        for p in d["posiciones"]:
            di = f"{fmt(p['dist_inf_pct'], 2, '%')} ({fmt(p['dist_inf_atr'], 1)} ATR)" if p["dist_inf_atr"] is not None else fmt(p["dist_inf_pct"], 2, "%")
            ds = f"{fmt(p['dist_sup_pct'], 2, '%')} ({fmt(p['dist_sup_atr'], 1)} ATR)" if p["dist_sup_atr"] is not None else fmt(p["dist_sup_pct"], 2, "%")
            A(f"| {p['par']} | {p['plataforma']}{' (gauge)' if p['stakeada'] else ''} | {p['situacion']} | {fmt(p['precio'], 4)} | "
              f"{fmt(p['rango_inf'], 4)} – {fmt(p['rango_sup'], 4)} | {di} | {ds} | {fmt_usd(p['valor_usd'])} | {fmt_usd(p['fees_usd'])} | "
              f"{fmt(p['ratio_earn_il'], 2)} | {p['tablero_veredicto'] or 'n/d'} |")
        A("")
        for p in d["posiciones"]:
            A(f"## {p['par']} · {p['plataforma']} ({p['cadena']}) · {p['situacion']}")
            A("")
            A(f"- Motivo: {p['situacion_motivo']}")
            A(f"- Pool `{p['pool']}` · fee {fmt(p['fee_bps'], 2, ' bps')} · clave `{p['clave']}`" + (" · stakeada en gauge" if p["stakeada"] else ""))
            A(f"- Composición: {fmt(p['base_amt'], 6)} {p['base']} + {fmt(p['cot_amt'], 4)} {p['cot']} → {fmt_usd(p['valor_usd'])} ({p['fuente_precios']})")
            A(f"- Rango {fmt(p['rango_inf'], 4)} – {fmt(p['rango_sup'], 4)} (semianchura {fmt(p['semianchura_pct'], 2, '%')}) · precio {fmt(p['precio'], 4)} · {'dentro' if p['en_rango'] else 'FUERA'}")
            A(f"- Distancia: inferior {fmt(p['dist_inf_pct'], 2, '%')} = {fmt(p['dist_inf_atr'], 2)} {p['vol_unidad']} · superior {fmt(p['dist_sup_pct'], 2, '%')} = {fmt(p['dist_sup_atr'], 2)}")
            if p["h4_fuera"] is not None:
                A(f"- Cierre H4 {fmt_usd(p['h4_cierre'])} ({p['h4_hora_utc']} UTC): {'FUERA de rango → stop' if p['h4_fuera'] else 'dentro de rango'}")
            A(f"- Fees pendientes: {fmt(p['fees_base'], 6)} {p['base']} + {fmt(p['fees_cot'], 4)} {p['cot']} = {fmt_usd(p['fees_usd'])} ({p['fees_origen']})")
            if p["manual"]:
                A(f"- Abierta hace {fmt(p['dias_abierta'], 1)} días · capital {fmt_usd(p.get('capital_usd'))} · stop manual {fmt(p.get('stop_manual'), 4)}")
                A(f"- Descomposición: IL {fmt_usd(p['il_usd'])} · exposición al precio {fmt_usd(p['exposicion_usd'])} · earn (cobros + pendientes) {fmt_usd(p['earn_usd'])} · earn/IL {fmt(p['ratio_earn_il'], 2)} (umbrales {d['parametros']['umbral_earn_il_entrar']} entrar / {d['parametros']['umbral_earn_il_reposicionar']} reposicionar)")
            else:
                A("- Sin datos manuales (entrada, cobros): IL y earn/IL no calculables. Añadir la posición a `posiciones_manuales` en la configuración.")
            if p["tablero_veredicto"]:
                A(f"- Tablero: {p['tablero_veredicto']} · neto MM {fmt(p['tablero_neto_pct'], 2, '%')} · {p.get('tablero_motivo') or ''}")
            A("")
    if d["solo_manual"]:
        A("## Posiciones solo manuales (sin lectura on-chain)")
        for x in d["solo_manual"]:
            A(f"- `{x['clave']}` · entrada {x.get('fecha_entrada')} · capital {fmt_usd(x.get('capital_usd'))} · {x.get('notas') or ''}")
        A("")
    A("## Notas")
    for n in d["notas"] or ["Ninguna"]:
        A(f"- {n}")
    A("")
    A("## Fuentes que fallaron")
    for e in d["errores"] or ["Ninguna"]:
        A(f"- {e}")
    A("")
    A("Fuentes: RPC Solana y Base (lectura directa de cuentas y contratos) · Binance BTCUSDT (precio, ATR, H4) · Frankfurter/BCE (EUR/USD) · tablero.json del propio repo.")
    return "\n".join(L) + "\n"


def html(d):
    plantilla = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.plantilla.html")
    with open(plantilla, encoding="utf-8") as f:
        t = f.read()
    datos = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    return t.replace("/*__DATOS__*/null", datos)


def main(argv):
    cfg_path = argv[argv.index("--config") + 1] if "--config" in argv else "posiciones.config.json"
    out_dir = argv[argv.index("--out") + 1] if "--out" in argv else None
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    d = recolectar(cfg, out_dir)
    if out_dir:
        with open(os.path.join(out_dir, "posiciones.json"), "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1, ensure_ascii=False)
        with open(os.path.join(out_dir, "posiciones.md"), "w", encoding="utf-8") as f:
            f.write(markdown(d))
        with open(os.path.join(out_dir, "dashboard.html"), "w", encoding="utf-8") as f:
            f.write(html(d))
        print(f"Escrito {out_dir}/posiciones.json, posiciones.md, dashboard.html · posiciones: {d['resumen']['n_posiciones']} · errores: {len(ERRORES)}")
        for e in ERRORES:
            print("  -", e)
    elif "--json" in argv:
        print(json.dumps(d, indent=2, ensure_ascii=False))
    else:
        print(markdown(d))


if __name__ == "__main__":
    main(sys.argv[1:])
