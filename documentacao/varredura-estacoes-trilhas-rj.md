# Trilhas RJ — varredura de estações pluviométricas

## Resultado e arquivos

A análise cobre os **126 registros** do catálogo. Para **125 trilhas com coordenadas** há pelo menos um candidato geográfico no Cemaden com acumulado publicado na captura. Para as **10 trilhas cadastradas no município do Rio de Janeiro**, foram ranqueadas também as estações municipais do Alerta Rio. A trilha `CGO-OUT-002` ficou sem candidatos devido à ausência de coordenadas.

- [vinculos-trilhas-estacoes.csv](vinculos-trilhas-estacoes.csv) contém uma linha por trilha, inclusive a pendência sem coordenadas.
- [inventario-estacoes-pluviometricas-rj.csv](inventario-estacoes-pluviometricas-rj.csv) registra 33 estações do Alerta Rio e 353 pluviômetros do Cemaden no RJ. Desses 353, 210 tinham status 0 e acumulado numérico não negativo na captura.
- A atualização declarada pelo painel do Cemaden foi **15/11/2026 às 11:04:41 UTC (08:04:41 no RJ)**. Esse é o horário do conjunto publicado. A resposta não informa o instante da última leitura nem a completude das 24 horas de cada estação.
- O inventário do Alerta Rio usa a tabela oficial de coordenadas do relatório anual de 2023. A camada de zonas e as leituras de 24 horas não puderam ser extraídas nesta rodada. Os candidatos municipais são provisórios, sujeitos à confirmação da zona, da localização atual e da série.

## Critério de associação e leitura do CSV

As estações foram ranqueadas pela distância de Haversine ao ponto de referência do catálogo. A distância é em linha reta. Os campos `min_gpx_km` e `max_gpx_km` indicam as distâncias mínima e máxima aos vértices do GPX, úteis para identificar percursos que se afastam da estação ao longo do trajeto.

| Grupo de campos | Interpretação |
|---|---|
| `cemaden_geografica_*` | Estação mais próxima no inventário do painel, inclusive quando seu acumulado está ausente. |
| `cemaden_principal_*` | Candidata mais próxima entre estações com status 0 e acumulado publicado na captura. |
| `cemaden_reserva_*` | Segunda candidata segundo o mesmo critério. Não combinar os acumulados das duas estações. |
| `alerta_rio_principal_*` e `alerta_rio_reserva_*` | Primeira e segunda mais próximas entre as estações municipais do relatório. Os prefixos indicam posição no ranking. |
| `*_codigo` e `*_id` | Código da estação no provedor e, quando disponível, ID interno. Preservar códigos como texto, inclusive zeros iniciais. |
| `*_acumulado_24h_mm` | Valor da captura do painel. Célula vazia indica ausência. Zero representa um valor publicado. |

A proximidade gera candidatos para revisão. Para aprovar um vínculo, conferir zona oficial na capital, representatividade do relevo e do trajeto, persistência da cobertura e horário da última leitura. A distância máxima ao GPX ajuda a identificar casos em que um único pluviômetro pode representar mal parte da rota. Em travessias de água, a bacia contribuinte também merece verificação.

## Cobertura preliminar por município

A faixa abaixo mede a distância ao ponto de referência, usando a candidata Cemaden com acumulado publicado na captura. Ela descreve o ranking e não constitui um critério de aceitação meteorológica.

| Município | Trilhas | Com candidata | Faixa de distância |
|---|---:|---:|---:|
| Angra dos Reis | 9 | 9 | 0,27–3,46 km |
| Arraial do Cabo | 10 | 10 | 31,86–38,70 km |
| Campos dos Goytacazes | 8 | 7 | 6,78–21,26 km |
| Itatiaia | 12 | 12 | 6,72–21,76 km |
| Mangaratiba | 8 | 8 | 1,72–5,12 km |
| Niterói | 9 | 9 | 1,22–3,61 km |
| Nova Friburgo | 9 | 9 | 0,11–1,82 km |
| Paraty | 8 | 8 | 1,22–11,26 km |
| Petrópolis | 8 | 8 | 0,93–2,48 km |
| Rio Bonito | 7 | 7 | 0,14–1,94 km |
| Rio de Janeiro | 10 | 10 | 2,19–22,36 km |
| Santa Maria Madalena | 8 | 8 | 1,44–2,92 km |
| Saquarema | 6 | 6 | 3,71–6,37 km |
| Teresópolis | 14 | 14 | 0,65–5,89 km |

