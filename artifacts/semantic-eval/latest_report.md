# Avaliação semântica da Camada 1

- queries_file: `schemas/semantic_eval_queries.json`
- limit: `5`
- total_queries: `12`
- total_pass: `11`
- total_fail: `1`
- hit_rate: `0.917`
- mean_first_hit_position: `1`

## Por consulta

| query_id | mode | pass | first_hit | top1 | topk |
| --- | --- | --- | --- | --- | --- |
| q01_google | top1_expected | pass | 1 | network-element-google-com | network-element-google-com, network-element-private-3a90795d7b253323412f06986452cdf7b04a79799f64d42701c6bee337774894, network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb |
| q02_example | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-172-66-147-243, network-element-private-e5e4eb362082983b48697c3dbcd90c19a3cd458a670fdbeba332847de775f73b |
| q03_hostname | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-google-com, network-element-172-217-172-14 |
| q04_google_hostname | top1_expected | pass | 1 | network-element-google-com | network-element-google-com, network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb, network-element-private-bddfd0b694656c19477775be628d8cce892af43b27dec0bcdea57b4ebebc4029 |
| q05_example_destination | top1_expected | pass | 1 | network-element-example-com | network-element-example-com, network-element-google-com, network-element-private-056aaea4ce5ae87524a26df5bc4dd58d6c985128aa0c4c5555874e9f83b96a06 |
| q06_public_destination | category_contains | pass | 1 | network-element-example-com | network-element-example-com, network-element-google-com, network-element-private-12fccf0c3e70a3e6cdad4324415e7e624c9d1ea9a2d59eced7e52de7f997200e |
| q07_public_node | category_contains | pass | 1 | network-element-2606-4700-10-ac42-93f3 | network-element-2606-4700-10-ac42-93f3, network-element-2800-3f0-4004-816-200e, network-element-2606-4700-10-6814-179a |
| q08_private_hop | category_contains | pass | 1 | network-element-private-29aa95ada5a94b4b0c9c5efbd89c0f653b2fa6ef6e32fb2fddc501ce1098b4bc | network-element-private-29aa95ada5a94b4b0c9c5efbd89c0f653b2fa6ef6e32fb2fddc501ce1098b4bc, network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18, network-element-private-d4d7f6fed55e978a09777557c4d91129ac4ff4340648d65b87ec9fe2542cb4c6 |
| q09_internal_hop | category_contains | pass | 1 | network-element-private-29aa95ada5a94b4b0c9c5efbd89c0f653b2fa6ef6e32fb2fddc501ce1098b4bc | network-element-private-29aa95ada5a94b4b0c9c5efbd89c0f653b2fa6ef6e32fb2fddc501ce1098b4bc, network-element-private-e5e4eb362082983b48697c3dbcd90c19a3cd458a670fdbeba332847de775f73b, network-element-private-06ded8985cc2eb5dc1b2130a35234064b7ec14d1ae22614c936fdd816a9f1469 |
| q10_private_node | category_contains | pass | 1 | network-element-private-2e495a249e3d9207a143c08d075faa37712153d5cb5628fcc7eefe004f89131c | network-element-private-2e495a249e3d9207a143c08d075faa37712153d5cb5628fcc7eefe004f89131c, network-element-private-c036d9813ccca06af905a3d9636dde84ec52979b82a5c6d6699e27ef0d02cff8, network-element-private-eadc32ff4b935e402b0951fa8b7faf7554fdc5f70cef842fd63e05c581e04e18 |
| q11_private_route_element | category_contains | pass | 1 | network-element-private-351ededb3ab4a698ed1adc70fc72691933295480663fc816724a1cab6d8acf43 | network-element-private-351ededb3ab4a698ed1adc70fc72691933295480663fc816724a1cab6d8acf43, network-element-private-250bbfb8d6e6d4f3b7f81ea6a8fef3280eab37a4473f7c9c7b5fb0826f8b2cd7, network-element-private-2f8ac85719139a946e97d3ef53526212b19f3323c26a1da3c688df130abd42ca |
| q12_private_hop_google | topk_contains | fail | 1 | network-element-private-316352014af1021ffe146d48ca41598e97b69078be3f83c0fe44f3aa541c82ad | network-element-private-316352014af1021ffe146d48ca41598e97b69078be3f83c0fe44f3aa541c82ad, network-element-private-5ba94f953381adcab3c590db351bef18fbcaca4406df8aa27e1c43258e68e7bb, network-element-private-bddfd0b694656c19477775be628d8cce892af43b27dec0bcdea57b4ebebc4029 |

## Leitura

- acertos: `11`
- falhas: `1`
- a avaliação usa `topomemory.network_element_semantic` e a busca semântica auxiliar atual
- a identidade determinística não é alterada por este benchmark
