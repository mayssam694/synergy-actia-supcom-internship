# NILM — MQTT → Telegraf → InfluxDB v2 → Grafana (Docker)

Pipeline temps réel pour la désagrégation d’énergie (NILM) :

```
Python/Replay ──▶ Mosquitto (MQTT) ──▶ Telegraf ──▶ InfluxDB v2 ──▶ Grafana ──▶ index.html 
```

* **Mosquitto** : broker MQTT (topic `nilm/predictions`).
* **Telegraf** : consomme JSON et écrit dans InfluxDB v2.
* **InfluxDB v2** : stockage (bucket `telemetry`).
* **Grafana** : visualisation (datasource InfluxDB v2 + dashboards créés manuellement + iframe dans `index.html`).
* **Python (`replay.py`)** : publie les données de `sample.json` sur MQTT.

---

## 1) Structure du projet

```
OUTPUTNILM/
├─ grafana/
│  └─ provisioning/datasources/influxdb.yml
├─ influxdb/                 # volume persistant
├─ mosquitto/
│  └─ config/mosquitto.conf
├─ telegraf/
│  └─ telegraf.conf
├─ .env
├─ docker-compose.yml
├─ index.html                #  Grafana panels
├─ replay.py                 # publisher Python
└─ sample.json               # dataset NILM (appliance predictions)
```

---

## 2) Pré-requis

* Docker Desktop  + Docker Compose v2
* Python 3.8+

## 3) Installation

### Étape 1 — Créer `.env`

```dotenv
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ORG=Mayssam-Workspace
INFLUXDB_BUCKET=telemetry
INFLUXDB_ADMIN_TOKEN=REPLACE_WITH_TOKEN

GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
MQTT_PORT=1883
```

### Étape 2— Lancer la stack

```bash
docker compose up -d --force-recreate
```

## 4) Publier les données (Publisher Python)

```bash
python replay.py
```

Ce script lit `sample.json` et envoie des points sur le topic `nilm/predictions`.

---

## 5) Accéder à Grafana

* URL : [http://localhost:3000](
* Login : `admin / admin` (par défaut)
* La datasource InfluxDB est déjà provisionnée.

### Créer les dashboards
Chaque utilisateur doit :

1. Aller dans **Dashboards → New → New Dashboard**.
2. Ajouter un **panel**.
3. Dans l’éditeur, écrire manuellement les requêtes Flux. Exemples :

   * **Aggregate + Dishwasher**
from(bucket: "telemetry")
  |> range(start: 2025-08-28T19:51:18Z, stop: 2025-08-28T20:53:58Z)
  |> filter(fn: (r) =>
      r._measurement == "nilm_points" and
      (r._field == "aggregate_power" or r._field == "predicted_power"))
  |> map(fn: (r) => ({ r with
        _field: if r._field == "aggregate_power" then "aggregate_total"
                else "dishwasher_pred"
      }))
  |> keep(columns: ["_time", "_field", "_value"])
  |> sort(columns: ["_time"])
* **Filtrer uniquement dishwasher**

  from(bucket: "telemetry")
  |> range(start: 2025-08-28T19:51:18Z, stop: 2025-08-28T20:53:58Z)
  |> filter(fn: (r) => r._measurement == "nilm_points" and r._field == "predicted_power")
  |> keep(columns: ["_time", "_value"])
  |> rename(columns: {_value: "dishwasher_pred"})
  |> sort(columns: ["_time"])


**Aggregate**
   from(bucket: "telemetry") 
   |> range(start: 2025-08-28T19:51:18Z, stop: 2025-08-28T20:53:58Z) 
   |> filter(fn: (r) => r._measurement == "nilm_points" and r._field == "aggregate_power") 
   |> keep(columns: ["_time", "_value"]) 
   |> rename(columns: {_value: "aggregate_total"}) 
   |> sort(columns: ["_time"])
4. Sauvegarder le dashboard.

> Les iframes définis dans `index.html` utilisent les UIDs des dashboards que tu auras créés à la main.

---

## 6) Intégration HTML

Ouvre `index.html` dans ton navigateur → tu verras les iframes Grafana.

⚠️ Assure-toi d’avoir dans Grafana :

```yaml
environment:
  - GF_SECURITY_ALLOW_EMBEDDING=true
```

## 7) Vérifier les données dans InfluxDB 
type graphe:table
from(bucket: "telemetry")
  |> range(start: time(v: 0))
  |> filter(fn: (r) => r._measurement == "nilm_points" and r.appliance == "dishwasher")
  |> aggregateWindow(every: 10s, fn: last, createEmpty: false)
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> rename(columns: {_time: "time"})
  |> sort(columns: ["time"])
  |> keep(columns: ["time","aggregate_power","predicted_power","status"])
## 8) Étapes pour un nouvel utilisateur

1. Cloner le repo et installer Docker + Python.
2. Remplir `.env` avec les infos InfluxDB (token, org, bucket).
3. Lancer `docker compose up -d`.
4. Vérifier que Grafana est accessible (`http://localhost:3000`).
5. Créer manuellement les dashboards et panels dans Grafana avec les requêtes Flux ci-dessus.
6. Lancer `python replay.py` pour publier les données.
7. Ouvrir `index.html` pour voir les dashboards embarqués.


