"""Formulário local de planejamento de trilhas."""
import argparse
import csv
from datetime import date, datetime, time
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from xml.etree.ElementTree import ParseError

import requests

from comparar_saidas import FUSO_LOCAL, PASTA, coletar_consulta, comparar_consulta
from inferencia import avaliar_consulta

CONSELHOS = {
    "TR04": "Confira as condições da descida e compare um horário com menos chuva.",
    "TR05": "Consulte as condições da travessia com o gestor antes de sair.",
    "TR06": "Consulte o gestor sobre a travessia diante da previsão de chuva a montante.",
    "TR08": "Compare horários e considere a margem de variação na duração da caminhada.",
    "TE01": "Considere levar uma camada extra para a queda de temperatura prevista.",
    "TE02": "Planeje roupa adequada para a temperatura mínima prevista.",
    "TE03": "Considere proteção contra chuva e frio e compare outro horário.",
    "TE04": "Planeje hidratação e considere um horário com menor sensação de calor.",
    "VE01": "Compare horários com menos rajadas durante a passagem pelo trecho exposto.",
    "VE02": "Considere adiar a passagem pelo trecho com visibilidade reduzida.",
    "VE03": "Confira os avisos de vento e considere outro horário, sobretudo se houver áreas expostas.",
    "VE04": "Considere outro horário e confira se a navegação exige referências visuais.",
    "OP02": "Considere antecipar a saída para planejar o retorno antes do pôr do sol.",
    "CH01": "Se o horário for flexível, consulte uma saída que deixe o pico fora da caminhada.",
    "CH02": "Considere adiar a saída e confira os avisos oficiais antes de decidir.",
    "CH03": "Planeje a proteção contra chuva para o percurso e reavalie a duração estimada.",
    "CH04": "Confira com a administração da trilha as condições do piso e do acesso antes de sair.",
    "CH05": "Confira com a administração da trilha as condições do piso e do acesso antes de sair.",
    "TR01": "Compare outro horário para deslocar a passagem pela escadaria para fora do pico previsto.",
    "TR02": "Considere adiar a passagem pela escadaria e consulte as condições do acesso.",
    "TR03": "Confira as condições da escadaria antes da saída.",
    "TR07": "Confira as condições da escadaria antes da saída.",
}


def catalogo():
    with (PASTA / "trilhas.csv").open(encoding="utf-8-sig", newline="") as arquivo:
        return {
            t["id_trilha"]: t for t in csv.DictReader(arquivo)
            if t["latitude_ref"] and t["longitude_ref"]
        }


def texto(valor):
    return escape(str(valor)) if valor is not None else "Indisponível"


def horario(valor):
    return datetime.fromisoformat(valor).strftime("%d/%m às %H:%M")


def milimetros(valor):
    return f"{valor:g} mm" if valor is not None else "Indisponível"


def consultar(campos):
    id_trilha = campos["trilha"]
    data = date.fromisoformat(campos["data"])
    horas = [time.fromisoformat(campos["saida"])]
    if campos.get("comparar"):
        outra = time.fromisoformat(campos["comparar"])
        if outra == horas[0]:
            raise ValueError("Escolha um segundo horário diferente da primeira saída.")
        horas.append(outra)
    duracao = int(campos["duracao"]) if campos.get("duracao") else None
    consulta = coletar_consulta(id_trilha, data, horas, duracao)
    resultado = comparar_consulta(consulta)
    avaliar_consulta(resultado, consulta)
    return resultado


def janela(nome, dados):
    pico = dados["pico_horario_na_cobertura_disponivel"]
    resumo = f'{milimetros(dados["chuva_prevista_estimada_mm"])} · cobertura {dados["cobertura_percentual"]:g}%'
    if pico:
        resumo += f' · pico de {milimetros(pico["chuva_mm"])} na hora de {horario(pico["inicio"])} a {horario(pico["fim"])}'
    return f"<li><strong>{texto(nome)}</strong><br>{texto(resumo)}</li>"


