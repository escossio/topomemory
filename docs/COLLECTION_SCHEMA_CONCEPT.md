# Schema conceitual da Camada 0

## Propósito

Este documento fecha o schema conceitual inicial de persistência da Camada 0.
Ele não define o SQL final, mas já estabelece entidades, relações, cardinalidades e a fronteira entre campos relacionais e blocos serializados.

O objetivo é dar base estável para a evolução futura sem contradizer os contratos já publicados em:

- [docs/RUN_CONTRACT.md](/docs/RUN_CONTRACT.md)
- [docs/INGESTION_BUNDLE.md](/docs/INGESTION_BUNDLE.md)
- [docs/RUN_MANIFEST_FORMAT.md](/docs/RUN_MANIFEST_FORMAT.md)
- [docs/INGESTION_BUNDLE_FORMAT.md](/docs/INGESTION_BUNDLE_FORMAT.md)

## Fronteira da Camada 0

- A Camada 0 usa a VM `10.45.0.4` como coletor oficial inicial.
- O `run` é a unidade mínima de verdade observada.
- O `ingestion_bundle` é a única porta oficial de entrada da Camada 1.
- Artefatos brutos não entram como contrato primário da Camada 1.
- O modelo conceitual precisa ser auditável, persistível e evolutivo desde já.

## Entidades mínimas

### 1. `collector`

Papel: identifica a origem controlada da observação.

Campos conceituais mínimos:

| Campo | Papel conceitual | Persistência inicial |
| --- | --- | --- |
| `collector_id` | chave estável do coletor | relacional |
| `collector_name` | nome legível do coletor | relacional |
| `collector_type` | tipo operacional do coletor | relacional |
| `location_hint` | pista de localização física/lógica | relacional |
| `network_context` | contexto de rede associado ao coletor | JSON/JSONB candidato |
| `is_active` | indica se o coletor está habilitado | relacional |

Observações:

- O `collector_id` deve suportar a identidade oficial inicial `vm-10.45.0.4`.
- O `network_context` pode evoluir depois para estrutura mais rica sem quebrar o contrato.

### 2. `run`

Papel: registra a execução delimitada da coleta.

Campos conceituais mínimos:

| Campo | Papel conceitual | Persistência inicial |
| --- | --- | --- |
| `run_id` | chave do run | relacional |
| `collector_id` | FK para `collector` | relacional |
| `target_type` | classe do alvo observado | relacional |
| `target_value` | valor concreto do alvo | relacional |
| `service_hint` | pista funcional do serviço | relacional |
| `scenario` | cenário funcional da coleta | relacional |
| `started_at` | início do run | relacional |
| `finished_at` | fim do run | relacional |
| `run_status` | resultado final do run | relacional |
| `collection_health` | leitura da saúde da coleta | relacional |
| `summary` | resumo curto do run | relacional |
| `tags` | marcadores livres | JSON/array candidato |
| `scenario_version` | versão do cenário funcional | relacional ou texto estável |
| `notes` | observações curtas e auditáveis | JSON/array candidato |

Campos alinhados ao manifesto de referência do run, mas não normalizados nesta etapa:

- `tools_enabled`
- `tools_succeeded`
- `tools_failed`

Esses campos ficam conceitualmente ligados ao material de manifesto do run e podem permanecer serializados até a fase de SQL final.

### 3. `run_artifact`

Papel: inventaria o que o run produziu ou referenciou.

Campos conceituais mínimos:

| Campo | Papel conceitual | Persistência inicial |
| --- | --- | --- |
| `artifact_id` | chave do artefato | relacional |
| `run_id` | FK para `run` | relacional |
| `artifact_type` | tipo do artefato | relacional |
| `artifact_path` | caminho ou chave do artefato | relacional |
| `artifact_status` | estado de materialização/validade | relacional |
| `artifact_format` | formato lógico ou MIME | relacional |
| `generated_at` | instante de geração | relacional |
| `notes` | observações sobre o artefato | JSON/array candidato |

Tipos esperados de `artifact_type`:

- `browser_capture`
- `dns_capture`
- `mtr_capture`
- `traceroute_capture`
- `pcap_capture`
- `summary`
- `screenshot`
- `manifest`

Observações:

- `artifact_path` pode representar um caminho de filesystem, um objeto lógico ou uma referência de armazenamento.
- `artifact_status` deve expressar se o artefato está materializado e confiável, sem forçar ainda um enum definitivo de produção.

### 4. `ingestion_bundle`

Papel: empacota o resultado da observação para ingestão na Camada 1.

Campos conceituais mínimos:

| Campo | Papel conceitual | Persistência inicial |
| --- | --- | --- |
| `bundle_id` | chave do bundle | relacional |
| `run_id` | FK para `run` | relacional |
| `bundle_version` | versão do bundle | relacional |
| `ingestion_confidence` | nível de confiança para ingestão | relacional |
| `run_context_json` | contexto serializado do run | JSON/JSONB |
| `observed_elements_json` | elementos observados serializados | JSON/JSONB |
| `observed_relations_json` | relações observadas serializadas | JSON/JSONB |
| `artifacts_manifest_json` | inventário serializado de artefatos | JSON/JSONB |
| `created_at` | instante de criação do bundle | relacional |
| `notes` | observações do bundle | JSON/array candidato |

