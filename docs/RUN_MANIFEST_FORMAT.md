# Formato de referência do manifesto do run

## Propósito

O manifesto do run é o registro serializável de referência de uma execução da Camada 0. Ele consolida identidade, escopo, tempo, ferramentas usadas, artefatos gerados e leitura final da coleta.

## Campos obrigatórios

- `run_id` (`string`): identificador único do run.
- `collector_id` (`string`): identificador do coletor responsável.
- `target_type` (`string`): classe do alvo observado.
- `target_value` (`string`): valor concreto do alvo.
- `service_hint` (`string`): pista funcional do serviço.
- `scenario` (`string`): cenário funcional da coleta.
- `started_at` (`string`, RFC 3339): instante de início.
- `finished_at` (`string`, RFC 3339): instante de fim.
- `run_status` (`string`): estado final do run.
- `collection_health` (`string`): leitura da qualidade da coleta.
- `tools_enabled` (`array<string>`): ferramentas liberadas ou usadas no run.
- `tools_succeeded` (`array<string>`): ferramentas que executaram com sucesso.
- `tools_failed` (`array<string>`): ferramentas que falharam ou não produziram resultado útil.
- `artifacts` (`array<object>`): inventário mínimo dos artefatos gerados.
- `notes` (`array<string>`): observações curtas e auditáveis.

## Campos opcionais

- `summary` (`string`): resumo curto do run.
- `tags` (`array<string>`): marcadores livres para organização.
- `scenario_version` (`string`): versão do cenário funcional, se houver necessidade de rastreio.

## Semântica dos campos

- `run_id`: precisa ser estável e único; é a chave primária conceitual do run.
- `collector_id`: identifica a origem operacional, por exemplo `vm-10.45.0.4`.
- `target_type`: diz como o alvo foi enquadrado, por exemplo `domain`, `service` ou `endpoint`.
- `target_value`: carrega o alvo concreto, por exemplo `facebook.com`.
- `service_hint`: resume o serviço esperado ou inferido, sem substituir a identidade canônica.
- `scenario`: descreve o contexto funcional da coleta, por exemplo `home_page`.
- `started_at`: marca o início do run.
- `finished_at`: marca o encerramento do run.
- `run_status`: descreve o resultado final da execução.
- `collection_health`: descreve a qualidade da coleta, não o sucesso funcional do alvo.
- `tools_enabled`: lista de ferramentas autorizadas ou planejadas para o run.
- `tools_succeeded`: lista de ferramentas que contribuíram com evidência útil.
- `tools_failed`: lista de ferramentas que falharam, ficaram indisponíveis ou não ajudaram.
- `artifacts`: inventário resumido dos artefatos produzidos.
- `notes`: observações curtas, sem narrativa longa.

## Diferença entre `run_status` e `collection_health`

- `run_status` responde se o run terminou com um resultado operacional aceito: `success`, `partial` ou `failed`.
- `collection_health` responde se a coleta ficou íntegra, degradada ou bloqueada, independentemente da utilidade parcial do material.
- Um run pode terminar como `partial` e ainda assim carregar `collection_health = degraded`.
- Um run com `failed` não precisa ter `collection_health = blocked` se houve evidência parcial, mas insuficiente para ingestão confiável.

## Exemplo de valores

- `run_id`: `run-2026-04-14-001`
- `collector_id`: `vm-10.45.0.4`
- `target_type`: `domain`
- `target_value`: `facebook.com`
- `service_hint`: `public_home_page`
- `scenario`: `home_page`
- `started_at`: `2026-04-14T09:00:00-03:00`
- `finished_at`: `2026-04-14T09:18:42-03:00`
- `run_status`: `partial`
- `collection_health`: `degraded`

## Regra de uso

Este formato é a referência documental para futura serialização da Camada 0. Ele não substitui o pipeline de coleta, mas define a estrutura esperada do manifesto produzido por cada run.

