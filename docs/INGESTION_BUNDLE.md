# Ingestion bundle

## Definição

`ingestion_bundle` é o pacote oficial de entrada da Camada 1. Ele é a única interface suportada entre a Camada 0 e a Camada 1.

## Regra oficial

- a Camada 0 entrega `ingestion_bundle`
- a Camada 1 consome somente esse bundle como porta oficial de entrada
- artefatos soltos não são interface oficial de ingestão

## Blocos mínimos

### `run_context`

Identidade e contexto do run de coleta.

Inclui, no mínimo:

- `run_id`
- `collector_id`
- `target_type`
- `target_value`
- `service_hint`
- `scenario`
- `started_at`
- `finished_at`
- `run_status`
- `collection_health`

### `observed_elements`

Lista dos elementos observados no run.

Representa entidades observadas em forma estruturada, ainda sem assumir identidade canônica final.

### `observed_relations`

Lista das relações observadas entre elementos.

Representa vínculos coletados, não necessariamente consolidados como verdade canônica.

### `artifacts_manifest`

Inventário dos artefatos associados ao run.

Deve apontar o que foi gerado, para que serve e qual é a relevância de cada item.

### `ingestion_confidence`

Leitura da confiança de ingestão do bundle.

Ela indica se o pacote está apto para:

- ingestão mínima
- ingestão completa
- rejeição

## O que cada bloco representa

- `run_context`: origem, escopo e estado do run
- `observed_elements`: coisas observadas
- `observed_relations`: relações observadas
- `artifacts_manifest`: evidências e materiais associados
- `ingestion_confidence`: grau de confiança para consumo pela Camada 1

## O que a Camada 1 pode assumir

Ao consumir um `ingestion_bundle`, a Camada 1 pode assumir que:

- o contexto do run é confiável e delimitado
- os elementos observados já estão minimamente organizados
- as relações observadas já estão explicitadas
- os artefatos relevantes já foram inventariados
- existe uma indicação clara do nível de confiança para ingestão

## O que a Camada 1 não deve precisar fazer

A Camada 1 não deve precisar:

- descobrir o contexto do run em arquivos dispersos
- reconstruir o cenário funcional do zero
- inferir o coletor responsável
- adivinhar quais artefatos pertencem ao run
- tratar artefatos brutos como contrato de entrada

## Níveis de ingestão

### Mínima

Há contexto suficiente para registrar elementos e relações essenciais sem perda de rastreabilidade.

### Completa

Há contexto, evidência e inventário suficientes para consumir o bundle com alta confiança.

### Rejeitada

O bundle não é confiável o bastante para ingestão disciplinada.

## Consequência prática

O `ingestion_bundle` é a fronteira formal entre observação controlada e memória canônica. A Camada 1 não deve operar diretamente sobre a saída bruta da Camada 0 sem esse pacote.

