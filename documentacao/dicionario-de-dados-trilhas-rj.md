# Dicionário de dados do Trilhas RJ

O catálogo reúne trilhas, fontes, marcadores e descrições. A integração meteorológica usa previsão horária por coordenada e precipitação observada por estação. Os quatro CSVs abaixo descrevem o esquema existente. Nas fontes externas, as tabelas indicam os campos de interesse e a estrutura proposta para a ingestão.

## 1. Catálogo Trilhas RJ

Os tipos são lógicos. Os arquivos CSV serializam os valores como texto. **PK** indica chave primária e **FK**, chave estrangeira. Campos vazios representam dados ausentes. Nomes de marcadores gravados como `null` devem ser interpretados como ausentes na importação. Datas usam ISO 8601. O campo `index` exibido em algumas prévias é gerado pelo leitor.

### trilhas.csv

Uma linha por percurso catalogado.

| Campo | Tipo ou unidade | Descrição |
|---|---|---|
| `id_trilha` | Texto · PK | Identificador interno do percurso, como `RIO-PNT-001`. |
| `nome` | Texto | Título do percurso na fonte. |
| `municipio` | Texto | Município de referência usado no agrupamento. Travessias podem cruzar limites municipais. |
| `uf` | Texto | Sigla da unidade federativa de referência, como `RJ`. |
| `pais` | Texto | País de referência. |
| `unidade_conservacao` | Texto | Unidade de conservação associada, quando identificada. |
| `modalidade` | Texto | Atividade registrada, como `Trekking`. |
| `tipo_percurso` | Texto | Formato publicado, como `Circular`, `Ida e volta` ou `Mão Única`. |
| `distancia_km` | Decimal · km | Comprimento do percurso publicado. |
| `duracao_min` | Inteiro · min | Duração total registrada ou obtida de relato ou GPX quando documentada. Pode incluir pausas e pernoites. |
| `dificuldade` | Texto | Classificação publicada pela fonte, quando disponível. |
| `ganho_elevacao_m` | Decimal · m | Soma das subidas ao longo do traçado. |
| `perda_elecavao_m` | Decimal · m | Magnitude acumulada das descidas. O nome corresponde ao cabeçalho atual do CSV. |
| `altitude_min_m` | Decimal · m | Menor altitude publicada do percurso. |
| `altitude_max_m` | Decimal · m | Maior altitude publicada do percurso. |
| `latitude_ref` | Decimal · graus | Latitude WGS 84 do ponto de referência, geralmente o primeiro ponto gravado no GPX. |
| `longitude_ref` | Decimal · graus | Longitude WGS 84 do mesmo ponto. |
| `geometria_url` | Texto | Referência ao traçado. Na base atual, pode conter um caminho relativo como `gpx/arquivo.gpx`. |

