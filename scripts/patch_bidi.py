import os
import sys

venv_site = os.path.join(os.path.dirname(os.path.dirname(__file__)), "venv", "Lib", "site-packages")
bidi_init = os.path.join(venv_site, "bidi", "__init__.py")

if not os.path.exists(bidi_init):
    print("[*] bidi/__init__.py no encontrado, saltando parche.")
    sys.exit(0)

with open(bidi_init, "r", encoding="utf-8") as f:
    content = f.read()

if "from .algorithm import get_display" in content and content.index("from .algorithm import get_display") < content.index("def main()"):
    print("[*] Parche bidi ya aplicado correctamente (a nivel de modulo).")
    sys.exit(0)

content = content.replace(
    "VERSION = '0.4.2'\n\n\ndef main():",
    "VERSION = '0.4.2'\n\nfrom .algorithm import get_display\n\n\ndef main():"
)

with open(bidi_init, "w", encoding="utf-8") as f:
    f.write(content)

print("[+] Parche bidi aplicado correctamente.")
