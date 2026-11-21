from datetime import timedelta
from math import asin, cos, radians, sin, sqrt
from xml.etree import ElementTree as ET


def distancia_km(ponto_a, ponto_b):
    lat_a, lon_a = map(radians, ponto_a)
    lat_b, lon_b = map(radians, ponto_b)
    h = (
        sin((lat_b - lat_a) / 2) ** 2
        + cos(lat_a) * cos(lat_b) * sin((lon_b - lon_a) / 2) ** 2
    )
    return 2 * 6371.0 * asin(sqrt(min(1.0, h)))


def ler_distancia_gpx(caminho):
    raiz = ET.parse(caminho).getroot()
    total = 0.0

    for segmento in raiz.findall(".//{*}trkseg"):
        pontos = [
            (float(ponto.attrib["lat"]), float(ponto.attrib["lon"]))
            for ponto in segmento.findall("{*}trkpt")
        ]
        total += sum(
            distancia_km(anterior, atual)
            for anterior, atual in zip(pontos, pontos[1:])
        )

    if total <= 0:
        raise ValueError("O GPX precisa ter um traçado com distância positiva.")
    return total


def estimar_janela_trecho(saida_utc, duracao_min, inicio_pct, fim_pct):
    inicio = saida_utc + timedelta(minutes=duracao_min * inicio_pct / 100)
    fim = saida_utc + timedelta(minutes=duracao_min * fim_pct / 100)
    if inicio >= fim:
        raise ValueError("A janela estimada do trecho precisa ter duração positiva.")
    return inicio, fim