[trilhas.csv](https://chatgpt.com/library?file_id=libfile_bbd82e14e908819190843c267604b226&account_id=personal)

### fontes.csv

Uma linha por fonte vinculada a um percurso.

| Campo | Tipo | Descrição |
|---|---|---|
| `id_fonte` | Texto · PK | Identificador interno da fonte. |
| `id_trilha` | Texto · FK | Percurso em `trilhas.csv`. |
| `url` | Texto · URL | Página de origem do registro. |
| `publicador` | Texto | Plataforma ou instituição que publica o registro. |
| `tipo_fonte` | Texto | Categoria de origem, como `relato_comunitario`. |
| `autor` | Texto | Identificação pública da autoria conforme a fonte. |
| `id_externo` | Texto | Identificador do registro no publicador. Identidade externa pela combinação de `publicador` e `id_externo`. |
| `periodo_registro` | Texto `AAAA-MM` | Mês e ano da gravação informados pela fonte. |
| `data_publicacao` | Data `AAAA-MM-DD` | Data em que o registro foi publicado. |
| `data_coleta` | Data `AAAA-MM-DD` | Data em que o projeto consultou o registro. |

[fontes.csv](https://chatgpt.com/library?file_id=libfile_70d2bf27680c8191bd2e42a167385232&account_id=personal)

### ponto_interesse.csv

Uma linha por marcador publicado para a trilha.

| Campo | Tipo ou unidade | Descrição |
|---|---|---|
| `id_ponto` | Texto · PK | Identificador interno do marcador. |
| `id_fonte` | Texto · FK | Fonte do marcador em `fontes.csv`. |
| `id_trilha` | Texto · FK | Percurso em `trilhas.csv`. Deve coincidir com a trilha vinculada à fonte. |
| `nome` | Texto | Nome apresentado na página. Pode se repetir entre marcadores. |
| `tipo_ponto` | Texto | Categoria publicada, como `Cachoeira` ou `Waypoint`. |
| `altitude_m` | Decimal · m | Altitude publicada para o marcador. |

[ponto_interesse.csv](https://chatgpt.com/library?file_id=libfile_5fcaf87e7a9481919311a560d18927d1&account_id=personal)

### trilha_texto.csv

Uma linha por trecho textual ou resumo do itinerário associado a uma fonte.

| Campo | Tipo | Descrição |
|---|---|---|
| `id_texto` | Texto · PK | Identificador interno do trecho. |
| `id_fonte` | Texto · FK | Origem do texto em `fontes.csv`. |
| `id_trilha` | Texto · FK | Percurso em `trilhas.csv`. Deve coincidir com a trilha vinculada à fonte. |
| `tipo_texto` | Texto | Categoria do conteúdo, como `descricao_itinerario`. |
| `texto` | Texto | Relato parafraseado ou resumo com características do percurso. Pode alimentar a extração de atributos de terreno. |

[trilha_texto.csv](https://chatgpt.com/library?file_id=libfile_c3808f9160c08191ab9a4ab51d616947&account_id=personal)

### Arquivos GPX

Cada arquivo contém um traçado associado ao catálogo pelo ID do Wikiloc extraído de `metadata/link/@href`. O caminho é resolvido a partir da pasta dos CSVs. Um segmento pode conter vários pontos ordenados.

| Elemento | Tipo ou unidade | Uso |
|---|---|---|
| `metadata/link/@href` | URL | Identificar a fonte do traçado. |
| `trk/trkseg/trkpt/@lat` | Decimal · graus | Latitude WGS 84 do ponto gravado. |
| `trk/trkseg/trkpt/@lon` | Decimal · graus | Longitude WGS 84 do ponto gravado. |
| `trk/trkseg/trkpt/ele` | Decimal · m | Elevação do ponto gravado, quando presente. |
| `trk/trkseg/trkpt/time` | Data e hora ISO 8601 | Horário do ponto, quando disponível. A diferença entre extremos só pode ser usada após verificar a coerência dos timestamps. |
| `wpt` | Elemento GPX opcional | Marcador independente. Os arquivos inspecionados não forneceram esses elementos. |

## 2. Open-Meteo — previsão horária

A Weather Forecast API recebe latitude, longitude e a lista de variáveis em `hourly`. Para o projeto, cada registro tratado representa uma hora de validade da previsão para uma trilha. A coleta guarda a coordenada solicitada e o horário de consulta.

| Campo da API | Tipo ou unidade | Descrição |
|---|---|---|
| `latitude`, `longitude` na solicitação | Decimal · graus | Ponto de referência cadastrado para a trilha. |
| `latitude`, `longitude` na resposta | Decimal · graus | Coordenadas da célula meteorológica retornada. |
| `timezone`, `utc_offset_seconds` | Texto, inteiro · s | Fuso e deslocamento aplicados à resposta. Solicitar UTC para integração. |
| `hourly.time` | Lista de datas e horas | Horários de validade das variáveis. Cada posição corresponde à mesma posição nas listas horárias. |
| `hourly.precipitation` | Decimal · mm | Precipitação total acumulada na hora anterior ao horário informado. |
| `hourly.precipitation_probability` | Inteiro · % | Probabilidade prevista de precipitação superior a 0,1 mm na hora anterior. |
| `hourly.apparent_temperature` | Decimal · °C | Temperatura aparente no horário indicado. |
| `hourly.wind_gusts_10m` | Decimal · km/h | Rajada máxima a 10 m durante a hora anterior. |
| `hourly_units` | Objeto | Unidades retornadas para as séries horárias. |

No armazenamento, cada previsão inclui `id_trilha` (FK), `valido_em_utc`, `coletado_em_utc` e os valores horários. A combinação desses três campos identifica uma hora dentro de uma coleta. Quando a origem fornecer o horário de emissão do modelo, registrá-lo separadamente em `emitido_em_utc`. Usar o horário local na interface.

[Documentação da Weather Forecast API](https://open-meteo.com/en/docs)

## 3. Alerta Rio — estações, zonas e chuva observada

O Alerta Rio é a referência inicial para o município do Rio de Janeiro. O portal fornece séries por estação e ano, e o serviço geográfico fornece estações e zonas pluviométricas. Os nomes abaixo representam os campos **tratados pelo projeto**.

| Campo tratado | Tipo ou unidade | Descrição |
|---|---|---|
| `id_estacao_origem` | Texto | Identificador da estação no cadastro, quando disponível. Validar a correspondência com a estação da série histórica. |
| `nome_estacao` | Texto | Nome publicado da estação. |
| `latitude_estacao`, `longitude_estacao` | Decimal · graus | Coordenadas da estação, convertidas para WGS 84 na ingestão. |
| `id_zona_origem`, `geometria_zona` | Texto, polígono | Identificação e geometria da zona pluviométrica para cruzamento espacial com a trilha. |
| `observado_em_utc` | Data e hora | Horário da leitura convertido para UTC após confirmar o fuso do arquivo ou serviço utilizado. |
| `janela_min` | Inteiro · min | Intervalo representado pelo acumulado, conforme o produto consultado. |
| `chuva_mm` | Decimal · mm | Precipitação medida na estação durante o intervalo indicado. |

Calcular chuva nas 24 horas anteriores à saída com um acumulado de 24 horas válido para o horário desejado ou com leituras de intervalos menores que cubram a janela sem sobreposição. Somar acumulados móveis sobrepostos contaria parte da chuva mais de uma vez.

[Dados pluviométricos do Alerta Rio](https://websempre.rio.rj.gov.br/dados/pluviometricos/plv/) · [Camadas oficiais de estações e zonas](https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Geotecnia/Estacoes_AlertaRio/FeatureServer)

## 4. Cemaden — estações e chuva observada

O Cemaden complementa a cobertura fora da capital. O Mapa Interativo permite consultar ou solicitar dados por UF, município, mês e ano. Os registros desse canal usam UTC. A tabela descreve os campos **tratados pelo projeto**.

| Campo tratado | Tipo ou unidade | Descrição |
|---|---|---|
| `id_estacao_origem` | Texto | Código da estação no Cemaden. |
| `nome_estacao` | Texto | Nome publicado da estação. |
| `municipio_estacao`, `uf_estacao` | Texto | Município e UF da instalação, quando fornecidos. |
| `latitude_estacao`, `longitude_estacao` | Decimal · graus | Localização da estação, normalizada para WGS 84. |
| `observado_em_utc` | Data e hora | Horário em UTC informado pela fonte. |
| `janela_min` | Inteiro · min | Intervalo de acumulação definido pelo produto ou arquivo utilizado. |
| `chuva_mm` | Decimal · mm | Valor pluviométrico associado ao horário e intervalo. |

Confirmar o significado do valor e do intervalo no canal escolhido antes de calcular acumulados. A localização, a cobertura temporal e a disponibilidade de cada estação devem ser verificadas antes de vinculá-la a uma trilha.

[Mapa Interativo do Cemaden](https://www2.cemaden.gov.br/mapainterativo/) · [Documentação da Plataforma de Entrega de Dados](https://sws.cemaden.gov.br/PED/api/ui/)

## 5. Integração das bases

| Conjunto tratado | Chave e campos principais |
|---|---|
| Vínculo trilha–estação | `id_trilha` (FK), `fonte_estacao`, `id_estacao_origem`, `metodo_vinculo`, `distancia_km`, `id_zona_origem` quando aplicável e `vinculado_em_utc`. Registrar a associação por zona ou por proximidade e sua data. |
| Observação de chuva | Chave lógica `fonte_estacao + id_estacao_origem + observado_em_utc + janela_min`. Guardar `chuva_mm`, `coletado_em_utc` e referência ao arquivo ou consulta de origem. |
| Previsão horária | Chave lógica `id_trilha + valido_em_utc + coletado_em_utc`. Guardar os valores horários, as coordenadas consultadas e a origem. |
| Cenário de caminhada | `id_trilha` (FK), `saida_em_utc`, `duracao_planejada_min`, `retorno_previsto_em_utc`, chuva observada nas 24 horas anteriores, resumo da previsão durante a janela e estado de disponibilidade dos dados. |

Consultar a previsão pela coordenada da trilha. Recuperar a chuva observada pela estação vinculada e pelo horário. Uma estação representa o ponto onde foi instalada. A previsão representa a célula do modelo associada ao ponto consultado. Guardar a origem de cada valor exibido. Usar zero apenas quando a fonte indicar zero. Se a trilha estiver sem coordenadas, a estação estiver indisponível ou a série estiver incompleta, registrar a condição correspondente.
