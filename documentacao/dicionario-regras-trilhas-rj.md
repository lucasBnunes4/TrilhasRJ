# Dicionário de regras do sistema especialista Trilhas RJ

Base de conhecimento **0.5.0** · **55 regras** · **44 habilitadas no piloto experimental** · **11 em proposta**.

## Como o motor decide se uma regra é acionada

1. Para cada horário de saída, o motor seleciona as regras marcadas como **Piloto** e monta os fatos a partir da previsão, da observação validada, da duração e dos trechos cadastrados. Regras em **Proposta** têm seus critérios documentados para uma futura implementação.
2. Regras de caminhada e diagnóstico geral são verificadas uma vez por saída. As regras de trecho e o diagnóstico `DQ03` são verificados separadamente para cada segmento que tem janela de passagem calculada.
3. O motor combina as condições com **E**. A igualdade conta nos limites inclusivos (`≥` e `≤`). Uma condição falsa basta para descartar a regra, mesmo se faltar outro dado. Se nenhuma condição for falsa e faltar um fato, a regra fica não avaliável.
4. Duas exceções alteram o estado para **Fora do escopo**. A `TE01` exige caminhada de pelo menos duas horas para entrar na avaliação. A `OP02` se aplica a saídas antes do pôr do sol. A `OP04` cobre saídas no horário do pôr do sol ou depois.

**Exemplo com a `CH05`.** Uma leitura validada de 22 mm cuja janela terminou cinco horas antes da saída aciona a regra. Com os mesmos 22 mm e sete horas de diferença, o critério de horário fica fora do limite. Se a estação publicar 22 mm sem cobertura confirmada, faltam dados válidos para avaliar essa regra.

## Como interpretar o resultado

- **Acionada** — todas as condições da regra foram atendidas.
- **Critério não atingido** — pelo menos uma condição conhecida é falsa.
- **Não avaliável** — falta um dado necessário e nenhuma condição conhecida descarta a regra.
- **Fora do escopo** — a regra de queda em duas horas recebe esse estado em caminhadas com duração menor que duas horas. A regra de pôr do sol recebe esse estado quando a saída já ocorre no horário do pôr do sol ou depois.
- **Sem regra de trecho na saída** — o motor só executa as regras localizadas quando a consulta inclui um segmento com janela de passagem calculável. Condições que exigem atributos de terreno dependem da evidência cadastrada.

O motor usa o maior nível entre as regras acionadas, na ordem **Atenção < Atenção alta < Crítico**. Regras informativas não elevam esse nível. A saída também sinaliza se a avaliação ficou incompleta. Os valores quantitativos são critérios experimentais do projeto.

## Catálogo de regras

A coluna **Como aciona** descreve a decisão em linguagem direta. A coluna de condições registra os fatos e operadores usados no código. **E** exige que todas as condições sejam atendidas. **Contém algum de** exige pelo menos um atributo da lista.

### Chuva durante e antes da caminhada

| ID / versão | Fenômeno | Condições de acionamento | Como aciona | Escopo | Nível | Situação |
|---|---|---|---|---|---|---|
| `CH01` / 1.1 | Pico horário de chuva | `pico_caminhada` ≥ 5 mm por hora amostrada | Quando o pico horário de chuva na caminhada é de pelo menos 5 mm na hora amostrada. | caminhada | Atencao | Piloto |
| `CH02` / 1.1 | Pico horário de maior intensidade | `pico_caminhada` ≥ 25 mm por hora amostrada | Quando o pico horário de chuva na caminhada é de pelo menos 25 mm na hora amostrada. | caminhada | Atencao alta | Piloto |
| `CH03` / 1.1 | Chuva acumulada durante a caminhada | `chuva_caminhada` ≥ 10 mm | Quando o total previsto durante a caminhada é de pelo menos 10 mm. | caminhada | Atencao | Piloto |
| `CH04` / 1.1 | Chuva prevista nas 24 h anteriores | `chuva_24h_prevista` ≥ 20 mm | Quando o total previsto nas 24 h anteriores à saída é de pelo menos 20 mm. | caminhada | Atencao | Piloto |
| `CH05` / 1.1 | Chuva observada antes de saída próxima | `chuva_24h_observada` ≥ 20 mm **e** `idade_observacao_na_saida` ≤ 6 h | Quando o total observado de 24 h validado é de pelo menos 20 mm **e** o tempo entre o fim da observação e a saída é de no máximo 6 h. | caminhada | Atencao | Piloto |