NOMES_FATOS = {
    "pico_caminhada": "Pico horário de chuva na caminhada",
    "pico_trecho": "Pico horário de chuva na passagem",
    "pico_trecho_duracao_alternativa": "Pico horário nas janelas com duração alternativa",
    "pico_montante": "Pico horário de chuva a montante",
    "chuva_caminhada": "Total de chuva durante a caminhada",
    "chuva_24h_prevista": "Chuva prevista nas 24 h anteriores à saída",
    "chuva_24h_observada": "Chuva observada em 24 h",
    "idade_observacao_na_saida": "Tempo entre o fim da observação e a saída",
    "atributos_trecho": "Características documentadas do trecho",
    "cobertura_caminhada": "Cobertura da previsão na caminhada",
    "cobertura_trecho": "Cobertura da previsão na passagem",
    "temp_min": "Temperatura mínima",
    "temp_max": "Temperatura máxima",
    "queda_2h": "Maior queda de temperatura em duas horas",
    "sensacao_min": "Sensação térmica mínima",
    "sensacao_max": "Sensação térmica máxima",
    "rajada_max": "Maior rajada na caminhada",
    "rajada_trecho": "Maior rajada durante a passagem",
    "visibilidade_min": "Visibilidade mínima na janela",
    "visibilidade_trecho": "Visibilidade mínima durante a passagem",
    "uv_max": "Índice UV máximo",
    "frio_com_chuva": "Sensação de até 8 °C e chuva de pelo menos 1 mm na mesma hora",
    "frio_com_vento": "Sensação de até 8 °C e rajada de pelo menos 40 km/h na mesma hora",
    "tempestade_prevista": "Código de tempestade na previsão horária",
    "granizo_previsto": "Código de granizo na previsão horária",
    "duracao_min": "Duração planejada",
    "saida_antes_do_nascer": "Saída antes de nascer o sol",
    "saida_apos_por_do_sol": "Saída no pôr do sol ou depois",
    "margem_luz_min": "Margem de luz no retorno",
    "minutos_pos_por_do_sol": "Tempo de retorno após o pôr do sol",
}
OPERADORES_TEXTO = {
    ">=": "≥", "<=": "≤", "==": "=", "intersecta": "inclui ao menos um de", "em": "está na lista",
}


def nome_fato(fato):
    return NOMES_FATOS.get(fato, fato.replace("_", " ").capitalize())


def valor_fato(valor, unidade):
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if isinstance(valor, list):
        return ", ".join(str(item).replace("_", " ") for item in valor) or "nenhum registrado"
    if isinstance(valor, (float, int)):
        numero = format(valor, ".12g").replace(".", ",")
        sufixo = "mm na hora" if unidade == "mm por hora amostrada" else unidade
        return f"{numero} {sufixo}".strip()
    return str(valor).replace("_", " ") if valor is not None else "indisponível"


def regra_explicada(regra):
    titulo = regra.get("fenomeno") or regra["id"]
    local = f' · {texto(regra["trecho"])}' if regra.get("trecho") else ""
    detalhes = []
    for condicao in regra.get("condicoes", []):
        fato = condicao["fato"]
        unidade = condicao.get("unidade", "")
        recebido = valor_fato(regra["valores"].get(fato), unidade)
        criterio = valor_fato(condicao["valor"], unidade)
        operador = OPERADORES_TEXTO.get(condicao["operador"], condicao["operador"])
        detalhes.append(f'{nome_fato(fato)} — {recebido} (critério {operador} {criterio})')
    evidencia = " · ".join(detalhes)
    return f'<strong>{texto(regra["id"])} · {texto(titulo)}</strong>{local} — {texto(evidencia)}'


def motivo_chuva_observada(observada):
    return observada.get("motivo") or {
        "cobertura_nao_verificada": "A fonte não confirmou a cobertura da janela de 24 h.",
        "cobertura_incompleta": "A janela de 24 h tem lacunas. A regra exige cobertura completa.",
        "desatualizado": "A leitura está fora da tolerância de atualização.",
    }.get(observada.get("estado"), "Faltou uma leitura válida com horário e cobertura verificáveis.")


