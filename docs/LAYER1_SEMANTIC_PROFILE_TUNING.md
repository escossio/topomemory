# Tuning de perfis semânticos da Camada 1

## Objetivo

Ajustar a representação textual usada pelo provider `openai` sem mudar:

- o schema da tabela semântica
- o dataset de avaliação
- a identidade determinística da Camada 1
- o provider de embedding

## Variantes testadas

- `control`
- `hostname_first`
- `role_scope_first`
- `hybrid`
- `private_node_first`

## Configuração da variante

Use `TOPOMEMORY_SEMANTIC_PROFILE_VARIANT`:

- `control` replica o texto atual congelado
- `hostname_first` prioriza hostname e label
- `role_scope_first` prioriza escopo e papel
- `hybrid` combina hostname forte e escopo/papel forte
- `private_node_first` reforça a ancoragem em `private node`

## Resultado agregado

Baselines de referência:

- hash: `11/12`, `hit_rate = 0.9166666666666666`
- openai inicial: `8/12`, `hit_rate = 0.6666666666666666`

Melhor variante encontrada nesta rodada:

- `hybrid`
- `11/12`
- `hit_rate = 0.9166666666666666`
- `mean_first_hit_position = 1.0909090909090908`

## Leitura operacional

- `control` confirmou que o texto antigo do provider `openai` foi reproduzido corretamente.
- `hostname_first` melhorou pouco e ainda falhou em hostname puro.
- `role_scope_first` recuperou `q03_hostname` e `q04_google_hostname` e empatou com o hash em hit rate.
- `hybrid` empatou em hit rate com `role_scope_first` e teve melhor `mean_first_hit_position`, então virou a variante vencedora.
- `private_node_first` não venceu; piorou o agregado e não recuperou `q10_private_node`.

## Limite observado

Mesmo com tuning de perfil, `q10_private_node` permaneceu como ponto fraco.
O ganho principal ficou em `q03_hostname`, `q04_google_hostname` e `q12_private_hop_google`.

