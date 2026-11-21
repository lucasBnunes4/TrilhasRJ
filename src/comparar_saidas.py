import argparse
import csv
import json
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zoneinfo import ZoneInfo

import requests
from inferencia import avaliar_consulta, pico_com_cobertura
from condicoes_meteorologicas import UNIDADES, ler_campos, luz_do_dia, resumo_meteorologico

from observacoes import consultar_chuva_da_trilha
from percurso import estimar_janela_trecho, ler_distancia_gpx
from trechos import consultar_terreno

from caminhos import PASTA
FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")
UMA_HORA = timedelta(hours=1)
VINTE_E_QUATRO_HORAS = timedelta(hours=24)
API_PREVISAO = "https://api.open-meteo.com/v1/forecast"
MAX_DIAS_PREVISAO = 16


def carregar_trilha(id_trilha):
    with (PASTA / "trilhas.csv").open(encoding="utf-8-sig", newline="") as arquivo:
        for trilha in csv.DictReader(arquivo):
            if trilha["id_trilha"] == id_trilha:
                if not trilha["latitude_ref"] or not trilha["longitude_ref"]:
                    raise ValueError(f"A trilha {id_trilha} está sem coordenadas.")
                return trilha

    raise ValueError(f"Trilha não encontrada: {id_trilha}")


def calcular_dias_previsao(consulta, ultimo_retorno):
    retorno_utc = ultimo_retorno.astimezone(UTC)
    fim_hora = retorno_utc.replace(minute=0, second=0, microsecond=0)
    if fim_hora < retorno_utc:
        fim_hora += UMA_HORA

    dias = (fim_hora.date() - consulta.astimezone(UTC).date()).days + 1
    return min(dias, MAX_DIAS_PREVISAO)


def obter_previsao(trilha, dias_previsao):
    resposta = requests.get(
        API_PREVISAO,
        params={
            "latitude": float(trilha["latitude_ref"]),
            "longitude": float(trilha["longitude_ref"]),
            "hourly": ",".join(("precipitation", *UNIDADES)),
            "daily": "sunrise,sunset",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timezone": "GMT",
            "forecast_days": dias_previsao,
        },
        timeout=15,
    )
    resposta.raise_for_status()
    return resposta.json(), datetime.now(UTC)


def ler_serie_previsao(dados):
    if dados["utc_offset_seconds"] != 0:
        raise ValueError("A resposta meteorológica precisa estar em UTC.")

    horarios = dados["hourly"]["time"]
    valores = dados["hourly"]["precipitation"]
    if len(horarios) != len(valores):
        raise ValueError("A série tem quantidades diferentes de horários e valores.")

    serie = {
        datetime.fromisoformat(horario).replace(tzinfo=UTC): valor
        for horario, valor in zip(horarios, valores)
    }
    return serie


def horario_local(instante):
    local = instante.astimezone(FUSO_LOCAL)
    return local.isoformat(timespec="seconds" if local.second else "minutes")