def motivo_lacuna(fato, cenario, observada):
    if fato in {"chuva_24h_observada", "idade_observacao_na_saida"}:
        return "Chuva observada de 24 h — " + motivo_chuva_observada(observada)
    if fato == "chuva_24h_prevista":
        cobertura = cenario["previsao_24h_antes_da_saida"]["cobertura_percentual"]
        return f"Chuva prevista antes da saída — {cobertura:g}% das 24 h cobertas. A regra exige a janela completa."
    if fato == "pico_montante":
        return "Chuva a montante — faltam séries completas das células validadas da bacia."
    if fato == "atributos_trecho":
        return "Terreno — o segmento não tem atributos de terreno documentados para a regra."
    if fato == "pico_trecho_duracao_alternativa":
        return "Duração alternativa — faltou cobertura de previsão em uma das janelas com duração ajustada."
    if fato in {"saida_antes_do_nascer", "saida_apos_por_do_sol", "minutos_pos_por_do_sol", "margem_luz_min"}:
        return f"{nome_fato(fato)} — faltou um horário solar aplicável à janela escolhida."
    if fato in {"tempestade_prevista", "granizo_previsto"}:
        return f"{nome_fato(fato)} — a série horária não tem códigos suficientes para decidir nesta janela."
    if fato in {"frio_com_chuva", "frio_com_vento"}:
        return f"{nome_fato(fato)} — faltaram dados horários coincidentes suficientes para decidir."
    return f"{nome_fato(fato)} — faltou cobertura ou valor utilizável na janela da regra."


def conselhos_e_lacunas(cenario, observada):
    regras = cenario["inferencia"]["regras"]
    prioridade = {"critico": 0, "atencao_alta": 1, "atencao": 2}
    acionadas = sorted(
        (r for r in regras if r["estado"] == "acionada"),
        key=lambda r: prioridade.get(r["nivel"], 3),
    )
    por_conselho = {}
    for regra in acionadas:
        conselho = regra.get("conselho") or CONSELHOS.get(regra["id"])
        if conselho:
            por_conselho.setdefault(conselho, []).append(regra)
    dicas = []
    for conselho, origens in por_conselho.items():
        motivos = "".join(f"<li>{regra_explicada(regra)}</li>" for regra in origens)
        dicas.append(f"<li><strong>{texto(conselho)}</strong><br>Motivos<ul>{motivos}</ul></li>")
    if not dicas:
        dicas.append("<li>Nenhuma das regras avaliadas acionou um conselho para este horário.</li>")

    lacunas = {}
    for regra in regras:
        if regra["estado"] == "fora_do_escopo":
            motivo = {
                "TE01": "A caminhada dura menos de duas horas.",
                "OP02": "A saída ocorre no pôr do sol ou depois. Esta regra compara o retorno de saídas diurnas.",
            }.get(regra["id"], "A condição de aplicação da regra ficou fora da janela da caminhada.")
            lacunas.setdefault(motivo, []).append(regra["id"])
        elif regra["estado"] == "nao_avaliavel":
            for fato in regra["entradas_indisponiveis"]:
                motivo = motivo_lacuna(fato, cenario, observada)
                lacunas.setdefault(motivo, []).append(regra["id"])
    itens = []
    for motivo, ids in lacunas.items():
        ids_texto = ", ".join(dict.fromkeys(ids))
        itens.append(f"<li>{texto(motivo)} <strong>{texto(ids_texto)}</strong></li>")
    if not cenario.get("trechos"):
        itens.append("<li>As análises de passagem por trechos exigem limites localizados e cadastrados no GPX.</li>")
    bloco = f'<h4>Limites da análise</h4><ul>{"".join(itens)}</ul>' if itens else ""
    return "".join(dicas), bloco


