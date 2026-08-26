"""Base de datos de leyes JPL para el servidor MCP jpl-leyes.

Modelo "DB comprimido en repo + FTS local on-demand":
- En el repo solo va corpus.db.zlib (corpus.db entero comprimido con zlib-9, SIN índices FTS).
- Al primer uso, _ensure_db() descomprime a corpus.db (gitignored) y construye las tablas
  FTS5 localmente desde los textos (~2-3 min la primera vez; después <10ms por consulta).
- Si no existe ni .db ni .zst, hace fallback al filesystem (leyes/*.md, ordenanzas/*/*.md).
Mantiene compatibilidad de firmas para callers existentes.
"""
from __future__ import annotations

import re
import sqlite3
import time
import zlib
from pathlib import Path
import unicodedata
import json

# Rutas integradas en k-LegalChile: data/jpl/
_JPL_ROOT = Path(__file__).resolve().parents[3] / "data" / "jpl"
CORPUS_DIR = _JPL_ROOT / "leyes"
ORDENANZAS_DIR = _JPL_ROOT / "ordenanzas"
DB_PATH = _JPL_ROOT / "corpus.db"
ZST_PATH = _JPL_ROOT / "corpus.db.zlib"
# Alternativa: sibling clone del repo privado
_ALT_ZST = Path(__file__).resolve().parents[3].parent / "K-LegalJPL" / "corpus.db.zlib"
_ALT_DB = Path(__file__).resolve().parents[3].parent / "K-LegalJPL" / "corpus.db"

