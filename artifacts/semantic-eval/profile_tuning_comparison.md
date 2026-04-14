# Comparação de tuning semântico

## Baselines

- hash: 11/12 | hit_rate=0.9166666666666666 | mean_first_hit_position=1
- openai inicial: 8/12 | hit_rate=0.6666666666666666 | mean_first_hit_position=1

## Variantes testadas

- `control`: 8/12 | hit_rate=0.6666666666666666 | mean_first_hit_position=1 | reindexed=0
- `hostname_first`: 9/12 | hit_rate=0.75 | mean_first_hit_position=1.2222222222222223 | reindexed=40
- `role_scope_first`: 11/12 | hit_rate=0.9166666666666666 | mean_first_hit_position=1.1818181818181819 | reindexed=40
- `hybrid`: 11/12 | hit_rate=0.9166666666666666 | mean_first_hit_position=1.0909090909090908 | reindexed=40
- `private_node_first`: 10/12 | hit_rate=0.8333333333333334 | mean_first_hit_position=1.1 | reindexed=40

## Quatro queries críticas

| variante | q03_hostname | q04_google_hostname | q10_private_node | q11_private_route_element | q12_private_hop_google |
| --- | --- | --- | --- | --- | --- |
| `control` | fail@5 | fail@none | fail@none | fail@none | pass@1 |
| `hostname_first` | fail@none | fail@none | fail@none | pass@2 | pass@1 |
| `role_scope_first` | pass@1 | pass@1 | fail@none | pass@3 | pass@1 |
| `hybrid` | pass@1 | pass@1 | fail@none | pass@2 | pass@1 |
| `private_node_first` | pass@1 | pass@1 | fail@none | fail@none | pass@1 |

## Vencedor

- `hybrid`
- motivo: Empatou com role_scope_first em hit_rate (11/12) e teve melhor mean_first_hit_position.

## Leitura

- A melhoria principal veio de reordenar e reforçar os fatos do perfil, não de mudar schema ou identidade determinística.
- `q10_private_node` permaneceu como o ponto fraco do benchmark congelado.
- O ganho mais estável ficou em `q03_hostname`, `q04_google_hostname` e `q12_private_hop_google`.
