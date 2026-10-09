"""Genera y carga los datos sinteticos de la planta ficticia.

Todo sale de una semilla fija: dos corridas producen exactamente los mismos datos, por lo que
las respuestas esperadas del conjunto de evaluacion no cambian.

Uso: python scripts/seed.py
Requiere DATABASE_URL y haber corrido scripts/setup_db.py.
"""

from __future__ import annotations

import math
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SEED = 42
TZ = timezone(timedelta(hours=-3))
START = datetime(2026, 9, 1, 0, 0, tzinfo=TZ)
STEP_HOURS = 2
N_READINGS = 360  # 30 dias, una lectura cada 2 horas: del 2026-09-01 00:00 al 2026-09-30 22:00
DATA_END_DATE = date(2026, 9, 30)

AREAS = [
    ("Toma de agua", "Captacion del agua cruda desde la fuente."),
    ("Bombeo de agua", "Impulsion del agua hacia las lineas de tratamiento."),
    ("Tratamiento primario", "Sedimentacion y remocion de solidos gruesos."),
    ("Tratamiento secundario", "Tratamiento biologico y ajuste de calidad."),
    ("Filtros", "Filtrado final del agua tratada."),
    ("Compresores de aire", "Sala de compresores de aire de planta."),
    ("Aire de instrumentos", "Linea de aire seco para instrumentos y valvulas."),
    ("Enfriamiento", "Torres y circuitos de agua de enfriamiento."),
    ("Calderas", "Generacion de vapor para procesos."),
    ("Sala de tableros", "Tableros de distribucion y control de motores."),
    ("Sala de transformadores", "Transformadores de la subestacion interna."),
    ("Extraccion de aire", "Ventilacion y extraccion de las naves."),
    ("Molienda", "Linea de molienda de materias primas."),
    ("Mezclado", "Linea de mezclado y dosificacion."),
    ("Envasado", "Linea de envasado y etiquetado."),
    ("Almacenamiento", "Deposito de producto terminado."),
    ("Servicios auxiliares", "Servicios generales de la planta."),
    ("Taller de mantenimiento", "Taller y banco de pruebas de mantenimiento."),
]
AREA_ID = {name: i + 1 for i, (name, _) in enumerate(AREAS)}

FIRST = ["Lucas", "Martina", "Joaquin", "Valentina", "Mateo", "Camila", "Tomas", "Julieta", "Nicolas", "Agustina",
         "Franco", "Sofia", "Bruno", "Carolina", "Emiliano", "Paula", "Ramiro", "Lorena", "Gonzalo", "Mariana"]
LAST = ["Ferreyra", "Acosta", "Benitez", "Cabrera", "Dominguez", "Echeverria", "Fontana", "Gimenez", "Herrera",
        "Ibarra", "Juarez", "Leiva", "Molina", "Navarro", "Ortiz", "Paredes", "Quiroga", "Rojas", "Sosa", "Villalba"]

