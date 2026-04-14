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

A forma operacional oficial agora é conexão TCP direta do runner para o host PostgreSQL na rede interna.

Motivo:

- o PostgreSQL do ambiente passa a escutar em `10.45.0.3`
- a VM `10.45.0.4` acessa o banco pela rede interna `10.45.0.0/16`
- o caminho oficial deixa de depender de túnel SSH reverso

Fluxo:

- o runner remoto usa `DATABASE_URL` apontando para `10.45.0.3:5432/topomemory`
- a autenticação usa `topomemory_app` com senha e `scram-sha-256`

Exemplo de forma oficial:

```bash
DATABASE_URL='postgresql://topomemory_app:<senha>@10.45.0.3:5432/topomemory'
```

## GRANTs mínimos

O role oficial do projeto usa o mínimo necessário para operar o schema próprio:

- ownership do database `topomemory`
- ownership do schema `topomemory`
- `USAGE`, `CREATE` no schema `topomemory`

O acesso oficial fica documentado em:

- [docs/DATABASE_ACCESS.md](/docs/DATABASE_ACCESS.md)

Não há acesso amplo fora da rede `10.45.0.0/16`.

## Execução remota oficial

O fluxo reproduzível fica dividido em dois scripts:

- [scripts/bootstrap_layer0_vm.sh](/scripts/bootstrap_layer0_vm.sh)
- [scripts/run_layer0_remote.sh](/scripts/run_layer0_remote.sh)

O runner remoto:

- prepara um diretório limpo na VM
- envia apenas `src/collect_minimal_run.py` e `src/ingest_run_bundle.py`
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
