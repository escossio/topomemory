# Troca de motor semântico: tentativa e bloqueio

## Objetivo da rodada

Trocar apenas o motor de embedding da camada semântica auxiliar e reindexar os `network_element` já consolidados.

## Motor antigo

- `topomemory-hash-embedding-v1`

## Motor novo pretendido

- embedding real via API

## Status da tentativa

Bloqueada por falta de credenciais e configuração viável no ambiente.

Evidência verificada localmente:

- `OPENAI_API_KEY` ausente
- `OPENAI_BASE_URL` ausente
- `AZURE_OPENAI_API_KEY` ausente
- `AZURE_OPENAI_ENDPOINT` ausente
- `sentence_transformers` não instalado
- `transformers` não instalado
- `torch` não instalado

## Consequência

Não houve troca efetiva de motor nesta rodada.
Não houve reindexação nova.
Não houve rerun do benchmark com motor diferente.

## Leitura operacional

A identidade determinística da Camada 1 permaneceu intacta.
A camada semântica auxiliar segue funcional com o baseline anterior, mas a evolução para um motor mais forte precisa de credencial ou dependência técnica adicional antes de qualquer reindexação.
