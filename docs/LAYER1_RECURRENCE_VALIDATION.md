# Validação de recorrência da Camada 1

## Objetivo

Validar a superfície de comparação entre runs equivalentes do mesmo alvo, sem abrir semântica, embeddings, `pgvector` operacional ou grafo.

## Alvo e cenário

- alvo: `google.com`
- cenário: `home_page`
- coletor: `vm-10.45.0.4`
- banco oficial: `10.45.0.3:5432/topomemory`
- role oficial: `topomemory_app`

## Runs gerados

- `run-20260414T201741+0000-google-com-7afada6e`
- `run-20260414T201750+0000-google-com-b3b2e968`
- `run-20260414T201756+0000-google-com-29535856`

## Execução usada

```bash
scripts/run_layer0_remote.sh google.com home_page
python3 src/expand_bundle_to_observations.py --run-id <run_id>
python3 src/consolidate_public_observations.py --run-id <run_id>
python3 src/report_layer1_audit.py --run-id <run_id> --summary-only
python3 src/report_layer1_run_diff.py --run-a <run_a> --run-b <run_b> --show-common --show-unique --show-path
```

## Evidência de execução remota

- o runner confirmou execução na VM `10.45.0.4` com `hostname=localhost`, `whoami=codex` e `psycopg=3.1.7`
- cada run retornou `run_dir` em `/tmp/topomemory-runner/runs/<run_id>`
- a coleta foi persistida diretamente no PostgreSQL oficial via `DATABASE_URL` apontando para `10.45.0.3:5432/topomemory`

## Evidência de persistência

Para cada um dos três runs:

- `topomemory.run = 1`
- `topomemory.run_artifact = 6`
- `topomemory.ingestion_bundle = 1`

## Evidência de expansão

Para cada um dos três bundles:

- `observed_element = 9`
- `observed_relation = 7`

## Evidência de consolidação

Para cada um dos três runs:

- `status = ok`
- `observed_elements = 9`
- `public_ip_consolidated = 2`
- `public_ip_matched = 2`
- `hostname_consolidated = 1`
- `hostname_matched = 1`
- `private_consolidated = 6`
- `private_new = 6`

## Auditoria por run

Para cada um dos três runs:

- `total_observed_elements = 9`
- `matched_existing_entity = 3`
- `new_entity_created = 6`
- `public = 3`
- `private = 6`
- `unresolved = 0`

## Diff entre runs equivalentes

Comparação usada:

- `run-20260414T201741+0000-google-com-7afada6e`
- `run-20260414T201750+0000-google-com-b3b2e968`

Resultado principal:

- `common_observed = 3`
- `common_network_elements = 3`
- `only_a_network_elements = 6`
- `only_b_network_elements = 6`
- `hop_prefix_common = 6`
- `path_prefix_common = 3`

Interseção real observada:

- `network-element-google-com`
- `network-element-172-217-172-14`
- `network-element-2800-3f0-4004-816-200e`

Esses três elementos cruzaram com o mesmo `comparison_key` e o mesmo `resolved_element_id` nos dois runs.

## Leitura operacional

- A recorrência do mesmo alvo e do mesmo cenário gerou interseção real por identidade resolvida.
- A parte pública estabilizou em três identidades canônicas compartilhadas.
- A parte privada variou nos hops posteriores, o que preservou diversidade sem destruir a interseção principal.
- A superfície de diff já é útil para comparar runs da mesma natureza antes de abrir qualquer frente semântica.

## Limitação observada

O runner remoto limpa `/tmp/topomemory-runner` a cada execução. Por isso, após a última coleta, o diretório persistente na VM reflete apenas o run mais recente; os anteriores ficam provados pelo `run_id`, pela ingestão no banco e pelo log salvo localmente.
