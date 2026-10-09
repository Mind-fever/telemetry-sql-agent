"""Pruebas de la capa de base de datos del principio I: aunque el validador de SQL fallara,
el rol agent_ro y la transaccion de solo lectura impiden escribir, y el timeout corta consultas lentas."""

from __future__ import annotations

import psycopg
import pytest

from telemetry_agent.db import run_readonly


@pytest.fixture(autouse=True)
def _need_db(db_available):
    if not db_available:
        pytest.skip("No hay base cargada.")


@pytest.mark.parametrize("statement", [
    "insert into areas (nombre, descripcion) values ('hack', 'x')",
    "update equipos set estado = 'operativo'",
    "delete from alarmas",
    "drop table alarmas",
    "truncate lecturas",
    "create table pirata (id int)",
])
def test_role_cannot_write_even_without_the_validator(statement):
    with pytest.raises(psycopg.Error):
        run_readonly(statement)


def test_data_is_intact_after_the_attempts():
    assert run_readonly("select count(*) as n from alarmas").rows[0]["n"] > 15


def test_slow_queries_are_cut_by_the_timeout(monkeypatch):
    monkeypatch.setenv("SQL_TIMEOUT_MS", "300")
    with pytest.raises(psycopg.errors.QueryCanceled):
        run_readonly("select pg_sleep(5)")


def test_row_cap_reports_truncation():
    result = run_readonly("select id from lecturas order by id", max_rows=10)
    assert len(result.rows) == 10 and result.truncated is True


def test_session_uses_the_plant_timezone():
    assert run_readonly("select current_setting('TimeZone') as tz").rows[0]["tz"] == "America/Argentina/Buenos_Aires"