# mapeo de aliases -> archivo en el corpus
ALIASES = {
    "18287": "Ley_18287_Procedimiento_JPL.md",
    "18.287": "Ley_18287_Procedimiento_JPL.md",
    "procedimiento": "Ley_18287_Procedimiento_JPL.md",
    "15231": "Ley_15231_DTO307_Organizacion_JPL.md",
    "15.231": "Ley_15231_DTO307_Organizacion_JPL.md",
    "organizacion": "Ley_15231_DTO307_Organizacion_JPL.md",
    "organización": "Ley_15231_DTO307_Organizacion_JPL.md",
    "jpl": "Ley_15231_DTO307_Organizacion_JPL.md",
    "18290": "Ley_18290_Transito_DFL1_2007.md",
    "18.290": "Ley_18290_Transito_DFL1_2007.md",
    "transito": "Ley_18290_Transito_DFL1_2007.md",
    "tránsito": "Ley_18290_Transito_DFL1_2007.md",
    "19925": "Ley_19925_Alcoholes.md",
    "19.925": "Ley_19925_Alcoholes.md",
    "alcoholes": "Ley_19925_Alcoholes.md",
    "19496": "Ley_19496_Consumidor.md",
    "19.496": "Ley_19496_Consumidor.md",
    "consumidor": "Ley_19496_Consumidor.md",
    "21020": "Ley_21020_Tenencia_Responsable.md",
    "21.020": "Ley_21020_Tenencia_Responsable.md",
    "tenencia": "Ley_21020_Tenencia_Responsable.md",
    "19300": "Ley_19300_Medio_Ambiente.md",
    "19.300": "Ley_19300_Medio_Ambiente.md",
    "ambiente": "Ley_19300_Medio_Ambiente.md",
    "18695": "Ley_18695_Municipalidades.md",
    "18.695": "Ley_18695_Municipalidades.md",
    "municipalidades": "Ley_18695_Municipalidades.md",
    "3063": "Ley_3063_Rentas_Municipales_DTO2385.md",
    "3.063": "Ley_3063_Rentas_Municipales_DTO2385.md",
    "rentas": "Ley_3063_Rentas_Municipales_DTO2385.md",
    "lgucl": "Ley_LGUC_DFL458_Ornato_Urbanismo.md",
    "lguc": "Ley_LGUC_DFL458_Ornato_Urbanismo.md",
    "458": "Ley_LGUC_DFL458_Ornato_Urbanismo.md",
    "urbanismo": "Ley_LGUC_DFL458_Ornato_Urbanismo.md",
    "constitucion": "Constitucion_Politica.md",
    "constitución": "Constitucion_Politica.md",
    "21155": "Ley_21155_Lactancia_Materna.md",
    "21.155": "Ley_21155_Lactancia_Materna.md",
    "lactancia": "Ley_21155_Lactancia_Materna.md",
    "maternidad": "Ley_21155_Lactancia_Materna.md",
    "21368": "Ley_21368_Plasticos_Un_Solo_Uso.md",
    "21.368": "Ley_21368_Plasticos_Un_Solo_Uso.md",
    "plásticos": "Ley_21368_Plasticos_Un_Solo_Uso.md",
    "plasticos": "Ley_21368_Plasticos_Un_Solo_Uso.md",
    "21100": "Ley_21100_Bolsas_Plasticas.md",
    "21.100": "Ley_21100_Bolsas_Plasticas.md",
    "bolsas": "Ley_21100_Bolsas_Plasticas.md",
    "19846": "Ley_19846_Calificacion_Cinematografica.md",
    "19.846": "Ley_19846_Calificacion_Cinematografica.md",
    "cine": "Ley_19846_Calificacion_Cinematografica.md",
    "cinematográfica": "Ley_19846_Calificacion_Cinematografica.md",
    "cinematografica": "Ley_19846_Calificacion_Cinematografica.md",
    "18490": "Ley_18490_SOAP_Seguro_Accidentes.md",
    "18.490": "Ley_18490_SOAP_Seguro_Accidentes.md",
    "soap": "Ley_18490_SOAP_Seguro_Accidentes.md",
    "seguro obligatorio": "Ley_18490_SOAP_Seguro_Accidentes.md",
    "18690": "Ley_18690_Almacenes_Generales_Deposito.md",
    "18.690": "Ley_18690_Almacenes_Generales_Deposito.md",
    "almacenes": "Ley_18690_Almacenes_Generales_Deposito.md",
    "depósito": "Ley_18690_Almacenes_Generales_Deposito.md",
    "deposito": "Ley_18690_Almacenes_Generales_Deposito.md",
    "17798": "Ley_17798_Control_Armas_DTO400.md",
    "17.798": "Ley_17798_Control_Armas_DTO400.md",
    "armas": "Ley_17798_Control_Armas_DTO400.md",
    "control de armas": "Ley_17798_Control_Armas_DTO400.md",
    "dto 400": "Ley_17798_Control_Armas_DTO400.md",
    "dto-400": "Ley_17798_Control_Armas_DTO400.md",
    "850": "Ley_Caminos_DFL850_1997.md",
    "dfl 850": "Ley_Caminos_DFL850_1997.md",
    "dfl-850": "Ley_Caminos_DFL850_1997.md",
    "caminos": "Ley_Caminos_DFL850_1997.md",
    "camino": "Ley_Caminos_DFL850_1997.md",
    "4023": "Ley_4023_Guia_Libre_Transito.md",
    "4.023": "Ley_4023_Guia_Libre_Transito.md",
    "guía": "Ley_4023_Guia_Libre_Transito.md",
    "guia": "Ley_4023_Guia_Libre_Transito.md",
    "libre tránsito": "Ley_4023_Guia_Libre_Transito.md",
    "libre transito": "Ley_4023_Guia_Libre_Transito.md",
    "13937": "Ley_13937_Letreros_Esquinas.md",
    "13.937": "Ley_13937_Letreros_Esquinas.md",
    "letreros": "Ley_13937_Letreros_Esquinas.md",
    "esquina": "Ley_13937_Letreros_Esquinas.md",
    "7889": "Ley_7889_Boletos_Loteria_Polla.md",
    "7.889": "Ley_7889_Boletos_Loteria_Polla.md",
    "boletos": "Ley_7889_Boletos_Loteria_Polla.md",
    "lotería": "Ley_7889_Boletos_Loteria_Polla.md",
    "polla": "Ley_7889_Boletos_Loteria_Polla.md",
    "18119": "Ley_18119_Empalmes_Clandestinos_Agua.md",
    "18.119": "Ley_18119_Empalmes_Clandestinos_Agua.md",
    "empalmes": "Ley_18119_Empalmes_Clandestinos_Agua.md",
    "agua potable": "Ley_18119_Empalmes_Clandestinos_Agua.md",
    "19040": "Ley_19040_Locomocion_Colectiva.md",
    "19.040": "Ley_19040_Locomocion_Colectiva.md",
    "locomoción": "Ley_19040_Locomocion_Colectiva.md",
    "locomocion": "Ley_19040_Locomocion_Colectiva.md",
    "19327": "Ley_19327_Violencia_Estadios_Futbol.md",
    "19.327": "Ley_19327_Violencia_Estadios_Futbol.md",
    "estadios": "Ley_19327_Violencia_Estadios_Futbol.md",
    "violencia": "Ley_19327_Violencia_Estadios_Futbol.md",
    "fútbol": "Ley_19327_Violencia_Estadios_Futbol.md",
    "futbol": "Ley_19327_Violencia_Estadios_Futbol.md",
    "19419": "Ley_19419_Tabaco.md",
    "19.419": "Ley_19419_Tabaco.md",
    "tabaco": "Ley_19419_Tabaco.md",
    "19473": "Ley_19473_Caza.md",
    "19.473": "Ley_19473_Caza.md",
    "caza": "Ley_19473_Caza.md",
    "19779": "Ley_19779_VIH_SIDA.md",
    "19.779": "Ley_19779_VIH_SIDA.md",
    "vih": "Ley_19779_VIH_SIDA.md",
    "sida": "Ley_19779_VIH_SIDA.md",
    "18450": "Ley_18450_Riego_Drenaje.md",
    "18.450": "Ley_18450_Riego_Drenaje.md",
    "riego": "Ley_18450_Riego_Drenaje.md",
    "drenaje": "Ley_18450_Riego_Drenaje.md",
    "18118": "Ley_18118_Martilleros_Publicos.md",
    "18.118": "Ley_18118_Martilleros_Publicos.md",
    "martillero": "Ley_18118_Martilleros_Publicos.md",
    "2565": "Ley_2565_Fomento_Forestal.md",
    "2.565": "Ley_2565_Fomento_Forestal.md",
    "forestal": "Ley_2565_Fomento_Forestal.md",
    "4363": "Ley_Bosques_DS4363_1931.md",
    "ds 4363": "Ley_Bosques_DS4363_1931.md",
    "ley de bosques": "Ley_Bosques_DS4363_1931.md",
    "bosques": "Ley_Bosques_DS4363_1931.md",
    "430": "Ley_Pesca_DS430_LGPA.md",
    "ds 430": "Ley_Pesca_DS430_LGPA.md",
    "pesca": "Ley_Pesca_DS430_LGPA.md",
    "lgpa": "Ley_Pesca_DS430_LGPA.md",
    "acuicultura": "Ley_Pesca_DS430_LGPA.md",
    "216": "Ley_216_Empadronamiento_Vecinal.md",
    "dfl 216": "Ley_216_Empadronamiento_Vecinal.md",
    "dfl-216": "Ley_216_Empadronamiento_Vecinal.md",
    "empadronamiento": "Ley_216_Empadronamiento_Vecinal.md",
    "padrón": "Ley_216_Empadronamiento_Vecinal.md",
    "padron": "Ley_216_Empadronamiento_Vecinal.md",
    "21600": "Ley_21600_SBAP_Biodiversidad.md",
    "21.600": "Ley_21600_SBAP_Biodiversidad.md",
    "sbap": "Ley_21600_SBAP_Biodiversidad.md",
    "biodiversidad": "Ley_21600_SBAP_Biodiversidad.md",
    "áreas protegidas": "Ley_21600_SBAP_Biodiversidad.md",
    "areas protegidas": "Ley_21600_SBAP_Biodiversidad.md",
    "20283": "Ley_20283_Bosque_Nativo.md",
    "20.283": "Ley_20283_Bosque_Nativo.md",
    "bosque nativo": "Ley_20283_Bosque_Nativo.md",
    "20256": "Ley_20256_Pesca_Recreativa.md",
    "20.256": "Ley_20256_Pesca_Recreativa.md",
    "pesca recreativa": "Ley_20256_Pesca_Recreativa.md",
    "21442": "Ley_21442_Copropiedad_Inmobiliaria.md",
    "21.442": "Ley_21442_Copropiedad_Inmobiliaria.md",
    "copropiedad": "Ley_21442_Copropiedad_Inmobiliaria.md",
    "condominio": "Ley_21442_Copropiedad_Inmobiliaria.md",
    "19866": "Ley_19866_SalvoConducto.md",
    "19.866": "Ley_19866_SalvoConducto.md",
    "salvo conducto": "Ley_19866_SalvoConducto.md",
    "salvoconducto": "Ley_19866_SalvoConducto.md",
    "20227": "Ley_20227.md",
    "20.227": "Ley_20227.md",
    "20879": "Ley_20879.md",
    "20.879": "Ley_20879.md",
    "dfl 725": "CODIGO_SANITARIO_DFL725.md",
    "codigo sanitario": "CODIGO_SANITARIO_DFL725.md",
    "código sanitario": "CODIGO_SANITARIO_DFL725.md",
    "sanitario": "CODIGO_SANITARIO_DFL725.md",
    "cpc": "CPC_CODIGO_PROCEDIMIENTO_CIVIL.md",
    "codigo procedimiento civil": "CPC_CODIGO_PROCEDIMIENTO_CIVIL.md",
    "código procedimiento civil": "CPC_CODIGO_PROCEDIMIENTO_CIVIL.md",
    "oguc": "OGUC_DS47_92.md",
    "ds 47": "OGUC_DS47_92.md",
    "47/92": "OGUC_DS47_92.md",
    "ordenanza general urbanismo": "OGUC_DS47_92.md",
    "atribuciones juzgados": "Atribuciones_Juzgados_Policia_Local.md",
    "atribuciones": "Atribuciones_Juzgados_Policia_Local.md",
    "ordenanza aseo": "Vina_del_Mar/Ordenanza_VDM_Aseo_DA1163_92.md",
    "aseo municipal vina": "Vina_del_Mar/Ordenanza_VDM_Aseo_DA1163_92.md",
    "d.a 1163": "Vina_del_Mar/Ordenanza_VDM_Aseo_DA1163_92.md",
    "ordenanza comercio via publica": "Vina_del_Mar/Ordenanza_VDM_ComercioViaPublica_5938_17.md",
    "comercio via publica vina": "Vina_del_Mar/Ordenanza_VDM_ComercioViaPublica_5938_17.md",
    "decreto 5938": "Vina_del_Mar/Ordenanza_VDM_ComercioViaPublica_5938_17.md",
    "derechos municipales vina": "Vina_del_Mar/Ordenanza_VDM_DerechosMunicipales_10297_19.md",
    "ordenanza derechos municipales": "Vina_del_Mar/Ordenanza_VDM_DerechosMunicipales_10297_19.md",
    "decreto 10297": "Vina_del_Mar/Ordenanza_VDM_DerechosMunicipales_10297_19.md",
    "ordenanza ferias libres": "Vina_del_Mar/Ordenanza_VDM_FeriasLibres_2277_77.md",
    "ferias libres vina": "Vina_del_Mar/Ordenanza_VDM_FeriasLibres_2277_77.md",
    "decreto 2277": "Vina_del_Mar/Ordenanza_VDM_FeriasLibres_2277_77.md",
    "ordenanza ocupacion via publica": "Vina_del_Mar/Ordenanza_VDM_OcupacionViaPublica_10986_11.md",
    "ocupacion via publica residuos": "Vina_del_Mar/Ordenanza_VDM_OcupacionViaPublica_10986_11.md",
    "decreto 10986": "Vina_del_Mar/Ordenanza_VDM_OcupacionViaPublica_10986_11.md",
    "ordenanza ocupacion bnup": "Vina_del_Mar/Ordenanza_VDM_OcupacionBNUP_DA1196_19.md",
    "ocupacion bnup": "Vina_del_Mar/Ordenanza_VDM_OcupacionBNUP_DA1196_19.md",
    "d.a 1196": "Vina_del_Mar/Ordenanza_VDM_OcupacionBNUP_DA1196_19.md",
    "dto 1196": "Vina_del_Mar/Ordenanza_VDM_OcupacionBNUP_DA1196_19.md",
    "ordenanza parques jardines": "Vina_del_Mar/Ordenanza_VDM_ParquesJardines_5418_98.md",
    "parques y jardines vina": "Vina_del_Mar/Ordenanza_VDM_ParquesJardines_5418_98.md",
    "decreto 5418": "Vina_del_Mar/Ordenanza_VDM_ParquesJardines_5418_98.md",
    "ordenanza publicidad": "Vina_del_Mar/Ordenanza_VDM_Publicidad_8422_98.md",
    "publicidad vina": "Vina_del_Mar/Ordenanza_VDM_Publicidad_8422_98.md",
    "decreto 8422": "Vina_del_Mar/Ordenanza_VDM_Publicidad_8422_98.md",
    "ordenanza rotura pavimentos": "Vina_del_Mar/Ordenanza_VDM_DerechosMunicipales_10502_17.md",
    "rotura pavimentos vina": "Vina_del_Mar/Ordenanza_VDM_DerechosMunicipales_10502_17.md",
    "decreto 10502": "Vina_del_Mar/Ordenanza_VDM_DerechosMunicipales_10502_17.md",
    "derechos municipales 2018": "Vina_del_Mar/Ordenanza_VDM_DerechosMunicipales_10502_17.md",
    "ordenanza transporte residuos": "Vina_del_Mar/Ordenanza_VDM_TransporteResiduos_11019_16.md",
    "transporte residuos vina": "Vina_del_Mar/Ordenanza_VDM_TransporteResiduos_11019_16.md",
    "decreto 11019": "Vina_del_Mar/Ordenanza_VDM_TransporteResiduos_11019_16.md",
    "aseo algarrobo": "algarrobo/Ordenanza_Aseo_509.md",
    "algarrobo aseo": "algarrobo/Ordenanza_Aseo_509.md",
    "derechos municipales algarrobo": "algarrobo/Ordenanza_DerechosMunicipales_1824.md",
    "algarrobo derechos municipales": "algarrobo/Ordenanza_DerechosMunicipales_1824.md",
    "decreto 1824 algarrobo": "algarrobo/Ordenanza_DerechosMunicipales_1824.md",
    "publicidad algarrobo": "algarrobo/Ordenanza_Publicidad_344.md",
    "algarrobo publicidad": "algarrobo/Ordenanza_Publicidad_344.md",
    "ruidos algarrobo": "algarrobo/Ordenanza_Ruidos_1800.md",
    "algarrobo ruidos": "algarrobo/Ordenanza_Ruidos_1800.md",
    "derechos municipales cabildo": "cabildo/Ordenanza_DerechosMunicipales_948.md",
    "cabildo derechos municipales": "cabildo/Ordenanza_DerechosMunicipales_948.md",
    "tenencia responsable cabildo": "cabildo/Ordenanza_TenenciaResponsable_408.md",
    "cabildo tenencia responsable": "cabildo/Ordenanza_TenenciaResponsable_408.md",
    "aseo calle larga": "calle_larga/Ordenanza_Aseo_1101 EXENTO.md",
    "calle larga aseo": "calle_larga/Ordenanza_Aseo_1101 EXENTO.md",
    "derechos municipales calle larga": "calle_larga/Ordenanza_DerechosMunicipales_45.md",
    "calle larga derechos municipales": "calle_larga/Ordenanza_DerechosMunicipales_45.md",
    "tenencia responsable calle larga": "calle_larga/Ordenanza_TenenciaResponsable_899 EXENTO.md",
    "calle larga tenencia responsable": "calle_larga/Ordenanza_TenenciaResponsable_899 EXENTO.md",
    "derechos municipales cartagena": "cartagena/Ordenanza_DerechosMunicipales_1020.md",
    "cartagena derechos municipales": "cartagena/Ordenanza_DerechosMunicipales_1020.md",
    "derechos municipales casablanca": "casablanca/Ordenanza_DerechosMunicipales_98.md",
    "casablanca derechos municipales": "casablanca/Ordenanza_DerechosMunicipales_98.md",
    "aseo catemu": "catemu/Ordenanza_Aseo_1183.md",
    "catemu aseo": "catemu/Ordenanza_Aseo_1183.md",
    "derechos municipales catemu": "catemu/Ordenanza_DerechosMunicipales_1180.md",
    "catemu derechos municipales": "catemu/Ordenanza_DerechosMunicipales_1180.md",
    "decreto 1180 catemu": "catemu/Ordenanza_DerechosMunicipales_1180.md",
    "mercado catemu": "catemu/Ordenanza_Mercado_1175-idNorma265048.md",
    "catemu mercado": "catemu/Ordenanza_Mercado_1175-idNorma265048.md",
    "decreto 1175 catemu": "catemu/Ordenanza_Mercado_1175-idNorma265048.md",
    "patentes catemu": "catemu/Ordenanza_Patentes_1176.md",
    "catemu patentes": "catemu/Ordenanza_Patentes_1176.md",
    "decreto 1176 catemu": "catemu/Ordenanza_Patentes_1176.md",
    "publicidad catemu": "catemu/Ordenanza_Publicidad_1177.md",
    "catemu publicidad": "catemu/Ordenanza_Publicidad_1177.md",
    "decreto 1177 catemu": "catemu/Ordenanza_Publicidad_1177.md",
    "residuos catemu": "catemu/Ordenanza_Residuos_9976 EXENTO.md",
    "catemu residuos": "catemu/Ordenanza_Residuos_9976 EXENTO.md",
    "ruidos catemu": "catemu/Ordenanza_Ruidos_1182.md",
    "catemu ruidos": "catemu/Ordenanza_Ruidos_1182.md",
    "decreto 1182 catemu": "catemu/Ordenanza_Ruidos_1182.md",
    "tenencia responsable catemu": "catemu/Ordenanza_TenenciaResponsable_644 EXENTO.md",
    "catemu tenencia responsable": "catemu/Ordenanza_TenenciaResponsable_644 EXENTO.md",
    "alcoholes concon": "concon/Ordenanza_Alcoholes_682.md",
    "concon alcoholes": "concon/Ordenanza_Alcoholes_682.md",
    "concón alcoholes": "concon/Ordenanza_Alcoholes_682.md",
    "tenencia responsable concon": "concon/Ordenanza_TenenciaResponsable_1068.md",
    "concon tenencia responsable": "concon/Ordenanza_TenenciaResponsable_1068.md",
    "concón tenencia responsable": "concon/Ordenanza_TenenciaResponsable_1068.md",
    "alcoholes el quisco": "el_quisco/Ordenanza_Alcoholes_1131.md",
    "el quisco alcoholes": "el_quisco/Ordenanza_Alcoholes_1131.md",
    "derechos municipales el quisco": "el_quisco/Ordenanza_DerechosMunicipales_921.md",
    "el quisco derechos municipales": "el_quisco/Ordenanza_DerechosMunicipales_921.md",
    "mercado el quisco": "el_quisco/Ordenanza_Mercado_189.md",
    "el quisco mercado": "el_quisco/Ordenanza_Mercado_189.md",
    "derechos municipales el tabo": "el_tabo/Ordenanza_DerechosMunicipales_466.md",
    "el tabo derechos municipales": "el_tabo/Ordenanza_DerechosMunicipales_466.md",
    "aseo hijuelas": "hijuelas/Ordenanza_Aseo_232.md",
    "hijuelas aseo": "hijuelas/Ordenanza_Aseo_232.md",
    "derechos municipales hijuelas": "hijuelas/Ordenanza_DerechosMunicipales_613.md",
    "hijuelas derechos municipales": "hijuelas/Ordenanza_DerechosMunicipales_613.md",
    "alcoholes isla de pascua": "isla_de_pascua/Ordenanza_Alcoholes_982.md",
    "isla de pascua alcoholes": "isla_de_pascua/Ordenanza_Alcoholes_982.md",
    "aseo isla de pascua": "isla_de_pascua/Ordenanza_Aseo_2114.md",
    "isla de pascua aseo": "isla_de_pascua/Ordenanza_Aseo_2114.md",
    "comercio via publica isla de pascua": "isla_de_pascua/Ordenanza_ComercioViaPublica_362.md",
    "isla de pascua comercio via publica": "isla_de_pascua/Ordenanza_ComercioViaPublica_362.md",
    "patentes isla de pascua": "isla_de_pascua/Ordenanza_Patentes_2278.md",
    "isla de pascua patentes": "isla_de_pascua/Ordenanza_Patentes_2278.md",
    "publicidad isla de pascua": "isla_de_pascua/Ordenanza_Publicidad_2276.md",
    "isla de pascua publicidad": "isla_de_pascua/Ordenanza_Publicidad_2276.md",
    "tenencia responsable isla de pascua": "isla_de_pascua/Ordenanza_TenenciaResponsable_737.md",
    "isla de pascua tenencia responsable": "isla_de_pascua/Ordenanza_TenenciaResponsable_737.md",
    "derechos municipales juan fernandez": "juan_fernandez/Ordenanza_DerechosMunicipales_77.md",
    "juan fernandez derechos municipales": "juan_fernandez/Ordenanza_DerechosMunicipales_77.md",
    "aseo la calera": "la_calera/Ordenanza_Aseo_699.md",
    "la calera aseo": "la_calera/Ordenanza_Aseo_699.md",
    "comercio via publica la calera": "la_calera/Ordenanza_ComercioViaPublica_172.md",
    "la calera comercio via publica": "la_calera/Ordenanza_ComercioViaPublica_172.md",
    "derechos municipales la calera": "la_calera/Ordenanza_DerechosMunicipales_935.md",
    "la calera derechos municipales": "la_calera/Ordenanza_DerechosMunicipales_935.md",
    "vehiculos la calera": "la_calera/Ordenanza_Vehiculos_212.md",
    "la calera vehiculos": "la_calera/Ordenanza_Vehiculos_212.md",
    "aseo la cruz": "la_cruz/Ordenanza_Aseo_481.md",
    "la cruz aseo": "la_cruz/Ordenanza_Aseo_481.md",
    "derechos municipales la cruz": "la_cruz/Ordenanza_DerechosMunicipales_1229.md",
    "la cruz derechos municipales": "la_cruz/Ordenanza_DerechosMunicipales_1229.md",
    "tenencia responsable la cruz": "la_cruz/Ordenanza_TenenciaResponsable_2296.md",
    "la cruz tenencia responsable": "la_cruz/Ordenanza_TenenciaResponsable_2296.md",
    "derechos municipales la ligua": "la_ligua/Ordenanza_DerechosMunicipales_S_N.md",
    "la ligua derechos municipales": "la_ligua/Ordenanza_DerechosMunicipales_S_N.md",
    "derechos municipales limache": "limache/Ordenanza_DerechosMunicipales_4304.md",
    "limache derechos municipales": "limache/Ordenanza_DerechosMunicipales_4304.md",
    "mercado limache": "limache/Ordenanza_Mercado_6837.md",
    "limache mercado": "limache/Ordenanza_Mercado_6837.md",
    "alcoholes llay-llay": "llay-llay/Ordenanza_Alcoholes_751.md",
    "llay-llay alcoholes": "llay-llay/Ordenanza_Alcoholes_751.md",
    "aseo llay-llay": "llay-llay/Ordenanza_Aseo_1889.md",
    "llay-llay aseo": "llay-llay/Ordenanza_Aseo_1889.md",
    "derechos municipales llay-llay": "llay-llay/Ordenanza_DerechosMunicipales_50.md",
    "llay-llay derechos municipales": "llay-llay/Ordenanza_DerechosMunicipales_50.md",
    "alcoholes los andes": "los_andes/Ordenanza_Alcoholes_1.md",
    "los andes alcoholes": "los_andes/Ordenanza_Alcoholes_1.md",
    "aseo los andes": "los_andes/Ordenanza_Aseo_2.md",
    "los andes aseo": "los_andes/Ordenanza_Aseo_2.md",
    "derechos municipales los andes": "los_andes/Ordenanza_DerechosMunicipales_1021.md",
    "los andes derechos municipales": "los_andes/Ordenanza_DerechosMunicipales_1021.md",
    "ferias libres los andes": "los_andes/Ordenanza_FeriasLibres_S_N.md",
    "los andes ferias libres": "los_andes/Ordenanza_FeriasLibres_S_N.md",
    "publicidad los andes": "los_andes/Ordenanza_Publicidad_21.md",
    "los andes publicidad": "los_andes/Ordenanza_Publicidad_21.md",
    "tenencia responsable los andes": "los_andes/Ordenanza_TenenciaResponsable_3.md",
    "los andes tenencia responsable": "los_andes/Ordenanza_TenenciaResponsable_3.md",
    "transito los andes": "los_andes/Ordenanza_Transito_1.md",
    "los andes transito": "los_andes/Ordenanza_Transito_1.md",
    "tránsito los andes": "los_andes/Ordenanza_Transito_1.md",
    "los andes tránsito": "los_andes/Ordenanza_Transito_1.md",
    "aseo nogales": "nogales/Ordenanza_Aseo_93.md",
    "nogales aseo": "nogales/Ordenanza_Aseo_93.md",
    "derechos municipales nogales": "nogales/Ordenanza_DerechosMunicipales_790.md",
    "nogales derechos municipales": "nogales/Ordenanza_DerechosMunicipales_790.md",
    "ruidos nogales": "nogales/Ordenanza_Ruidos_1265.md",
    "nogales ruidos": "nogales/Ordenanza_Ruidos_1265.md",
    "tenencia responsable nogales": "nogales/Ordenanza_TenenciaResponsable_2496.md",
    "nogales tenencia responsable": "nogales/Ordenanza_TenenciaResponsable_2496.md",
    "aseo olmue": "olmue/Ordenanza_Aseo_1265.md",
    "olmue aseo": "olmue/Ordenanza_Aseo_1265.md",
    "derechos municipales olmue": "olmue/Ordenanza_DerechosMunicipales_1138.md",
    "olmue derechos municipales": "olmue/Ordenanza_DerechosMunicipales_1138.md",
    "alcoholes panquehue": "panquehue/Ordenanza_Alcoholes_1068.md",
    "panquehue alcoholes": "panquehue/Ordenanza_Alcoholes_1068.md",
    "aseo panquehue": "panquehue/Ordenanza_Aseo_2.md",
    "panquehue aseo": "panquehue/Ordenanza_Aseo_2.md",
    "derechos municipales panquehue": "panquehue/Ordenanza_DerechosMunicipales_2330.md",
    "panquehue derechos municipales": "panquehue/Ordenanza_DerechosMunicipales_2330.md",
    "decreto 2330 panquehue": "panquehue/Ordenanza_DerechosMunicipales_2330.md",
    "decreto 1182 panquehue": "panquehue/Ordenanza_87296.md",
    "residuos panquehue": "panquehue/Ordenanza_Residuos_8.md",
    "panquehue residuos": "panquehue/Ordenanza_Residuos_8.md",
    "ruidos panquehue": "panquehue/Ordenanza_Ruidos_2.md",
    "panquehue ruidos": "panquehue/Ordenanza_Ruidos_2.md",
    "subvenciones panquehue": "panquehue/Ordenanza_Subvenciones_1786.md",
    "panquehue subvenciones": "panquehue/Ordenanza_Subvenciones_1786.md",
    "tenencia responsable panquehue": "panquehue/Ordenanza_TenenciaResponsable_1.md",
    "panquehue tenencia responsable": "panquehue/Ordenanza_TenenciaResponsable_1.md",
    "vehiculos panquehue": "panquehue/Ordenanza_Vehiculos_1.md",
    "panquehue vehiculos": "panquehue/Ordenanza_Vehiculos_1.md",
    "aseo papudo": "papudo/Ordenanza_Aseo_321.md",
    "papudo aseo": "papudo/Ordenanza_Aseo_321.md",
    "derechos municipales papudo": "papudo/Ordenanza_DerechosMunicipales_384.md",
    "papudo derechos municipales": "papudo/Ordenanza_DerechosMunicipales_384.md",
    "alcoholes petorca": "petorca/Ordenanza_Alcoholes_620.md",
    "petorca alcoholes": "petorca/Ordenanza_Alcoholes_620.md",
    "decreto 620 petorca": "petorca/Ordenanza_Alcoholes_620.md",
    "derechos municipales petorca": "petorca/Ordenanza_DerechosMunicipales_1633.md",
    "petorca derechos municipales": "petorca/Ordenanza_DerechosMunicipales_1633.md",
    "decreto 1633 petorca": "petorca/Ordenanza_DerechosMunicipales_1633.md",
    "ferias libres petorca": "petorca/Ordenanza_FeriasLibres_2001 EXENTO.md",
    "petorca ferias libres": "petorca/Ordenanza_FeriasLibres_2001 EXENTO.md",
    "derechos municipales puchuncavi": "puchuncavi/Ordenanza_DerechosMunicipales_480.md",
    "puchuncavi derechos municipales": "puchuncavi/Ordenanza_DerechosMunicipales_480.md",
    "puchuncaví derechos municipales": "puchuncavi/Ordenanza_DerechosMunicipales_480.md",
    "patentes puchuncavi": "puchuncavi/Ordenanza_Patentes_1342.md",
    "puchuncavi patentes": "puchuncavi/Ordenanza_Patentes_1342.md",
    "puchuncaví patentes": "puchuncavi/Ordenanza_Patentes_1342.md",
    "aseo putaendo": "putaendo/Ordenanza_Aseo_1948.md",
    "putaendo aseo": "putaendo/Ordenanza_Aseo_1948.md",
    "derechos municipales putaendo": "putaendo/Ordenanza_DerechosMunicipales_1949.md",
    "putaendo derechos municipales": "putaendo/Ordenanza_DerechosMunicipales_1949.md",
    "patentes putaendo": "putaendo/Ordenanza_Patentes_2923.md",
    "putaendo patentes": "putaendo/Ordenanza_Patentes_2923.md",
    "subvenciones putaendo": "putaendo/Ordenanza_Subvenciones_S_N.md",
    "putaendo subvenciones": "putaendo/Ordenanza_Subvenciones_S_N.md",
    "alcoholes quillota": "quillota/Ordenanza_Alcoholes_1933.md",
    "quillota alcoholes": "quillota/Ordenanza_Alcoholes_1933.md",
    "aseo quillota": "quillota/Ordenanza_Aseo_619.md",
    "quillota aseo": "quillota/Ordenanza_Aseo_619.md",
    "decreto 619 quillota": "quillota/Ordenanza_Aseo_619.md",
    "tarifas aseo quillota": "quillota/Ordenanza_Aseo_2280.md",
    "quillota tarifas aseo": "quillota/Ordenanza_Aseo_2280.md",
    "comercio via publica quillota": "quillota/Ordenanza_ComercioViaPublica_842.md",
    "quillota comercio via publica": "quillota/Ordenanza_ComercioViaPublica_842.md",
    "derechos municipales quillota": "quillota/Ordenanza_DerechosMunicipales_2364.md",
    "quillota derechos municipales": "quillota/Ordenanza_DerechosMunicipales_2364.md",
    "decreto 2364 quillota": "quillota/Ordenanza_DerechosMunicipales_2364.md",
    "ruidos quillota": "quillota/Ordenanza_Ruidos_175.md",
    "quillota ruidos": "quillota/Ordenanza_Ruidos_175.md",
    "subvenciones quillota": "quillota/Ordenanza_Subvenciones_3353.md",
    "quillota subvenciones": "quillota/Ordenanza_Subvenciones_3353.md",
    "tenencia responsable quillota": "quillota/Ordenanza_TenenciaResponsable_2779.md",
    "quillota tenencia responsable": "quillota/Ordenanza_TenenciaResponsable_2779.md",
    "vehiculos quillota": "quillota/Ordenanza_Vehiculos_220.md",
    "quillota vehiculos": "quillota/Ordenanza_Vehiculos_220.md",
    "derechos municipales quilpue": "quilpue/Ordenanza_DerechosMunicipales_8.md",
    "quilpue derechos municipales": "quilpue/Ordenanza_DerechosMunicipales_8.md",
    "quilpué derechos municipales": "quilpue/Ordenanza_DerechosMunicipales_8.md",
    "ferias libres quilpue": "quilpue/Ordenanza_FeriasLibres_2.md",
    "quilpue ferias libres": "quilpue/Ordenanza_FeriasLibres_2.md",
    "quilpué ferias libres": "quilpue/Ordenanza_FeriasLibres_2.md",
    "alcoholes quintero": "quintero/Ordenanza_Alcoholes_1328.md",
    "quintero alcoholes": "quintero/Ordenanza_Alcoholes_1328.md",
    "decreto 1328 quintero": "quintero/Ordenanza_Alcoholes_1328.md",
    "derechos municipales quintero": "quintero/Ordenanza_DerechosMunicipales_14.md",
    "quintero derechos municipales": "quintero/Ordenanza_DerechosMunicipales_14.md",
    "mercado quintero": "quintero/Ordenanza_Mercado_S_N.md",
    "quintero mercado": "quintero/Ordenanza_Mercado_S_N.md",
    "ruidos quintero": "quintero/Ordenanza_Ruidos_202.md",
    "quintero ruidos": "quintero/Ordenanza_Ruidos_202.md",
    "aseo rinconada": "rinconada/Ordenanza_Aseo_1433.md",
    "rinconada aseo": "rinconada/Ordenanza_Aseo_1433.md",
    "derechos municipales rinconada": "rinconada/Ordenanza_DerechosMunicipales_3566.md",
    "rinconada derechos municipales": "rinconada/Ordenanza_DerechosMunicipales_3566.md",
    "aseo san antonio": "san_antonio/Ordenanza_Aseo_6.md",
    "san antonio aseo": "san_antonio/Ordenanza_Aseo_6.md",
    "parquimetros san antonio": "san_antonio/Ordenanza_Parquimetros_7.md",
    "san antonio parquimetros": "san_antonio/Ordenanza_Parquimetros_7.md",
    "subvenciones san antonio": "san_antonio/Ordenanza_Subvenciones_838.md",
    "san antonio subvenciones": "san_antonio/Ordenanza_Subvenciones_838.md",
    "aseo san esteban": "san_esteban/Ordenanza_Aseo_2079.md",
    "san esteban aseo": "san_esteban/Ordenanza_Aseo_2079.md",
    "derechos municipales san esteban": "san_esteban/Ordenanza_DerechosMunicipales_172.md",
    "san esteban derechos municipales": "san_esteban/Ordenanza_DerechosMunicipales_172.md",
    "aseo san felipe": "san_felipe/Ordenanza_Aseo_S_N.md",
    "san felipe aseo": "san_felipe/Ordenanza_Aseo_S_N.md",
    "derechos municipales san felipe": "san_felipe/Ordenanza_DerechosMunicipales_S_N.md",
    "san felipe derechos municipales": "san_felipe/Ordenanza_DerechosMunicipales_S_N.md",
    "mercado san felipe": "san_felipe/Ordenanza_Mercado_583 EXENTO.md",
    "san felipe mercado": "san_felipe/Ordenanza_Mercado_583 EXENTO.md",
    "decreto 583 san felipe": "san_felipe/Ordenanza_Mercado_583 EXENTO.md",
    "transito san felipe": "san_felipe/Ordenanza_Transito_32.md",
    "san felipe transito": "san_felipe/Ordenanza_Transito_32.md",
    "tránsito san felipe": "san_felipe/Ordenanza_Transito_32.md",
    "san felipe tránsito": "san_felipe/Ordenanza_Transito_32.md",
    "vehiculos san felipe": "san_felipe/Ordenanza_Vehiculos_24.md",
    "san felipe vehiculos": "san_felipe/Ordenanza_Vehiculos_24.md",
    "alcoholes santa maria": "santa_maria/Ordenanza_Alcoholes_1.md",
    "santa maria alcoholes": "santa_maria/Ordenanza_Alcoholes_1.md",
    "aseo santa maria": "santa_maria/Ordenanza_Aseo_1 EXENTO.md",
    "santa maria aseo": "santa_maria/Ordenanza_Aseo_1 EXENTO.md",
    "derechos municipales santa maria": "santa_maria/Ordenanza_DerechosMunicipales_1.md",
    "santa maria derechos municipales": "santa_maria/Ordenanza_DerechosMunicipales_1.md",
    "alcoholes santo domingo": "santo_domingo/Ordenanza_Alcoholes_1053.md",
    "santo domingo alcoholes": "santo_domingo/Ordenanza_Alcoholes_1053.md",
    "derechos municipales santo domingo": "santo_domingo/Ordenanza_DerechosMunicipales_614.md",
    "santo domingo derechos municipales": "santo_domingo/Ordenanza_DerechosMunicipales_614.md",
    "aseo valparaiso": "valparaiso/Ordenanza_Aseo_546.md",
    "valparaiso aseo": "valparaiso/Ordenanza_Aseo_546.md",
    "valparaíso aseo": "valparaiso/Ordenanza_Aseo_546.md",
    "derechos municipales valparaiso": "valparaiso/Ordenanza_DerechosMunicipales_7005.md",
    "valparaiso derechos municipales": "valparaiso/Ordenanza_DerechosMunicipales_7005.md",
    "valparaíso derechos municipales": "valparaiso/Ordenanza_DerechosMunicipales_7005.md",
    "decreto 7005 valparaiso": "valparaiso/Ordenanza_DerechosMunicipales_7005.md",
    "ferias libres valparaiso": "valparaiso/Ordenanza_FeriasLibres_1629.md",
    "valparaiso ferias libres": "valparaiso/Ordenanza_FeriasLibres_1629.md",
    "valparaíso ferias libres": "valparaiso/Ordenanza_FeriasLibres_1629.md",
    "publicidad valparaiso": "valparaiso/Ordenanza_Publicidad_2082.md",
    "valparaiso publicidad": "valparaiso/Ordenanza_Publicidad_2082.md",
    "valparaíso publicidad": "valparaiso/Ordenanza_Publicidad_2082.md",
    "alcoholes villa alemana": "villa_alemana/Ordenanza_Alcoholes_1405-idNorma231783.md",
    "villa alemana alcoholes": "villa_alemana/Ordenanza_Alcoholes_1405-idNorma231783.md",
    "aseo villa alemana": "villa_alemana/Ordenanza_Aseo_1486-idNorma1064541.md",
    "villa alemana aseo": "villa_alemana/Ordenanza_Aseo_1486-idNorma1064541.md",
    "derechos municipales villa alemana": "villa_alemana/Ordenanza_DerechosMunicipales_1512-idNorma1110281.md",
    "villa alemana derechos municipales": "villa_alemana/Ordenanza_DerechosMunicipales_1512-idNorma1110281.md",
    "ferias libres villa alemana": "villa_alemana/Ordenanza_FeriasLibres_1259-idNorma253605.md",
    "villa alemana ferias libres": "villa_alemana/Ordenanza_FeriasLibres_1259-idNorma253605.md",
    "mercado villa alemana": "villa_alemana/Ordenanza_Mercado_1354-idNorma1110882.md",
    "villa alemana mercado": "villa_alemana/Ordenanza_Mercado_1354-idNorma1110882.md",
    "residuos villa alemana": "villa_alemana/Ordenanza_Residuos_468-idNorma1131717.md",
    "villa alemana residuos": "villa_alemana/Ordenanza_Residuos_468-idNorma1131717.md",
    "tenencia responsable villa alemana": "villa_alemana/Ordenanza_TenenciaResponsable_1767-idNorma1021441.md",
    "villa alemana tenencia responsable": "villa_alemana/Ordenanza_TenenciaResponsable_1767-idNorma1021441.md",
    "alcoholes zapallar": "zapallar/Ordenanza_Alcoholes_3972.md",
    "zapallar alcoholes": "zapallar/Ordenanza_Alcoholes_3972.md",
    "decreto 3972 zapallar": "zapallar/Ordenanza_Alcoholes_3972.md",
    "aseo zapallar": "zapallar/Ordenanza_Aseo_4699.md",
    "zapallar aseo": "zapallar/Ordenanza_Aseo_4699.md",
    "decreto 4699 zapallar": "zapallar/Ordenanza_Aseo_4699.md",
    "derechos municipales zapallar": "zapallar/Ordenanza_DerechosMunicipales_3940.md",
    "zapallar derechos municipales": "zapallar/Ordenanza_DerechosMunicipales_3940.md",
    "decreto 3940 zapallar": "zapallar/Ordenanza_DerechosMunicipales_3940.md",
    "publicidad zapallar": "zapallar/Ordenanza_Publicidad_1689.md",
    "zapallar publicidad": "zapallar/Ordenanza_Publicidad_1689.md",
    "ruidos zapallar": "zapallar/Ordenanza_Ruidos_18.md",
    "zapallar ruidos": "zapallar/Ordenanza_Ruidos_18.md",
    "dto 172": "Reglamento_19925_Alcoholes_TituloII_art57_DTO172.md",
    "reglamento alcoholes": "Reglamento_19925_Alcoholes_TituloII_art57_DTO172.md",
    "dto 98": "Reglamento_19925_Alcoholes_40bis40ter_DTO98.md",
    "dto 212": "Reglamento_18290_Transito_TransportePublico_DTO212.md",
    "reglamento transporte publico": "Reglamento_18290_Transito_TransportePublico_DTO212.md",
    "dto 170": "Reglamento_18290_LicenciasConductor_DTO170.md",
    "reglamento licencias": "Reglamento_18290_LicenciasConductor_DTO170.md",
    "dto 1007": "Reglamento_21020_Tenencia_DS1007.md",
    "ds 1007": "Reglamento_21020_Tenencia_DS1007.md",
    "reglamento tenencia": "Reglamento_21020_Tenencia_DS1007.md",
}

