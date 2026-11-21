"""Avaliação experimental das regras meteorológicas do Trilhas RJ."""

import json
import operator
from datetime import datetime

from caminhos import PASTA

ARQUIVO_REGRAS = PASTA / "conhecimento" / "regras.json"
OPERADORES = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "em": lambda valor, opcoes: valor in opcoes,
    "intersecta": lambda a, b: bool(set(a).intersection(b)),
}
NIVEIS = {"atencao": 1, "atencao_alta": 2, "critico": 3}


def avaliar_condicoes(condicoes, fatos):
    estados = []
    for condicao in condicoes:
        valor = fatos.get(condicao["fato"])
        operador = OPERADORES[condicao["operador"]]
        estados.append(None if valor is None else operador(valor, condicao["valor"]))
    if False in estados:
        return "criterio_nao_atingido"
    if None in estados:
        return "nao_avaliavel"
    return "acionada"


def pico_com_cobertura(janela):
    if janela.get("cobertura_percentual") != 100:
        return None
    return (janela.get("pico_horario_na_cobertura_disponivel") or {}).get("chuva_mm")


def avaliar_cenario(cenario, consulta, regras, saida):
    observacao = consulta["chuva_observada_24h"]
    observada = None
    idade = None
    fim = observacao.get("fim_janela_utc")
    if observacao.get("estado") == "disponivel" and observacao.get("cobertura_percentual") == 100 and fim:
        idade = (saida - datetime.fromisoformat(fim)).total_seconds() / 3600
        if idade >= 0:
            observada = observacao.get("acumulado_mm")
        else:
            idade = None

    trecho = cenario.get("trecho", {}).get("previsao", {})
    atributos = None
    if consulta["id_trilha"] == "RIO-PNT-001" and consulta.get("trecho_pct") == [52.0024, 52.6186]:
        atributos = ["escadaria"]

    anterior = cenario["previsao_24h_antes_da_saida"]
    fatos = {
        "pico_caminhada": pico_com_cobertura(cenario),
        "chuva_caminhada": cenario["chuva_prevista_estimada_mm"],
        "chuva_24h_prevista": anterior["chuva_prevista_estimada_mm"],
        "chuva_24h_observada": observada,
        "idade_observacao_na_saida": idade,
        "cobertura_caminhada": cenario["cobertura_percentual"],
        "pico_trecho": pico_com_cobertura(trecho),
        "cobertura_trecho": trecho.get("cobertura_percentual"),
        "atributos_trecho": atributos,
    }
    meteo = cenario.get("meteorologia", {})
    meteo_trecho = cenario.get("trecho", {}).get("meteorologia", {})
    luz = cenario.get("luz_do_dia", {})
    fatos.update(meteo)
    fatos.update(
        rajada_trecho=meteo_trecho.get("rajada_max"),
        visibilidade_trecho=meteo_trecho.get("visibilidade_min"),
        minutos_pos_por_do_sol=luz.get("minutos_pos_por_do_sol"),
    )
    duracao = consulta["duracao_min"]
    fatos.update(luz, duracao_min=duracao)
    resultados = []
    segmentos = cenario.get("trechos", [cenario["trecho"]] if trecho else [])
    aplicacoes = [
        (regra, segmento)
        for regra in regras
        for segmento in (segmentos if regra["escopo"] == "trecho"
                         or "cobertura_trecho" in regra["entradas_exigidas"] else [None])
    ]
    for regra, segmento in aplicacoes:
        condicoes = regra["condicao"]["todas"]
        fatos_regra = fatos
        if segmento is not None:
            previsao = segmento["previsao"]
            meteo_segmento = segmento.get("meteorologia", {})
            picos = [pico_com_cobertura(j) for j in segmento.get("duracoes_alternativas", [])]
            fatos_regra = {
                **fatos,
                **meteo_segmento,
                "atributos_trecho": segmento.get("atributos", atributos),
                "pico_trecho": pico_com_cobertura(previsao),
                "cobertura_trecho": previsao["cobertura_percentual"],
                "pico_montante": segmento.get("pico_montante"),
                "pico_trecho_duracao_alternativa": max(picos)
                if picos and all(p is not None for p in picos) else None,
                "rajada_trecho": meteo_segmento.get("rajada_max"),
                "visibilidade_trecho": meteo_segmento.get("visibilidade_min"),
            }
        valores = {c["fato"]: fatos_regra.get(c["fato"]) for c in condicoes}
        estado = avaliar_condicoes(condicoes, valores)
        if (regra["id"] == "TE01" and duracao < 120) or (
            regra["id"] == "OP02" and luz.get("saida_apos_por_do_sol")
        ):
            estado = "fora_do_escopo"
        resultados.append({
            "id": regra["id"],
            "versao": regra["versao"],
            "fenomeno": regra["fenomeno"],
            "trecho": segmento.get("nome") if segmento else None,
            "fonte_trecho": segmento.get("fonte") if segmento else None,
            "estado": estado,
            "nivel": regra["nivel"],
            "valores": valores,
            "entradas_indisponiveis": [fato for fato, valor in valores.items() if valor is None and estado != "fora_do_escopo"],
            "condicoes": condicoes,
            "referencias": regra["referencias"],
            "mensagem": regra["mensagem"] if estado == "acionada" else None,
            "conselho": regra.get("conselho") if estado == "acionada" else None,
        })

    niveis = [r["nivel"] for r in resultados if r["estado"] == "acionada" and r["nivel"] in NIVEIS]
    incompleta = any(r["estado"] == "nao_avaliavel" for r in resultados)
    return {
        "nivel": max(niveis, key=NIVEIS.get) if niveis else None,
        "avaliacao_incompleta": incompleta,
        "estado": "fatores_identificados" if niveis else (
            "avaliacao_incompleta" if incompleta else "nenhum_fator_identificado"
        ),
        "evidencia_terreno": "documentacao/trecho-piloto-pico-da-tijuca.md" if atributos else None,
        "regras": resultados,
    }


def avaliar_consulta(resultado, consulta):
    base = json.loads(ARQUIVO_REGRAS.read_text(encoding="utf-8"))
    regras = [regra for regra in base["regras"] if regra["estado_revisao"] == "revisada_para_piloto"]
    resultado["inferencia"] = {
        "modo": "experimental",
        "versao_base": base["versao_base"],
        "referencias": base["referencias"],
    }
    for cenario, saida in zip(resultado["cenarios"], consulta["saidas"]):
        cenario["inferencia"] = avaliar_cenario(cenario, consulta, regras, datetime.fromisoformat(saida))
