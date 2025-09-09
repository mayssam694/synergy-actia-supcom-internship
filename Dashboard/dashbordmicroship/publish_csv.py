#!/usr/bin/env python3
# pip install pandas paho-mqtt python-dateutil

import time
from pathlib import Path
import pandas as pd
from dateutil import tz
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

# ===================== PARAMÈTRES =====================
FRIDGE_CSV = Path("txttocsv\mesuresfridge_puissance_active.csv")
TV_CSV     = Path("txttocsv\mesurestv_puissance_active.csv")
BROKER     = "localhost"
PORT       = 1884
TOPIC      = "home/power"
MEAS       = "power"
INTERVAL_S = 10          # scan toutes les X secondes
START_MODE = "all"       # "all" = envoie l'historique au 1er cycle, "tail" = démarre à la fin
LOCAL_TZ   = tz.gettz("Africa/Tunis")
# ======================================================

# --- helpers -----------------------------------------------------------------
def _read_csv_any(csv_path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(csv_path, sep=None, engine="python", decimal=",")
    except Exception:
        return pd.read_csv(csv_path, sep=None, engine="python", decimal=".")

def _guess_cols(df: pd.DataFrame):
    ts_candidates = [c for c in df.columns if "timestamp" in c.lower()
                     or "date" in c.lower() or "time" in c.lower()]
    if not ts_candidates:
        raise ValueError(f"Aucune colonne de temps trouvée. Colonnes vues: {list(df.columns)}")
    ts_col = ts_candidates[0]

    pwr_candidates = [c for c in df.columns if any(k in c.lower()
                      for k in ["puissance", "watt", "power", "p (w)"])]
    if not pwr_candidates:
        raise ValueError(f"Aucune colonne 'puissance' trouvée. Colonnes vues: {list(df.columns)}")
    return ts_col, pwr_candidates[0]

def _to_epoch_ns(dt_series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(dt_series, dayfirst=True, errors="coerce")
    if parsed.isna().any():
        bad = dt_series[parsed.isna()].head(3)
        raise ValueError(f"Timestamps illisibles (exemples): {list(bad)}")
    localized = parsed.dt.tz_localize(LOCAL_TZ, nonexistent='shift_forward', ambiguous='NaT')
    if localized.isna().any():
        localized = parsed.apply(lambda d: d.replace(tzinfo=LOCAL_TZ))
    return localized.astype("int64")  # évite le FutureWarning

def df_from_csv(csv_path: Path) -> pd.DataFrame:
    df = _read_csv_any(csv_path)
    ts_col, pwr_col = _guess_cols(df)
    out = pd.DataFrame({
        "epoch_ns": _to_epoch_ns(df[ts_col]),
        "watts": pd.to_numeric(df[pwr_col], errors="coerce")
    })
    return out.dropna(subset=["watts"]).sort_values("epoch_ns")

def publish_new_points(client, csv_path: Path, appliance_tag: str,
                       last_sent_ns: int | None) -> int | None:
    """
    Publie seulement les lignes où epoch_ns > last_sent_ns.
    Renvoie le nouveau last_sent_ns (inchangé si rien envoyé).
    """
    if not csv_path.exists():
        print(f"[WARN] Fichier introuvable: {csv_path.resolve()}")
        return last_sent_ns

    df = df_from_csv(csv_path)
    if last_sent_ns is not None:
        df = df[df["epoch_ns"] > last_sent_ns]

    if df.empty:
        return last_sent_ns

    max_ns = last_sent_ns or -1
    for row in df.itertuples(index=False):
        line = f"{MEAS},appliance={appliance_tag} watts={float(row.watts)} {int(row.epoch_ns)}"
        client.publish(TOPIC, payload=line, qos=0, retain=False)
        if row.epoch_ns > max_ns:
            max_ns = int(row.epoch_ns)
    print(f"[INFO] {appliance_tag}: +{len(df)} points envoyés")
    return max_ns

# --- main loop ---------------------------------------------------------------
def main():
    # MQTT
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    # États: dernier timestamp publié pour chaque appareil
    last_sent = {"fridge": None, "tv": None}

    # Mode "tail": démarre à la fin (n'envoie pas l'historique)
    if START_MODE == "tail":
        for tag, p in (("fridge", FRIDGE_CSV), ("tv", TV_CSV)):
            if p.exists():
                try:
                    last_sent[tag] = int(df_from_csv(p)["epoch_ns"].max())
                except Exception:
                    last_sent[tag] = None

    print(f"Daemon démarré (scan {INTERVAL_S}s). Ctrl+C pour arrêter.")
    try:
        while True:
            try:
                last_sent["fridge"] = publish_new_points(client, FRIDGE_CSV, "fridge", last_sent["fridge"])
                last_sent["tv"]     = publish_new_points(client, TV_CSV,     "tv",     last_sent["tv"])
            except Exception as e:
                print(f"[WARN] Cycle erreur: {e}")
            time.sleep(INTERVAL_S)
    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
        print("Bye.")

if __name__ == "__main__":
    main()
