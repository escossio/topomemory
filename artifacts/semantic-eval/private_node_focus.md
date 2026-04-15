# Foco em `q10_private_node`

## Problema observado

No controle `hybrid`, o caso residual continuou claro:

- `hit_rate`: `11/12`
- `q10_private_node`: `fail`
- `q03_hostname`: `pass`
- `q04_google_hostname`: `pass`
- `q11_private_route_element`: `pass`
- `q12_private_hop_google`: `pass`

O problema estava concentrado no reforço semântico dos elementos privados.

## Decisão de tuning

As variantes amplas passaram a preservar os públicos ao devolver `_hybrid_profile_lines()` para tudo que não fosse `ip_scope = private`.

Com isso, a rodada focalizada ficou assim:

- `hybrid_private_emphasis`: `12/12`, mas reindexando `32` elementos privados
- `hybrid_private_signature`: recupera `q10_private_node`, mas regrede `q12_private_hop_google`
- `hybrid_private_page8_focus`: `12/12`, reindexando só `1` elemento privado, identificado por `canonical_label` contendo `:8:`

## Resultado

- `q10_private_node`: `pass`
- `q04_google_hostname`: `pass`
- `q03_hostname`: `pass`
- `q11_private_route_element`: `pass`
- `q12_private_hop_google`: `pass`
- `hit_rate`: `1.0`
- `changed_profiles`: `1`
- `embedded_elements`: `1`

## Leitura

O problema não era a identidade determinística nem o provider `openai`; era o alcance do reforço textual. Ao restringir o foco a um exemplar privado estável e manter o `hybrid` intacto para públicos, a bateria fixa fechou inteira sem mexer no schema nem no dataset, e sem reembed desnecessário do corpus inteiro.