# --- Parser robusto de artículos ---
# Maneja tanto el formato limpio ("## Artículo 14") como el texto refundido con
# anotaciones marginales (Ley 18.290 DFL 1/2007): "Art. 163 Nº 5" con refs al
# margen derecho ("D.O 07.02.1984", "LEY Nº18.290", "Art. 165 Nº 6") que en el
# OCR aparecen con sangría grande y NO son inicios de artículo.

_ART_MARKER = re.compile(
    r"^\s{0,9}(?:#{1,6}\s+)?(?:A[Rr][Tt][IÍí][Cc][Uu][Ll][Oo]|Art\.|Art\u00ba?)\s+"
    r"(?:(?:N[°º]?\s*)?(\d+)(?:\s*(bis|ter|qu[áa]ter|quinquies|sexies|septies))?(?:\s*N[°º]\s*(\d+))?|(único|unico|primero|segundo|tercero))"
    r"[°º.\-:\s]*",
)
_PALABRA_ORDINAL = {"unico": 0, "único": 0, "primero": 1, "segundo": 2, "tercero": 3, "cuarto": 4, "quinto": 5}
_ANOTACION_INICIO = re.compile(r"^(D\.?\s?O\.?|LEY\s*N[°º]?\s*\d|Rectificaci[óo]n)\b", re.IGNORECASE)


