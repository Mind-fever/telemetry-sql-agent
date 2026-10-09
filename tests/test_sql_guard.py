"""Pruebas del validador de SQL (principio I, FR-007, SC-002)."""

from __future__ import annotations

import pytest

from telemetry_agent.sql_guard import validate_sql


@pytest.mark.parametrize("query", [
    "select count(*) from alarmas where severidad = 'critica'",
    "SELECT e.codigo, count(*) FROM alarmas a JOIN sensores s ON s.id = a.sensor_id "
    "JOIN equipos e ON e.id = s.equipo_id GROUP BY e.codigo ORDER BY 2 DESC LIMIT 5;",
    "with c as (select equipo_id, count(*) n from ordenes_mantenimiento group by 1) select * from c where n > 3",
    "select nombre from tecnicos union select nombre from areas",
    "select * from equipos where nombre ilike '%motor%'",
])
def test_valid_reads_are_accepted(query):
    result = validate_sql(query)
    assert result.ok, result.reason


@pytest.mark.parametrize("query", [
    "delete from alarmas",
    "DELETE FROM alarmas WHERE id = 1",
    "update equipos set estado = 'operativo'",
    "insert into areas (nombre, descripcion) values ('x', 'y')",
    "drop table alarmas",
    "truncate lecturas",
    "alter table equipos add column x int",
    "create table t (id int)",
    "grant all on equipos to public",
    "select * into nueva from equipos",
    "select * from equipos for update",
])
def test_writes_are_rejected_as_not_read_only(query):
    result = validate_sql(query)
    assert not result.ok
    assert result.kind == "not_read_only", (query, result)


def test_multiple_statements_are_rejected():
    result = validate_sql("select 1 from equipos; delete from alarmas")
    assert not result.ok


def test_write_hidden_in_cte_is_rejected():
    result = validate_sql("with x as (delete from alarmas returning *) select * from x")
    assert not result.ok


@pytest.mark.parametrize("query", [
    "select * from doc_chunks",
    "select * from pg_catalog.pg_tables",
    "select * from information_schema.tables",
    "select * from public.equipos",
    "select * from pg_roles",
])
def test_tables_outside_the_allowed_list_are_rejected(query):
    result = validate_sql(query)
    assert not result.ok
    assert result.kind == "invalid"


@pytest.mark.parametrize("query", [
    "select pg_sleep(10)",
    "select pg_read_file('/etc/passwd')",
    "select set_config('x', 'y', false) from equipos",
])
def test_dangerous_functions_are_rejected(query):
    assert not validate_sql(query).ok


@pytest.mark.parametrize("query", ["", "   ", ";", "esto no es sql"])
def test_garbage_is_rejected(query):
    assert not validate_sql(query).ok
