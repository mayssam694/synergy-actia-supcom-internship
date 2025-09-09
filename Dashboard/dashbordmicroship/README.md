# NILM — MQTT → Telegraf → InfluxDB v2 → Grafana (Docker)

Pipeline temps réel pour la désagrégation d’énergie (NILM) :

```
Python/Replay ──▶ Mosquitto (MQTT) ──▶ Telegraf ──▶ InfluxDB v2 ──▶ Grafana ──▶ index.html 
```

* **Mosquitto** : broker MQTT (topic `home/power`).
* **Telegraf** : consomme JSON et écrit dans InfluxDB v2.
* **InfluxDB v2** : stockage (bucket `fridge_tv_data`).
* **Grafana** : visualisation (datasource InfluxDB v2 + dashboards créés manuellement + iframe dans `index.html`).
* **Python (`publish_csv.py`)** : publie les données de `mesurestv_puissance_active.csv` et `mesuresfridge_puissance_active.csv` sur MQTT.

---

## 1) Structure du projet

```
DASHBORDMICROSHIP/
├─ grafana/
│  └─ provisioning/datasources/influxdb.yml
├─ influxdb/                 # volume persistant
├─ mosquitto/
│  └─ mosquitto.conf
├─ telegraf/
│  └─ telegraf.conf
├─ .env
├─ docker-compose.yml
├─ index.html                # embed Grafana panels
├─ publish_csv.py                 # publisher Python
└─                
```

---

## 2) Pré-requis

* Docker Desktop + Docker Compose v2
* Python 3.8+

## 3) Installation

### Étape 1 — Créer `.env`

```dotenv
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ORG=Mayssam-Workspace
INFLUXDB_BUCKET=fridge_tv_data
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
python publish_csv.py
```

Ce script lit `mesurestv_puissance_active.csv` et `mesuresfridge_puissance_active.csv` et envoie des points sur le topic `home/power`.

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

   * **Fridge**

  from(bucket: "fridge_tv_data")
  |> range(start: 2025-08-25T10:28:02Z, stop: 2025-08-25T11:41:12Z)
  |> filter(fn: (r) => r._measurement == "power" and r._field == "watts" and r.appliance == "fridge")
  |> group(columns: ["_measurement","appliance"])
  |> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
  |> filter(fn: (r) => r._value >= 0.0 and r._value <= 200.0)   // borne plausible pour un frigo

* **TV**

from(bucket: "fridge_tv_data")
  |> range(start: 2025-08-25T12:36:37Z, stop: 2025-08-25T13:38:37Z)
  |> filter(fn: (r) => r._measurement == "power")
  |> filter(fn: (r) => r._field == "watts")
  |> filter(fn: (r) => r.appliance == "tv")
  |> aggregateWindow(every: 1s, fn: last, createEmpty: false)

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

---
## 7) Étapes pour un nouvel utilisateur

1. Cloner le repo et installer Docker + Python.
2. Remplir `.env` avec les infos InfluxDB (token, org, bucket).
3. Lancer `docker compose up -d`.
4. Vérifier que Grafana est accessible (`http://localhost:3000`).
5. Créer manuellement les dashboards et panels dans Grafana avec les requêtes Flux ci-dessus.
6. Lancer `python replay.py` pour publier les données.
7. Ouvrir `index.html` pour voir les dashboards embarqués.


