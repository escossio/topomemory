# VM coletora `10.45.0.4`

## Papel na arquitetura

Esta VM é o ambiente oficial inicial de coleta controlada. Ela existe para produzir observações disciplinadas, com baixo acoplamento e rastreabilidade clara.

## O que deve observar

- elementos de rede e serviço relevantes para a rota
- relações entre elementos observados
- sinais necessários para memória canônica e saúde operacional
- dados suficientes para alimentar a telemetria temporal e a projeção do grafo

## Conceito de run de coleta

Um run de coleta é uma execução controlada, identificável e repetível que registra o que foi observado, quando foi observado e em qual contexto. O run é a unidade de rastreio da Camada 0.

O contrato formal desse run está documentado em [RUN_CONTRACT.md](/docs/RUN_CONTRACT.md) e a saída oficial para a Camada 1 está documentada em [INGESTION_BUNDLE.md](/docs/INGESTION_BUNDLE.md).

## Por que ela é Camada 0

- é o ponto de entrada da observação controlada
- não decide a verdade canônica
- não resolve identidade final de elementos
- não calcula saúde operacional sozinha
- apenas inicia e registra a coleta inicial

## Origem oficial inicial

`10.45.0.4` é a origem oficial inicial de coleta controlada para bootstrap do sistema e validação das camadas superiores.

## Saída esperada

A VM deve produzir um `ingestion_bundle` consistente, com manifesto do run, elementos observados, relações observadas, inventário de artefatos e leitura de confiança de ingestão.
