import sqlite3
import pandas as pd

# Pfade zu deinen SQLite-Dateien
db1_file = "data/sensors_2026.db"
db2_file = "../data/sensors_2026.db"

table = "hourly_values"
keys = ["sensor_id", "hour"]


def get_data(db_path, table_name, index_keys):
    """Lädt die Daten und setzt den zusammengesetzten Index."""
    conn = sqlite3.connect(db_path)
    with conn:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    df.set_index(index_keys, inplace=True)
    return df


# 1. Daten laden
df1 = get_data(db1_file, table, keys)
df2 = get_data(db2_file, table, keys)

# 2. Nur Zeilen mit gleichen IDs heraussuchen
common_ids = df1.index.intersection(df2.index)
df1_c = df1.loc[common_ids].sort_index()
df2_c = df2.loc[common_ids].sort_index()

# 3. Maske für unterschiedliche Werte erstellen
diff_mask = df1_c != df2_c
rows_with_diff = diff_mask.any(axis=1)

# 4. Schöne Vergleichstabelle bauen, wenn Unterschiede existieren
if rows_with_diff.any():
    print(f"\n🔎 Unterschiede in Tabelle '{table}':")

    # Filtert nur die Zeilen und Spalten, die sich tatsächlich unterscheiden
    df1_diff = df1_c[rows_with_diff]
    df2_diff = df2_c[rows_with_diff]

    # Nutzt die Pandas-eigene Compare-Funktion für die Nebeneinander-Darstellung
    result = df1_diff.compare(df2_diff, keep_shape=False, keep_equal=False)

    # Spalten für die Anzeige umbenennen (self -> db1, other -> db2)
    result.rename(columns={"self": "db1", "other": "db2"}, inplace=True)

    # Zeige alle Zeilen ohne Kürzung an
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None
    ):
        print(result)
else:
    print(
        f"\n✅ Keine Inhaltsunterschiede in den gemeinsamen Zeilen von '{table}' gefunden."
    )
