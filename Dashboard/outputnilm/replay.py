#!/usr/bin/env python3
import json, time, datetime
import paho.mqtt.client as mqtt

# ---------- Config ----------
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC       = "nilm/predictions"
APPLIANCE   = "dishwasher"
STEP        = 1            # sauter 1 point sur n → échantillonnage
SPEED       = 0.05         # délai entre publications
JSON_FILE   = "sample.json"

# Garder seulement les offsets (ts < 1e9) et ignorer les timestamps UNIX
KEEP_ONLY_OFFSETS = True
FIRST_N_POINTS    = 480     # nombre de points à publier (None pour tous)

# ---------- Helpers ----------
def ts_to_iso(base_dt: datetime.datetime, ts_val: float) -> str:
    """Convertit un offset (secondes) OU un timestamp unix en ISO8601 Z."""
    if ts_val >= 1_000_000_000:  # timestamp unix (secondes)
        dt = datetime.datetime.fromtimestamp(ts_val, tz=datetime.timezone.utc)
    else:  # offset à partir de base_dt
        dt = base_dt.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=float(ts_val))
    # format RFC3339Nano pour Telegraf json_time_format = "2006-01-02T15:04:05.999999Z"
    return dt.isoformat(timespec="microseconds").replace("+00:00", "Z")

def publish_once(client: mqtt.Client) -> None:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        blob = json.load(f)

    base_dt = datetime.datetime.fromisoformat(blob["datetime"])
    pred = blob["predictions"][APPLIANCE]
    ts_list = pred["timestamps"]
    agg_list = pred["aggregate_power"]
    pp_list  = pred["predicted_power"]
    st_list  = pred["status"]

    n = min(len(ts_list), len(agg_list), len(pp_list), len(st_list))

    rows = []
    for i in range(0, n, STEP):
        ts_val = float(ts_list[i])

        # Filtrer: on ne garde que les offsets si demandé
        if KEEP_ONLY_OFFSETS and ts_val >= 1_000_000_000:
            continue

        rows.append({
            "appliance": APPLIANCE,                               # "dishwasher"
            "datetime":  ts_to_iso(base_dt, ts_val),              # clé temps utilisée par Telegraf
            "aggregate_power": float(agg_list[i]),                # TOTAL maison
            "predicted_power": float(pp_list[i]),                 # prédiction dishwasher
            "status":          int(st_list[i]),                   # état dishwasher
        })

    # Ordonner strictement par temps (sécurité)
    rows.sort(key=lambda r: r["datetime"])

    # Ne garder que les 480 premiers points si demandé
    if FIRST_N_POINTS is not None:
        rows = rows[:FIRST_N_POINTS]

    # Publication
    count = 0
    for msg in rows:
        client.publish(TOPIC, json.dumps(msg), qos=0)
        count += 1
        time.sleep(SPEED)

    print(f"Publié {count} points ({'offsets only' if KEEP_ONLY_OFFSETS else 'offsets+unix triés'}).")

# ---------- Callbacks ----------
def on_connect(client, userdata, flags, rc, properties=None):
    print("MQTT connected, rc=", rc)

def on_publish(client, userdata, mid):
    pass  # dé-commente pour debug: print("Published mid=", mid)

# ---------- Main ----------
def main():
    client = mqtt.Client()  # Paho v1/v2 compatible avec ces callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    try:
        while True:
            publish_once(client)
            print("Relecture du fichier terminée, attente 5s…")
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
