"""Subpaquete JPL — corpus de leyes y ordenanzas para Juzgados de Policía Local."""

from .db import (
    DB_PATH as JPL_DB_PATH,
    ZST_PATH as JPL_ZST_PATH,
    _ensure_db as jpl_ensure_db,
    _use_db as jpl_use_db,
    buscar_ley as jpl_buscar_ley,
    buscar_articulo as jpl_buscar_articulo,
    verificar_vigencia as jpl_verificar_vigencia,
    listar_leyes as jpl_listar_leyes,
    listar_ordenanzas as jpl_listar_ordenanzas,
    buscar_ordenanza as jpl_buscar_ordenanza,
    buscar_texto as jpl_buscar_texto,
    listar_manuales as jpl_listar_manuales,
)

__all__ = [
    "JPL_DB_PATH",
    "JPL_ZST_PATH",
    "jpl_ensure_db",
    "jpl_use_db",
    "jpl_buscar_ley",
    "jpl_buscar_articulo",
    "jpl_verificar_vigencia",
    "jpl_listar_leyes",
    "jpl_listar_ordenanzas",
    "jpl_buscar_ordenanza",
    "jpl_buscar_texto",
    "jpl_listar_manuales",
]