# (tipo, prefijo del codigo, primer numero, cantidad, fabricantes, areas posibles, magnitudes)
EQUIPMENT_SPEC = [
    ("bomba", "P", 101, 10, ["Hidrotec", "Aquamar", "Flujosur"],
     ["Toma de agua", "Bombeo de agua", "Tratamiento primario", "Tratamiento secundario", "Filtros"],
     ["vibracion", "presion", "temperatura"]),
    ("motor", "M", 301, 10, ["Motrex", "Electrodina", "Rotomax"],
     ["Bombeo de agua", "Tratamiento primario", "Compresores de aire", "Molienda", "Mezclado", "Envasado"],
     ["temperatura", "vibracion", "corriente"]),
    ("compresor", "C", 201, 8, ["Aerocomp", "Presurizar", "Neumatec"],
     ["Compresores de aire", "Aire de instrumentos", "Enfriamiento"],
     ["presion", "temperatura", "vibracion"]),
    ("ventilador", "V", 401, 6, ["Ventix", "Aerflow"],
     ["Extraccion de aire", "Calderas", "Enfriamiento"],
     ["vibracion", "corriente"]),
    ("transformador", "T", 501, 6, ["Voltara", "Transelec"],
     ["Sala de transformadores", "Sala de tableros", "Servicios auxiliares"],
     ["temperatura", "corriente"]),
]
NAME_BASE = {
    "bomba": "Bomba centrifuga",
    "motor": "Motor electrico",
    "compresor": "Compresor de tornillo",
    "ventilador": "Ventilador axial",
    "transformador": "Transformador de distribucion",
}
UNITS = {"temperatura": "C", "vibracion": "mm/s", "presion": "bar", "corriente": "A"}
SPECIALTY_FOR = {
    "vibracion": "mecanica",
    "temperatura": "lubricacion",
    "presion": "instrumentacion",
    "corriente": "electrica",
}
PREVENTIVE_TEXT = {
    "bomba": "Mantenimiento preventivo de bomba: inspeccion de sello mecanico, rodamientos y alineacion.",
    "motor": "Mantenimiento preventivo de motor: lubricacion de rodamientos, limpieza y medicion de aislacion.",
    "compresor": "Mantenimiento preventivo de compresor: cambio de filtros, revision de aceite y valvulas.",
    "ventilador": "Mantenimiento preventivo de ventilador: balanceo de rotor y revision de correas.",
    "transformador": "Mantenimiento preventivo de transformador: inspeccion termografica y ajuste de bornes.",
}
CORRECTIVE_TEXT = {
    "vibracion": "Correccion por vibracion elevada: revision de rodamientos, alineacion y fijaciones.",
    "temperatura": "Correccion por temperatura elevada: revision de lubricacion y ventilacion.",
    "presion": "Correccion por presion fuera de rango: revision de valvulas, sellos y filtros.",
    "corriente": "Correccion por corriente elevada: revision de conexiones y carga del equipo.",
}

# Episodios que se fuerzan para que existan casos conocidos en las preguntas de evaluacion.
# (codigo, magnitud) -> lista de (indice de inicio, largo en lecturas, severidad)
FORCED = {
    ("C-201", "vibracion"): [(40, 4, "alerta"), (150, 5, "critica"), (300, 4, "critica")],
    ("P-101", "vibracion"): [(60, 4, "critica"), (210, 3, "alerta")],
    ("P-101", "presion"): [(120, 4, "alerta")],
    ("M-301", "temperatura"): [(90, 5, "critica"), (330, 4, "alerta")],
    # Alarmas que siguen abiertas al final del periodo (la ultima lectura sigue sobre el umbral).
    ("V-401", "vibracion"): [(355, 5, "critica")],
    ("T-501", "temperatura"): [(356, 4, "alerta")],
    ("P-103", "presion"): [(357, 3, "alerta")],
}


def _round(value: float, digits: int = 2) -> float:
    return round(value, digits)