### Condições do terreno e passagem por trechos

| ID / versão | Fenômeno | Condições de acionamento | Como aciona | Escopo | Nível | Situação |
|---|---|---|---|---|---|---|
| `TR01` / 1.1 | Chuva na passagem por escadaria | `atributos_trecho` contém algum de `escadaria` **e** `pico_trecho` ≥ 5 mm por hora amostrada | Quando o trecho tem pelo menos um destes atributos — escadaria **e** o pico horário de chuva na passagem é de pelo menos 5 mm na hora amostrada. | trecho | Atencao | Piloto |
| `TR02` / 1.1 | Pico de chuva na passagem por escadaria | `atributos_trecho` contém algum de `escadaria` **e** `pico_trecho` ≥ 25 mm por hora amostrada | Quando o trecho tem pelo menos um destes atributos — escadaria **e** o pico horário de chuva na passagem é de pelo menos 25 mm na hora amostrada. | trecho | Atencao alta | Piloto |
| `TR03` / 1.1 | Chuva antecedente e superfície exposta | `atributos_trecho` contém algum de `escadaria`, `rocha_lisa`, `solo_argiloso` **e** `chuva_24h_prevista` ≥ 20 mm | Quando o trecho tem pelo menos um destes atributos — escadaria, rocha lisa, solo argiloso **e** o total previsto nas 24 h anteriores à saída é de pelo menos 20 mm. | trecho | Atencao | Piloto |
| `TR04` / 1.1 | Chuva durante descida em piso sensível | `atributos_trecho` contém algum de `descida_ingreme` **e** `atributos_trecho` contém algum de `rocha_lisa`, `solo_argiloso`, `escadaria` **e** `pico_trecho` ≥ 5 mm por hora amostrada | Quando o trecho tem pelo menos um destes atributos — descida ingreme **e** o trecho tem pelo menos um destes atributos — rocha lisa, solo argiloso, escadaria **e** o pico horário de chuva na passagem é de pelo menos 5 mm na hora amostrada. | trecho | Atencao | Piloto |
| `TR05` / 1.1 | Chuva coincidente com travessia | `atributos_trecho` contém algum de `travessia_curso_dagua` **e** `pico_trecho` ≥ 10 mm por hora amostrada | Quando o trecho tem pelo menos um destes atributos — travessia curso dagua **e** o pico horário de chuva na passagem é de pelo menos 10 mm na hora amostrada. | trecho | Atencao alta | Piloto |
| `TR06` / 1.1 | Chuva prevista a montante | `atributos_trecho` contém algum de `travessia_curso_dagua`, `area_de_cachoeira` **e** `pico_montante` ≥ 10 mm por hora amostrada | Quando o trecho tem pelo menos um destes atributos — travessia curso dagua, area de cachoeira **e** o pico horário de chuva a montante é de pelo menos 10 mm na hora amostrada. | trecho | Atencao alta | Piloto |
| `TR07` / 1.1 | Chuva observada e terreno sensível | `atributos_trecho` contém algum de `escadaria`, `rocha_lisa`, `solo_argiloso` **e** `chuva_24h_observada` ≥ 20 mm **e** `idade_observacao_na_saida` ≤ 6 h | Quando o trecho tem pelo menos um destes atributos — escadaria, rocha lisa, solo argiloso **e** o total observado de 24 h validado é de pelo menos 20 mm **e** o tempo entre o fim da observação e a saída é de no máximo 6 h. | trecho | Atencao | Piloto |
| `TR08` / 1.1 | Coincidência sensível à duração da caminhada | `pico_trecho` < 5 mm por hora amostrada **e** `pico_trecho_duracao_alternativa` ≥ 5 mm por hora amostrada | Quando o pico horário de chuva na passagem é inferior a 5 mm na hora amostrada **e** o maior pico nas janelas de passagem com duração alternativa é de pelo menos 5 mm na hora amostrada. | trecho | Informativo | Piloto |