_MARGEN_FINAL = re.compile(
    r"\s*(?:LEY\s*N[°º]?\s*[\d.]+[\s.]*|D\.?\s?O\.?\s*[\d.\-]+[\s.]*|Art\.\s*\d+\s*N[°º]?\s*\d+[\s.]*)+$",
    re.IGNORECASE,
)

def _reparar_texto(lineas: list[str]) -> str:
    """Une líneas, repara palabras cortadas por guión, quita anotaciones
    marginales pegadas al final de líneas de contenido y colapsa espacios."""
    limpias = []
    for l in lineas:
        if not l:
            continue
        s = l.strip()
        if s:
            s = _MARGEN_FINAL.sub("", s).strip()
        if s:
            limpias.append(s)
    texto = " ".join(limpias)
    texto = re.sub(r"([a-záéíóúñü])-\s+([a-záéíóúñü])", r"\1\2", texto)
    texto = re.sub(r"\s{2,}", " ", texto)
    return texto.strip()


def _extraer_articulos(texto: str) -> list[dict]:
    """Extrae artículos de un texto de ley, tolerando anotaciones marginales.

    Devuelve [{numero: int, texto: str, numerales: [{numeral, texto}]}].
    Los segmentos consecutivos del mismo artículo (numerales "Art. 165 Nº 5",
    "Art. 165 Nº 6"...) se fusionan en un solo artículo.
    """
    segmentos: list[dict] = []
    actual: dict | None = None
    for linea in texto.splitlines():
        stripped = linea.strip()
        if not stripped:
            continue
        indent = len(linea) - len(linea.lstrip(" "))
        # Columna marginal del texto refundido (sangría grande = anotación)
        if indent >= 10:
            continue
        # Anotaciones que nunca son contenido (aunque vengan a la izquierda)
        if len(stripped) <= 60 and _ANOTACION_INICIO.match(stripped):
            continue
        m = _ART_MARKER.match(linea)
        if m:
            if actual:
                segmentos.append(actual)
            palabra = (m.group(4) or "").lower()
            if palabra:
                numero = _PALABRA_ORDINAL.get(palabra, 1)
                numeral = ""
                ordinal = ""
            else:
                numero = int(m.group(1)) if m.group(1) else 1
                numeral = m.group(3) or ""
                # bis/ter/quater... = artículo DISTINTO (no numeral del mismo)
                ordinal = (m.group(2) or "").lower()
            resto = linea[m.end():].strip()
            actual = {"numero": numero, "numeral": numeral, "ordinal": ordinal,
                      "lineas": [resto] if resto else []}
            continue
        if actual is not None:
            actual["lineas"].append(stripped)
    if actual:
        segmentos.append(actual)
    # Fusionar segmentos consecutivos del mismo artículo (mismo número Y mismo
    # ordinal: "Art. 165 Nº 5"/"Art. 165 Nº 6" se fusionan; "200"/"200 bis" NO)
    fusionados: list[dict] = []
    for seg in segmentos:
        clave = (seg["numero"], seg.get("ordinal", ""))
        if fusionados and fusionados[-1]["clave"] == clave:
            fusionados[-1]["numerales"].append({"numeral": seg["numeral"], "texto": _reparar_texto(seg["lineas"])})
        else:
            fusionados.append({
                "clave": clave,
                "numero": seg["numero"],
                "numerales": [{"numeral": seg["numeral"], "texto": _reparar_texto(seg["lineas"])}],
            })
    for a in fusionados:
        a["texto"] = " ".join(n["texto"] for n in a["numerales"] if n["texto"]).strip()
    return fusionados


