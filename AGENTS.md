# AGENTS — Reglas para asistentes automatizados

## Control de versiones (git)

- Antes de hacer `git push`, verificar que no haya conflictos de merge sin resolver (marcas `<<<<<<<`, `=======`, `>>>>>>>`) en ningún archivo del proyecto.
- Si durante un `git rebase`, `git merge` o `git pull` surge un conflicto, AVISAR AL USUARIO antes de resolverlo. No resolver conflictos automáticamente sin autorización.
- Si se detectan conflictos existentes en el código (dejados por operaciones anteriores), informar al usuario antes de modificarlos.

## Base de datos (archivos .db, .sqlite, etc.)

- Antes de hacer `git pull`, verificar si algún archivo de base de datos (*.db, *.sqlite, etc.) figura en los cambios del remoto (`git diff --name-only HEAD..origin/main`).
- Si aparece:
  1. Extraer schema de la versión local y remota para compararlos.
  2. Si el schema NO cambió (solo data), preservar la BD local y descartar la versión remota.
  3. Si el schema SÍ cambió (nuevas tablas/columnas), AVISAR AL USUARIO antes de resolver. No reemplazar la BD automáticamente.
- Para extraer schemas (ejemplo con SQLite):
  ```bash
  sqlite3 archivo.db ".schema"           # local
  git show :archivo.db | sqlite3 ".schema"  # remoto (versión del index)
  ```
