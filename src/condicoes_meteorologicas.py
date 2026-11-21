"""Indicadores horários na célula meteorológica de referência da trilha."""

from datetime import UTC, datetime, timedelta
from math import isfinite

HORA = timedelta(hours=1)
DUAS_HORAS = 2 * HORA
UNIDADES = {
    "temperature_2m": "°C",
    "apparent_temperature": "°C",
    "wind_gusts_10m": "km/h",
    "visibility": "m",
    "weather_code": "wmo code",
    "uv_index": "",
}


def instante_utc(valor):
    instante = datetime.fromisoformat(valor)
    return instante.replace(tzinfo=UTC) if instante.tzinfo is None else instante.astimezone(UTC)


def ler_campos(previsao):
    dados = previsao.get("hourly", {})
    horarios = [instante_utc(t) for t in dados.get("time", [])]
    campos = {}
    unidades = previsao.get("hourly_units", {})
    for campo, unidade in {**UNIDADES, "precipitation": "mm"}.items():
        valores = dados.get(campo) or []
        if str(unidades.get(campo, unidade)).casefold() != unidade.casefold() or len(valores) != len(horarios):
            campos[campo] = {}
            continue
        campos[campo] = {
            hora: valor for hora, valor in zip(horarios, valores)
            if isinstance(valor, (int, float)) and isfinite(valor)
        }
    return campos


def interpolar(serie, instante):
    hora = instante.replace(minute=0, second=0, microsecond=0)
    inicial = serie.get(hora)
    if hora == instante:
        return inicial
    final = serie.get(hora + HORA)
    if inicial is None or final is None:
        return None
    return inicial + (final - inicial) * ((instante - hora) / HORA)


def amostrar(serie, inicio, fim):
    horas = [inicio]
    hora = inicio.replace(minute=0, second=0, microsecond=0) + HORA
    while hora < fim:
        horas.append(hora)
        hora += HORA
    horas.append(fim)
    amostras = [(t, interpolar(serie, t)) for t in horas]
    return amostras if all(v is not None for _, v in amostras) else []


def resumo_meteorologico(campos, inicio, fim):
    inicio, fim = inicio.astimezone(UTC), fim.astimezone(UTC)
    temperatura = campos["temperature_2m"]
    temperaturas = amostrar(temperatura, inicio, fim)
    sensacoes = amostrar(campos["apparent_temperature"], inicio, fim)
    visibilidades = amostrar(campos["visibility"], inicio, fim)
    hora = inicio.replace(minute=0, second=0, microsecond=0) + HORA
    rajadas = []
    codigos = []
    indices_uv = []
    sensacoes_com_chuva = []
    sensacoes_com_vento = []
    while hora - HORA < fim:
        rajada = campos["wind_gusts_10m"].get(hora)
        rajadas.append(rajada)
        # O código WMO é instantâneo. Considerar amostras dentro da janela.
        marca = hora - HORA
        if inicio <= marca:
            codigos.append(campos.get("weather_code", {}).get(marca))
        indices_uv.append(campos.get("uv_index", {}).get(hora))
        chuva = campos.get("precipitation", {}).get(hora)
        janela_inicio, janela_fim = max(inicio, marca), min(fim, hora)
        sensacoes_hora = amostrar(campos["apparent_temperature"], janela_inicio, janela_fim)
        minima = min((v for _, v in sensacoes_hora), default=None)
        sensacoes_com_chuva.append(coincidencia(minima, chuva, 1))
        sensacoes_com_vento.append(coincidencia(minima, rajada, 40))
        hora += HORA

    if fim.minute == fim.second == fim.microsecond == 0:
        codigos.append(campos.get("weather_code", {}).get(fim))
    queda = None
    if temperaturas and fim - inicio >= DUAS_HORAS:
        ultimo = fim - DUAS_HORAS
        candidatos = {inicio, ultimo}
        for t, _ in temperaturas:
            candidatos.update(x for x in (t, t - DUAS_HORAS) if inicio <= x <= ultimo)
        queda = max(
            ((interpolar(temperatura, t) - interpolar(temperatura, t + DUAS_HORAS), t)
             for t in sorted(candidatos)),
            key=lambda par: par[0],
        )

    return {
        "temp_max": max((v for _, v in temperaturas), default=None),
        "uv_max": max(indices_uv) if indices_uv and None not in indices_uv else None,
        "tempestade_prevista": algum(c in (95, 96, 97, 99) if c is not None else None for c in codigos),
        "granizo_previsto": algum(c in (96, 99) if c is not None else None for c in codigos),
        "frio_com_chuva": algum(sensacoes_com_chuva),
        "frio_com_vento": algum(sensacoes_com_vento),
        "temp_min": min((v for _, v in temperaturas), default=None),
        "queda_2h": max(0, queda[0]) if queda else None,
        "janela_queda_2h": [queda[1].isoformat(), (queda[1] + DUAS_HORAS).isoformat()] if queda else None,
        "sensacao_min": min((v for _, v in sensacoes), default=None),
        "sensacao_max": max((v for _, v in sensacoes), default=None),
        "rajada_max": max(rajadas) if rajadas and all(v is not None for v in rajadas) else None,
        "visibilidade_min": min((v for _, v in visibilidades), default=None),
    }


def algum(estados):
    estados = list(estados)
    if True in estados:
        return True
    if estados and None not in estados:
        return False
    return None


def coincidencia(sensacao, evento, limiar):
    if (sensacao is not None and sensacao > 8) or (evento is not None and evento < limiar):
        return False
    if sensacao is None or evento is None:
        return None
    return True


def luz_do_dia(previsao, saida, retorno):
    pores_do_sol = [
        instante_utc(t).astimezone(saida.tzinfo)
        for t in previsao.get("daily", {}).get("sunset", []) if t
    ]
    por_do_sol = next((t for t in pores_do_sol if t.date() == saida.date()), None)
    nascimentos = [
        instante_utc(t).astimezone(saida.tzinfo)
        for t in previsao.get("daily", {}).get("sunrise", []) if t
    ]
    nascer = next((t for t in nascimentos if t.date() == saida.date()), None)
    diurna = por_do_sol is not None and saida < por_do_sol and (nascer is None or saida >= nascer)
    return {
        "nascer_do_sol": nascer.isoformat() if nascer else None,
        "saida_antes_do_nascer": saida < nascer if nascer else None,
        "margem_luz_min": (por_do_sol - retorno).total_seconds() / 60 if diurna and nascer is not None else None,
        "por_do_sol": por_do_sol.isoformat() if por_do_sol else None,
        "saida_apos_por_do_sol": saida >= por_do_sol if por_do_sol else None,
        "minutos_pos_por_do_sol": max(0, (retorno - por_do_sol).total_seconds() / 60)
        if por_do_sol and saida < por_do_sol else None,
    }
