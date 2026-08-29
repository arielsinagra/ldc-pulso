# ldc-pulso

Tablero de datos del Pulso LDC (Laboratorio DeFi Crypto). Lo genera `ldc_tablero.py`
en el iMac los sábados a las 08:15 y lo publica aquí; la tarea programada de Claude
lo lee a las 09:00 desde `raw.githubusercontent.com`.

Contenido: precios, volatilidad realizada e implícita de BTC, régimen, anchura de
rango y break-even de un LP concentrado, TVL, derivados, stablecoins, y escaneo de
pools en Orca, Raydium y Aerodrome. Solo datos públicos. No emite dirección.

- `tablero.md` — última ejecución, legible
- `tablero.json` — la misma ejecución, completa (incluye todos los pools escaneados)
- `historico/AAAA-MM-DD.json` — una copia por ejecución, para recalibrar umbrales

Uso manual: `python3 ldc_tablero.py` (markdown por pantalla) o `./publicar.sh`
(genera y publica). Solo librería estándar de Python; sin claves.

## Automatización

`com.arielsinagra.ldc-pulso.plist` es la fuente del agente launchd que ejecuta
`publicar.sh` los sábados a las 08:15 (hora local del Mac). La copia que corre de
verdad vive en `~/Library/LaunchAgents/`; este archivo es solo la fuente versionada.
Si se cambia, hay que reinstalarla para que launchd la recargue:

```sh
cp com.arielsinagra.ldc-pulso.plist ~/Library/LaunchAgents/
launchctl bootout   gui/$(id -u)/com.arielsinagra.ldc-pulso
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.arielsinagra.ldc-pulso.plist
```

`launchctl kickstart -k gui/$(id -u)/com.arielsinagra.ldc-pulso` fuerza una ejecución
inmediata. El registro queda en `~/Library/Logs/ldc-pulso.log`.