### Avisos oficiais de tempestade, chuva intensa e vento

| ID / versão | Fenômeno | Condições de acionamento | Como aciona | Escopo | Nível | Situação |
|---|---|---|---|---|---|---|
| `AC01` / 1.0 | Aviso oficial de chuvas intensas: potencial | `nivel_chuva_oficial` = `potencial` | Acionaria quando o nível do aviso oficial de chuva é potencial categoria. | caminhada | Atencao | Proposta |
| `AC02` / 1.0 | Aviso oficial de chuvas intensas: perigo | `nivel_chuva_oficial` = `perigo` | Acionaria quando o nível do aviso oficial de chuva é perigo categoria. | caminhada | Atencao alta | Proposta |
| `AC03` / 1.0 | Aviso oficial de chuvas intensas: grande_perigo | `nivel_chuva_oficial` = `grande_perigo` | Acionaria quando o nível do aviso oficial de chuva é grande perigo categoria. | caminhada | Critico | Proposta |
| `AT01` / 1.0 | Aviso oficial de tempestade: potencial | `nivel_tempestade_oficial` = `potencial` | Acionaria quando o nível do aviso oficial de tempestade é potencial categoria. | caminhada | Atencao | Proposta |
| `AT02` / 1.0 | Aviso oficial de tempestade: perigo | `nivel_tempestade_oficial` = `perigo` | Acionaria quando o nível do aviso oficial de tempestade é perigo categoria. | caminhada | Atencao alta | Proposta |
| `AT03` / 1.0 | Aviso oficial de tempestade: grande_perigo | `nivel_tempestade_oficial` = `grande_perigo` | Acionaria quando o nível do aviso oficial de tempestade é grande perigo categoria. | caminhada | Critico | Proposta |
| `AT04` / 1.0 | Tempestade e exposição do trecho | `nivel_tempestade_oficial` pertence a `potencial`, `perigo`, `grande_perigo` **e** `atributos_trecho` contém algum de `crista_exposta`, `cume_exposto`, `laje_exposta` | Acionaria quando o nível do aviso oficial de tempestade é um destes — potencial, perigo, grande perigo **e** o trecho tem pelo menos um destes atributos — crista exposta, cume exposto, laje exposta. | trecho | Atencao alta | Proposta |
| `AV01` / 1.0 | Aviso oficial de vento: potencial | `nivel_vento_oficial` = `potencial` | Acionaria quando o nível do aviso oficial de vento é potencial categoria. | caminhada | Atencao | Proposta |
| `AV02` / 1.0 | Aviso oficial de vento: perigo | `nivel_vento_oficial` = `perigo` | Acionaria quando o nível do aviso oficial de vento é perigo categoria. | caminhada | Atencao alta | Proposta |
| `AV03` / 1.0 | Aviso oficial de vento: grande_perigo | `nivel_vento_oficial` = `grande_perigo` | Acionaria quando o nível do aviso oficial de vento é grande perigo categoria. | caminhada | Critico | Proposta |

### Temperatura e sensação térmica

| ID / versão | Fenômeno | Condições de acionamento | Como aciona | Escopo | Nível | Situação |
|---|---|---|---|---|---|---|
| `TE01` / 1.1 | Queda prevista de temperatura | `queda_2h` ≥ 6 °C | Em caminhadas de pelo menos 120 min, quando a queda de temperatura em duas horas é de pelo menos 6 °C. | caminhada | Atencao | Piloto |
| `TE02` / 1.1 | Temperatura mínima baixa | `temp_min` ≤ 10 °C | Quando a temperatura mínima do ar é de no máximo 10 °C. | caminhada | Atencao | Piloto |
| `TE03` / 1.2 | Frio e chuva na mesma hora | `frio_com_chuva` = verdadeiro | Quando em uma mesma hora da janela, a sensação é de até 8 °C e a chuva é de pelo menos 1 mm. | caminhada | Atenção alta | Piloto |
| `TE04` / 1.1 | Sensação térmica elevada | `sensacao_max` ≥ 35 °C | Quando a sensação térmica máxima é de pelo menos 35 °C. | caminhada | Atencao | Piloto |

