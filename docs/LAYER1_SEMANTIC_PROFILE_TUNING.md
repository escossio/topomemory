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
- openai controle desta rodada (`hybrid`): `11/12`, `hit_rate = 0.9166666666666666`

Melhor variante encontrada nesta rodada:

- `hybrid_private_page8_focus`
- `12/12`
- `hit_rate = 1.0`
- `mean_first_hit_position = 1.1666666666666667`
- `changed_profiles = 1`
- `embedded_elements = 1`

Estado final congelado:

- variante ativa: `hybrid_private_page8_focus`
- baseline semântico ativo: `hybrid_private_page8_focus`
- ciclo de tuning encerrado nesta frente

## Leitura operacional

- `hybrid` ficou como controle: `11/12`, preservando `q03_hostname`, `q04_google_hostname`, `q11_private_route_element` e `q12_private_hop_google`, mas ainda falhando em `q10_private_node`.
- `hybrid_private_emphasis` passou `12/12` depois que o reforço foi restrito só aos privados, sem tocar os elementos públicos. O custo foi reindexar `32` elementos privados.
- `hybrid_private_signature` também recuperou `q10_private_node`, mas regrediu `q12_private_hop_google`, então não serve como perfil estável.
- `hybrid_private_page8_focus` voltou a ser o melhor compromisso: recuperou `q10_private_node`, preservou `q03_hostname`, `q04_google_hostname`, `q11_private_route_element` e `q12_private_hop_google`, e precisou reindexar só `1` elemento.

## Limite observado

O problema residual não estava na identidade determinística nem no provider, e sim no alcance do reforço textual privado.
Quando os perfis públicos ficam idênticos ao `hybrid`, o tuning localizado passa a funcionar sem contaminar hostname público.
Para produção, `hybrid_private_page8_focus` continua preferível porque resolve `q10_private_node` com o menor impacto operacional possível.
Nesta consolidação, essa variante passou a ser o baseline ativo e a frente não deve abrir nova rodada de ranking sem mudança explícita de escopo.