def generate_dataset(seed: int = SEED) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(seed)

    areas = [{"id": i + 1, "nombre": n, "descripcion": d} for i, (n, d) in enumerate(AREAS)]

    names = [f"{f} {l}" for f, l in zip(rng.sample(FIRST, len(FIRST)), rng.sample(LAST, len(LAST)))]
    specialties = (["mecanica"] * 6) + (["electrica"] * 5) + (["instrumentacion"] * 5) + (["lubricacion"] * 4)
    turnos = ["manana", "tarde", "noche"]
    tecnicos = []
    for i in range(20):
        tecnicos.append({
            "id": i + 1,
            "nombre": names[i],
            "especialidad": specialties[i],
            "turno": turnos[i % 3],
            "fecha_ingreso": date(2012, 1, 1) + timedelta(days=rng.randint(0, 365 * 13)),
        })

    equipos: list[dict[str, Any]] = []
    equipo_mags: dict[int, list[str]] = {}
    eid = 0
    for tipo, prefix, first, count, makers, areas_pool, mags in EQUIPMENT_SPEC:
        for k in range(count):
            eid += 1
            codigo = f"{prefix}-{first + k}"
            if codigo == "P-101":
                area = "Bombeo de agua"
            else:
                area = areas_pool[k % len(areas_pool)]
            estado = "operativo"
            roll = rng.random()
            if roll < 0.08:
                estado = "en mantenimiento"
            elif roll < 0.11:
                estado = "fuera de servicio"
            if codigo in ("P-101", "C-201", "M-301"):
                estado, crit = "operativo", "alta"
            else:
                crit = rng.choices(["alta", "media", "baja"], weights=[3, 5, 3])[0]
            equipos.append({
                "id": eid,
                "codigo": codigo,
                "nombre": f"{NAME_BASE[tipo]} {codigo}",
                "tipo": tipo,
                "fabricante": makers[k % len(makers)],
                "area_id": AREA_ID[area],
                "fecha_instalacion": date(2012, 1, 1) + timedelta(days=rng.randint(0, 365 * 12)),
                "estado": estado,
                "criticidad": crit,
            })
            equipo_mags[eid] = mags

    sensores: list[dict[str, Any]] = []
    sid = 0
    eq_by_id = {e["id"]: e for e in equipos}
    for eq in equipos:
        for mag in equipo_mags[eq["id"]]:
            sid += 1
            alert, crit = _thresholds(rng, eq["tipo"], mag)
            sensores.append({
                "id": sid,
                "equipo_id": eq["id"],
                "magnitud": mag,
                "unidad": UNITS[mag],
                "umbral_alerta": alert,
                "umbral_critico": crit,
            })

    # --- lecturas con episodios de valores elevados ---
    lecturas: list[dict[str, Any]] = []
    episodes_by_sensor: dict[int, list[tuple[int, int, str]]] = {}
    lid = 0
    for s in sensores:
        eq = eq_by_id[s["equipo_id"]]
        episodes = _plan_episodes(rng, eq["codigo"], s["magnitud"])
        episodes_by_sensor[s["id"]] = episodes
        values = _base_series(rng, s["umbral_alerta"])
        for start, length, sev in episodes:
            _apply_episode(rng, values, start, length, sev, s["umbral_alerta"], s["umbral_critico"])
        for i, v in enumerate(values):
            lid += 1
            lecturas.append({
                "id": lid,
                "sensor_id": s["id"],
                "fecha_hora": START + timedelta(hours=STEP_HOURS * i),
                "valor": _round(v),
            })

    # --- alarmas derivadas de las lecturas ---
    alarmas: list[dict[str, Any]] = []
    by_sensor: dict[int, list[dict[str, Any]]] = {}
    for r in lecturas:
        by_sensor.setdefault(r["sensor_id"], []).append(r)
    aid = 0
    for s in sensores:
        eq = eq_by_id[s["equipo_id"]]
        series = by_sensor[s["id"]]
        i = 0
        while i < len(series):
            if series[i]["valor"] > float(s["umbral_alerta"]):
                j = i
                while j + 1 < len(series) and series[j + 1]["valor"] > float(s["umbral_alerta"]):
                    j += 1
                peak = max(r["valor"] for r in series[i:j + 1])
                sev = "critica" if peak >= float(s["umbral_critico"]) else "alerta"
                aid += 1
                still_open = j == len(series) - 1
                umbral = s["umbral_critico"] if sev == "critica" else s["umbral_alerta"]
                alarmas.append({
                    "id": aid,
                    "sensor_id": s["id"],
                    "lectura_id": series[i]["id"],
                    "severidad": sev,
                    "fecha_inicio": series[i]["fecha_hora"],
                    "fecha_fin": None if still_open else series[j]["fecha_hora"] + timedelta(hours=STEP_HOURS),
                    "descripcion": (
                        f"{s['magnitud'].capitalize()} {'critica' if sev == 'critica' else 'elevada'} en "
                        f"{eq['codigo']}: pico de {peak} {s['unidad']}, umbral {umbral} {s['unidad']}."
                    ),
                })
                i = j + 1
            else:
                i += 1

    # --- ordenes de mantenimiento ---
    tec_by_spec: dict[str, list[dict[str, Any]]] = {}
    for t in tecnicos:
        tec_by_spec.setdefault(t["especialidad"], []).append(t)
    sensor_by_id = {s["id"]: s for s in sensores}
    ordenes: list[dict[str, Any]] = []
    oid = 0

    def make_order(equipo, tecnico, alarma_id, tipo, prioridad, created: date, text: str) -> None:
        nonlocal oid
        oid += 1
        estado, cierre, horas = _order_state(rng, created)
        ordenes.append({
            "id": oid,
            "equipo_id": equipo["id"],
            "tecnico_id": tecnico["id"],
            "alarma_id": alarma_id,
            "tipo": tipo,
            "prioridad": prioridad,
            "estado": estado,
            "fecha_creacion": created,
            "fecha_cierre": cierre,
            "descripcion": text,
            "horas_trabajadas": horas,
        })

    for a in alarmas:
        s = sensor_by_id[a["sensor_id"]]
        eq = eq_by_id[s["equipo_id"]]
        p = 0.75 if a["severidad"] == "critica" else 0.25
        if rng.random() < p:
            tec = rng.choice(tec_by_spec[SPECIALTY_FOR[s["magnitud"]]])
            created = a["fecha_inicio"].date() + timedelta(days=rng.randint(0, 1))
            created = min(created, DATA_END_DATE)
            make_order(eq, tec, a["id"], "correctivo", "alta" if a["severidad"] == "critica" else "media",
                       created, CORRECTIVE_TEXT[s["magnitud"]])
    for eq in equipos:
        for _ in range(2):
            tec = rng.choice(tecnicos)
            created = date(2026, 9, 1) + timedelta(days=rng.randint(0, 29))
            prio = {"alta": "media", "media": "media", "baja": "baja"}[eq["criticidad"]]
            make_order(eq, tec, None, "preventivo", prio, created, PREVENTIVE_TEXT[eq["tipo"]])

    return {
        "areas": areas, "tecnicos": tecnicos, "equipos": equipos, "sensores": sensores,
        "lecturas": lecturas, "alarmas": alarmas, "ordenes_mantenimiento": ordenes,
    }


