import csv
from datetime import UTC, datetime, timedelta
from math import isfinite

import requests

CEMADEN_RJ = "https://resources.cemaden.gov.br/graficos/interativo/getJson2.php?uf=RJ"
ALERTA_RIO_DADOS = "https://websempre.rio.rj.gov.br/dados/pluviometricos/plv/"
TOLERANCIA_PILOTO = timedelta(minutes=30)


def ler_chuva_observada_24h(caminho, rede, codigo_estacao, consulta_em, atraso_maximo):
    resultado = {
        "rede": rede,
        "codigo_estacao": codigo_estacao,
        "estado": "indisponivel",
        "acumulado_mm": None,
        "cobertura_percentual": None,
    }
    ultima = None

    try:
        with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
            for linha in csv.DictReader(arquivo):
                if (linha["rede"], linha["codigo_estacao"]) != (rede, codigo_estacao):
                    continue
                fim = datetime.fromisoformat(linha["fim_janela"])
                valor = float(linha["acumulado_mm"])
                if fim.utcoffset() is None or not isfinite(valor) or valor < 0:
                    raise ValueError("Horário sem fuso ou acumulado inválido.")
                cobertura = linha.get("cobertura_percentual")
                cobertura = float(cobertura) if cobertura else None
                if cobertura is not None and not 0 <= cobertura <= 100:
                    raise ValueError("Cobertura fora do intervalo de 0 a 100%.")

                fim = fim.astimezone(UTC)
                if fim <= consulta_em and (ultima is None or fim > ultima[0]):
                    ultima = (fim, valor, cobertura, linha)
    except FileNotFoundError:
        return {**resultado, "motivo": "Arquivo de observações ausente."}
    except (OSError, csv.Error, KeyError, TypeError, ValueError) as erro:
        return {**resultado, "motivo": f"Falha ao ler a observação: {erro}"}

    if ultima is None:
        return {**resultado, "motivo": "Sem observação válida até a consulta."}

    fim, valor, cobertura, linha = ultima
    resultado.update({
        "estacao": linha["estacao"],
        "fonte_url": linha["fonte_url"],
        "inicio_janela_utc": (fim - timedelta(hours=24)).isoformat(),
        "fim_janela_utc": fim.isoformat(),
        "idade_leitura_segundos": (consulta_em - fim).total_seconds(),
        "acumulado_publicado_mm": valor,
        "cobertura_percentual": cobertura,
    })
    if consulta_em - fim > atraso_maximo:
        return {
            **resultado,
            "estado": "desatualizado",
            "motivo": "O fim da janela excede a tolerância do piloto.",
        }

    if cobertura is None:
        return {**resultado, "estado": "cobertura_nao_verificada"}
    if cobertura < 100:
        return {**resultado, "estado": "cobertura_incompleta"}

    return {
        **resultado,
        "estado": "disponivel",
        "acumulado_mm": valor,
        "metodo": "acumulado de 24 h publicado pela fonte",
    }


def ler_cemaden(estacoes, codigo, id_interno, referencia, tolerancia):
    resultado = {
        "rede": "Cemaden",
        "codigo_estacao": codigo,
        "fonte_url": CEMADEN_RJ,
        "estado": "indisponivel",
        "acumulado_mm": None,
        "cobertura_percentual": None,
    }
    if estacoes is None:
        return {**resultado, "motivo": "Canal do Cemaden indisponível."}
    estacao = estacoes.get(id_interno)
    if estacao is None:
        return {**resultado, "motivo": "Estação sem registro no canal consultado."}
    resultado["estacao"] = estacao.get("nomeestacao")
    try:
        fim = datetime.strptime(estacao["datahoraUltimovalor"], "%d/%m/%y %H:%M").replace(
            tzinfo=UTC
        )
    except (KeyError, TypeError, ValueError):
        return {**resultado, "motivo": "A estação não informou um horário de leitura válido."}
    if fim > referencia:
        return {**resultado, "motivo": "Horário da leitura posterior à consulta."}
    resultado["ultima_leitura_utc"] = fim.isoformat()
    try:
        valor = float(estacao["acc24hr"])
        if not isfinite(valor) or valor < 0:
            raise ValueError("Acumulado inválido.")
    except (KeyError, TypeError, ValueError):
        return {**resultado, "motivo": "Estação sem acumulado de 24 h utilizável."}

    resultado.update({
        "inicio_janela_nominal_utc": (fim - timedelta(hours=24)).isoformat(),
        "fim_janela_nominal_utc": fim.isoformat(),
        "acumulado_publicado_mm": valor,
    })
    resultado["idade_leitura_segundos"] = (referencia - fim).total_seconds()
    if referencia - fim > tolerancia:
        return {**resultado, "estado": "desatualizado", "motivo": "Leitura fora da tolerância."}
    return {
        **resultado,
        "estado": "cobertura_nao_verificada",
        "motivo": "A fonte publica o total e a última leitura, sem informar lacunas na janela.",
    }


def consultar_chuva_da_trilha(caminho_vinculos, caminho_observacoes, id_trilha, consulta_em):
    resultado = {
        "estado": "indisponivel",
        "acumulado_mm": None,
        "cobertura_percentual": None,
        "motivo": "Sem estação aprovada para esta trilha.",
    }
    try:
        with caminho_vinculos.open(encoding="utf-8-sig", newline="") as arquivo:
            vinculos = sorted(
                (linha for linha in csv.DictReader(arquivo) if linha["id_trilha"] == id_trilha),
                key=lambda linha: int(linha["prioridade"]),
            )
    except (OSError, csv.Error, KeyError, TypeError, ValueError) as erro:
        return {**resultado, "motivo": f"Falha ao ler os vínculos: {erro}"}
    ids_cemaden = {}
    estacoes_cemaden = None
    if any(vinculo["rede"] == "Cemaden" for vinculo in vinculos):
        try:
            inventario = caminho_vinculos.with_name("inventario-estacoes-pluviometricas-rj.csv")
            with inventario.open(encoding="utf-8-sig", newline="") as arquivo:
                ids_cemaden = {
                    linha["codigo"]: linha["id_interno"]
                    for linha in csv.DictReader(arquivo)
                    if linha["rede"] == "Cemaden"
                }
            resposta = requests.get(CEMADEN_RJ, timeout=8)
            resposta.raise_for_status()
            estacoes_cemaden = {
                str(estacao["idestacao"]): estacao for estacao in resposta.json()
            }
        except (OSError, csv.Error, KeyError, TypeError, ValueError, requests.RequestException):
            pass

    for indice, vinculo in enumerate(vinculos):
        observacao = ler_chuva_observada_24h(
            caminho_observacoes,
            vinculo["rede"],
            vinculo["codigo_estacao"],
            consulta_em,
            TOLERANCIA_PILOTO,
        )
        if vinculo["rede"] == "Alerta Rio":
            observacao.setdefault("fonte_url", ALERTA_RIO_DADOS)
        if vinculo.get("distancia_km"):
            observacao["distancia_referencia_km"] = float(vinculo["distancia_km"])
        if observacao["estado"] == "disponivel":
            return observacao
        if vinculo["rede"] == "Cemaden" and observacao["estado"] == "indisponivel":
            codigo = vinculo["codigo_estacao"]
            leitura_online = ler_cemaden(
                estacoes_cemaden, codigo, ids_cemaden.get(codigo), consulta_em,
                TOLERANCIA_PILOTO,
            )
            observacao.update(leitura_online)
        if not observacao.get("estacao") and vinculo.get("nome_estacao"):
            observacao["estacao"] = vinculo["nome_estacao"]
        if indice == 0:
            resultado = observacao
    return resultado