### Rajadas e visibilidade

| ID / versão | Fenômeno | Condições de acionamento | Como aciona | Escopo | Nível | Situação |
|---|---|---|---|---|---|---|
| `VE01` / 1.1 | Rajadas em trecho exposto | `atributos_trecho` contém algum de `crista_exposta`, `cume_exposto`, `laje_exposta` **e** `rajada_trecho` ≥ 50 km/h | Quando o trecho tem pelo menos um destes atributos — crista exposta, cume exposto, laje exposta **e** a maior rajada na passagem é de pelo menos 50 km/h. | trecho | Atencao alta | Piloto |
| `VE02` / 1.1 | Baixa visibilidade e navegação sensível | `atributos_trecho` contém algum de `navegacao_dificil`, `crista_exposta`, `cume_exposto` **e** `visibilidade_trecho` ≤ 500 m | Quando o trecho tem pelo menos um destes atributos — navegacao dificil, crista exposta, cume exposto **e** a menor visibilidade na passagem é de no máximo 500 m. | trecho | Atencao alta | Piloto |
| `VE03` / 1.0 | Rajada elevada no percurso | `rajada_max` ≥ 50 km/h | Quando a maior rajada na caminhada é de pelo menos 50 km/h. | caminhada | Atencao | Piloto |
| `VE04` / 1.0 | Visibilidade reduzida no percurso | `visibilidade_min` ≤ 500 m | Quando a menor visibilidade na caminhada é de no máximo 500 m. | caminhada | Atencao | Piloto |

### Acesso e luz do dia

| ID / versão | Fenômeno | Condições de acionamento | Como aciona | Escopo | Nível | Situação |
|---|---|---|---|---|---|---|
| `OP01` / 1.0 | Interdição oficial aplicável | `interdicao_confirmada` = verdadeiro | Acionaria quando há interdição oficial confirmada. | caminhada | Critico | Proposta |
| `OP02` / 1.1 | Retorno após o pôr do sol | `minutos_pos_por_do_sol` > 0 min | Para saída antes do pôr do sol, quando o tempo de retorno após o pôr do sol é superior a 0 min. | caminhada | Atencao | Piloto |

### Cobertura e diagnóstico

| ID / versão | Fenômeno | Condições de acionamento | Como aciona | Escopo | Nível | Situação |
|---|---|---|---|---|---|---|
| `DQ01` / 1.1 | Previsão parcial na caminhada | `cobertura_caminhada` > 0 % **e** `cobertura_caminhada` < 100 % | Quando a cobertura da previsão na caminhada é superior a 0% **e** a cobertura da previsão na caminhada é inferior a 100%. | diagnóstico | Informativo | Piloto |
| `DQ02` / 1.1 | Caminhada fora da série disponível | `cobertura_caminhada` = 0 % | Quando a cobertura da previsão na caminhada é 0 %. | diagnóstico | Informativo | Piloto |
| `DQ03` / 1.1 | Cobertura insuficiente no trecho | `cobertura_trecho` < 100 % | Quando a cobertura da previsão na passagem é inferior a 100%. | diagnóstico | Informativo | Piloto |

### Regras acrescentadas na versão 0.5.0

