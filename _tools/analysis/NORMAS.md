# NORMAS DE LA CAPA DE ANÁLISIS

Esta carpeta (`_tools/analysis/`) guarda **explicaciones redactadas tras analizar
el código real**. Ese texto es el que aparece en el visor
`EXPLICACION DE CODIGO/`, con prioridad sobre cualquier docstring existente.

La regla de oro: **la explicación nace de leer y entender el código, no de copiar
un comentario.** Si el archivo ya tiene docstring, se conserva aparte (el visor
lo muestra como "Docstring original"), pero lo que el lector ve primero es el
análisis.

## Formato de un archivo de análisis

Se escribe **un o varios archivos** por sección, todos con prefijo
`analysis_` (el generador los carga con `analysis_*.py` y fusiona todos).
Para secciones chicas: `analysis_core.py`. Para secciones grandes que se
dividen en partes: `analysis_tests_1.py`, `analysis_tests_2.py`, etc.

```python
"""Explicaciones analizadas de <sección> (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "core/database.py": {
        "proposito": "Una o dos oraciones: qué es este archivo y por qué existe.",
        "simbolos": {
            "get_db": "Qué hace esta función, qué recibe y qué devuelve.",
            "sync_schema": "…",
        },
    },
}
```

- La **clave externa** es la ruta exacta del archivo (la que imprime
  `--inventario`), con `/` y sin `./`.
- La **clave interna `simbolos`** es exactamente el nombre del símbolo que
  imprime `--inventario`. Si no coincide, no se aplica.
- **Métodos repetidos**: cuando un mismo nombre aparece varias veces en el
  archivo (varios `__init__`, varios `validate_email` en clases distintas,
  etc.), la clave interna debe ser **calificada**: `"Clase.metodo"` en lugar de
  `"metodo"`. El generador busca primero la clave calificada y, si no existe,
  cae al nombre simple. Usá la calificación siempre que haya ambigüedad; en
  métodos únicos alcanza el nombre simple.

## Reglas de redacción

1. **Siempre en castellano**, lenguaje claro y sencillo, pensado en quien no
   conoce el proyecto. Nada de jerga innecesaria.
2. **Sale del análisis del cuerpo de la función**: qué recibe, qué hace paso a
   paso, qué consulta o modifica, qué devuelve y para qué sirve en el sistema.
   No reescribas el docstring: amplíalo con lo que el código hace de verdad.
3. **Extensión**: 1–3 oraciones útiles en general; si la función es compleja
   (validaciones, estados, cálculos), extendé lo que haga falta. Nunca texto de
   relleno.
4. **Precisión**: si el código lanza excepciones, aplica filtros, toca una tabla
   concreta o delega en otro servicio, **decilo**. Eso es lo que hace útil la
   explicación.
5. **Cobertura total**: cada símbolo del `--inventario` debe tener entrada. El
   que quede sin entrada se queda con su docstring viejo (o sin nada).
6. **No inventar símbolos** que no estén en el inventario: se ignoran.
7. **Proósito por archivo**: explicá qué problema resuelve el archivo dentro de
   AUTOPASS, no repitas su nombre.

## Cómo obtener el lote a cubrir

```powershell
$env:PYTHONUTF8=1; .\venv\Scripts\python.exe _tools\generate_code_docs.py --inventario <seccion>
```

`<seccion>` puede ser un id de sección (`core`, `services`, `tests`, `css`,
`frontend-admin`…) o la ruta completa de un archivo.

## Notas por tipo de archivo

- **Python / JavaScript**: explicar cada clase, método y función. Si un mismo
  nombre de método se repite en el archivo, calificá la clave (`Clase.metodo`).
- **Templates (`.html` de `templates/`)**: los "símbolos" son los bloques
  `{% block %}`; explicar qué renderiza cada bloque dentro de la página.
- **CSS**: los "símbolos" son selectores. **No se explica selector por
  selector** (no son funciones): se redacta un `proposito` exhaustivo del
  archivo indicando qué estiliza cada zona y para qué sirve. En CSS la
  cobertura cuenta con el `proposito` del archivo: el `simbolos` puede quedar
  vacío.
- **Migraciones Alembic**: `proposito` con qué cambia el esquema; el símbolo
  sintético `upgrade / downgrade` puede explicarse en `proposito`.

## Verificación final

**No ejecutes `generate_code_docs.py` sin flags**: escribe
`EXPLICACION DE CODIGO/data.js` y si varios lotes corren a la vez se pisan entre
sí. Escribe el visor una sola persona, al final.

Para verificar tu lote usá el chequeo de cobertura (no escribe nada):

```powershell
$env:PYTHONUTF8=1; .\venv\Scripts\python.exe _tools\generate_code_docs.py --cobertura <seccion>
```

Y validá la sintaxis de tu archivo:

```powershell
$env:PYTHONUTF8=1; .\venv\Scripts\python.exe -c "import ast; ast.parse(open(r'_tools/analysis/analysis_<tu_archivo>.py', encoding='utf-8').read()); print('AST OK')"
```

También podés filtrar tu lote con `--cobertura <seccion>` antes de empezar, para
ver qué te falta.

No commitear nunca sin pedido explícito del usuario.
