# Avaliação semântica da Camada 1

- queries_file: `schemas/semantic_eval_queries.json`
- limit: `5`
- profile_variant: `hybrid`
- embedding_provider: `openai`
- embedding_model: `text-embedding-3-small`
- total_queries: `12`
- total_pass: `11`
- total_fail: `1`
- hit_rate: `0.917`
- mean_first_hit_position: `1.0909090909090908`

## Por consulta

| query_id | mode | pass | first_hit | top1 | topk |
| --- | --- | --- | --- | --- | --- |
| q01_google | top1_expected | pass | 1 | network-element-google-com | network-element-google-com, network-element-example-com, network-element-2800-3f0-4004-816-200e |
| q02_example | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-private-e5e4eb362082983b48697c3dbcd90c19a3cd458a670fdbeba332847de775f73b, network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 |
| q03_hostname | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-2606-4700-10-6814-179a, network-element-2606-4700-10-ac42-93f3 |
| q04_google_hostname | top1_expected | pass | 1 | network-element-google-com | network-element-google-com, network-element-2800-3f0-4004-816-200e, network-element-example-com |
| q05_example_destination | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-2800-3f0-4004-816-200e, network-element-google-com |
| q06_public_destination | category_contains | pass | 1 | network-element-example-com | network-element-example-com, network-element-2800-3f0-4004-816-200e, network-element-2606-4700-10-6814-179a |
| q07_public_node | category_contains | pass | 1 | network-element-2606-4700-10-6814-179a | network-element-2606-4700-10-6814-179a, network-element-2800-3f0-4004-816-200e, network-element-2606-4700-10-ac42-93f3 |
| q08_private_hop | category_contains | pass | 1 | network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb | network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb, network-element-private-bddfd0b694656c19477775be628d8cce892af43b27dec0bcdea57b4ebebc4029, network-element-private-924fb7435fc86393014b7ca32e8071f6013ee4f2e069ca8889d7865a0b2b31ca |
| q09_internal_hop | category_contains | pass | 1 | network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb | network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb, network-element-private-bddfd0b694656c19477775be628d8cce892af43b27dec0bcdea57b4ebebc4029, network-element-private-d1f108f975366192392317b35d4ba688a29b4e4bb638d418eef28a3a4e5ec9c7 |
| q10_private_node | category_contains | fail | none | network-element-2606-4700-10-6814-179a | network-element-2606-4700-10-6814-179a, network-element-2606-4700-10-ac42-93f3, network-element-104-20-23-154 |
| q11_private_route_element | category_contains | pass | 2 | network-element-example-com | network-element-example-com, network-element-private-d70b9c217705396f81b3f93e1ab46e94d9ede1fa1313ec668ff4389634bae23f, network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 |
| q12_private_hop_google | topk_contains | pass | 1 | network-element-google-com | network-element-google-com, network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb, network-element-private-924fb7435fc86393014b7ca32e8071f6013ee4f2e069ca8889d7865a0b2b31ca |

## Leitura

- acertos: `11`
- falhas: `1`
- a avaliação usa `topomemory.network_element_semantic` e a busca semântica auxiliar atual
- a identidade determinística não é alterada por este benchmark
