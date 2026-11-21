"""Gera um painel HTML local a partir de uma consulta gravada do Trilhas RJ."""
import argparse
import json
from html import escape
from pathlib import Path

from comparar_saidas import comparar_consulta
from inferencia import ARQUIVO_REGRAS, avaliar_condicoes, avaliar_consulta, pico_com_cobertura


def exibir(valor):
    return escape(str(valor)) if valor is not None else "Indisponível"


def painel(consulta):
    if consulta["versao"] != 1:
        raise ValueError("Versão de consulta gravada incompatível.")
    resultado = comparar_consulta(consulta)
    avaliar_consulta(resultado, consulta)
    regra = next(r for r in resultado["cenarios"][0]["inferencia"]["regras"] if r["id"] == "CH01")
    base = json.loads(ARQUIVO_REGRAS.read_text(encoding="utf-8"))
    nomes = {r["id"]: r["fenomeno"] for r in base["regras"]}
    cartoes = []
    for cenario in resultado["cenarios"]:
        inferencia = cenario["inferencia"]
        trecho = cenario.get("trecho", {}).get("previsao", {})
        pico = pico_com_cobertura(cenario)
        pico_trecho = pico_com_cobertura(trecho)
        comparacao = []
        tr01 = next((r for r in inferencia["regras"] if r["id"] == "TR01"), None)
        if tr01 and tr01["valores"]["atributos_trecho"] is not None:
            fatos = {**tr01["valores"], "pico_trecho": pico}
            inteira = avaliar_condicoes(tr01["condicoes"], fatos)
            comparacao = [
                ("TR01 com pico da caminhada inteira", inteira.replace("_", " ")),
                ("TR01 com pico na passagem", tr01["estado"].replace("_", " ")),
            ]

        metricas = [
            ("Fim da caminhada", cenario["fim"]),
            ("Passagem estimada", f'{trecho["inicio"]} a {trecho["fim"]}' if trecho else None),
            ("Chuva na caminhada (mm)", cenario["chuva_prevista_estimada_mm"]),
            ("Chuva prevista nas 24 h anteriores (mm)", cenario["previsao_24h_antes_da_saida"]["chuva_prevista_estimada_mm"]),
            ("Pico da hora inteira na caminhada (mm)", pico),
            ("Pico da hora inteira no trecho (mm)", pico_trecho),
            ("Cobertura da caminhada (%)", cenario["cobertura_percentual"]),
            ("Cobertura do trecho (%)", trecho.get("cobertura_percentual")),
            *comparacao,
            ("Nível experimental", inferencia["nivel"]),
            ("Avaliação incompleta", "Sim" if inferencia["avaliacao_incompleta"] else "Não"),
        ]
        campos = "".join(f"<dt>{escape(rotulo)}</dt><dd>{exibir(valor)}</dd>" for rotulo, valor in metricas)
        linhas = []
        for r in inferencia["regras"]:
            lacunas = ", ".join(r["entradas_indisponiveis"])
            detalhe = r["mensagem"] or (f"Entradas ausentes: {lacunas}" if lacunas else "")
            linhas.append(f'<li><strong>{exibir(r["id"])} · {exibir(nomes[r["id"]])}</strong> '
                          f'<span>{exibir(r["estado"].replace("_", " "))}</span>'
                          f'<div>{exibir(detalhe)}</div></li>')
        cartoes.append(f'<section><h2>Saída {exibir(cenario["inicio"])}</h2><dl>{campos}</dl>'
                       f'<h3>Regras avaliadas</h3><ul>{"".join(linhas)}</ul></section>')

    obs = resultado["chuva_observada_24h"]
    fonte = resultado["fonte_previsao"]
    return f"""<!doctype html>
<html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trilhas RJ · Comparação de saídas</title>
<style>
body{{margin:0;background:#f1f4ed;color:#183429;font:16px/1.5 system-ui}}
main{{max-width:1160px;margin:auto;padding:32px 20px}}
header{{border-bottom:2px solid #9aaa99;margin-bottom:24px}}
h1{{font-size:clamp(2rem,5vw,3rem);line-height:1.05;margin-bottom:16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,450px),1fr));gap:18px}}
section{{background:#fff;border:1px solid #d2dbd0;padding:20px;border-radius:12px}}
dl{{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px}}
dt{{color:#3c5a4b}}dd{{margin:0;overflow-wrap:anywhere}}li{{margin-bottom:8px}}span{{color:#3c5a4b}}
</style>
<main><header><h1>Comparação de saídas</h1>
<p>{exibir(resultado["nome"])}</p>
<p><strong>Fonte da previsão</strong> {exibir(fonte)} · <strong>Base experimental</strong> {exibir(base["versao_base"])}</p>
<p><strong>Chuva observada compartilhada</strong> {exibir(obs.get("estado"))} · estação {exibir(obs.get("codigo_estacao"))} · total {exibir(obs.get("acumulado_mm"))} mm · cobertura {exibir(obs.get("cobertura_percentual"))}%</p>
<p>{exibir(obs.get("motivo", ""))}</p>
<p>A comparação da TR01 mantém a evidência da escadaria e o limiar. Cada variante usa o pico da sua janela. A referência de pico da caminhada é {exibir(regra["condicoes"][0]["valor"])} mm.</p>
</header><div class="grid">{"".join(cartoes)}</div></main></html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captura", type=Path)
    parser.add_argument("saida_html", type=Path)
    args = parser.parse_args()
    try:
        consulta = json.loads(args.captura.read_text(encoding="utf-8"))
        html = painel(consulta)
        with args.saida_html.open("x", encoding="utf-8") as arquivo:
            arquivo.write(html)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        parser.exit(1, f"Erro: {erro}\n")


if __name__ == "__main__":
    main()