| ID | Fenômeno | Condições | Como aciona | Escopo | Nível | Conselho |
|---|---|---|---|---|---|---|
| `TE05` | Frio em travessia com imersão | `atributos_trecho` contém algum de `travessia_com_imersao` **e** `sensacao_min` ≤ 8 °C | Quando o trecho tem pelo menos um destes atributos — travessia com imersao **e** a sensação térmica mínima é de no máximo 8 °C. | trecho | atenção alta | Prefira um percurso que evite entrar na água. Leve camadas de isolamento e roupa seca protegida da água. |
| `TE06` | Frio com vento na mesma hora | `frio_com_vento` = verdadeiro | Quando em uma mesma hora da janela, a sensação é de até 8 °C e a rajada é de pelo menos 40 km/h. | caminhada | atenção alta | Agasalhe-se em camadas e leve proteção impermeável e uma muda seca. Se houver confusão ou fala arrastada após exposição ao frio, interrompa a caminhada e acione socorro. |
| `TE07` | Sensação térmica muito elevada | `sensacao_max` ≥ 40 °C | Quando a sensação térmica máxima é de pelo menos 40 °C. | caminhada | atenção alta | Adie a saída para um horário mais fresco. Prefira um horário mais fresco. Leve água, beba regularmente e planeje pausas à sombra. |
| `TE08` | Caminhada prolongada em condições de calor | `sensacao_max` ≥ 35 °C **e** `duracao_min` ≥ 120 min | Quando a sensação térmica máxima é de pelo menos 35 °C **e** a duração planejada é de pelo menos 120 min. | caminhada | atenção | Prefira um horário mais fresco. Leve água, beba regularmente e planeje pausas à sombra. |
| `TE09` | Calor em trecho exposto ou de subida | `sensacao_max` ≥ 35 °C **e** `atributos_trecho` contém algum de `exposto_ao_sol`, `subida_ingreme` | Quando a sensação térmica máxima é de pelo menos 35 °C **e** o trecho tem pelo menos um destes atributos — exposto ao sol, subida ingreme. | trecho | atenção alta | Evite que a subida ou o trecho exposto coincida com o pico de calor. Prefira um horário mais fresco. Leve água, beba regularmente e planeje pausas à sombra. |
| `TE10` | Temperatura do ar muito baixa | `temp_min` ≤ 5 °C | Quando a temperatura mínima do ar é de no máximo 5 °C. | caminhada | atenção alta | Agasalhe-se em camadas e leve proteção impermeável e uma muda seca. Se houver confusão ou fala arrastada após exposição ao frio, interrompa a caminhada e acione socorro. |
| `TE11` | Temperatura do ar elevada | `temp_max` ≥ 35 °C | Quando a temperatura máxima do ar é de pelo menos 35 °C. | caminhada | atenção | Prefira um horário mais fresco. Leve água, beba regularmente e planeje pausas à sombra. |
| `SO01` | Exposição solar com índice UV elevado | `uv_max` ≥ 3 índice | Quando o índice UV máximo é de pelo menos 3. | caminhada | atenção | Use protetor solar, chapéu e óculos com proteção UV. Reaplique o protetor conforme as instruções do produto. |
| `SO02` | Índice UV muito alto | `uv_max` ≥ 8 índice | Quando o índice UV máximo é de pelo menos 8. | caminhada | atenção alta | Evite o horário de maior radiação e procure sombra nas pausas. Use protetor solar, chapéu e óculos com proteção UV. Reaplique o protetor conforme as instruções do produto. |
| `MT01` | Tempestade na previsão horária | `tempestade_prevista` = verdadeiro | Quando há pelo menos uma hora na janela com código WMO 95, 96, 97 ou 99. | caminhada | crítico | Adie a caminhada. Se ouvir trovão, procure uma edificação fechada ou um veículo fechado com teto metálico. Evite árvores isoladas e saliências rochosas. Aguarde pelo menos 30 minutos após o último trovão antes de voltar à área aberta. |
| `MT02` | Granizo associado a tempestade | `granizo_previsto` = verdadeiro | Quando há pelo menos uma hora na janela com código WMO 96 ou 99. | caminhada | crítico | Adie a caminhada. Se ouvir trovão, procure uma edificação fechada ou um veículo fechado com teto metálico. Evite árvores isoladas e saliências rochosas. Aguarde pelo menos 30 minutos após o último trovão antes de voltar à área aberta. |
| `MT03` | Tempestade durante a passagem por trecho exposto | `tempestade_prevista` = verdadeiro **e** `atributos_trecho` contém algum de `crista_exposta`, `cume_exposto`, `laje_exposta` | Quando há pelo menos uma hora na janela com código WMO 95, 96, 97 ou 99 **e** o trecho tem pelo menos um destes atributos — crista exposta, cume exposto, laje exposta. | trecho | crítico | Adie a caminhada. Se ouvir trovão, procure uma edificação fechada ou um veículo fechado com teto metálico. Evite árvores isoladas e saliências rochosas. Aguarde pelo menos 30 minutos após o último trovão antes de voltar à área aberta. |
| `VE05` | Rajada muito forte na caminhada | `rajada_max` ≥ 70 km/h | Quando a maior rajada na caminhada é de pelo menos 70 km/h. | caminhada | atenção alta | Adie a saída ou escolha outro percurso. Confira os avisos oficiais de vento. |
| `VE06` | Rajada muito forte em terreno exposto | `rajada_trecho` ≥ 70 km/h **e** `atributos_trecho` contém algum de `crista_exposta`, `cume_exposto`, `laje_exposta` | Quando a maior rajada na passagem é de pelo menos 70 km/h **e** o trecho tem pelo menos um destes atributos — crista exposta, cume exposto, laje exposta. | trecho | crítico | Adie a passagem pelo trecho exposto enquanto persistir a previsão de rajadas fortes. |
| `VE07` | Visibilidade muito limitada | `visibilidade_min` ≤ 100 m | Quando a menor visibilidade na caminhada é de no máximo 100 m. | caminhada | atenção alta | Considere adiar ou escolher um percurso conhecido e sinalizado. Se perder a referência do caminho, interrompa o avanço e reavalie a navegação. |
| `OP03` | Saída antes do nascer do sol | `saida_antes_do_nascer` = verdadeiro | Quando a saída ocorre antes do nascer do sol. | caminhada | atenção | Prefira sair após o nascer do sol. Se a saída no escuro for planejada, leve lanterna de cabeça e bateria reserva. |
| `OP04` | Saída ao pôr do sol ou depois | `saida_apos_por_do_sol` = verdadeiro | Quando a saída ocorre no horário do pôr do sol ou depois. | caminhada | atenção alta | Prefira reagendar para um horário diurno. Em uma saída noturna planejada, leve lanterna de cabeça e bateria reserva. |
| `OP05` | Margem de luz reduzida no retorno | `margem_luz_min` ≥ 0 min **e** `margem_luz_min` ≤ 30 min | Quando a margem de luz no retorno é de pelo menos 0 min **e** a margem de luz no retorno é de no máximo 30 min. | caminhada | atenção | Antecipe a saída para incluir margem de retorno antes do pôr do sol. Leve uma lanterna. |
| `TR09` | Chuva intensa a montante de travessia | `atributos_trecho` contém algum de `travessia_curso_dagua`, `travessia_com_imersao`, `area_de_cachoeira` **e** `pico_montante` ≥ 25 mm por hora amostrada | Quando o trecho tem pelo menos um destes atributos — travessia curso dagua, travessia com imersao, area de cachoeira **e** o pico horário de chuva a montante é de pelo menos 25 mm na hora amostrada. | trecho | atenção alta | Prefira um percurso sem essa travessia. Se houver correnteza forte ou subida rápida da água, não atravesse e afaste-se do leito. |

