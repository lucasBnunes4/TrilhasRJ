"""Evidência de terreno e identificação de candidatos por trilha."""

import csv
import json

from caminhos import PASTA
TERMOS = ("escadaria", "ponte", "travessia de rio", "travessia de córrego", "cachoeira",
          "rocha lisa", "descida íngreme", "solo argiloso")


def consultar_terreno(id_trilha):
    cadastro = json.loads((PASTA / "conhecimento/trechos.json").read_text(encoding="utf-8"))
    registros = cadastro.get(id_trilha, [])
    fontes_registradas = {t["fonte"] for t in registros}
    candidatos = [t for t in registros if t["estado"] != "documentado"]
    with (PASTA / "ponto_interesse.csv").open(encoding="utf-8-sig", newline="") as arquivo:
        for ponto in csv.DictReader(arquivo):
            if ponto["id_trilha"] != id_trilha or ponto["id_ponto"] in fontes_registradas:
                continue
            descricao = f'{ponto["nome"]} {ponto["tipo_ponto"]}'.casefold()
            if any(termo in descricao for termo in TERMOS):
                candidatos.append({
                    "id": ponto["id_ponto"], "nome": ponto["nome"], "fonte": ponto["id_fonte"],
                    "altitude_m": ponto["altitude_m"], "estado": "localizacao_pendente",
                })
    return {
        "documentados": [t for t in registros if t["estado"] == "documentado"],
        "candidatos": candidatos,
    }