def _thresholds(rng: random.Random, tipo: str, mag: str) -> tuple[float, float]:
    if mag == "temperatura":
        alert = rng.choice([80.0, 85.0]) if tipo != "transformador" else 85.0
        return alert, alert + (15.0 if tipo != "transformador" else 20.0)
    if mag == "vibracion":
        return (5.6, 9.0) if tipo == "compresor" else (4.5, 7.1)
    if mag == "presion":
        return (8.5, 10.5) if tipo == "compresor" else (8.0, 10.0)
    alert = rng.choice([25.0, 40.0, 60.0, 80.0])
    return alert, round(alert * 1.2, 1)


def _base_series(rng: random.Random, alert: float) -> list[float]:
    base = float(alert) * rng.uniform(0.55, 0.72)
    phase = rng.uniform(0, 2 * math.pi)
    values = []
    for i in range(N_READINGS):
        daily = math.sin(2 * math.pi * (i % 12) / 12 + phase) * 0.05 * float(alert)
        noise = rng.gauss(0, 0.025 * float(alert))
        values.append(max(0.01, base + daily + noise))
    return values


def _plan_episodes(rng: random.Random, codigo: str, mag: str) -> list[tuple[int, int, str]]:
    forced = list(FORCED.get((codigo, mag), []))
    n_random = rng.choices([0, 1, 2, 3, 4], weights=[20, 30, 25, 15, 10])[0]
    episodes = list(forced)
    occupied = [(s - 3, s + l + 3) for s, l, _ in episodes]
    attempts = 0
    while n_random > 0 and attempts < 60:
        attempts += 1
        length = rng.randint(2, 6)
        start = rng.randint(2, N_READINGS - length)
        if any(not (start + length + 3 <= lo or start >= hi) for lo, hi in occupied):
            continue
        sev = "critica" if rng.random() < 0.35 else "alerta"
        episodes.append((start, length, sev))
        occupied.append((start - 3, start + length + 3))
        n_random -= 1
    return sorted(episodes)


