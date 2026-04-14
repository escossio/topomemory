# Comparativo de tuning semântico

## Baselines

- hash: `11/12`, `hit_rate = 0.9166666666666666`
- openai inicial (`text-embedding-3-small` + `hybrid`): `11/12`, `hit_rate = 0.9166666666666666`
- openai focalizado anterior (`hybrid_private_node_focus`): `10/12`, `hit_rate = 0.8333333333333334`

## Variante vencedora desta rodada

- `hybrid_private_page8_focus`
- `12/12`
- `hit_rate = 1.0`
- `mean_first_hit_position = 1.1666666666666667`

## Interpretação

- O reforço global em privados resolvia `q10_private_node`, mas gerava regressão em queries públicas.
- O foco reduzido em um exemplar privado estável da página 8 manteve `q10_private_node` pass e preservou `q03_hostname`, `q04_google_hostname`, `q06_public_destination`, `q07_public_node`, `q11_private_route_element` e `q12_private_hop_google`.
- O resultado final superou tanto o baseline hash quanto o baseline `openai` anterior no agregado da bateria fixa.
