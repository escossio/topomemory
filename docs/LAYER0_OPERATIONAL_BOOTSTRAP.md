# Bootstrap operacional da Camada 0

## Objetivo

Fechar o caminho mínimo e reproduzível para executar a coleta real da Camada 0 na VM oficial `10.45.0.4`, sem abrir a Camada 1 e sem expandir o coletor além do baseline.

## Dependências mínimas da VM

O host `10.45.0.4` precisa ter:

- `python3`
- uma ferramenta de resolução DNS: `dig`, `host` ou `getent`
- `traceroute`
- `curl`
- `python3-psycopg`

Se algum item faltar, o bootstrap pode instalar o conjunto mínimo via `apt` quando houver `sudo`.

## Conexão oficial ao PostgreSQL

A forma operacional inicial é um túnel SSH reverso a partir do host que executa o runner local.

Motivo:

- o PostgreSQL do ambiente atual escuta apenas em `127.0.0.1`
- a VM `10.45.0.4` precisa enxergar o banco sem abrir a topologia do banco para a rede
- o túnel reduz mudanças estruturais e mantém a prova reproduzível

Fluxo:

- o host local abre `127.0.0.1:5432` para a VM como `127.0.0.1:15432`
- o runner remoto usa `DATABASE_URL` apontando para `127.0.0.1:15432`

Exemplo de forma oficial:

```bash
ssh -N -R 15432:127.0.0.1:5432 \
  -i /lab/projects/livecopilot/lab/vms/livecopilot-validation/admin_sshkey \
  codex@10.45.0.4
```

## GRANTs mínimos

O role de ingestão usa o mínimo necessário:

- `USAGE` no schema `topomemory`
- `SELECT`, `INSERT`, `UPDATE`, `DELETE` nas tabelas `topomemory.collector`, `topomemory.run`, `topomemory.run_artifact` e `topomemory.ingestion_bundle`

O SQL oficial fica em:

- [sql/001_layer0_minimum_grants.sql](/sql/001_layer0_minimum_grants.sql)

Não há sequência nem privilégio adicional requerido nesta rodada.

## Execução remota oficial

O fluxo reproduzível fica dividido em dois scripts:

- [scripts/bootstrap_layer0_vm.sh](/scripts/bootstrap_layer0_vm.sh)
- [scripts/run_layer0_remote.sh](/scripts/run_layer0_remote.sh)

O runner remoto:

- prepara um diretório limpo na VM
- envia apenas `src/collect_minimal_run.py` e `src/ingest_run_bundle.py`
- sobe o túnel SSH reverso
- executa a coleta
- executa a ingestão
- retorna a pasta do run

## Variáveis mínimas

- `DATABASE_URL`
- `target`
- `scenario`

## Validação mínima

Depois do run, validar:

- existência de `run_manifest.json`
- existência de `ingestion_bundle.json`
- persistência em `topomemory.run`
- persistência em `topomemory.run_artifact`
- persistência em `topomemory.ingestion_bundle`

## Limites

- A Camada 1 permanece fechada.
- O coletor não foi ampliado.
- O browser/DevTools continua fora do fluxo.