def renderizar_chuva_observada(observada):
    disponivel = observada.get("estado") == "disponivel"
    total = observada.get("acumulado_mm") if disponivel else None
    publicado = observada.get("acumulado_publicado_mm")
    codigo = observada.get("codigo_estacao")
    estacao = observada.get("estacao") or (f"Estação {codigo}" if codigo else "Sem estação identificada")
    distancia = observada.get("distancia_referencia_km")
    identificacao = " · ".join(parte for parte in (
        estacao, observada.get("rede"),
        f"código {codigo}" if codigo and observada.get("estacao") else None,
        f"{distancia:g} km da referência da trilha" if distancia is not None else None,
    ) if parte)
    fonte = observada.get("fonte_url")
    link = f' · <a href="{texto(fonte)}">Fonte da estação</a>' if fonte and fonte.startswith("https://") else ""
    inicio = observada.get("inicio_janela_utc")
    fim = observada.get("fim_janela_utc")
    rotulo_janela = "Janela de 24 h"
    if not (inicio and fim):
        inicio = observada.get("inicio_janela_nominal_utc")
        fim = observada.get("fim_janela_nominal_utc")
        if inicio and fim:
            rotulo_janela = "Janela nominal de 24 h"
    ultima_leitura = observada.get("ultima_leitura_utc") or observada.get("fim_janela_nominal_utc")
    cobertura = observada.get("cobertura_percentual")
    detalhes = [
        (rotulo_janela, f"{horario_local(inicio)} a {horario_local(fim)}" if inicio and fim else "Indisponível"),
        ("Cobertura das 24 h", f"{cobertura:g}%" if cobertura is not None else "Não informada"),
        ("Última leitura informada", horario_local(ultima_leitura) if ultima_leitura else "Não informada"),
    ]
    if total is None and publicado is not None:
        detalhes.append(("Acumulado publicado, sem uso na regra", milimetros(publicado)))
    indicadores = "".join(
        f"<div><dt>{texto(rotulo)}</dt><dd>{texto(valor)}</dd></div>" for rotulo, valor in detalhes
    )
    uso = (
        "Leitura disponível para a regra de chuva observada, que considera o horário de cada saída."
        if total is not None else f"Leitura indisponível para a regra. {motivo_chuva_observada(observada)}"
    )
    acumulado = f"<strong>{milimetros(total)}</strong> acumulados em 24 h" if total is not None else (
        "<strong>Acumulado de 24 h indisponível</strong>"
    )
    return (
        '<div class="chuva-observada"><h3>Chuva observada na estação</h3>'
        f'<p class="acumulado-observado">{acumulado}</p><p>{texto(identificacao)}{link}</p>'
        f'<dl>{indicadores}</dl><p>{texto(uso)}</p></div>'
    )


