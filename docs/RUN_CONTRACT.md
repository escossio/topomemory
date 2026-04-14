# Contrato do run de coleta

## O que é um run

Run é a unidade mínima de coleta controlada da Camada 0. Ele registra uma execução delimitada, auditável e repetível de observação sobre um alvo específico.

## Papel do run na Camada 0

- organizar a execução da coleta
- amarrar observação, contexto e evidência
- produzir um pacote estruturado para a Camada 1
- impedir que a Camada 1 precise inferir contexto a partir de artefatos soltos

## Coletor oficial inicial

A VM `10.45.0.4` é o coletor oficial inicial. Todo contrato de run parte desse ambiente como origem controlada de observação.

## Identidade mínima do run

Todo run deve carregar, no mínimo, os seguintes campos:

- `run_id`: identificador único do run
- `collector_id`: identificador da VM ou coletor responsável
- `target_type`: tipo do alvo observado
- `target_value`: valor concreto do alvo
- `service_hint`: pista funcional do serviço relacionado
- `scenario`: cenário funcional da coleta
- `started_at`: início do run
- `finished_at`: fim do run
- `run_status`: estado final do run
- `collection_health`: leitura da qualidade da coleta

## Tipos de entrada possíveis

O `target_type` pode representar:

- domínio ou URL
- serviço lógico
- endpoint conhecido

O `target_value` deve ser o valor operacional concreto correspondente ao tipo escolhido.

## Importância do cenário funcional

O `scenario` explica por que o run existe. Ele orienta quais sinais fazem sentido coletar, quais ferramentas podem ser usadas e o que a Camada 1 pode esperar do pacote final.

## Ferramentas possíveis de coleta

A Camada 0 pode usar, conforme o cenário:

- browser
- devtools/network
- dns
- mtr
- traceroute
- tcpdump
- curl/check

## Artefatos mínimos

Um run deve produzir, no mínimo:

- manifesto do run
- inventário de artefatos gerados
- observações estruturadas
- relações observadas, quando existirem
- leitura de `collection_health`

Artefatos brutos, capturas e saídas auxiliares podem existir, mas não são a interface oficial de entrada da Camada 1.

## Manifesto do run

O manifesto do run é o resumo oficial da execução. Ele consolida identidade, contexto, tempo, estado final e referência aos artefatos relevantes.

Ele deve permitir responder:

- o que foi observado
- em qual cenário
- por qual coletor
- quando começou e terminou
- qual foi o estado final
- qual foi o nível de saúde da coleta

## Estados possíveis

O `run_status` pode ser:

- `success`: coleta concluída com pacote apto para ingestão
- `partial`: coleta útil, mas incompleta
- `failed`: coleta insuficiente ou inválida para ingestão confiável

## Regra sobre falha parcial

Falha parcial não invalida automaticamente o run. Se houver evidência suficiente e contexto confiável, o resultado pode seguir para ingestão parcial ou revisão manual.

## collection_health

`collection_health` resume a qualidade operacional do que foi coletado.

Valores de referência:

- `healthy`: observação suficiente e consistente para ingestão
- `degraded`: observação útil, mas com lacunas ou ruído
- `blocked`: observação insuficiente para formar um pacote confiável

## O que a Camada 1 pode assumir

Ao receber um run válido, a Camada 1 pode assumir que:

- o contexto do alvo está explícito
- o coletor é conhecido
- o cenário funcional está declarado
- o tempo do run está delimitado
- os artefatos relevantes foram manifestados
- a qualidade da coleta foi classificada
- a ingestão pode começar sem reconstituir o run a partir de arquivos soltos

