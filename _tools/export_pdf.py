import os
import re
import subprocess
from markdown_it import MarkdownIt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
md_path = os.path.join(BASE_DIR, "Info proyecto", "INFORME_TESTING_Y_VALIDACIONES.md")
html_path = os.path.join(BASE_DIR, "Info proyecto", "temp_informe.html")
pdf_path = os.path.join(BASE_DIR, "Info proyecto", "INFORME_TESTING_Y_VALIDACIONES.pdf")

with open(md_path, "r", encoding="utf-8") as f:
    text = f.read()

# Reemplaza bloque mermaid con un diagrama HTML limpio y elegante para impresión
mermaid_pattern = re.compile(r"```mermaid[\s\S]*?```")
diagram_html = """
<div class="diagram-container">
  <div class="diagram-step"><strong>1. Guards de Arquitectura y Diseño</strong><br><small>11 comprobaciones estáticas automáticas</small></div>
  <div class="diagram-arrow">&#9660;</div>
  <div class="diagram-step"><strong>2. Pruebas Unitarias y de Schemas</strong><br><small>&gt;400 casos de validación declarativa (Pydantic / FastAPI)</small></div>
  <div class="diagram-arrow">&#9660;</div>
  <div class="diagram-step"><strong>3. Pruebas de Integración de Servicios</strong><br><small>&gt;350 casos de reglas de negocio y flujos completos</small></div>
  <div class="diagram-arrow">&#9660;</div>
  <div class="diagram-step"><strong>4. Pruebas de Concurrencia y Carreras Reales</strong><br><small>Fases 0 a 6 (Advisory Locks + PostgreSQL GIST Constraints)</small></div>
  <div class="diagram-arrow">&#9660;</div>
  <div class="diagram-step"><strong>5. Pruebas de Hardware e IoT</strong><br><small>WebSocket, Broker MQTT y Serie USB para Arduino Uno</small></div>
</div>
"""
text = mermaid_pattern.sub(diagram_html, text)

md = MarkdownIt("gfm-like").disable("linkify")
body_html = md.render(text)

css = """
@page {
    size: A4;
    margin: 1.6cm 1.4cm 1.6cm 1.4cm;
}
body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
    color: #1e293b;
    line-height: 1.5;
    font-size: 9pt;
    background: #ffffff;
    margin: 0;
    padding: 0;
}
h1 {
    color: #0f172a;
    font-size: 16pt;
    font-weight: 700;
    border-bottom: 2.5px solid #2563eb;
    padding-bottom: 5px;
    margin-top: 0;
    margin-bottom: 12px;
}
h2 {
    color: #1e3a8a;
    font-size: 12pt;
    font-weight: 600;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 3px;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
}
h3 {
    color: #0369a1;
    font-size: 10pt;
    font-weight: 600;
    margin-top: 12px;
    margin-bottom: 4px;
    page-break-after: avoid;
}
p, ul, ol {
    margin-top: 0;
    margin-bottom: 6px;
}
li {
    margin-bottom: 2px;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 6px;
    margin-bottom: 12px;
    font-size: 8pt;
    page-break-inside: auto;
}
tr {
    page-break-inside: avoid;
    page-break-after: auto;
}
th {
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    text-align: left;
    padding: 5px 7px;
    border: 1px solid #94a3b8;
}
td {
    padding: 4px 7px;
    border: 1px solid #cbd5e1;
    vertical-align: top;
}
tbody tr:nth-child(even) {
    background-color: #f8fafc;
}
code {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 7.5pt;
    background-color: #f1f5f9;
    padding: 1px 3px;
    border-radius: 3px;
    color: #0f172a;
    border: 1px solid #e2e8f0;
}
pre {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 3px solid #2563eb;
    padding: 6px 10px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 7.5pt;
    overflow-x: auto;
    page-break-inside: avoid;
    margin-bottom: 8px;
}
pre code {
    background: none;
    border: none;
    padding: 0;
}
hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 12px 0;
}
.diagram-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 12px 0;
    page-break-inside: avoid;
}
.diagram-step {
    background: #eff6ff;
    border: 1.5px solid #3b82f6;
    border-radius: 6px;
    padding: 6px 14px;
    text-align: center;
    width: 60%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.diagram-step strong {
    color: #1e3a8a;
    font-size: 8.5pt;
}
.diagram-step small {
    color: #475569;
    font-size: 7.5pt;
}
.diagram-arrow {
    color: #3b82f6;
    font-size: 10pt;
    margin: 1px 0;
}
"""

full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>INFORME DE TESTING Y VALIDACIONES — AUTOPASS</title>
<style>{css}</style>
</head>
<body>
{body_html}
</body>
</html>"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(full_html)

edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_exe,
    "--headless",
    "--disable-gpu",
    "--run-all-compositor-stages-before-draw",
    "--no-pdf-header-footer",
    f"--print-to-pdf={pdf_path}",
    html_path,
]

print(f"Ejecutando conversion hacia: {pdf_path}")
res = subprocess.run(cmd, capture_output=True, text=True)

if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
    print(f"PDF generado exitosamente ({os.path.getsize(pdf_path):,} bytes)")
else:
    print(f"Error generando PDF: {res.stderr}")

if os.path.exists(html_path):
    os.remove(html_path)
