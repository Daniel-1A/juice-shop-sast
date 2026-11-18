#!/usr/bin/env python3
"""Gate de licencias sobre un SBOM CycloneDX (JSON) leído desde stdin.

BLOQUEA (exit 1): GPL, AGPL o SSPL según la política del proyecto.
BLOQUEA (exit 1): inventario de componentes ausente o vacío.
AVISA (::warning): componentes sin licencia declarada.
Ver security/politica-de-bloqueo.md
"""
import json
import re
import sys

DENY = re.compile(r"\b(A?GPL-[0-9.]+(-only|-or-later)?|SSPL-[0-9.]+)\b", re.I)


def licencias(componente):
    out = []
    for entrada in componente.get("licenses") or []:
        if "expression" in entrada:
            out.append(entrada["expression"])
        lic = entrada.get("license", {})
        if lic.get("id") or lic.get("name"):
            out.append(lic.get("id") or lic.get("name"))
    return out


def main():
    sbom = json.load(sys.stdin.buffer)
    componentes = sbom.get("components")
    if not isinstance(componentes, list) or not componentes:
        print("::error title=SBOM inválido::Se esperaba un inventario de componentes no vacío.")
        return 1

    bloqueos, sin_licencia = [], []
    for c in componentes:
        nombre = f'{c.get("name")}@{c.get("version")}'
        lics = licencias(c)
        if not lics:
            sin_licencia.append(nombre)
            continue
        # Una expresión "MIT OR GPL-3.0" permite elegir MIT: solo bloquea si
        # TODAS las alternativas están en la lista de denegadas.
        for expr in lics:
            alternativas = re.split(r"\s+OR\s+", expr)
            if all(DENY.search(a) for a in alternativas):
                bloqueos.append(f"{nombre}: {expr}")
    total = len(componentes)
    print(f"Componentes analizados: {total}")
    print(f"Sin licencia declarada: {len(sin_licencia)}")
    if sin_licencia:
        print(f"::warning title=Licencias::{len(sin_licencia)} componentes sin licencia declarada (solo aviso)")
    if bloqueos:
        for b in bloqueos:
            print(f"::error title=Licencia denegada::{b}")
        return 1
    print("OK: ninguna licencia denegada (GPL/AGPL/SSPL).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
