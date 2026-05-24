#!/bin/bash

###############################################################################
# Historische Sensor-Daten vom Server importieren
#
# Verwendung:
#
#   ./import_from_server.sh
#       -> aktuelles + vorheriges Jahr
#
#   ./import_from_server.sh 2025
#       -> nur Jahr 2025
#
#   ./import_from_server.sh 2013 2026
#       -> Bereich 2013 bis 2026
#
# Version: 2026.05.12 18:16
#
###############################################################################

# -----------------------------------------------------------------------------
# Konfiguration
# -----------------------------------------------------------------------------

SERVER="smarthomedata"

# Python-Script auf dem Remote-Server
REMOTE_SCRIPT="~/getpokeydata.py"

# -----------------------------------------------------------------------------
# Lokale Pfade
# -----------------------------------------------------------------------------

# Absoluter Pfad des aktuellen Script-Verzeichnisses
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Zielordner für heruntergeladene Datenbanken
LOCAL_DATA_DIR="$SCRIPT_DIR/data"

# Ordner sicherstellen
mkdir -p "$LOCAL_DATA_DIR"

# -----------------------------------------------------------------------------
# Anzeige leeren
# -----------------------------------------------------------------------------

clear

echo "============================================================"
echo " Starte Datenimport vom Server"
echo "============================================================"
echo ""

# -----------------------------------------------------------------------------
# Remote Python-Import starten
# -----------------------------------------------------------------------------

if [ $# -eq 2 ]; then

    START_YEAR="$1"
    END_YEAR="$2"

    echo "Importiere Jahre $START_YEAR bis $END_YEAR ..."
    echo ""

    ssh -t "$SERVER" \
        "cd ~ && python3 getpokey_data.py ${START_YEAR}-${END_YEAR}"

elif [ $# -eq 1 ]; then

    YEAR="$1"

    echo "Importiere Jahr $YEAR ..."
    echo ""

    ssh -t "$SERVER" \
        "cd ~ && python3 getpokey_data.py $YEAR"

else

    CURRENT_YEAR=$(date +%Y)
    PREVIOUS_YEAR=$((CURRENT_YEAR - 1))

    echo "Importiere Standardjahre:"
    echo "  $PREVIOUS_YEAR"
    echo "  $CURRENT_YEAR"
    echo ""

    ssh -t "$SERVER" \
        "cd ~ && python3 getpokeydata.py"
fi

# Fehlerprüfung SSH
if [ $? -ne 0 ]; then
    echo ""
    echo "FEHLER: Remote-Import fehlgeschlagen."
    exit 1
fi

# -----------------------------------------------------------------------------
# Datenbanken herunterladen
# -----------------------------------------------------------------------------

echo ""
echo "============================================================"
echo " Lade Datenbanken herunter"
echo "============================================================"
echo ""

if [ $# -eq 2 ]; then

    for ((YEAR=$START_YEAR; YEAR<=$END_YEAR; YEAR++)); do

        FILE="sensors_${YEAR}.db"

        echo "Lade $FILE herunter ..."

        scp "$SERVER":~/"$FILE" "$LOCAL_DATA_DIR/"

        if [ $? -ne 0 ]; then
            echo "WARNUNG: Datei $FILE konnte nicht geladen werden."
        fi
    done

elif [ $# -eq 1 ]; then

    FILE="sensors_${YEAR}.db"

    echo "Lade $FILE herunter ..."

    scp "$SERVER":~/"$FILE" "$LOCAL_DATA_DIR/"

    if [ $? -ne 0 ]; then
        echo "WARNUNG: Datei $FILE konnte nicht geladen werden."
    fi

else

    FILE1="sensors_${PREVIOUS_YEAR}.db"
    FILE2="sensors_${CURRENT_YEAR}.db"

    echo "Lade $FILE1 herunter ..."
    scp "$SERVER":~/"$FILE1" "$LOCAL_DATA_DIR/"

    echo "Lade $FILE2 herunter ..."
    scp "$SERVER":~/"$FILE2" "$LOCAL_DATA_DIR/"
fi

# -----------------------------------------------------------------------------
# Ergebnis anzeigen
# -----------------------------------------------------------------------------

echo ""
echo "============================================================"
echo " Heruntergeladene Dateien"
echo "============================================================"
echo ""

ls -lh "$LOCAL_DATA_DIR"/sensors_*.db 2>/dev/null