O conselho da TE03 orienta agasalho em camadas, impermeável e uma muda seca. As regras MT usam códigos previstos pelo modelo. Os avisos oficiais continuam nas regras AT, AC e AV em proposta. Para travessias com imersão, o atributo deve ser registrado com evidência no trecho.

## Dicionário dos fatos

| Fato | Unidade | Definição |
|---|---|---|
| `pico_caminhada` | mm por hora amostrada | Maior total de uma hora que sobrepõe a caminhada. Usar pico_horario_na_cobertura_disponivel.chuva_mm de cenarios[*]. |
| `chuva_caminhada` | mm | Total proporcional à sobreposição durante a caminhada, com cobertura integral. Usar chuva_prevista_estimada_mm de cenarios[*]. |
| `pico_trecho` | mm por hora amostrada | Maior total de uma hora que se sobrepõe à passagem do trecho documentado. Usar trecho.previsao.pico_horario_na_cobertura_disponivel.chuva_mm. |
| `chuva_24h_prevista` | mm | Total de previsao_24h_antes_da_saida, exatamente 24 h anteriores à saída e cobertura integral. |
| `chuva_24h_observada` | mm | Usar chuva_observada_24h.acumulado_mm quando estado=disponivel e cobertura integral confirmada. Preservar a janela efetiva da estação e informar a idade da leitura. |
| `idade_observacao_na_saida` | h | Diferença entre a saída e o fim da janela observada. Futuro da observação deve ser tratado como indisponível. |
| `atributos_trecho` | lista | Atributos localizados com evidência identificável e passagem estimável. Evidência atualmente documentada para a escadaria piloto; a ingestão estruturada é necessária. |
| `cobertura_caminhada` | % | Percentual retornado no cenário, incluindo 0 se a fonte consultada não cobrir a caminhada. |
| `cobertura_trecho` | % | Percentual de cobertura da previsão retornado para o trecho. |
| `distancia_passagem` | km | Distância acumulada do trecho, com identificação de ida ou volta. |
| `nivel_tempestade_oficial` | categoria | Maior nível oficial entre avisos de tempestade que intersectam simultaneamente o GPX e a caminhada. Normalizar como potencial, perigo ou grande_perigo. Sem aviso só com consulta de cobertura confirmada; se não, usar nulo. |
| `nivel_chuva_oficial` | categoria | Idem para aviso de chuvas intensas. |
| `nivel_vento_oficial` | categoria | Idem para aviso de vento. |
| `interdicao_confirmada` | booleano | Comunicado vigente do órgão gestor que abrange a trilha ou acesso indispensável. Ausência só quando a fonte consultada permitir confirmação. |
| `pico_montante` | mm por hora amostrada | Maior acumulado horário previsto na bacia a montante da travessia, em células da bacia contribuinte, nas 6 h anteriores à passagem até seu término, com cobertura espacial e temporal validada. |
| `temp_min` | °C | Mínima da temperatura prevista no intervalo da caminhada. |
| `queda_2h` | °C | Maior diferença T(t)-T(t+2h) dentro da caminhada. Aplicável apenas se a caminhada durar pelo menos 2 h. |
| `sensacao_min` | °C | Mínima prevista de apparent_temperature durante a caminhada. |
| `sensacao_max` | °C | Máxima prevista de apparent_temperature durante a caminhada. |
| `rajada_trecho` | km/h | Maior rajada horária que se sobrepõe à passagem pelo trecho, conforme a convenção da fonte. |
| `visibilidade_trecho` | m | Menor visibilidade prevista durante a passagem, com amostragem espacial e temporal declaradas. |
| `minutos_pos_por_do_sol` | min | Maior entre zero e minutos entre o pôr do sol local e o retorno estimado para a caminhada diurna. |
| `pico_trecho_duracao_alternativa` | mm por hora amostrada | Pico horário de precipitação no trajeto estimado após recalcular a passagem com duração 20% menor ou maior. Usar o maior pico das duas alternativas com cobertura integral. |
| `rajada_max` | km/h | Rajada elevada no percurso na célula de referência durante a caminhada. |
| `visibilidade_min` | m | Visibilidade reduzida no percurso na célula de referência durante a caminhada. |
| `frio_com_chuva` | booleano | Sensação térmica de até 8 °C e chuva amostrada de pelo menos 1 mm na mesma hora que coincide com a janela. |
| `frio_com_vento` | booleano | Sensação térmica de até 8 °C e rajada amostrada de pelo menos 40 km/h na mesma hora que coincide com a janela. |
| `temp_max` | °C | Temperatura máxima prevista na janela. |
| `uv_max` | índice | Maior índice UV horário que coincide com a janela. |
| `tempestade_prevista` | booleano | Detecção de código WMO horário 95, 96, 97 ou 99 dentro da janela. |
| `granizo_previsto` | booleano | Detecção de código WMO horário 96 ou 99 dentro da janela. |
| `duracao_min` | min | Duração planejada da caminhada. |
| `saida_antes_do_nascer` | booleano | Saída anterior ao nascer do sol da data local. |
| `saida_apos_por_do_sol` | booleano | Saída no horário do pôr do sol ou depois dele. |
| `margem_luz_min` | min | Minutos do retorno estimado até o pôr do sol para saída diurna. Valor negativo indica retorno após o pôr do sol. |

