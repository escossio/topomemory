# Comparativo de tuning semântico

## Baselines

- hash: `11/12`, `hit_rate = 0.9166666666666666`
- openai controle (`text-embedding-3-small` + `hybrid`): `11/12`, `hit_rate = 0.9166666666666666`
- openai focalizado amplo (`hybrid_private_emphasis`): `12/12`, `hit_rate = 1.0`, `embedded_elements = 32`
- openai focalizado por assinatura (`hybrid_private_signature`): `11/12`, `hit_rate = 0.9166666666666666`, com regressão em `q12_private_hop_google`

## Variante vencedora desta rodada

- `hybrid_private_page8_focus`
- `12/12`
- `hit_rate = 1.0`
- `mean_first_hit_position = 1.1666666666666667`
- `changed_profiles = 1`
- `embedded_elements = 1`

## Interpretação

- `hybrid` continua sendo um bom controle, mas ainda perde `q10_private_node`.
- `hybrid_private_emphasis` passou sem regressão depois que o tuning passou a tocar só privados, mas custa reindexar `32` elementos.
- `hybrid_private_signature` mostrou que assinatura textual extra pode empurrar `q10_private_node`, mas puxa demais o espaço privado e derruba `q12_private_hop_google`.
- `hybrid_private_page8_focus` entrega o mesmo `12/12` do reforço amplo, só que com mudança local em `1` elemento privado.
- O resultado final continua acima do baseline hash e do controle `hybrid`, sem mexer na identidade determinística.
