#!/usr/bin/env bash
# Code Quality Check: Ruff
# Usage: ./check.sh          (nur Ausgabe)
#        ./check.sh --save   (Ausgabe + speichern in check_result.txt)
#        ./check.sh --fix    (auto-fix Linting + Formatierung)

PYTHON=$([ -f ../.venv/bin/python ] && echo ../.venv/bin/python || echo python3)
VENV_BIN=$(dirname "$PYTHON")
RUFF="${VENV_BIN}/ruff"
command -v "$RUFF" &>/dev/null || RUFF="ruff"

SAVE=false
FIX=false

for arg in "$@"; do
    case "$arg" in
        --save) SAVE=true ;;
        --fix)  FIX=true ;;
    esac
done

run_checks() {
    if ! command -v "$RUFF" &>/dev/null; then
        echo "⚠️  ruff nicht installiert: pip install ruff"
        return
    fi

    if [ "$FIX" = true ]; then
        echo "=== RUFF (Fix Linting) ==="
        $RUFF check --fix .
        echo ""
        echo "=== RUFF (Format) ==="
        $RUFF format .
    else
        echo "=== RUFF (Linting) ==="
        $RUFF check .
        echo ""
        echo "=== RUFF (Formatting) ==="
        $RUFF format --check .
    fi

    echo ""
    echo "✅ Check abgeschlossen: $(date '+%Y-%m-%d %H:%M:%S')"
}

if [ "$SAVE" = true ]; then
    run_checks 2>&1 | tee check_result.txt
    echo ""
    echo "📄 Ergebnis gespeichert: check_result.txt"
else
    run_checks
fi
