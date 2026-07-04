# AGENTS — Reglas para asistentes automatizados

## Control de versiones (git)

- Antes de hacer `git push`, verificar que no haya conflictos de merge sin resolver (marcas `<<<<<<<`, `=======`, `>>>>>>>`) en ningún archivo del proyecto.
- Si durante un `git rebase`, `git merge` o `git pull` surge un conflicto, AVISAR AL USUARIO antes de resolverlo. No resolver conflictos automáticamente sin autorización.
- Si se detectan conflictos existentes en el código (dejados por operaciones anteriores), informar al usuario antes de modificarlos.
