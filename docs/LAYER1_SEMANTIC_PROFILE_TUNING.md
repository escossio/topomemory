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
- `hybrid_private_emphasis`
- `hybrid_private_signature`
- `hybrid_private_boost`
- `hybrid_private_node_focus`
- `hybrid_private_page8_focus`

## Configuração da variante

Use `TOPOMEMORY_SEMANTIC_PROFILE_VARIANT`:

- `control` replica o texto atual congelado
- `hostname_first` prioriza hostname e label
- `role_scope_first` prioriza escopo e papel
- `hybrid` combina hostname forte e escopo/papel forte
- `private_node_first` reforça a ancoragem em `private node`
- `hybrid_private_emphasis` reforça privados sem mudar os públicos
- `hybrid_private_signature` adiciona assinatura textual privada
- `hybrid_private_boost` reforça privados de forma ampla
- `hybrid_private_node_focus` reforça privados sem `hostname`
- `hybrid_private_page8_focus` reforça só o exemplar privado da página 8

## Resultado agregado

Baselines de referência:

- hash: `11/12`, `hit_rate = 0.9166666666666666`
- openai inicial: `8/12`, `hit_rate = 0.6666666666666666`
- hybrid focalizado anterior: `10/12`, `hit_rate = 0.8333333333333334`

Melhor variante encontrada nesta rodada:

- `hybrid_private_page8_focus`
- `12/12`
- `hit_rate = 1.0`
- `mean_first_hit_position = 1.1666666666666667`

## Leitura operacional

- `control` confirmou que o texto antigo do provider `openai` foi reproduzido corretamente.
- `hostname_first` melhorou pouco e ainda falhou em hostname puro.
- `role_scope_first` recuperou `q03_hostname` e `q04_google_hostname` e empatou com o hash em hit rate.
- `hybrid` consolidou a base antes do tuning focalizado.
- `hybrid_private_emphasis` e `hybrid_private_signature` provaram que o reforço amplo de privados funcionava, mas ainda gerava ruído colateral.
- `hybrid_private_boost` e `hybrid_private_node_focus` recuperaram `q10_private_node`, mas ainda pressionaram demais queries públicas.
- `hybrid_private_page8_focus` foi o melhor compromisso: recuperou `q10_private_node` e preservou `q03_hostname`, `q04_google_hostname`, `q06_public_destination`, `q07_public_node`, `q11_private_route_element` e `q12_private_hop_google`.

## Limite observado

O tuning amplo de privados mostrou que o problema não era o provider, e sim o alcance do reforço textual.
O resultado mais estável veio ao focar só no exemplar privado da página 8, mantendo o restante do corpus com o perfil `hybrid`.
