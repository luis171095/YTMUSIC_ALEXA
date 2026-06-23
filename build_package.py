#!/usr/bin/env python3
"""Empaqueta la skill para AWS Lambda (runtime Python 3.10, Linux x86_64).

Uso:
    python build_package.py            # solo arma el .zip con lo que ya hay
    python build_package.py --install  # primero instala las dependencias y luego arma el .zip

IMPORTANTE: las dependencias con extensiones en C (rapidfuzz/Levenshtein, etc.)
DEBEN instalarse para Linux/Python 3.10, NO para tu PC. Por eso se usan los flags
--platform manylinux2014_x86_64 --implementation cp --python-version 3.10 --only-binary=:all:
El resultado se sube a Lambda con `aws lambda update-function-code` o por la consola.
"""
import os
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(os.path.dirname(ROOT), "alexa_skill.zip")

# Carpetas que NUNCA van dentro del paquete (artefactos de desarrollo / secretos).
EXCLUDE_DIRS = {".git", ".claude", "__pycache__", ".vscode", ".idea", ".pytest_cache"}
EXCLUDE_FILES = {"cookies.txt", ".env", os.path.basename(OUTPUT)}


def install_dependencies():
    """Instala las dependencias de requirements.txt como wheels de Linux/Py3.10."""
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--platform", "manylinux2014_x86_64",
        "--implementation", "cp",
        "--python-version", "3.10",
        "--only-binary=:all:",
        "--target", ROOT,
        "-r", os.path.join(ROOT, "requirements.txt"),
    ]
    print("Instalando dependencias para Linux/Python 3.10...")
    subprocess.check_call(cmd)


def build_zip():
    """Comprime el código + dependencias en alexa_skill.zip."""
    count = 0
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for current, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f in EXCLUDE_FILES or f.endswith(".pyc"):
                    continue
                full = os.path.join(current, f)
                rel = os.path.relpath(full, ROOT)
                z.write(full, rel)
                count += 1
    size_mb = round(os.path.getsize(OUTPUT) / 1024 / 1024, 2)
    print(f"Listo: {OUTPUT}  ({count} archivos, {size_mb} MB)")
    if size_mb > 250:
        print("ADVERTENCIA: supera el limite de 250 MB descomprimido de Lambda.")


if __name__ == "__main__":
    if "--install" in sys.argv:
        install_dependencies()
    build_zip()