def _apply_episode(rng, values, start, length, sev, alert, crit) -> None:
    alert, crit = float(alert), float(crit)
    peak = crit * rng.uniform(1.01, 1.08) if sev == "critica" else alert * rng.uniform(1.03, 1.12)
    if sev == "alerta":
        peak = min(peak, crit * 0.98)
    for j in range(length):
        mid = (length - 1) / 2
        shape = 1.0 - 0.7 * (abs(j - mid) / mid) if mid else 1.0
        values[start + j] = alert + (peak - alert) * max(0.3, shape)
    # el pico exacto cae en la lectura central
    values[start + length // 2] = peak


def _order_state(rng: random.Random, created: date):
    if created >= DATA_END_DATE - timedelta(days=6):
        estado = rng.choices(["abierta", "en curso"], weights=[6, 4])[0]
    else:
        estado = rng.choices(["cerrada", "en curso"], weights=[9, 1])[0]
    cierre = None
    horas = None
    if estado == "cerrada":
        cierre = created + timedelta(days=rng.randint(1, 6))
        if cierre > DATA_END_DATE:
            estado, cierre = "en curso", None
    if estado == "cerrada":
        horas = round(rng.uniform(1, 12) * 2) / 2
    elif estado == "en curso":
        horas = round(rng.uniform(0.5, 6) * 2) / 2
    return estado, cierre, horas


TABLE_ORDER = ["areas", "tecnicos", "equipos", "sensores", "lecturas", "alarmas", "ordenes_mantenimiento"]
COLUMNS = {
    "areas": ["id", "nombre", "descripcion"],
    "tecnicos": ["id", "nombre", "especialidad", "turno", "fecha_ingreso"],
    "equipos": ["id", "codigo", "nombre", "tipo", "fabricante", "area_id", "fecha_instalacion", "estado", "criticidad"],
    "sensores": ["id", "equipo_id", "magnitud", "unidad", "umbral_alerta", "umbral_critico"],
    "lecturas": ["id", "sensor_id", "fecha_hora", "valor"],
    "alarmas": ["id", "sensor_id", "lectura_id", "severidad", "fecha_inicio", "fecha_fin", "descripcion"],
    "ordenes_mantenimiento": ["id", "equipo_id", "tecnico_id", "alarma_id", "tipo", "prioridad", "estado",
                              "fecha_creacion", "fecha_cierre", "descripcion", "horas_trabajadas"],
}


def load(conn, data: dict[str, list[dict[str, Any]]]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "truncate ordenes_mantenimiento, alarmas, lecturas, sensores, equipos, tecnicos, areas "
            "restart identity cascade"
        )
        for table in TABLE_ORDER:
            cols = COLUMNS[table]
            with cur.copy(f"copy {table} ({', '.join(cols)}) from stdin") as copy:
                for row in data[table]:
                    copy.write_row([row[c] for c in cols])
            if "id" in cols:
                cur.execute(
                    f"select setval(pg_get_serial_sequence('{table}', 'id'), (select max(id) from {table}))"
                )
    conn.commit()


def main() -> None:
    from telemetry_agent.db import connect_admin

    data = generate_dataset()
    with connect_admin() as conn:
        load(conn, data)
    for table in TABLE_ORDER:
        print(f"{table}: {len(data[table])} filas")


if __name__ == "__main__":
    main()