# Compatibilidad: marcadores antiguos (ya no usados por _articulos)
ART_START = _ART_MARKER
TITULO_START = re.compile(r"^\s*##\s+TITULO", re.IGNORECASE)

_cache: dict[str, list[dict]] = {}

def _slug(nombre: str) -> str:
    return nombre.lower().replace("ley", "").replace("n", "").replace("ñ", "").strip()

def _match_alias(clave: str) -> str | None:
    clave_norm = clave.strip().lower()
    if clave_norm in ALIASES:
        return ALIASES[clave_norm]
    for k, v in ALIASES.items():
        if k in clave_norm or clave_norm in k:
            return v
    for f in CORPUS_DIR.glob("*.md"):
        if _slug(f.stem) and _slug(clave_norm) in _slug(f.stem):
            return f.name
    return None

META_FIELD = re.compile(r"\*\*([^:]+):\*\*\s*([^|]+)")

_ensured = False

def _ensure_fts() -> None:
    """Verifica tablas FTS; si faltan, las crea y puebla desde los textos. Corre una vez."""
    con = _db_conn()
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE name LIKE '%_fts'")
    have = {r[0] for r in cur.fetchall()}
    need = {"leyes_fts", "ordenanzas_fts", "manuales_fts"} - have
    if not need:
        con.close()
        return
    print(f"[jpl-leyes] Construyendo índices FTS locales ({sorted(need)})... puede tardar ~1-2 min")
    t0 = time.perf_counter()
    tokenizer = 'unicode61 "remove_diacritics 1"'
    schemas = {
        "leyes_fts": "CREATE VIRTUAL TABLE leyes_fts USING fts5(titulo, texto, content='', tokenize='{tok}')",
        "ordenanzas_fts": "CREATE VIRTUAL TABLE ordenanzas_fts USING fts5(titulo, texto, comuna, materia, content='', tokenize='{tok}')",
        "manuales_fts": "CREATE VIRTUAL TABLE manuales_fts USING fts5(nombre, texto, categoria, content='', tokenize='{tok}')",
    }
    try:
        for name in sorted(need):
            cur.execute(schemas[name].format(tok=tokenizer))
    except sqlite3.OperationalError:
        # fallback sin remove_diacritics
        tokenizer = "unicode61"
        for name in ["leyes_fts", "ordenanzas_fts", "manuales_fts"]:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {name}")
            except Exception:
                pass
        for name in sorted(need):
            cur.execute(schemas[name].format(tok=tokenizer))
    con.commit()
    cur.execute("INSERT INTO leyes_fts(rowid, titulo, texto) SELECT id, titulo, texto FROM leyes")
    cur.execute("INSERT INTO ordenanzas_fts(rowid, titulo, texto, comuna, materia) SELECT id, titulo, texto, comuna, materia FROM ordenanzas")
    cur.execute("INSERT INTO manuales_fts(rowid, nombre, texto, categoria) SELECT id, nombre, texto, categoria FROM manuales")
    con.commit()
    con.close()
    print(f"[jpl-leyes] FTS listo en {time.perf_counter()-t0:.0f}s — próximas consultas serán instantáneas")

