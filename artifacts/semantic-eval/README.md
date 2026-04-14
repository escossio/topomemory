# Artefatos da avaliação semântica

Este diretório guarda o baseline executável da busca semântica da Camada 1.

Arquivos esperados:

- `latest_results.json`: saída estruturada do benchmark
- `latest_report.md`: relatório humano da rodada atual

Uso típico:

```bash
python3 src/evaluate_semantic_search.py \
  --queries-file schemas/semantic_eval_queries.json \
  --limit 5 \
  --json-out artifacts/semantic-eval/latest_results.json \
  --markdown-out artifacts/semantic-eval/latest_report.md
```

O conteúdo daqui é auxiliar e serve para comparar o motor atual com versões futuras.