def renderizar_resultado(resultado):
    observada = resultado["chuva_observada_24h"]
    cartoes = []
    for cenario in resultado["cenarios"]:
        inferencia = cenario["inferencia"]
        previsao = janela("Durante a caminhada", cenario)
        previsao += janela("Nas 24 horas anteriores à saída", cenario["previsao_24h_antes_da_saida"])
        if cenario.get("trechos"):
            for segmento in cenario["trechos"]:
                trecho = segmento["previsao"]
                nome = segmento.get("nome", "Trecho")
                previsao += janela(f'{nome} · {horario(trecho["inicio"])} a {horario(trecho["fim"])}', trecho)
        else:
            previsao += "<li>Análise disponível para o percurso inteiro. A passagem por trechos depende de localização validada.</li>"
        candidatos = resultado.get("trechos_candidatos", [])
        if candidatos:
            nomes = ", ".join(t["nome"] for t in candidatos)
            previsao += f"<li>Pontos de interesse com localização pendente no GPX · {texto(nomes)}</li>"
        meteo = cenario["meteorologia"]
        luz = cenario["luz_do_dia"]
        indicadores = [
            ("Temperatura mínima", meteo["temp_min"], "°C"),
            ("Temperatura máxima", meteo.get("temp_max"), "°C"),
            ("Índice UV máximo", meteo.get("uv_max"), ""),
            ("Sensação térmica mínima", meteo["sensacao_min"], "°C"),
            ("Sensação térmica máxima", meteo["sensacao_max"], "°C"),
            ("Maior rajada horária", meteo["rajada_max"], "km/h"),
            ("Visibilidade mínima", meteo["visibilidade_min"], "m"),
        ]
        if meteo["janela_queda_2h"]:
            inicio, fim = meteo["janela_queda_2h"]
            indicadores.append((f"Queda entre {horario_local(inicio)} e {horario_local(fim)}",
                                meteo["queda_2h"], "°C"))
        meteo_html = "".join(
            f"<li>{texto(rotulo)} · {f'{valor:.1f} {unidade}' if valor is not None else 'Indisponível'}</li>"
            for rotulo, valor, unidade in indicadores
        )
        por_do_sol = horario_local(luz["por_do_sol"]) if luz["por_do_sol"] else "Indisponível"
        meteo_html += f"<li>Pôr do sol · {por_do_sol}</li>"
        if luz["saida_apos_por_do_sol"]:
            meteo_html += "<li>A saída escolhida ocorre no horário do pôr do sol ou depois dele.</li>"
        regras = inferencia["regras"]
        dicas, lacunas = conselhos_e_lacunas(cenario, observada)
        estado_ch05 = next((regra["estado"] for regra in regras if regra["id"] == "CH05"), None)
        uso_observada = {
            "acionada": "A chuva observada acionou um conselho para esta saída.",
            "criterio_nao_atingido": "A chuva observada foi avaliada e ficou fora dos critérios de volume ou horário da regra.",
        }.get(estado_ch05)
        uso_observada_html = f"<p>{texto(uso_observada)}</p>" if uso_observada else ""
        auditoria = "".join(
            f'<li>{regra_explicada(r)} · {texto(r["estado"].replace("_", " "))}</li>'
            for r in regras
        )
        cartoes.append(
            f'<article><h3>Saída {horario(cenario["inicio"])}</h3>'
            f'<p>Retorno estimado em {horario(cenario["fim"])}</p><ul>{previsao}</ul>'
            f'<h4>Condições na referência da trilha</h4><ul>{meteo_html}</ul>'
            f'<h4>Conselhos de planejamento</h4><ul>{dicas}</ul>{uso_observada_html}{lacunas}'
            f'<details><summary>Detalhes de todas as regras</summary><ul>{auditoria}</ul></details></article>'
        )
    return (
        f'<section aria-labelledby="resultado"><div class="resumo-consulta"><h2 id="resultado">{texto(resultado["nome"])}</h2>'
        f'<p>Duração estimada de {resultado["duracao_min"]} min. '
        f'<a href="https://open-meteo.com/">Previsão do Open-Meteo</a> · coleta {horario_local(resultado["coletado_em_utc"])}.</p>'
        f'{renderizar_chuva_observada(observada)}'
        f'<p>As regras são experimentais. Consulte também os <a href="https://avisos.inmet.gov.br/">avisos oficiais</a> e as condições de acesso.</p>'
        f'</div><div class="resultados">{"".join(cartoes)}</div></section>'
    )


def horario_local(valor):
    return datetime.fromisoformat(valor).astimezone(FUSO_LOCAL).strftime("%d/%m às %H:%M")


