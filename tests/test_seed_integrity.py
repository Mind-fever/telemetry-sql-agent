"""Pruebas de los datos sinteticos (FR-001, FR-002) y de las reglas del modelo de datos."""

from __future__ import annotations

import pytest

TABLES = ["areas", "tecnicos", "equipos", "sensores", "lecturas", "alarmas", "ordenes_mantenimiento"]


def test_each_table_has_more_than_15_rows(dataset):
    assert len(TABLES) >= 5
    for table in TABLES:
        assert len(dataset[table]) > 15, table


def test_dataset_is_deterministic():
    import seed

    a = seed.generate_dataset()
    b = seed.generate_dataset()
    for table in TABLES:
        assert a[table] == b[table], table


def test_foreign_keys_resolve(dataset):
    ids = {t: {r["id"] for r in dataset[t]} for t in TABLES}
    assert all(e["area_id"] in ids["areas"] for e in dataset["equipos"])
    assert all(s["equipo_id"] in ids["equipos"] for s in dataset["sensores"])
    assert all(r["sensor_id"] in ids["sensores"] for r in dataset["lecturas"])
    assert all(a["sensor_id"] in ids["sensores"] and a["lectura_id"] in ids["lecturas"] for a in dataset["alarmas"])
    for o in dataset["ordenes_mantenimiento"]:
        assert o["equipo_id"] in ids["equipos"]
        assert o["tecnico_id"] in ids["tecnicos"]
        assert o["alarma_id"] is None or o["alarma_id"] in ids["alarmas"]


def test_thresholds_are_ordered(dataset):
    assert all(s["umbral_critico"] > s["umbral_alerta"] for s in dataset["sensores"])


def test_closing_date_only_when_closed(dataset):
    for o in dataset["ordenes_mantenimiento"]:
        assert (o["estado"] == "cerrada") == (o["fecha_cierre"] is not None)
        assert o["fecha_cierre"] is None or o["fecha_cierre"] >= o["fecha_creacion"]


def test_alarms_match_their_readings(dataset):
    sensors = {s["id"]: s for s in dataset["sensores"]}
    readings = {r["id"]: r for r in dataset["lecturas"]}
    for a in dataset["alarmas"]:
        s = sensors[a["sensor_id"]]
        first = readings[a["lectura_id"]]
        assert first["sensor_id"] == s["id"]
        assert first["valor"] > float(s["umbral_alerta"])
        assert first["fecha_hora"] == a["fecha_inicio"]
        if a["fecha_fin"] is not None:
            assert a["fecha_fin"] > a["fecha_inicio"]


def test_corrective_orders_come_from_alarms_and_preventive_do_not(dataset):
    for o in dataset["ordenes_mantenimiento"]:
        assert (o["tipo"] == "correctivo") == (o["alarma_id"] is not None)


def test_known_cases_for_evaluation_exist(dataset):
    eq = {e["codigo"]: e for e in dataset["equipos"]}
    c201 = eq["C-201"]["id"]
    vib = [s for s in dataset["sensores"] if s["equipo_id"] == c201 and s["magnitud"] == "vibracion"]
    assert len(vib) == 1
    alarms = sorted((a for a in dataset["alarmas"] if a["sensor_id"] == vib[0]["id"]), key=lambda a: a["fecha_inicio"])
    assert len(alarms) >= 3
    assert alarms[-1]["severidad"] == "critica"
    assert eq["P-101"]["area_id"] == 2  # Bombeo de agua


def test_some_alarms_are_open_and_some_closed(dataset):
    open_count = sum(1 for a in dataset["alarmas"] if a["fecha_fin"] is None)
    assert 0 < open_count < len(dataset["alarmas"])
    assert any(a["severidad"] == "critica" for a in dataset["alarmas"])
    assert any(a["severidad"] == "alerta" for a in dataset["alarmas"])


def test_database_matches_dataset(dataset, db_available):
    if not db_available:
        pytest.skip("No hay base cargada (correr scripts/setup_db.py y scripts/seed.py).")
    from telemetry_agent.db import connect_admin

    with connect_admin() as conn:
        for table in TABLES:
            (n,) = conn.execute(f"select count(*) from {table}").fetchone()
            assert n == len(dataset[table]), table
