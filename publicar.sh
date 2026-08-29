#!/bin/zsh
# LDC — genera el tablero y lo publica en GitHub.
# Lo lanza launchd los sábados a las 08:15 (com.arielsinagra.ldc-pulso.plist)
# y se puede ejecutar a mano en cualquier momento: ./publicar.sh
set -u
REPO="${LDC_REPO:-$HOME/claude_code_app/ldc-pulso}"
LOG="$HOME/Library/Logs/ldc-pulso.log"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

cd "$REPO" || { echo "$(date -u +%FT%TZ) no existe $REPO" >> "$LOG"; exit 1; }
{
  echo "── $(date -u +%FT%TZ) inicio"
  git pull --ff-only --quiet || echo "pull falló (se sigue con la copia local)"
  python3 ldc_tablero.py --out "$REPO" || { echo "script falló"; exit 1; }
  git add tablero.md tablero.json historico/
  if git diff --cached --quiet; then
    echo "sin cambios que publicar"
  else
    git commit --quiet -m "tablero $(date -u +%F)"
    git push --quiet && echo "publicado" || echo "push falló"
  fi
  echo "── fin"
} >> "$LOG" 2>&1