Valores esperados para `ingestion_confidence`:

- `minimal`
- `complete`
- `rejected`

## Relações e cardinalidades

### `collector -> run`

- Cardinalidade inicial: `1:N`
- Um `collector` pode executar vários `run`.
- Todo `run` pertence a exatamente um `collector`.
- O coletor oficial inicial continua sendo a VM `10.45.0.4`.

### `run -> run_artifact`

- Cardinalidade inicial: `1:N`
- Um `run` pode gerar ou referenciar vários `run_artifact`.
- Todo `run_artifact` pertence a exatamente um `run`.
- Artefatos não devem ser modelados como interface primária da Camada 1.

### `run -> ingestion_bundle`

- Cardinalidade lógica inicial: `1:1`
- A recomendação desta rodada é tratar o bundle como derivado único do run, com flexibilidade futura para versionamento.
- Na prática conceitual, isso significa `0..1` bundle enquanto o run está sendo fechado e `1` bundle materializado como representação oficial da ingestão.
- O `ingestion_bundle` é persistido como objeto próprio, mas não separa sua identidade do `run`.

### `ingestion_bundle -> run_artifact`

- Relação indireta, via `artifacts_manifest_json`.
- O bundle referencia os artefatos do run, mas não é dono direto deles.
- A posse conceitual dos artefatos permanece no `run`.

## O que fica relacional nesta etapa

Devem ser fortes e relacionais desde já:

- identidades primárias (`collector_id`, `run_id`, `artifact_id`, `bundle_id`)
- chaves estrangeiras (`collector_id` em `run`, `run_id` em `run_artifact`, `run_id` em `ingestion_bundle`)
- tempo de execução (`started_at`, `finished_at`, `generated_at`, `created_at`)
- estados de ciclo de vida (`run_status`, `collection_health`, `artifact_status`, `ingestion_confidence`)
- atributos de classificação estáveis (`target_type`, `target_value`, `service_hint`, `scenario`, `artifact_type`, `artifact_format`, `collector_type`, `is_active`)
- `bundle_version`, para permitir evolução futura sem ambiguidade

## O que pode permanecer em JSON nesta etapa

Podem permanecer serializados porque têm estrutura mais volátil ou porque ainda representam fronteira entre Camada 0 e Camada 1:

- `collector.network_context`
- `run.tags`
- `run.notes`
- `run_artifact.notes`
- `ingestion_bundle.run_context_json`
- `ingestion_bundle.observed_elements_json`
- `ingestion_bundle.observed_relations_json`
- `ingestion_bundle.artifacts_manifest_json`

## Decisão sobre normalização futura

Nesta rodada, `observed_elements_json` e `observed_relations_json` continuam serializados.
A normalização deles deve acontecer depois, quando a Camada 1 precisar de entidades canônicas mais estáveis.

Se a evolução exigir, estes blocos podem ser extraídos depois para estruturas como:

- `observed_element_stub`
- `observed_relation_stub`

Esses stubs ficam como apoio futuro de modelagem, sem entrar no núcleo obrigatório desta rodada.

## Alinhamento com os contratos documentados

### `docs/RUN_CONTRACT.md`

- O documento de contrato define o run como unidade mínima e valida o uso do coletor oficial inicial.
- O schema conceitual transforma esse contrato em entidades persistíveis com `collector`, `run` e `run_artifact`.
- `run_status` e `collection_health` ficam explícitos como campos relacionais, não como inferência livre.

### `docs/RUN_MANIFEST_FORMAT.md`

- O manifesto serializável do run é representado conceitualmente por `run` + `run_artifact`.
- Os campos `tools_enabled`, `tools_succeeded`, `tools_failed` e `notes` permanecem ligados ao registro do manifesto e não precisam ser normalizados agora.
- O item `manifest` em `run_artifact` cobre o artefato canônico do próprio run.

### `docs/INGESTION_BUNDLE.md`

- O bundle continua sendo a única porta oficial de entrada da Camada 1.
- `ingestion_bundle` materializa essa fronteira como entidade própria.
- `run_context_json`, `observed_elements_json`, `observed_relations_json` e `artifacts_manifest_json` ficam como blocos serializados de passagem.

### `docs/INGESTION_BUNDLE_FORMAT.md`

- O formato serializável do bundle é refletido diretamente nos campos JSON do `ingestion_bundle`.
- `ingestion_confidence` fica persistido como estado claro do pacote.
- A estrutura mínima dos blocos é preservada sem forçar normalização precoce.

## Resumo prático

- `collector` identifica a origem.
- `run` registra a observação delimitada.
- `run_artifact` inventaria as evidências produzidas pelo run.
- `ingestion_bundle` empacota contexto, observações e inventário para a Camada 1.
- A relação inicial entre `run` e `ingestion_bundle` é tratada como `1:1` lógica.
- Os blocos observacionais mais voláteis ficam serializados em JSON/JSONB por enquanto.
- O desenho já prepara uma transição limpa para o SQL definitivo, sem retrabalho estrutural grande.