def resumir_janela(serie, inicio, fim, *, previsao_a_partir_de=None):
    inicio_utc = inicio.astimezone(UTC)
    fim_utc = fim.astimezone(UTC)

    # O valor associado a fim_hora representa (fim_hora - 1 h, fim_hora].
    inicio_disponivel = inicio_utc
    if previsao_a_partir_de is not None:
        inicio_disponivel = max(inicio_utc, previsao_a_partir_de.astimezone(UTC))
    fim_hora = inicio_disponivel.replace(minute=0, second=0, microsecond=0) + UMA_HORA
    acumulado = 0.0
    tempo_coberto = timedelta()
    pico = None

    while inicio_disponivel < fim_utc and fim_hora - UMA_HORA < fim_utc:
        inicio_hora = fim_hora - UMA_HORA
        sobreposicao = min(fim_utc, fim_hora) - max(inicio_disponivel, inicio_hora)
        segundos = sobreposicao.total_seconds()
        valor = serie.get(fim_hora)

        if segundos > 0 and valor is not None:
            acumulado += valor * segundos / 3600
            tempo_coberto += sobreposicao
            if pico is None or valor > pico["chuva_mm"]:
                pico = {
                    "inicio": horario_local(inicio_hora),
                    "fim": horario_local(fim_hora),
                    "chuva_mm": valor,
                }

        fim_hora += UMA_HORA

    duracao = fim_utc - inicio_utc
    completa = tempo_coberto == duracao

    return {
        "inicio": horario_local(inicio),
        "fim": horario_local(fim),
        "cobertura_percentual": 100.0 if completa else min(99.9, round(100 * tempo_coberto / duracao, 1)),
        "chuva_prevista_estimada_mm": round(acumulado, 2) if completa else None,
        "pico_horario_na_cobertura_disponivel": pico,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trilha")
    parser.add_argument("--data", type=date.fromisoformat)
    parser.add_argument("--saidas", nargs=2, type=time.fromisoformat)
    parser.add_argument("--duracao", type=int, help="Duração planejada em minutos")
    parser.add_argument(
        "--trecho",
        nargs=2,
        type=float,
        metavar=("INICIO_PCT", "FIM_PCT"),
        help="Limites percentuais da distância acumulada do GPX",
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--salvar-consulta", type=Path, help="Grava os insumos em um novo JSON")
    modo.add_argument("--reproduzir", type=Path, help="Recalcula os cenários gravados sem internet")
    parser.add_argument("--inferencia-experimental", action="store_true",
                        help="Avalia as regras de chuva revisadas para o piloto")
    args = parser.parse_args()
    if args.reproduzir:
        if any(valor is not None for valor in (args.trilha, args.data, args.saidas, args.duracao, args.trecho)):
            parser.error("--reproduzir usa os parâmetros gravados no JSON.")
    elif args.data is None or args.saidas is None:
        parser.error("Informe --data e --saidas para uma consulta ao vivo.")

    try:
        if args.reproduzir:
            consulta = json.loads(args.reproduzir.read_text(encoding="utf-8"))
            if consulta["versao"] != 1:
                raise ValueError("Versão de consulta gravada incompatível.")
        else:
            consulta = preparar_consulta(args)
        resultado = comparar_consulta(consulta)
        if args.inferencia_experimental:
            avaliar_consulta(resultado, consulta)
        if args.salvar_consulta:
            conteudo = json.dumps(consulta, ensure_ascii=False, indent=2, allow_nan=False)
            with args.salvar_consulta.open("x", encoding="utf-8") as arquivo:
                arquivo.write(conteudo + "\n")
    except (ValueError, KeyError, TypeError, OSError, ParseError, requests.RequestException) as erro:
        parser.exit(1, f"Erro: {erro}\n")

    print(json.dumps(resultado, ensure_ascii=False, indent=2))


def preparar_consulta(args):
    return coletar_consulta(args.trilha or "RIO-PNT-001", args.data, args.saidas, args.duracao, args.trecho)


def coletar_consulta(id_trilha, data, horarios, duracao=None, trecho=None):
    trilha = carregar_trilha(id_trilha)
    origem_duracao = "informada pelo usuário"
    if duracao is None:
        duracao = int(float(trilha["duracao_min"] or "0"))
        origem_duracao = "duração registrada no catálogo"
    if duracao <= 0:
        raise ValueError("Informe uma duração positiva com --duracao.")

    saidas = [
        datetime.combine(data, hora, tzinfo=FUSO_LOCAL)
        for hora in horarios
    ]
    agora = datetime.now(UTC)
    if any(saida.astimezone(UTC) <= agora for saida in saidas):
        raise ValueError("Escolha horários de saída no futuro.")

    retornos = [saida.astimezone(UTC) + timedelta(minutes=duracao) for saida in saidas]
    terreno = consultar_terreno(id_trilha)
    documentados = terreno["documentados"]
    if trecho is not None:
        documentados = [t for t in documentados if t["limites_pct"] == list(trecho)]
    elif documentados:
        trecho = documentados[0]["limites_pct"]
    ultimo = max(retornos)
    if trecho is not None:
        ultimo = max(ultimo, max(saidas).astimezone(UTC) + timedelta(minutes=duracao * 1.2))
    dias_previsao = calcular_dias_previsao(agora, ultimo)

    chuva_observada = consultar_chuva_da_trilha(
        PASTA / "vinculos-aprovados.csv",
        PASTA / "observacao-piloto.csv",
        trilha["id_trilha"],
        agora,
    )

    distancia_gpx = None
    if trecho is not None:
        inicio_pct, fim_pct = trecho
        if not 0 <= inicio_pct < fim_pct <= 100:
            raise ValueError("Use 0 <= início < fim <= 100 para o trecho.")
        if not trilha["geometria_url"]:
            raise ValueError("A trilha está sem referência ao GPX.")
        distancia_gpx = ler_distancia_gpx(PASTA / trilha["geometria_url"])

    previsao, coletado_em = obter_previsao(trilha, dias_previsao)
    previsoes_montante = {}
    for t in documentados:
        pontos = t.get("amostragem_montante_validada", [])
        if pontos:
            previsoes_montante[t["id"]] = []
        for lat, lon in pontos:
            try:
                dados, _ = obter_previsao({"latitude_ref": lat, "longitude_ref": lon}, dias_previsao)
                ler_serie_previsao(dados)
            except (requests.RequestException, KeyError, TypeError, ValueError):
                dados = None
            previsoes_montante[t["id"]].append(dados)
    return {
        "versao": 1,
        "id_trilha": trilha["id_trilha"],
        "nome": trilha["nome"],
        "latitude_ref": float(trilha["latitude_ref"]),
        "longitude_ref": float(trilha["longitude_ref"]),
        "geometria_url": trilha["geometria_url"],
        "duracao_min": duracao,
        "origem_duracao": origem_duracao,
        "saidas": [saida.isoformat() for saida in saidas],
        "trecho_pct": trecho,
        "trechos_documentados": documentados,
        "trechos_candidatos": terreno["candidatos"],
        "previsoes_montante": previsoes_montante,
        "distancia_gpx_km": distancia_gpx,
        "fonte_previsao": "Open-Meteo",
        "fonte_previsao_url": API_PREVISAO,
        "dias_previsao_solicitados": dias_previsao,
        "consulta_em_utc": agora.isoformat(),
        "coletado_em_utc": coletado_em.isoformat(),
        "chuva_observada_24h": chuva_observada,
        "previsao": previsao,
    }


def comparar_consulta(consulta):
    agora = datetime.fromisoformat(consulta["consulta_em_utc"])
    saidas = [datetime.fromisoformat(saida) for saida in consulta["saidas"]]
    duracao = consulta["duracao_min"]
    retornos = [saida.astimezone(UTC) + timedelta(minutes=duracao) for saida in saidas]
    distancia_gpx = consulta["distancia_gpx_km"]
    serie = ler_serie_previsao(consulta["previsao"])
    campos = ler_campos(consulta["previsao"])
    cenarios = [
        resumir_janela(serie, saida, retorno)
        for saida, retorno in zip(saidas, retornos)
    ]

    for saida, retorno, cenario in zip(saidas, retornos, cenarios):
        cenario["meteorologia"] = resumo_meteorologico(campos, saida, retorno)
        cenario["luz_do_dia"] = luz_do_dia(consulta["previsao"], saida, retorno)
        cenario["previsao_antes_da_saida"] = resumir_janela(serie, agora, saida)
        cenario["previsao_24h_antes_da_saida"] = resumir_janela(
            serie,
            saida.astimezone(UTC) - VINTE_E_QUATRO_HORAS,
            saida,
            previsao_a_partir_de=agora,
        )
        if distancia_gpx is not None:
            trechos = consulta.get("trechos_documentados") or [{
                "limites_pct": consulta["trecho_pct"],
            }]
            cenario["trechos"] = [
                resumir_trecho(t, consulta, serie, campos, saida.astimezone(UTC), agora)
                for t in trechos
            ]
            cenario["trecho"] = cenario["trechos"][0]
    return {
        "id_trilha": consulta["id_trilha"],
        "nome": consulta["nome"],
        "duracao_min": duracao,
        "origem_duracao": consulta["origem_duracao"],
        "fonte_previsao": consulta["fonte_previsao"],
        "dias_previsao_solicitados": consulta["dias_previsao_solicitados"],
        "consulta_em_utc": agora.isoformat(timespec="seconds"),
        "coletado_em_utc": datetime.fromisoformat(consulta["coletado_em_utc"]).isoformat(timespec="seconds"),
        "chuva_observada_24h": consulta["chuva_observada_24h"],
        "cenarios": cenarios,
        "trechos_candidatos": consulta.get("trechos_candidatos", []),
    }


def resumir_trecho(trecho, consulta, serie, campos, saida, agora):
    inicio_pct, fim_pct = trecho["limites_pct"]
    distancia = consulta["distancia_gpx_km"]
    duracao = consulta["duracao_min"]
    inicio, fim = estimar_janela_trecho(saida, duracao, inicio_pct, fim_pct)
    alternativas = []
    for fator in (0.8, 1.2):
        a, b = estimar_janela_trecho(saida, duracao * fator, inicio_pct, fim_pct)
        alternativas.append(resumir_janela(serie, a, b))
    amostras = consulta.get("previsoes_montante", {}).get(trecho.get("id"), [])
    picos = [
        pico_com_cobertura(resumir_janela(
            ler_serie_previsao(dados), inicio - timedelta(hours=6), fim,
            previsao_a_partir_de=agora,
        )) if dados is not None else None
        for dados in amostras
    ]
    return {
        **trecho,
        "distancia_inicio_km": round(distancia * inicio_pct / 100, 3),
        "distancia_fim_km": round(distancia * fim_pct / 100, 3),
        "previsao": resumir_janela(serie, inicio, fim),
        "meteorologia": resumo_meteorologico(campos, inicio, fim),
        "duracoes_alternativas": alternativas,
        "pico_montante": max(picos) if picos and all(p is not None for p in picos) else None,
    }


if __name__ == "__main__":
    main()
