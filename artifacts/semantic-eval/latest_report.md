# Avaliação semântica da Camada 1

- queries_file: `schemas/semantic_eval_queries.json`
- limit: `5`
- embedding_provider: `openai`
- embedding_model: `text-embedding-3-small`
- total_queries: `12`
- total_pass: `8`
- total_fail: `4`
- hit_rate: `0.667`
- mean_first_hit_position: `1`

## Por consulta

| query_id | mode | pass | first_hit | top1 | topk |
| --- | --- | --- | --- | --- | --- |
| q01_google | top1_expected | pass | 1 | network-element-google-com | network-element-google-com, network-element-example-com, network-element-2800-3f0-4004-816-200e |
| q02_example | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-private-d1f108f975366192392317b35d4ba688a29b4e4bb638d418eef28a3a4e5ec9c7, network-element-private-2e495a249e3d9207a143c08d075faa37712153d5cb5628fcc7eefe004f89131c |
| q03_hostname | top1_expected | fail | 5 | network-element-2606-4700-10-6814-179a | network-element-2606-4700-10-6814-179a, network-element-2606-4700-10-ac42-93f3, network-element-104-20-23-154 |
| q04_google_hostname | top1_expected | fail | none | network-element-2606-4700-10-6814-179a | network-element-2606-4700-10-6814-179a, network-element-2606-4700-10-ac42-93f3, network-element-2800-3f0-4004-816-200e |
| q05_example_destination | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-google-com, network-element-2606-4700-10-6814-179a |
| q06_public_destination | category_contains | pass | 1 | network-element-example-com | network-element-example-com, network-element-2800-3f0-4004-816-200e, network-element-2606-4700-10-6814-179a |
| q07_public_node | category_contains | pass | 1 | network-element-2606-4700-10-6814-179a | network-element-2606-4700-10-6814-179a, network-element-2606-4700-10-ac42-93f3, network-element-2800-3f0-4004-816-200e |
| q08_private_hop | category_contains | pass | 1 | network-element-private-4933ed6d0b1a178122f167355cf9bfb31ddd3c2cfaad6a9fd74655d89a6025b1 | network-element-private-4933ed6d0b1a178122f167355cf9bfb31ddd3c2cfaad6a9fd74655d89a6025b1, network-element-private-351ededb3ab4a698ed1adc70fc72691933295480663fc816724a1cab6d8acf43, network-element-private-9f3c970cdcbecb41f657da1a2d47fb784a678842c4e75425bfbad143aba91a08 |
| q09_internal_hop | category_contains | pass | 1 | network-element-private-4933ed6d0b1a178122f167355cf9bfb31ddd3c2cfaad6a9fd74655d89a6025b1 | network-element-private-4933ed6d0b1a178122f167355cf9bfb31ddd3c2cfaad6a9fd74655d89a6025b1, network-element-private-316352014af1021ffe146d48ca41598e97b69078be3f83c0fe44f3aa541c82ad, network-element-private-056aaea4ce5ae87524a26df5bc4dd58d6c985128aa0c4c5555874e9f83b96a06 |
| q10_private_node | category_contains | fail | none | network-element-2606-4700-10-6814-179a | network-element-2606-4700-10-6814-179a, network-element-2606-4700-10-ac42-93f3, network-element-104-20-23-154 |
| q11_private_route_element | category_contains | fail | none | network-element-example-com | network-element-example-com, network-element-172-66-147-243, network-element-2606-4700-10-6814-179a |
| q12_private_hop_google | topk_contains | pass | 1 | network-element-google-com | network-element-google-com, network-element-private-316352014af1021ffe146d48ca41598e97b69078be3f83c0fe44f3aa541c82ad, network-element-private-4933ed6d0b1a178122f167355cf9bfb31ddd3c2cfaad6a9fd74655d89a6025b1 |

## Leitura

- acertos: `8`
- falhas: `4`
- a avaliação usa `topomemory.network_element_semantic` e a busca semântica auxiliar atual
- a identidade determinística não é alterada por este benchmark
