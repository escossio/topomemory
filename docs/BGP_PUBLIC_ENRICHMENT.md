# Enriquecimento público de BGP

## Definição

O enriquecimento público de BGP é uma frente futura do Topomemory para consultar fontes externas de roteamento e usar esse contexto como apoio analítico, sem alterar a fonte primária da verdade observada localmente.

Ele entra como módulo auxiliar futuro, separado da observação controlada já existente, e não altera o contrato da Camada 0 nem a consolidação da Camada 1.

## Motivação

Algumas informações úteis para explicar tráfego e alcance global não aparecem na coleta local controlada. Fontes públicas de BGP podem trazer contexto complementar sobre ASN, prefixos e visibilidade global de rotas.

## Fontes públicas possíveis

- RIPEstat Data API
- RouteViews API
- BGPKIT API/Broker

## Papel no projeto

- enriquecimento externo futuro
- apoio de contexto para leitura de tráfego e roteamento
- não é fonte primária da verdade
- não substitui a observação da VM da Camada 0
- não altera a memória canônica da Camada 1
- não muda o comportamento do sistema nesta fase

## Usos futuros possíveis

- enriquecer contexto de ASN e prefixo
- comparar rota observada localmente com visibilidade global
- apoiar explicações sobre caminhos e mudanças de tráfego
- ajudar leituras futuras de inteligência de tráfego e decisão de caminho

## Limites

- não prova sozinho o que aconteceu no ambiente observado
- depende de disponibilidade, cobertura e qualidade das fontes externas
- não substitui coleta local controlada
- não muda a verdade canônica da Camada 1
- não é componente ativo nesta fase
- não adiciona integração funcional nesta rodada

## Status

Frente futura documentada. Não implementada nesta fase.
