# Avaliação semântica da Camada 1

- queries_file: `schemas/semantic_eval_queries.json`
- limit: `5`
- profile_variant: `hybrid_private_page8_focus`
- embedding_provider: `openai`
- embedding_model: `text-embedding-3-small`
- total_queries: `12`
- total_pass: `12`
- total_fail: `0`
- hit_rate: `1.000`
- mean_first_hit_position: `1.1666666666666667`

## Por consulta

| query_id | mode | pass | first_hit | top1 | topk |
| --- | --- | --- | --- | --- | --- |
| q01_google | top1_expected | pass | 1 | network-element-google-com | network-element-google-com, network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-example-com |
| q02_example | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-private-e5e4eb362082983b48697c3dbcd90c19a3cd458a670fdbeba332847de775f73b |
| q03_hostname | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-2606-4700-10-6814-179a, network-element-2606-4700-10-ac42-93f3 |
| q04_google_hostname | top1_expected | pass | 1 | network-element-google-com | network-element-google-com, network-element-2800-3f0-4004-816-200e, network-element-example-com |
| q05_example_destination | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-2800-3f0-4004-816-200e, network-element-google-com |
| q06_public_destination | category_contains | pass | 2 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-example-com, network-element-2800-3f0-4004-816-200e |
| q07_public_node | category_contains | pass | 2 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-2606-4700-10-6814-179a, network-element-2800-3f0-4004-816-200e |
| q08_private_hop | category_contains | pass | 1 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb, network-element-private-bddfd0b694656c19477775be628d8cce892af43b27dec0bcdea57b4ebebc4029 |
| q09_internal_hop | category_contains | pass | 1 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb, network-element-private-bddfd0b694656c19477775be628d8cce892af43b27dec0bcdea57b4ebebc4029 |
| q10_private_node | category_contains | pass | 1 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-2606-4700-10-6814-179a, network-element-2606-4700-10-ac42-93f3 |
| q11_private_route_element | category_contains | pass | 1 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-example-com, network-element-private-d70b9c217705396f81b3f93e1ab46e94d9ede1fa1313ec668ff4389634bae23f |
| q12_private_hop_google | topk_contains | pass | 1 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 | network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-google-com, network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb |

## Spotlight

- q03_hostname: `pass`, first_hit = `1`, top1 = `network-element-example-com`
- q04_google_hostname: `pass`, first_hit = `1`, top1 = `network-element-google-com`
- q10_private_node: `pass`, first_hit = `1`, top1 = `network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18`
- q11_private_route_element: `pass`, first_hit = `1`, top1 = `network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18`
- q12_private_hop_google: `pass`, first_hit = `1`, top1 = `network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18`

## Leitura

- acertos: `12`
- falhas: `0`
- a avaliação usa `topomemory.network_element_semantic` e a busca semântica auxiliar atual
- a identidade determinística não é alterada por este benchmark