def pagina(trilhas, campos, resultado=None, erro=None):
    opcoes = ['<option value="">Selecione uma trilha</option>']
    for id_trilha, trilha in trilhas.items():
        selecionada = " selected" if id_trilha == campos.get("trilha") else ""
        opcoes.append(
            f'<option value="{texto(id_trilha)}" data-duracao="{texto(trilha["duracao_min"])}"{selecionada}>'
            f'{texto(trilha["nome"])} · {texto(trilha["municipio"])}</option>'
        )
    alerta = f'<p role="alert" class="erro">{texto(erro)}</p>' if erro else ""
    conteudo = renderizar_resultado(resultado) if resultado else ""
    hoje = datetime.now(FUSO_LOCAL).date().isoformat()
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#30251d">
<title>Planeje sua trilha · Trilhas RJ</title>
<style>
:root{{
  color-scheme:light;
  --terra:#914b31;
  --terra-escura:#713821;
  --texto:#2e2620;
  --suave:#66574b;
  --linha:#e3d8c9;
  --papel:#fffdf8;
  --fundo:#f4eee3;
  --verde:#354b36;
}}
*,*::before,*::after{{box-sizing:border-box}}
body{{margin:0;background:var(--fundo);color:var(--texto);font:16px/1.55 "Instrument Sans",system-ui,sans-serif}}
.hero{{background:#34271e;position:relative;isolation:isolate;color:#fff8eb;overflow:hidden}}
.hero::before{{content:"";position:absolute;inset:0;z-index:-1;background:
  linear-gradient(90deg,#231910ed 0%,#2b2017c4 41%,#33251a29 100%),
  url("/assets/serra-trilhas-rj.png") center 48% / cover no-repeat}}
.hero-conteudo,main{{max-width:1160px;margin:auto;padding-inline:clamp(18px,5vw,48px)}}
.hero-conteudo{{padding-top:28px;padding-bottom:107px}}
.marca{{display:inline-flex;align-items:center;gap:12px;color:#fff8eb;text-decoration:none;font-weight:750;letter-spacing:.04em}}
.marca-icone{{display:inline-grid;place-items:center;width:32px;height:32px;border:1px solid #fff8eb70;border-radius:9px}}
.marca-icone::before{{content:"";width:22px;height:16px;background:#f0c69d;clip-path:polygon(0 100%,35% 26%,48% 55%,70% 0,100% 100%)}}
h1,h2,h3{{font-family:"Instrument Serif",Georgia,serif;font-weight:500;letter-spacing:-.025em}}
h1{{max-width:800px;margin:36px 0 12px;font-size:clamp(3.5rem,8vw,6.5rem);line-height:.98}}
.hero p{{max-width:480px;margin:0;color:#f1e5d4;font-size:1.04rem}}
main{{position:relative;margin-top:-46px;padding-bottom:64px}}
form,article,.resumo-consulta{{border:1px solid var(--linha);border-radius:18px;background:var(--papel)}}
form{{padding:clamp(18px,4vw,34px);box-shadow:0 14px 34px #51391e18;border-top:4px solid var(--terra)}}
label{{display:block;font-size:.9rem;font-weight:700;margin-bottom:7px}}
.primeira-linha,.horarios{{display:grid;gap:16px}}
.primeira-linha{{grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);align-items:start}}
.horarios{{grid-template-columns:repeat(2,minmax(0,1fr))}}
.campo{{min-width:0}}.duracao{{margin-top:18px}}
input,select{{width:100%;min-height:48px;color:var(--texto);background:#faf6ed;border:1px solid #ccbaa6;border-radius:9px;font:inherit;padding:9px 12px}}
input[type="number"],input[name="comparar"]{{max-width:220px}}
#duracao-ajuda{{font-size:.84rem;color:var(--suave);margin:6px 0 0}}
form details{{padding-top:16px;margin-top:18px;border-top:1px solid var(--linha)}}
details summary{{font-weight:700;color:var(--verde);cursor:pointer}}
form details label{{margin-top:12px}}
button{{min-height:49px;border:1px solid transparent;border-radius:9px;padding:10px 20px;background:var(--terra);color:#fff;font:inherit;font-weight:750;cursor:pointer;margin-top:22px}}
button:hover{{background:var(--terra-escura)}}
:focus-visible{{outline:3px solid #bc7b3e;outline-offset:3px}}
a{{color:var(--terra-escura);text-underline-offset:3px}}
.erro{{background:#fff1ea;border:1px solid #c6896f;color:#742d20;border-radius:10px;padding:14px 16px;margin:0 0 12px}}
.resultados{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,385px),1fr));gap:16px}}
section{{margin-top:34px}}
.resumo-consulta,article{{padding:clamp(16px,3vw,25px)}}
.resumo-consulta{{margin-bottom:16px}}
.resumo-consulta p{{margin:6px 0;color:var(--suave)}}
.chuva-observada{{margin:16px 0;padding:16px;border:1px solid var(--linha);border-radius:12px;background:var(--fundo);overflow-wrap:anywhere}}
.chuva-observada h3{{font-size:1.2rem;color:var(--verde)}}
.chuva-observada .acumulado-observado strong{{font-size:1.35rem;color:var(--terra-escura)}}
.chuva-observada dl{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,215px),1fr));gap:8px 16px;margin:12px 0}}
.chuva-observada dt{{font-weight:700}}
.chuva-observada dd{{margin:0;color:var(--suave)}}
article{{min-width:0;border-top:4px solid var(--verde);overflow-wrap:anywhere}}
h2,h3{{margin:0 0 8px;font-size:clamp(1.65rem,3vw,2.35rem);line-height:1.12}}
h4{{margin:20px 0 6px;color:var(--verde)}}article p{{margin-top:0;color:var(--suave)}}
ul{{padding-left:1.2rem}}li{{margin-bottom:6px}}
article details{{border-top:1px solid var(--linha);padding-top:12px}}
@media (max-width:700px){{
  .primeira-linha{{grid-template-columns:1fr}}
  .hero-conteudo{{padding-bottom:85px}}
  .hero::before{{background-position:center,63% center}}
  h1{{margin-top:27px}}
}}
@media (max-width:370px){{.horarios{{grid-template-columns:1fr}}}}
</style></head>
<body><header class="hero"><div class="hero-conteudo">
<a class="marca" href="/"><span class="marca-icone" aria-hidden="true"></span>Trilhas RJ</a>
<h1>Planeje sua trilha</h1>
<p>Escolha o percurso e seu horário de saída para conferir a previsão e as recomendações.</p>
</div></header><main>
{alerta}<form action="/" method="post" aria-label="Planejamento da trilha">
<div class="primeira-linha"><div class="campo">
<label for="trilha">Trilha</label><select name="trilha" id="trilha" required>{"".join(opcoes)}</select></div>
<div class="horarios"><div class="campo"><label for="data">Data</label><input type="date" name="data" id="data" min="{hoje}" value="{texto(campos.get("data", hoje))}" required></div>
<div class="campo"><label for="saida">Horário de saída</label><input type="time" name="saida" id="saida" value="{texto(campos.get("saida", ""))}" required></div></div></div>
<div class="duracao"><label for="duracao">Duração estimada em minutos</label>
<input type="number" min="1" name="duracao" id="duracao" value="{texto(campos.get("duracao", ""))}" aria-describedby="duracao-ajuda">
<p id="duracao-ajuda">Deixe em branco para usar a duração do catálogo, se disponível.</p></div>
<details {"open" if campos.get("comparar") else ""}><summary>Comparar com outro horário</summary>
<label for="comparar">Segunda saída na mesma data</label><input type="time" id="comparar" name="comparar" value="{texto(campos.get("comparar", ""))}"></details>
<button type="submit">Consultar trilha</button></form>{conteudo}</main>
<script>
const trilha = document.querySelector('#trilha');
const duracao = document.querySelector('#duracao');
function atualizarDuracao() {{
  const padrao = trilha.selectedOptions[0].dataset.duracao;
  duracao.placeholder = padrao || 'Informe uma estimativa';
  duracao.required = Boolean(trilha.value && !padrao);
}}
trilha.addEventListener('change', atualizarDuracao);
atualizarDuracao();
</script></body></html>"""


class Planejador(BaseHTTPRequestHandler):
    def responder(self, html, status=200):
        corpo = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path == "/assets/serra-trilhas-rj.png":
            imagem = PASTA / "src" / "assets" / "serra-trilhas-rj.png"
            try:
                corpo = imagem.read_bytes()
            except OSError:
                return self.send_error(404)
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        if self.path != "/":
            return self.send_error(404)
        self.responder(pagina(catalogo(), {}))

    def do_POST(self):
        if self.path != "/":
            return self.send_error(404)
        tamanho = self.headers.get("Content-Length", "")
        if not tamanho.isdecimal() or len(tamanho) > 4 or int(tamanho) > 4096:
            return self.send_error(413)
        corpo = self.rfile.read(int(tamanho)).decode("utf-8", errors="replace")
        campos = {chave: valores[0] for chave, valores in parse_qs(corpo).items()}
        trilhas = catalogo()
        try:
            if not campos.keys() >= {"trilha", "data", "saida"} or campos["trilha"] not in trilhas:
                raise ValueError("Selecione a trilha, a data e o horário de saída.")
            resultado = consultar(campos)
        except requests.RequestException:
            return self.responder(pagina(trilhas, campos, erro="A consulta à previsão falhou. Tente novamente em instantes."), 502)
        except (ValueError, OverflowError, ParseError) as erro:
            return self.responder(pagina(trilhas, campos, erro=str(erro)), 400)
        except (KeyError, OSError, TypeError):
            return self.responder(pagina(trilhas, campos, erro="Não foi possível ler os dados da consulta."), 502)
        self.responder(pagina(trilhas, campos, resultado))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--porta", type=int, default=8000)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.porta), Planejador) as servidor:
        print(f"Abra http://127.0.0.1:{servidor.server_port}", flush=True)
        servidor.serve_forever()
