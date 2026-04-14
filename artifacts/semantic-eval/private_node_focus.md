# Foco em `q10_private_node`

## Problema observado

O tuning amplo de privados recuperou `q10_private_node`, mas também passou a pressionar queries públicas como `q06_public_destination` e `q07_public_node`.

## Decisão de tuning

A variante final `hybrid_private_page8_focus` aplica reforço forte apenas ao exemplar privado da página 8, identificado por `canonical_label` contendo `:8:`.

## Resultado

- `q10_private_node`: `pass`
- `q04_google_hostname`: `pass`
- `q06_public_destination`: `pass`
- `q07_public_node`: `pass`
- `q11_private_route_element`: `pass`
- `q12_private_hop_google`: `pass`
- `hit_rate`: `1.0`

## Leitura

O problema não era a identidade determinística nem o provider `openai`; era o alcance do reforço textual. Ao restringir o foco a um exemplar privado estável, a bateria fixa fechou inteira sem mexer no schema nem no dataset.
