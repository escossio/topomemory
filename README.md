# topomemory

topomemory é o núcleo documental e arquitetural para organizar coleta controlada, memória canônica, saúde operacional, consulta semântica auxiliar e projeções do grafo de operação de rotas e entregas.

## Visão geral

O projeto separa observação, memória, saúde, tempo, projeção e ação em camadas explícitas. A intenção é manter um modelo disciplinado, auditável e fácil de evoluir sem misturar telemetria bruta com verdade canônica.

## Arquitetura em camadas

- Camada 0: Ambiente de Coleta Controlado
- Camada 1: Memória Topológica / Memória Canônica dos Elementos
- Base conceitual de dependências do serviço, alimentando a Camada 2
- Camada 2: Saúde Operacional da Rota
- Camada 3: Telemetria Temporal / Prometheus
- Camada 4: Projeção e Geração do Grafo Operacional
- Camada 5: Operação, Incidente e Ação

## Componentes principais

- VM oficial de coleta inicial: `10.45.0.4`
- Banco principal: `PostgreSQL`, com `pgvector` como direção conceitual e database dedicado `topomemory`
- Prometheus: camada temporal e base de séries observáveis
- Zabbix: componente operacional de monitoramento, não o cérebro do sistema

## Status atual

Fase de bootstrap arquitetural. A Camada 0 já tem coleta real mínima validada e opera com execução remota na VM `10.45.0.4` e persistência direta no PostgreSQL oficial `10.45.0.3:5432/topomemory` via `topomemory_app`, sem túnel SSH. A Camada 1 já normaliza `observed_elements` e `observed_relations` e tem o baseline mínimo documentado em [LAYER1_BASELINE.md](/docs/LAYER1_BASELINE.md). A identidade determinística segue como fonte da verdade; a frente semântica agora existe em tabela própria, como consulta auxiliar, sem merge automático.

Uma frente futura de enriquecimento BGP público também está documentada em [BGP_PUBLIC_ENRICHMENT.md](/docs/BGP_PUBLIC_ENRICHMENT.md), como apoio externo e não como fonte primária da verdade.

A Camada 1 também já tem uma superfície de auditoria operacional em SQL e CLI para inspecionar `matched_existing_entity`, `new_entity_created` e `skipped_*` por run e bundle, sem abrir semântica.

Ela também tem uma superfície analítica de comparação entre runs para enxergar elementos comuns, exclusivos e divergência de caminho sem abrir embeddings.

## Documentação

- [Arquitetura](/docs/ARCHITECTURE.md)
- [Camadas](/docs/LAYERS.md)
- [Decisões](/docs/DECISIONS.md)
- [VM 10.45.0.4](/docs/COLLECTOR_VM_10.45.0.4.md)
- [Modelo conceitual do banco](/docs/DATABASE_CONCEPT.md)
- [Acesso ao banco](/docs/DATABASE_ACCESS.md)
- [Schema conceitual da Camada 0](/docs/COLLECTION_SCHEMA_CONCEPT.md)
- [Notas do SQL inicial da Camada 0](/docs/LAYER0_SQL_NOTES.md)
- [Bootstrap do banco](/docs/DB_BOOTSTRAP.md)
- [Bootstrap operacional da Camada 0](/docs/LAYER0_OPERATIONAL_BOOTSTRAP.md)
- [Ingestão mínima da Camada 0](/docs/LAYER0_INGESTION.md)
- [Normalização mínima da Camada 1](/docs/LAYER1_MINIMAL_NORMALIZATION.md)
- [Auditoria operacional da Camada 1](/docs/LAYER1_AUDIT.md)
- [Comparação entre runs da Camada 1](/docs/LAYER1_RUN_DIFF.md)
- [Baseline semântico auxiliar da Camada 1](/docs/LAYER1_SEMANTIC_BASELINE.md)
- [Avaliação da busca semântica da Camada 1](/docs/LAYER1_SEMANTIC_EVAL.md)
- [Contrato do run](/docs/RUN_CONTRACT.md)
- [Ingestion bundle](/docs/INGESTION_BUNDLE.md)
- [Formato do manifesto do run](/docs/RUN_MANIFEST_FORMAT.md)
- [Formato do ingestion bundle](/docs/INGESTION_BUNDLE_FORMAT.md)
- [Enriquecimento público de BGP](/docs/BGP_PUBLIC_ENRICHMENT.md)
