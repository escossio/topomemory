# Arquitetura

## Visão geral

topomemory organiza observação e operação em um fluxo controlado:

1. uma VM de coleta controlada executa a observação inicial;
2. as observações são registradas como eventos e relações;
3. a memória canônica consolida a identidade dos elementos;
4. a saúde operacional da rota é calculada sobre a base observada;
5. a telemetria temporal registra a evolução ao longo do tempo;
6. o grafo operacional é projetado a partir da memória e da telemetria;
7. a operação e a resposta a incidentes usam essa leitura consolidada.

O contrato formal dessa passagem da Camada 0 para a Camada 1 está documentado em [RUN_CONTRACT.md](/docs/RUN_CONTRACT.md) e [INGESTION_BUNDLE.md](/docs/INGESTION_BUNDLE.md).

## Ordem das camadas

- Camada 0: Ambiente de Coleta Controlado
- Camada 1: Memória Topológica / Memória Canônica dos Elementos
- Base conceitual de dependências do serviço
- Camada 2: Saúde Operacional da Rota
- Camada 3: Telemetria Temporal / Prometheus
- Camada 4: Projeção e Geração do Grafo Operacional
- Camada 5: Operação, Incidente e Ação

## Relação entre as camadas

- A Camada 0 produz coleta disciplinada e reprodutível.
- A Camada 1 consolida elementos e relações canônicas.
- A base conceitual de dependências do serviço alimenta a Camada 2, mas não é uma camada executável separada.
- A saída oficial da Camada 0 para a Camada 1 é o `ingestion_bundle`.
- A Camada 2 traduz observação e dependência em leitura operacional da rota.
- A Camada 3 preserva o tempo como dimensão analítica própria.
- A Camada 4 projeta o grafo operacional; ela não define a verdade, apenas a representa.
- A Camada 5 consome as leituras anteriores para ação, incidente e resposta.

## Distinções importantes

- Observação: sinais brutos e relações coletadas.
- Memória: identidade canônica dos elementos observados.
- Saúde: condição operacional agregada da rota.
- Tempo: evolução temporal da telemetria.
- Grafo: projeção derivada do modelo canônico.
- Operação: decisão e ação sobre o sistema.

## Camada 1 mínima

A primeira implementação relacional da Camada 1 normaliza as observações do `ingestion_bundle` em `observed_element` e `observed_relation`.

- O vínculo com `bundle_id` e `run_id` permanece explícito.
- `element_index` e `relation_index` preservam a identidade local dentro do bundle.
- `raw_json` permanece disponível para auditoria.
- O detalhe da consolidação canônica mínima fica em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md).

## Identidade canônica mínima

A Camada 1 mínima já consolidou um baseline determinístico e conservador. Ela cobre IP público por `canonical_ip`, hostname/PTR forte quando não há IP canônico e IP privado por assinatura determinística local. O contrato completo, as limitações e os tipos de decisão ficam em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md).

## Enriquecimento externo futuro

Há também uma frente futura de enriquecimento público de BGP para apoiar contexto de ASN, prefixo e visibilidade global.

- fontes como RIPEstat, RouteViews e BGPKIT podem complementar leituras futuras
- isso não substitui a observação local da Camada 0
- isso não redefine a verdade canônica da Camada 1
- a Camada 0 continua sendo a verdade observada local
- a Camada 1 continua sendo a memória topológica canônica
- o enriquecimento BGP público é um módulo auxiliar futuro, não um componente ativo
- o detalhe da frente fica em [BGP_PUBLIC_ENRICHMENT.md](/docs/BGP_PUBLIC_ENRICHMENT.md)

## Interface formal da Camada 0

- O run de coleta é a unidade mínima da Camada 0.
- O `ingestion_bundle` é a interface oficial de entrada da Camada 1.
- Artefatos soltos, por si só, não constituem o contrato de ingestão.