def _ensure_db() -> bool:
    """Garantiza corpus.db local: descomprime .zst si falta y construye FTS on-demand. Una sola vez."""
    global _ensured
    if _ensured:
        return DB_PATH.exists()
    _ensured = True
    if DB_PATH.exists():
        try:
            _ensure_fts()
        except Exception as e:
            print(f"[jpl-leyes][warn] no se pudo verificar/construir FTS: {e}")
        return True
    # Try alternative sibling clone location
    alt_zst = _ALT_ZST
    alt_db = _ALT_DB
    if not ZST_PATH.exists() and alt_zst.exists():
        try:
            _JPL_ROOT.mkdir(parents=True, exist_ok=True)
            import shutil; shutil.copy2(str(alt_zst), str(ZST_PATH))
        except Exception:
            pass
    if alt_db.exists() and not DB_PATH.exists():
        try:
            _JPL_ROOT.mkdir(parents=True, exist_ok=True)
            import shutil; shutil.copy2(str(alt_db), str(DB_PATH))
        except Exception:
            pass
    if not ZST_PATH.exists():
        return False
    mb = ZST_PATH.stat().st_size / 1024 / 1024
    print(f"[jpl-leyes] Primer arranque: descomprimiendo corpus.db.zlib ({mb:.1f} MB)...")
    t0 = time.perf_counter()
    raw = zlib.decompress(ZST_PATH.read_bytes())
    DB_PATH.write_bytes(raw)
    print(f"[jpl-leyes] corpus.db listo ({len(raw)/1024/1024:.1f} MB) en {time.perf_counter()-t0:.0f}s")
    try:
        _ensure_fts()
    except Exception as e:
        print(f"[jpl-leyes][warn] FTS pendiente (reintento en próxima consulta): {e}")
    return True

def _use_db() -> bool:
    return _ensure_db()