## Cobertura e fontes de dados

- Os acumulados e os extremos usados pelas regras exigem cobertura integral da janela pertinente. As regras de diagnóstico usam o percentual de cobertura.
- O pico de chuva representa o total da hora amostrada que coincide com a janela. O acumulado rateia horas parcialmente sobrepostas, assumindo distribuição uniforme dentro da hora.
- A chuva observada e a prevista são fatos separados. A observação exige cobertura confirmada e o motor verifica a idade da medição em relação à saída nas regras que usam esse critério.
- A previsão usa a coordenada de referência da trilha. Nas regras localizadas, o sistema recorta a previsão pela janela de passagem. A chuva a montante exige amostragem da área contribuinte validada para o trecho.
- As regras de avisos oficiais e interdição estão em proposta e ficam fora da execução atual. A matriz registra seus critérios declarados na base.

## Referências registradas na base

- [Base de conhecimento](../conhecimento/regras.json)
- [Motor de inferência](../src/inferencia.py)
- [Cadastro de trechos](../conhecimento/trechos.json)
- [Open-Meteo, convenções das variáveis horárias](https://open-meteo.com/en/docs)
- [INMET, avisos especiais](https://portal.inmet.gov.br/servicos/avisos-especiais)
- [Ministério do Turismo, Turismo Seguro em Ambientes Naturais](https://www.gov.br/turismo/pt-br/centrais-de-conteudo-/publicacoes/consumidor-turista/consumidor-turista-no-5-turismo-seguro-em-ambientes-naturais.pdf)
- [ICMBio, Plano de Manejo do Parque Nacional da Tijuca](https://www.gov.br/icmbio/pt-br/assuntos/biodiversidade/unidade-de-conservacao/unidades-de-biomas/mata-atlantica/lista-de-ucs/parna-da-tijuca/arquivos/parna_tijuca_pm.pdf)
- [Planejamento Trilhas RJ](https://chatgpt.com/library?file_id=libfile_b0a71fd1cf788191a0b37df11ccce7bd&account_id=personal)
- [Alerta Rio, Termos Meteorológicos](https://www.sistema-alerta-rio.com.br/previsao-do-tempo/termosmet/)
- [CDC · Reconhecimento de hipotermia](https://www.cdc.gov/natural-disasters/psa-toolkit/recognizing-hypothermia.html)
- [CDC · Exposição a água fria](https://www.cdc.gov/natural-disasters/psa-toolkit/treating-hypothermia.html)
- [CDC · Calor e atividade física](https://www.cdc.gov/extreme-heat/risk-factors/extreme-heat-and-athletes.html)
- [NWS · Proteção contra raios](https://www.weather.gov/safety/lightning-tips)
- [OMS · Índice UV e proteção solar](https://www.who.int/news-room/questions-and-answers/item/radiation-the-ultraviolet-(uv)-index)
- [Corpo de Bombeiros · Cabeça d’água](https://www.comunicacao.pr.gov.br/external-print/pdf/node/aen/adaf01f6-2ba7-4cd1-9434-a906f6704132)