- **37 trilhas** tinham como estação Cemaden mais próxima uma estação diferente da primeira candidata com leitura publicada. **43** ficaram a mais de 5 km da primeira candidata com leitura, incluindo **30** a mais de 10 km. Esses cortes servem para organizar a revisão.
- **Arraial do Cabo.** A estação Centro, em Cabo Frio, foi a mais próxima geograficamente para os dez registros, mas apareceu sem acumulado. A candidata com leitura ficou em Araruama para os dez. Manter chuva observada pendente até validar uma estação representativa.
- **Itatiaia.** Maromba foi a candidata geográfica em nove percursos e estava sem acumulado na captura. A candidata com leitura nesses casos estava em Resende. O contraste entre distâncias e o relevo faz desses vínculos prioridade de revisão.
- **Capital.** Começar pelo ranking do Alerta Rio. Para o Pico da Tijuca (`RIO-PNT-001`), Alto da Boa Vista (28) fica a 0,686 km da referência. Para Piabas–Prainha (`RIO-PEPB-001`), Grota Funda (25) fica a 1,311 km. Ambos ainda dependem da confirmação da zona e das leituras.

## O que o sistema precisa para usar a chuva observada

| Campo ou verificação | Como usar |
|---|---|
| Rede, código, coordenadas e método do vínculo | Selecionar a estação revisada e manter a rastreabilidade do valor. |
| Horário de referência e duração da janela | Usar um acumulado de 24 h com fim conhecido ou calcular a partir de intervalos completos e não sobrepostos. |
| Precipitação em mm | Conservar o valor bruto e registrar se veio pronto do provedor ou se foi agregado pelo projeto. |
| Última medição e cobertura | Distinguir série atual, atrasada, incompleta e indisponível. A data da publicação do painel é metadado do conjunto. |
| Origem e horário de coleta | Permitir auditoria de uma consulta e reprodução em cenários gravados. |

**Alerta Rio.** Obter a camada oficial de zonas pluviométricas e associar cada ponto à estação da zona. Usar o portal de séries por estação e ano para validar uma amostra histórica. Para a operação, verificar um canal de leituras recentes com carimbo de tempo. Se forem usados incrementos de 15 minutos, 24 horas alinhadas exigem 96 intervalos consecutivos. Confirmar o intervalo e a unidade da série antes de agregar.

**Cemaden.** O arquivo do mapa serve para inventário e triagem do acumulado publicado. Para verificar recência individual e lacunas, obter séries do Mapa Interativo ou consultar a Plataforma de Entrega de Dados com acesso autorizado. Distinguir acumulados móveis de incrementos. Quando o valor publicado estiver ausente ou a série não oferecer a janela necessária, marcar a chuva observada como indisponível e apresentar separadamente a previsão do percurso.

## Fontes

- [Relatório anual do Alerta Rio, tabela 1](https://www.sistema-alerta-rio.com.br/wp-content/uploads/2016/07/RELATORIO_ANUAL_CHUVA_2023.pdf)
- [Camadas oficiais de estações e zonas do Alerta Rio](https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Geotecnia/Estacoes_AlertaRio/FeatureServer)
- [Portal de séries do Alerta Rio](https://websempre.rio.rj.gov.br/dados/pluviometricos/plv/)
- [Mapa Interativo do Cemaden](https://mapainterativo.cemaden.gov.br/)
- [Dados públicos do mapa do Cemaden](https://resources.cemaden.gov.br/dados/311_24.json)
- [Plataforma de Entrega de Dados do Cemaden](https://sws.cemaden.gov.br/)