def _decompress(valor) -> str:
    """Acepta TEXT plano (nuevo esquema), BLOB zlib (legacy) o None."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    try:
        return zlib.decompress(valor).decode("utf-8", errors="ignore")
    except Exception:
        try:
            return valor.decode("utf-8", errors="ignore")  # fallback si no está comprimido
        except Exception:
            return ""

def _db_conn():
    return sqlite3.connect(str(DB_PATH))

def _resolver(nombre: str) -> Path:
    p = CORPUS_DIR / nombre
    if p.exists():
        return p
    p = ORDENANZAS_DIR / nombre
    if p.exists():
        return p
    return CORPUS_DIR / nombre

def _leer(nombre: str) -> str:
    # Si DB existe, leer de allí
    if _use_db():
        # intentar leyes
        try:
            con = _db_conn()
            cur = con.cursor()
            cur.execute("SELECT texto FROM leyes WHERE archivo=?", (nombre,))
            row = cur.fetchone()
            if row:
                con.close()
                return _decompress(row[0])
            # intentar ordenanzas (archivo es comuna/archivo)
            cur.execute("SELECT texto FROM ordenanzas WHERE archivo=?", (nombre,))
            row = cur.fetchone()
            if row:
                con.close()
                return _decompress(row[0])
            # intentar por nombre solo
            cur.execute("SELECT texto FROM ordenanzas WHERE archivo LIKE ?", (f"%/{nombre}",))
            row = cur.fetchone()
            con.close()
            if row:
                return _decompress(row[0])
        except Exception:
            pass
        try:
            con.close()
        except Exception:
            pass
    p = _resolver(nombre)
    if not p.exists():
        raise FileNotFoundError(f"No existe {p}")
    return p.read_text(encoding="utf-8-sig", errors="ignore")

def _metadata(nombre: str) -> dict:
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            # leyes
            cur.execute("SELECT tipo, numero, organismo, publicacion, version, estado, idNorma FROM leyes WHERE archivo=?", (nombre,))
            row = cur.fetchone()
            if row:
                con.close()
                return {"Tipo": row[0] or "", "N°": row[1] or "", "Organismo": row[2] or "", "Publicación": row[3] or "", "Versión BCN vigente": row[4] or "", "Estado": row[5] or "", "idNorma BCN": row[6] or "", "idNorma": row[6] or ""}
            # ordenanzas
            cur.execute("SELECT tipo, numero, organismo, publicacion, estado FROM ordenanzas WHERE archivo=?", (nombre,))
            # ordenanzas no tiene tipo/organismo en nuevo esquema, pero intentamos por archivo LIKE
            cur.execute("SELECT decreto, idNorma, publicacion, estado, comuna FROM ordenanzas WHERE archivo=?", (nombre,))
            row = cur.fetchone()
            if row:
                con.close()
                return {"N°": row[0] or "", "idNorma": row[1] or "", "idNorma BCN": row[1] or "", "Publicación": row[2] or "", "Estado": row[3] or "", "Organismo": row[4] or ""}
            cur.execute("SELECT decreto, idNorma, publicacion, estado FROM ordenanzas WHERE archivo LIKE ?", (f"%/{nombre}",))
            row = cur.fetchone()
            con.close()
            if row:
                return {"N°": row[0] or "", "idNorma": row[1] or "", "idNorma BCN": row[1] or "", "Publicación": row[2] or "", "Estado": row[3] or ""}
            con.close()
        except Exception:
            try:
                con.close()
            except Exception:
                pass
    texto = _leer(nombre)
    meta = {}
    for line in texto.splitlines()[:12]:
        for m in META_FIELD.finditer(line):
            meta[m.group(1)] = m.group(2).strip()
    return meta

def _leer_texto_completo(nombre: str) -> str:
    return _leer(nombre)

def listar_leyes() -> list[dict]:
    """Devuelve todas las leyes del corpus con metadatos. Usa DB si existe, sino filesystem."""
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            cur.execute("SELECT archivo, tipo, numero, organismo, version, estado, idNorma FROM leyes ORDER BY archivo")
            rows = cur.fetchall()
            con.close()
            resultado = []
            for archivo, tipo, numero, organismo, version, estado, idNorma in rows:
                resultado.append({
                    "archivo": archivo,
                    "tipo": tipo or "",
                    "numero": numero or "",
                    "organismo": organismo or "",
                    "version": version or "",
                    "estado": estado or "",
                    "idNorma": idNorma or "",
                })
            return resultado
        except Exception:
            pass
    # fallback filesystem
    resultado = []
    for f in sorted(CORPUS_DIR.glob("*.md")):
        if f.name.startswith("INDICE"):
            continue
        meta = _metadata(f.name)
        resultado.append({
            "archivo": f.name,
            "tipo": meta.get("Tipo", ""),
            "numero": meta.get("N°") or meta.get("Nº") or meta.get("Numero", ""),
            "organismo": meta.get("Organismo", ""),
            "version": meta.get("Versión BCN vigente") or meta.get("Versión", ""),
            "estado": meta.get("Estado", ""),
            "idNorma": meta.get("idNorma BCN") or meta.get("idNorma", ""),
        })
    return resultado

def _articulos(nombre: str) -> list[dict]:
    if nombre in _cache:
        return _cache[nombre]
    texto = _leer(nombre)
    arts = _extraer_articulos(texto)
    _cache[nombre] = arts
    return arts

def buscar_articulo(ley: str, articulo: int | str) -> list[dict]:
    """Busca un artículo por número en una ley. Soporta numeral con punto
    (ej. '163.5' → artículo 163 N° 5) y ordinales ('unico', 'primero')."""
    archivo = _match_alias(ley)
    if not archivo:
        return []
    s = str(articulo).strip().lower().replace("°", "").replace("º", "")
    numeral: str | None = None
    if s in _PALABRA_ORDINAL:
        numero = _PALABRA_ORDINAL[s]
    else:
        partes = s.split(".")
        try:
            numero = int(partes[0])
        except ValueError:
            return []
        if len(partes) > 1 and partes[1]:
            numeral = partes[1]
    matches: list[dict] = []
    for a in _articulos(archivo):
        if a["numero"] != numero:
            continue
        base = {"ley": archivo.replace(".md", ""), "articulo": a["numero"]}
        if numeral:
            for n in a.get("numerales", []):
                if (n["numeral"] or "").strip().lower() == numeral:
                    return [dict(base, numeral=n["numeral"], texto=n["texto"])]
            # El numeral no existe como segmento separado (p.ej. "201.1" donde
            # el N° 1 es un ítem interno del texto): devolver el artículo completo.
            matches.append(a)
            continue
        matches.append(a)
    # Ante números duplicados (p.ej. DFL: arts. del decreto + arts. de la ley
    # refundida), prevalece la última aparición (cuerpo legal propiamente tal);
    # si hay variantes con ordinal ("200", "200 bis"), gana la sin ordinal.
    if matches:
        simples = [a for a in matches if not a["clave"][1]]
        a = (simples or matches)[-1]
        return [{
            "ley": archivo.replace(".md", ""),
            "articulo": a["numero"],
            "texto": a["texto"],
            "numerales": a.get("numerales", []),
        }]
    return []

_ley_texto_cache: dict[str, str] = {}
_ley_lineas_cache: dict[str, list[str]] = {}

def _texto_ley(archivo: str) -> str:
    """Texto de una ley con cache en memoria (descomprime una sola vez)."""
    if archivo not in _ley_texto_cache:
        _ley_texto_cache[archivo] = _leer(archivo)
    return _ley_texto_cache[archivo]

def _lineas_ley(archivo: str) -> list[str]:
    """Líneas en minúsculas de una ley, cacheadas para escaneo rápido."""
    if archivo not in _ley_lineas_cache:
        _ley_lineas_cache[archivo] = _texto_ley(archivo).lower().splitlines()
    return _ley_lineas_cache[archivo]

def _terminos(consulta: str) -> list[str]:
    return [t for t in re.findall(r"[a-záéíóúñü0-9]+", consulta.lower()) if len(t) > 2]

def _extraer_extractos(lineas: list[str], terminos: list[str], max_extractos: int = 5) -> tuple[int, list[str]]:
    """Devuelve (n_coincidencias, extractos con contexto) para líneas que
    contengan alguno de los términos, priorizando las que tienen más."""
    hits: list[tuple[int, str]] = []
    for i, l in enumerate(lineas):
        ll = l.lower()
        score = sum(1 for t in terminos if t in ll)
        if score:
            ctx = " ".join(x.strip() for x in lineas[max(0, i - 1):i + 2] if x.strip())
            hits.append((score, _reparar_texto([ctx])))
    if not hits:
        return 0, []
    hits.sort(key=lambda x: -x[0])
    vistos: set[str] = set()
    extractos: list[str] = []
    for _, ctx in hits:
        key = ctx[:80].lower()
        if key in vistos:
            continue
        vistos.add(key)
        extractos.append(ctx)
        if len(extractos) >= max_extractos:
            break
    return len(hits), extractos

def buscar_ley(consulta: str, limite: int = 15) -> list[dict]:
    """Búsqueda por palabras (AND flexible) en el texto de todas las leyes.
    Encuentra términos aunque la frase exacta no exista en una sola línea."""
    terminos = _terminos(consulta)
    if not terminos:
        return []
    filas: list[tuple[str, str]] = []
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            cur.execute("SELECT archivo, titulo FROM leyes")
            filas = cur.fetchall()
            con.close()
        except Exception:
            filas = []
    if not filas:
        for f in sorted(CORPUS_DIR.glob("*.md")):
            if f.name.startswith("INDICE"):
                continue
            filas.append((f.name, ""))
    resultado = []
    for archivo, titulo in filas:
        lineas = _lineas_ley(archivo)
        n, extractos = _extraer_extractos(lineas, terminos)
        if not n:
            continue
        # términos distintos presentes en toda la ley (relevancia temática)
        texto_lower = "\n".join(lineas)
        distintos = sum(1 for t in terminos if t in texto_lower)
        densidad = n / max(len(lineas), 1)
        resultado.append({
            "ley": archivo.replace(".md", ""),
            "titulo": titulo or "",
            "coincidencias": n,
            "terminos_distintos": distintos,
            "densidad": round(densidad, 6),
            "extractos": extractos,
        })
    # Ranking: primero relevancia temática (términos distintos), luego total
    # de coincidencias, y densidad al final (evita que una ley chica con pocas
    # menciones gane por tamaño sobre la ley núcleo de la materia)
    resultado.sort(key=lambda x: (-x["terminos_distintos"], -x["coincidencias"], -x["densidad"]))
    for r in resultado:
        r.pop("densidad", None)
    return resultado[:limite]

def normativa_alternativa(materia: str) -> list[dict]:
    import json
    kb_path = CORPUS_DIR / "knowledge_base.json"
    if not kb_path.exists():
        return []
    kb = json.loads(kb_path.read_text(encoding="utf-8"))
    seccion = kb.get("normativa_alternativa", {})
    materia_norm = materia.replace(" ", "_").lower()
    if materia_norm in seccion:
        return seccion[materia_norm]
    return seccion.get("fuera_corpus_jpl_requiere_buscarse_en_bcn", [])

def verificar_vigencia(ley: str) -> list[dict]:
    """Devuelve metadatos de vigencia de una ley. Si DB existe, lee de allí."""
    archivo = _match_alias(ley)
    if not archivo:
        return [{
            "ley": ley,
            "archivo": None,
            "Estado": "FUERA DE CORPUS JPL",
            "observacion": "La norma no fue encontrada en el corpus local. Buscar en BCN/LeyChile y verificar vigencia antes de citar.",
            "vigente_en_corpus": False,
        }]
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            cur.execute("SELECT archivo, tipo, numero, organismo, version, estado, idNorma FROM leyes WHERE archivo=?", (archivo,))
            row = cur.fetchone()
            con.close()
            if row:
                arch, tipo, numero, organismo, version, estado, idNorma = row
                meta = {"archivo": arch, "Tipo": tipo or "", "N°": numero or "", "Organismo": organismo or "", "Versión BCN vigente": version or "", "Versión": version or "", "Estado": estado or "", "idNorma BCN": idNorma or "", "idNorma": idNorma or ""}
                if not meta.get("Estado"):
                    meta["Estado"] = "PENDIENTE verificación en BCN (metadata ausente en conversión)"
                    meta["vigente_en_corpus"] = False
                else:
                    meta["vigente_en_corpus"] = meta.get("Estado") == "no derogado"
                return [meta]
            else:
                # intentar por nombre base
                con = _db_conn()
                cur = con.cursor()
                cur.execute("SELECT archivo, tipo, numero, organismo, version, estado, idNorma FROM leyes WHERE archivo LIKE ?", (f"%{archivo}%",))
                row = cur.fetchone()
                con.close()
                if row:
                    arch, tipo, numero, organismo, version, estado, idNorma = row
                    meta = {"archivo": arch, "Tipo": tipo or "", "N°": numero or "", "Organismo": organismo or "", "Versión BCN vigente": version or "", "Versión": version or "", "Estado": estado or "", "idNorma BCN": idNorma or "", "idNorma": idNorma or ""}
                    meta["vigente_en_corpus"] = meta.get("Estado") == "no derogado"
                    return [meta]
        except Exception:
            pass
    meta = _metadata(archivo)
    meta["archivo"] = archivo
    if not meta.get("Estado"):
        meta["Estado"] = "PENDIENTE verificación en BCN (metadata ausente en conversión)"
        meta["vigente_en_corpus"] = False
    else:
        meta["vigente_en_corpus"] = meta.get("Estado") == "no derogado"
    return [meta]

def _normalizar_municipalidad(nombre: str) -> str:
    n = unicodedata.normalize("NFD", nombre)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return n.strip().lower().replace(" ", "_")

def listar_ordenanzas(municipalidad: str | None = None) -> list[dict]:
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            if municipalidad:
                norm = _normalizar_municipalidad(municipalidad)
                # buscar carpeta exacta (case-insensitive via lower)
                cur.execute("SELECT DISTINCT comuna FROM ordenanzas")
                comunas = [r[0] for r in cur.fetchall()]
                target = None
                for c in comunas:
                    if c.lower() == norm.lower() or _normalizar_municipalidad(c) == norm:
                        target = c
                        break
                if not target:
                    target = norm
                cur.execute("SELECT comuna, archivo, decreto, materia, idNorma, publicacion, estado, titulo FROM ordenanzas WHERE comuna=? ORDER BY archivo", (target,))
                rows = cur.fetchall()
                con.close()
                if not rows:
                    # fallback like
                    con = _db_conn()
                    cur = con.cursor()
                    cur.execute("SELECT comuna, archivo, decreto, materia, idNorma, publicacion, estado, titulo FROM ordenanzas WHERE comuna LIKE ? ORDER BY archivo", (f"%{norm}%",))
                    rows = cur.fetchall()
                    con.close()
                resultado = []
                for comuna, archivo, decreto, materia, idNorma, publicacion, estado, titulo in rows:
                    fname = archivo.split("/")[-1] if "/" in archivo else archivo
                    resultado.append({
                        "municipalidad": comuna,
                        "archivo": fname,
                        "tipo": "",
                        "numero": decreto or "",
                        "organismo": "",
                        "publicacion": publicacion or "",
                        "estado": estado or "",
                    })
                return resultado
            else:
                cur.execute("SELECT comuna, count(*) FROM ordenanzas GROUP BY comuna ORDER BY comuna")
                rows = cur.fetchall()
                con.close()
                return [{"municipalidad": c, "ordenanzas": n} for c, n in rows]
        except Exception:
            try:
                con.close()
            except Exception:
                pass
    if not ORDENANZAS_DIR.exists():
        return []
    if municipalidad:
        carpeta = ORDENANZAS_DIR / _normalizar_municipalidad(municipalidad)
        if not carpeta.exists():
            # fallback: buscar case-insensitive
            for p in ORDENANZAS_DIR.iterdir():
                if p.is_dir() and _normalizar_municipalidad(p.name) == _normalizar_municipalidad(municipalidad):
                    carpeta = p
                    break
            else:
                return []
        resultado = []
        for f in sorted(carpeta.glob("*.md")):
            if f.name.upper().startswith("INDICE"):
                continue
            rel = f"{carpeta.name}/{f.name}"
            meta = _metadata(rel)
            resultado.append({
                "municipalidad": carpeta.name,
                "archivo": f.name,
                "tipo": meta.get("Tipo", ""),
                "numero": meta.get("N°") or meta.get("Nº") or "",
                "organismo": meta.get("Organismo", ""),
                "publicacion": meta.get("Publicación", ""),
                "estado": meta.get("Estado", ""),
            })
        return resultado
    resultado = []
    for carpeta in sorted(ORDENANZAS_DIR.iterdir()):
        if not carpeta.is_dir() or carpeta.name.startswith("_"):
            continue
        n = len([f for f in carpeta.glob("*.md") if not f.name.upper().startswith("INDICE")])
        resultado.append({"municipalidad": carpeta.name, "ordenanzas": n})
    return resultado

def buscar_ordenanza(municipalidad: str, materia: str, limite: int = 15) -> list[dict]:
    q = materia.strip().lower()
    norm_muni = _normalizar_municipalidad(municipalidad)
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            # Resolver comuna exacta
            cur.execute("SELECT DISTINCT comuna FROM ordenanzas")
            comunas = [r[0] for r in cur.fetchall()]
            target = None
            for c in comunas:
                if _normalizar_municipalidad(c) == norm_muni or c.lower() == norm_muni:
                    target = c
                    break
            if not target:
                con.close()
                return []
            # FTS con filtro por comuna
            # Primero FTS MATCH sobre materia/texto
            try:
                cur.execute("SELECT ordenanzas.archivo, ordenanzas.comuna, ordenanzas.texto FROM ordenanzas JOIN ordenanzas_fts ON ordenanzas.id = ordenanzas_fts.rowid WHERE ordenanzas.comuna=? AND ordenanzas_fts MATCH ? ORDER BY rank LIMIT ?", (target, materia, limite*2))
                rows = cur.fetchall()
            except sqlite3.OperationalError:
                rows = []
            if not rows:
                # fallback LIKE scan sobre esa comuna
                cur.execute("SELECT archivo, comuna, texto FROM ordenanzas WHERE comuna=?", (target,))
                rows = cur.fetchall()
            con.close()
            resultado = []
            for archivo, comuna, blob in rows:
                texto = _decompress(blob)
                lineas = texto.splitlines()
                coincidencias = [l.strip() for l in lineas if q in l.lower()]
                if coincidencias:
                    fname = archivo.split("/")[-1] if "/" in archivo else archivo
                    resultado.append({
                        "municipalidad": comuna,
                        "archivo": fname,
                        "coincidencias": len(coincidencias),
                        "extractos": coincidencias[:8],
                    })
            resultado.sort(key=lambda x: -x["coincidencias"])
            return resultado[:limite]
        except Exception:
            try:
                con.close()
            except Exception:
                pass
    carpeta = ORDENANZAS_DIR / norm_muni
    if not carpeta.exists():
        for p in ORDENANZAS_DIR.iterdir():
            if p.is_dir() and _normalizar_municipalidad(p.name) == norm_muni:
                carpeta = p
                break
        else:
            return []
    resultado = []
    for f in sorted(carpeta.glob("*.md")):
        if f.name.upper().startswith("INDICE"):
            continue
        try:
            texto = f.read_text(encoding="utf-8-sig", errors="ignore")
        except (UnicodeDecodeError, OSError):
            continue
        lineas = texto.splitlines()
        coincidencias = [l.strip() for l in lineas if q in l.lower()]
        if coincidencias:
            resultado.append({
                "municipalidad": carpeta.name,
                "archivo": f.name,
                "coincidencias": len(coincidencias),
                "extractos": coincidencias[:8],
            })
    resultado.sort(key=lambda x: -x["coincidencias"])
    return resultado[:limite]

def buscar_texto(consulta: str, limite: int = 10) -> list[dict]:
    """Búsqueda full-text simultánea en leyes + ordenanzas + manuales.
    Leyes y manuales se escanean por palabras (rápido, ~50ms en caliente);
    ordenanzas vía índice FTS (miles de archivos)."""
    terminos = _terminos(consulta)
    if not terminos:
        return []
    resultados: list[dict] = []

    # 1) Leyes (scan en memoria con cache)
    for r in buscar_ley(consulta, limite=5):
        resultados.append({
            "tipo": "ley",
            "referencia": r["ley"],
            "coincidencias": r["coincidencias"],
            "extractos": r["extractos"],
        })

    # 2) Manuales (6 documentos, scan directo)
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            cur.execute("SELECT nombre, texto FROM manuales")
            for nombre, blob in cur.fetchall():
                texto = _decompress(blob)
                n, extractos = _extraer_extractos(texto.splitlines(), terminos, max_extractos=3)
                if n:
                    resultados.append({"tipo": "manual", "referencia": nombre, "coincidencias": n, "extractos": extractos})
            con.close()
        except Exception:
            pass

    # 3) Ordenanzas vía FTS (MATCH con términos entre comillas unidos por AND)
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE name='ordenanzas_fts'")
            if cur.fetchone():
                match_q = " AND ".join(f'"{t}"' for t in terminos)
                try:
                    cur.execute(
                        "SELECT ordenanzas.archivo, ordenanzas.comuna, ordenanzas.texto "
                        "FROM ordenanzas JOIN ordenanzas_fts ON ordenanzas.id = ordenanzas_fts.rowid "
                        "WHERE ordenanzas_fts MATCH ? ORDER BY rank LIMIT ?",
                        (match_q, limite),
                    )
                    for archivo, comuna, blob in cur.fetchall():
                        texto = _decompress(blob)
                        n, extractos = _extraer_extractos(texto.splitlines(), terminos, max_extractos=3)
                        fname = archivo.split("/")[-1] if "/" in archivo else archivo
                        resultados.append({
                            "tipo": "ordenanza",
                            "referencia": f"{comuna}/{fname}",
                            "coincidencias": n,
                            "extractos": extractos,
                        })
                except sqlite3.OperationalError:
                    pass
            con.close()
        except Exception:
            pass

    resultados.sort(key=lambda x: -x["coincidencias"])
    return resultados[:limite]

# --- Manuales / prompts ---
MANUALES_MAP = {
    "sentencia": "FORMATOS-SENTENCIAS",
    "resolucion-corta": "FORMATOS-RESOLUCIONES-CORTAS",
    "comparendo-declaracion": "FORMATOS-COMPARENDOS-DECLARACIONES",
    "certificado-exhorto": "FORMATOS-CERTIFICADOS-EXHORTOS",
    "oficio-prescripcion": "FORMATOS-OFICIOS-PRESCRIPCION",
    "plazos": "PLAZOS",
}

def _get_manual_text(nombre: str) -> str | None:
    """Lee manual por nombre (stem sin .md) desde DB o filesystem."""
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            cur.execute("SELECT texto FROM manuales WHERE nombre=?", (nombre,))
            row = cur.fetchone()
            if row:
                con.close()
                return _decompress(row[0])
            # probar con LIKE
            cur.execute("SELECT texto FROM manuales WHERE nombre LIKE ?", (f"%{nombre}%",))
            row = cur.fetchone()
            con.close()
            if row:
                return _decompress(row[0])
            else:
                con.close()
        except Exception:
            pass
    # fallback filesystem
    for p in list((_JPL_ROOT / "formatos").glob("*.md")) + list((Path(__file__).resolve().parent.parent.parent / ".opencode" / "skills" / "jpl" / "formatos").glob("*.md")):
        if p.stem.lower() == nombre.lower() or nombre.lower() in p.stem.lower():
            try:
                return p.read_text(encoding="utf-8-sig", errors="ignore")
            except Exception:
                continue
    return None

def listar_manuales() -> list[dict]:
    if _use_db():
        try:
            con = _db_conn()
            cur = con.cursor()
            cur.execute("SELECT nombre, categoria FROM manuales ORDER BY nombre")
            rows = cur.fetchall()
            con.close()
            return [{"nombre": n, "categoria": c} for n, c in rows]
        except Exception:
            pass
    return []
