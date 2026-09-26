"""Pruebas sin red del lector de posiciones. Ejecutar: python3 -m unittest tests/test_lp_posiciones.py
Cubren: base58, PDA, keccak/selector, matemática de rango, decodificación de
cuentas sintéticas de Orca, Raydium y Aerodrome, y las métricas del protocolo."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lp_posiciones as lp  # noqa: E402

CFG = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "posiciones.config.json")))
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
CBBTC = "cbbtcf3aa214zXHbiAZQwf4122FBYbraNdFqgw4iMij"
MERCADO = {"btc_precio": 80000.0, "btc_fuente": "test", "atr_pct": 3.0, "atr_dias": 14,
           "h4_cierre": 80500.0, "h4_hora_utc": "2026-09-26 08:00", "eurusd": 1.17}


def tick_de_precio(p, d0, d1):
    """tick tal que 1.0001^tick = p·10^(d1−d0)"""
    import math
    return round(math.log(p * 10 ** (d1 - d0), 1.0001))


class Codificacion(unittest.TestCase):
    def test_base58_ida_y_vuelta(self):
        for s in (USDC, "11111111111111111111111111111111", lp.b58encode(b"\x00\x00\x01\xff")):
            self.assertEqual(lp.b58encode(lp.b58decode(s)), s)

    def test_pda_fuera_de_curva(self):
        prog = lp.b58decode(CFG["contratos"]["orca_whirlpool_program"])
        pda, bump = lp.find_program_address([b"position", lp.b58decode(USDC)], prog)
        self.assertEqual(len(pda), 32)
        self.assertFalse(lp._en_curva(pda))
        self.assertTrue(0 <= bump <= 255)

    def test_pda_orca_sol_usdc_conocida(self):
        """Whirlpool SOL/USDC ts=4 (Czfq…44zE, mainnet). Verifica base58 y PDA contra una dirección real."""
        prog = lp.b58decode(CFG["contratos"]["orca_whirlpool_program"])
        cfg_ = lp.b58decode("2LecshUwdy9xi7meFgHtFJQNSKk4KdTrcpvaB56dP2NQ")
        sol = lp.b58decode("So11111111111111111111111111111111111111112")
        pda, _ = lp.find_program_address([b"whirlpool", cfg_, sol, lp.b58decode(USDC), (4).to_bytes(2, "little")], prog)
        self.assertEqual(lp.b58encode(pda), "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE")

    def test_keccak_y_selector(self):
        self.assertEqual(lp.keccak256(b"").hex(), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
        self.assertEqual(lp.selector("transfer(address,uint256)"), "a9059cbb")
        self.assertEqual(lp.SEL["balanceOf"], "70a08231")


class Matematica(unittest.TestCase):
    def test_cantidades_en_bordes(self):
        a, b = lp.sqrt_precio_tick(-1000), lp.sqrt_precio_tick(1000)
        x0, x1 = lp.cantidades(10 ** 12, a, a, b)
        self.assertGreater(x0, 0); self.assertEqual(x1, 0)
        x0, x1 = lp.cantidades(10 ** 12, b, a, b)
        self.assertEqual(x0, 0); self.assertGreater(x1, 0)
        x0, x1 = lp.cantidades(10 ** 12, 1.0, a, b)
        self.assertGreater(x0, 0); self.assertGreater(x1, 0)

    def test_fee_growth_inside_dentro(self):
        M = 2 ** 128
        self.assertEqual(lp.fee_growth_inside(1000, 100, 200, -10, 10, 0, M), 700)


def cuenta_orca_posicion(whirlpool_b, mint_b, liq, tl, tu, owed_a=0, owed_b=0):
    b = bytearray(216)
    b[8:40] = whirlpool_b; b[40:72] = mint_b
    b[72:88] = liq.to_bytes(16, "little")
    b[88:92] = tl.to_bytes(4, "little", signed=True); b[92:96] = tu.to_bytes(4, "little", signed=True)
    b[112:120] = owed_a.to_bytes(8, "little"); b[136:144] = owed_b.to_bytes(8, "little")
    return bytes(b)


def cuenta_orca_whirlpool(mint_a_b, mint_b_b, sqrt_x64, tick_cur, fee_rate=3000, ts=64):
    b = bytearray(8 + 261 + 384)
    b[41:43] = ts.to_bytes(2, "little"); b[45:47] = fee_rate.to_bytes(2, "little")
    b[65:81] = sqrt_x64.to_bytes(16, "little"); b[81:85] = tick_cur.to_bytes(4, "little", signed=True)
    b[101:133] = mint_a_b; b[181:213] = mint_b_b
    return bytes(b)


class RPCFalsoSolana:
    def __init__(self, cuentas):
        self.tabla = cuentas
    def cuentas(self, keys):
        return {k: self.tabla[k] for k in keys if k in self.tabla}
    def decimales_mint(self, m):
        return None


class Orca(unittest.TestCase):
    def test_posicion_btc_usdc_en_rango(self):
        prog = CFG["contratos"]["orca_whirlpool_program"]
        mint_nft = "BPFLoaderUpgradeab1e11111111111111111111111"  # cualquier pubkey sirve de mint sintético
        whirl = "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE"
        # Pool cbBTC(8)/USDC(6): precio 80.000 USDC por cbBTC → precio crudo = 80000·10^(6−8) = 800
        import math
        tick_cur = tick_de_precio(80000, 8, 6)
        sqrt_x64 = int(math.sqrt(1.0001 ** tick_cur) * 2 ** 64)
        tl, tu = tick_de_precio(70000, 8, 6), tick_de_precio(90000, 8, 6)
        pda, _ = lp.find_program_address([b"position", lp.b58decode(mint_nft)], lp.b58decode(prog))
        rpc = RPCFalsoSolana({
            lp.b58encode(pda): (cuenta_orca_posicion(lp.b58decode(whirl), lp.b58decode(mint_nft), 5 * 10 ** 9, tl, tu, owed_a=1000, owed_b=250000), prog),
            whirl: (cuenta_orca_whirlpool(lp.b58decode(CBBTC), lp.b58decode(USDC), sqrt_x64, tick_cur), prog),
        })
        lp.ERRORES.clear(); lp.NOTAS.clear()
        pos = lp.leer_orca(rpc, "wallet", [mint_nft], CFG)
        self.assertEqual(len(pos), 1)
        p = lp.enriquecer(pos[0], CFG, MERCADO, None, {}, rpc, None)
        self.assertEqual(p["par"], "cbBTC/USDC")
        self.assertTrue(p["en_rango"])
        self.assertAlmostEqual(p["precio"], 80000, delta=80000 * 0.0002)
        self.assertAlmostEqual(p["rango_inf"], 70000, delta=70000 * 0.0002)
        self.assertAlmostEqual(p["rango_sup"], 90000, delta=90000 * 0.0002)
        self.assertAlmostEqual(p["dist_inf_atr"], 12.5 / 3.0, places=1)
        self.assertEqual(p["situacion"], "EN RANGO")
        self.assertFalse(p["h4_fuera"])
        self.assertIsNotNone(p["valor_usd"])
        # fees: 1000 sat cbBTC + 0.25 USDC
        self.assertAlmostEqual(p["fees_usd"], 1000 / 1e8 * 80000 + 0.25, places=4)

    def test_stop_por_cierre_h4(self):
        prog = CFG["contratos"]["orca_whirlpool_program"]
        mint_nft = "BPFLoaderUpgradeab1e11111111111111111111111"
        whirl = "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE"
        import math
        tick_cur = tick_de_precio(80000, 8, 6)
        sqrt_x64 = int(math.sqrt(1.0001 ** tick_cur) * 2 ** 64)
        tl, tu = tick_de_precio(70000, 8, 6), tick_de_precio(80200, 8, 6)  # cierre H4 80.500 queda fuera
        pda, _ = lp.find_program_address([b"position", lp.b58decode(mint_nft)], lp.b58decode(prog))
        rpc = RPCFalsoSolana({
            lp.b58encode(pda): (cuenta_orca_posicion(lp.b58decode(whirl), lp.b58decode(mint_nft), 10 ** 9, tl, tu), prog),
            whirl: (cuenta_orca_whirlpool(lp.b58decode(CBBTC), lp.b58decode(USDC), sqrt_x64, tick_cur), prog),
        })
        p = lp.enriquecer(lp.leer_orca(rpc, "w", [mint_nft], CFG)[0], CFG, MERCADO, None, {}, rpc, None)
        self.assertTrue(p["h4_fuera"])
        self.assertEqual(p["situacion"], "STOP")

    def test_il_con_datos_manuales(self):
        prog = CFG["contratos"]["orca_whirlpool_program"]
        mint_nft = "BPFLoaderUpgradeab1e11111111111111111111111"
        whirl = "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE"
        import math
        tick_cur = tick_de_precio(80000, 8, 6)
        sqrt_x64 = int(math.sqrt(1.0001 ** tick_cur) * 2 ** 64)
        tl, tu = tick_de_precio(70000, 8, 6), tick_de_precio(90000, 8, 6)
        pda, _ = lp.find_program_address([b"position", lp.b58decode(mint_nft)], lp.b58decode(prog))
        rpc = RPCFalsoSolana({
            lp.b58encode(pda): (cuenta_orca_posicion(lp.b58decode(whirl), lp.b58decode(mint_nft), 5 * 10 ** 9, tl, tu), prog),
            whirl: (cuenta_orca_whirlpool(lp.b58decode(CBBTC), lp.b58decode(USDC), sqrt_x64, tick_cur), prog),
        })
        man = {mint_nft: {"clave": mint_nft, "fecha_entrada": "2026-09-01T00:00:00Z", "precio_entrada": 75000,
                          "token_base_entrada": 0.0025, "token_cot_entrada": 200.0, "capital_usd": 400, "cobros_usd": 3.0}}
        p = lp.enriquecer(lp.leer_orca(rpc, "w", [mint_nft], CFG)[0], CFG, MERCADO, None, man, rpc, None)
        self.assertTrue(p["manual"])
        self.assertGreater(p["dias_abierta"], 20)
        # HODL: 0.0025·80000 + 200 = 400 ; entrada: 0.0025·75000 + 200 = 387.5 → exposición +12.5
        self.assertAlmostEqual(p["exposicion_usd"], 12.5, places=6)
        self.assertEqual(p["il_usd"], p["valor_usd"] - 400.0)
        self.assertAlmostEqual(p["earn_usd"], 3.0 + (p["fees_usd"] or 0.0), places=9)


def cuenta_ray_posicion(mint_b, pool_b, liq, tl, tu, owed0=0, owed1=0):
    b = bytearray(281)
    b[9:41] = mint_b; b[41:73] = pool_b
    b[73:77] = tl.to_bytes(4, "little", signed=True); b[77:81] = tu.to_bytes(4, "little", signed=True)
    b[81:97] = liq.to_bytes(16, "little")
    b[129:137] = owed0.to_bytes(8, "little"); b[137:145] = owed1.to_bytes(8, "little")
    return bytes(b)


def cuenta_ray_pool(cfg_b, mint0_b, mint1_b, dec0, dec1, sqrt_x64, tick_cur, ts=1):
    b = bytearray(1544)
    b[9:41] = cfg_b; b[73:105] = mint0_b; b[105:137] = mint1_b
    b[233] = dec0; b[234] = dec1; b[235:237] = ts.to_bytes(2, "little")
    b[253:269] = sqrt_x64.to_bytes(16, "little"); b[269:273] = tick_cur.to_bytes(4, "little", signed=True)
    return bytes(b)


class Raydium(unittest.TestCase):
    def test_estable_usdc_usdt_fuera_de_rango(self):
        prog = CFG["contratos"]["raydium_clmm_program"]
        USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
        mint_nft = "BPFLoaderUpgradeab1e11111111111111111111111"
        pool = "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE"
        amm = "2LecshUwdy9xi7meFgHtFJQNSKk4KdTrcpvaB56dP2NQ"
        import math
        tick_cur = tick_de_precio(1.0020, 6, 6)      # USDT por USDC = 1.002 → fuera del rango 0.998–1.001
        sqrt_x64 = int(math.sqrt(1.0001 ** tick_cur) * 2 ** 64)
        tl, tu = tick_de_precio(0.998, 6, 6), tick_de_precio(1.001, 6, 6)
        pda, _ = lp.find_program_address([b"position", lp.b58decode(mint_nft)], lp.b58decode(prog))
        cfgb = bytearray(117); cfgb[47:51] = (100).to_bytes(4, "little")  # trade_fee_rate 100 = 1 bp
        rpc = RPCFalsoSolana({
            lp.b58encode(pda): (cuenta_ray_posicion(lp.b58decode(mint_nft), lp.b58decode(pool), 10 ** 9, tl, tu), prog),
            pool: (cuenta_ray_pool(lp.b58decode(amm), lp.b58decode(USDC), lp.b58decode(USDT), 6, 6, sqrt_x64, tick_cur), prog),
            amm: (bytes(cfgb), prog),
        })
        pos = lp.leer_raydium(rpc, "w", [mint_nft], CFG)
        self.assertEqual(len(pos), 1)
        self.assertAlmostEqual(pos[0]["fee_bps"], 1.0)
        p = lp.enriquecer(pos[0], CFG, MERCADO, None, {}, rpc, None)
        self.assertEqual(p["tipo"], "estable-usd")
        self.assertFalse(p["en_rango"])
        self.assertEqual(p["situacion"], "FUERA DE RANGO")
        self.assertEqual(p["base_amt"], 0.0)  # precio por encima del rango: todo en token1 (USDT), token0 agotado
        self.assertGreater(p["base_amt"] + p["cot_amt"], 0)


class RPCFalsoEvm:
    def __init__(self, respuestas):
        self.r = respuestas
    def call(self, to, data):
        return self.r.get((to.lower(), data[:8]), None) if (to.lower(), data[:8]) in self.r else self.r.get((to.lower(), data))


class Aerodrome(unittest.TestCase):
    def test_posicion_stakeada_por_gauge(self):
        cfg = json.loads(json.dumps(CFG))
        cfg["pools_aerodrome"] = ["0x000000000000000000000000000000000000AAAA"]
        npm = cfg["contratos"]["aerodrome_slipstream_nft_manager"].lower()
        fab = cfg["contratos"]["aerodrome_slipstream_factory"].lower()
        pool = "0x000000000000000000000000000000000000aaaa"
        gauge = "0x000000000000000000000000000000000000bbbb"
        usdc = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"; cbbtc = "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"
        import math
        # token0 = USDC(6), token1 = cbBTC(8): precio crudo token1/token0 = (1/80000)·10^(8−6)... = 0.00125·100 = 0.125
        tick_cur = round(math.log(1 / 80000 * 10 ** (8 - 6), 1.0001))
        sqrt96 = int(math.sqrt(1.0001 ** tick_cur) * 2 ** 96)
        tl = round(math.log(1 / 90000 * 10 ** (8 - 6), 1.0001)); tu = round(math.log(1 / 70000 * 10 ** (8 - 6), 1.0001))
        wallet = "0x1111111111111111111111111111111111111111"
        tid = 4242
        pos_words = [0, 0, int(usdc, 16), int(cbbtc, 16), 100 % 2 ** 256, tl % 2 ** 256, tu % 2 ** 256, 10 ** 12, 0, 0, 5 * 10 ** 6, 1000]
        r = {
            (npm, lp.SEL["balanceOf"]): [0],
            (pool, lp.SEL["gauge"]): [int(gauge, 16)],
            (gauge, lp.SEL["stakedValues"]): [0x20, 1, tid],
            (npm, lp.SEL["positions"]): pos_words,
            (fab, lp.SEL["getPool"]): [int(pool, 16)],
            (pool, lp.SEL["slot0"]): [sqrt96, tick_cur % 2 ** 256, 0, 0, 0, 1],
            (pool, lp.SEL["fee"]): [500],
            (pool, lp.SEL["fgg0"]): None, (pool, lp.SEL["fgg1"]): None,
        }
        rpc = RPCFalsoEvm(r)
        lp.NOTAS.clear()
        pos = lp.leer_aerodrome(rpc, wallet, cfg)
        self.assertEqual(len(pos), 1)
        self.assertTrue(pos[0]["stakeada"])
        self.assertAlmostEqual(pos[0]["fee_bps"], 5.0)
        p = lp.enriquecer(pos[0], cfg, MERCADO, None, {}, None, rpc)
        self.assertEqual(p["par"], "cbBTC/USDC")   # orientado a BTC como base aunque sea token1
        self.assertAlmostEqual(p["precio"], 80000, delta=80000 * 0.0002)
        self.assertAlmostEqual(p["rango_inf"], 70000, delta=70000 * 0.0003)
        self.assertAlmostEqual(p["rango_sup"], 90000, delta=90000 * 0.0003)
        self.assertTrue(p["en_rango"])
        self.assertAlmostEqual(p["fees_usd"], 5.0 + 1000 / 1e8 * 80000, places=6)


class Salidas(unittest.TestCase):
    def test_markdown_y_html_sin_posiciones(self):
        d = {"version_script": "1.0", "generado_utc": "2026-09-26T12:00:00+00:00", "mercado": MERCADO,
             "wallets": {"solana": [], "base": []}, "parametros": CFG["parametros"],
             "resumen": {"n_posiciones": 0, "valor_usd": None, "fees_pendientes_usd": None, "alertas": []},
             "posiciones": [], "solo_manual": [], "tablero": {"ultima_vela": None, "regimen": None, "rv30": None, "drift": None},
             "notas": [], "errores": []}
        md = lp.markdown(d)
        self.assertIn("Sin posiciones abiertas", md)
        h = lp.html(d)
        self.assertIn('"n_posiciones": 0', h)
        self.assertNotIn("/*__DATOS__*/null", h)


if __name__ == "__main__":
    unittest.main()
