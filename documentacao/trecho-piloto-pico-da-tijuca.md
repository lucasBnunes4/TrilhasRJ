# Trecho piloto do Pico da Tijuca

**Trilha `RIO-PNT-001` · acesso final ao cume pela escadaria, na subida**

O catálogo identifica a escadaria e o cume nos registros `RIO-PNT-001-F01-P17` e `RIO-PNT-001-F01-P18`, ambos da fonte `RIO-PNT-001-F01`. O plano de manejo confirma a escadaria esculpida na rocha no acesso ao pico. Uma foto georreferenciada fornece uma referência espacial próxima à escadaria (−22.943468, −43.285496), a cerca de 8 m do ponto 208 na subida do GPX.

| Limite escolhido no GPX | Ponto (contagem a partir de 1) | Latitude, longitude | Elevação GPX | Distância acumulada | Fração do percurso |
|---|---:|---|---:|---:|---:|
| Aproximação da escadaria | 207 | −22.943394, −43.285430 | 985,3 m | 7,446 km | 52,0024% |
| Chegada à área do cume | 210 | −22.943796, −43.286113 | 1.028,5 m | 7,535 km | 52,6186% |

Os limites delimitam aproximadamente o acesso final até o cume, incluindo o entorno da escadaria. A foto fornece a posição da câmera, e a altitude do ponto de interesse ajuda a identificar a aproximação. A posição exata do primeiro e do último degrau permanece sem levantamento. A seleção segue a ordem dos pontos na subida, pois o traçado volta a passar pelo entorno da escadaria depois do cume.

As distâncias vêm da soma entre pontos consecutivos do [GPX local](../gpx/portao-pnt-pico-da-tijuca-portao-pnt-sem-pressa.gpx), com a mesma função usada pelo comparador. O traçado local mede 14,319 km. O intervalo selecionado mede aproximadamente 88 m.

Em `trabFinal/src`, execute:

```bash
python3 comparar_saidas.py \
  --trilha RIO-PNT-001 \
  --data "$(TZ=America/Sao_Paulo date -d '+7 days' +%F)" \
  --saidas 08:00 11:00 \
  --trecho 52.0024 52.6186
```

O comando usa a duração cadastrada. Para repetir a duração de 120 minutos adotada no teste anterior, acrescente `--duracao 120`. Nesse teste, a passagem estimada começa cerca de 1h02min24s após a saída e termina cerca de 1h03min09s após a saída. O comparador usa a previsão da coordenada de referência da trilha na janela estimada de passagem.

## Fontes

- [Relato e pontos de interesse de Rossana Spena no Wikiloc](https://pt.wikiloc.com/trilhas-trekking/portao-pnt-pico-da-tijuca-portao-pnt-sem-pressa-64855460)
- [Plano de Manejo do Parque Nacional da Tijuca, ICMBio](https://www.gov.br/icmbio/pt-br/assuntos/biodiversidade/unidade-de-conservacao/unidades-de-biomas/mata-atlantica/lista-de-ucs/parna-da-tijuca/arquivos/parna_tijuca_pm.pdf)
- [Foto georreferenciada da escadaria, Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Escadaria_do_Pico_da_Tijuca.jpg)
