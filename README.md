# API de vendas — Workshop Skyone Studio

**Próximo passo:** siga [Publicar e conectar ao Skyone](PUBLICAR_E_CONECTAR.md). O código está pronto para envio ao GitHub; o Render executará a API, fornecendo a URL HTTPS. O arquivo `render.yaml` permite criar o serviço pelo recurso **New > Blueprint** do Render.

Branch de implantação: `main`.

# API do workshop — vendas e produtos

API REST didática para demonstrar ingestão, camadas Bronze/Silver/Gold e modelo estrela no Skyone Studio. Todos os dados são fictícios. O código e o guia foram preparados em 27/10/2026.

## 1. Executar no Windows

1. Baixe o repositório como ZIP e extraia-o, ou clone com `git clone --branch main https://github.com/anacpais/repos-ana-pais.git`. Abra a pasta que contém `app.py`.
2. Tenha Python 3.10 ou superior instalado. Se necessário, obtenha em https://www.python.org/downloads/ e habilite a opção de adicionar Python ao PATH durante a instalação.
3. Abra a pasta extraída. Digite `cmd` na barra de endereço do Explorador de Arquivos e pressione Enter. O terminal abrirá nessa pasta.
4. Confira a instalação:

```bat
py --version
```

5. Inicie o servidor:

```bat
py app.py
```

Se o comando `py` não existir, tente `python app.py`. Não precisa executar `pip install`: só usamos a biblioteca padrão do Python. Os dados já estão gerados no repositório.

6. Abra no navegador:

- http://localhost:8000/docs — documentação navegável.
- http://localhost:8000/health — teste de disponibilidade.
- http://localhost:8000/produtos?tamanho=2000 — todos os produtos.
- http://localhost:8000/vendas?tamanho=2000 — todos os registros de venda.

Mantenha o terminal aberto enquanto usar a API. Para encerrar, pressione Ctrl+C. Também pode iniciar com um duplo clique em `iniciar_windows.bat`.

Se a porta estiver ocupada, no Prompt de Comando execute:

```bat
set PORT=8001
py app.py
```

Acesse então a porta 8001. No PowerShell, o equivalente é `$env:PORT="8001"` seguido de `py app.py`.

No macOS/Linux, na pasta do projeto, use `python3 app.py`.

## 2. O que foi criado e em que ordem

### Passo 1 — Definir o contrato dos dados

O objetivo é responder: quais categorias geram mais receita e como as vendas evoluem por mês?

Defini duas entidades: produtos e itens de venda. Cada pedido tem dois itens. A chave de um item é a combinação `id_venda` + `numero_item`; apenas `id_venda` não é único. Isso será o grão da fato.

Campos de `/produtos`:

| Campo | Tipo JSON | Significado |
|---|---|---|
| id_produto | inteiro | Identificador de origem |
| nome | texto | Nome comercial |
| categoria | texto | Categoria ainda sem padronização |
| marca | texto | Marca |
| descricao | texto | Descrição |
| preco_atual | número | Preço atual do cadastro, em reais |

Campos de `/vendas`:

| Campo | Tipo JSON | Significado |
|---|---|---|
| id_venda | texto | Número do pedido |
| numero_item | inteiro | Posição do item no pedido |
| data_venda | texto AAAA-MM-DD | Data de negócio, sem horário |
| id_produto | inteiro | Referência ao produto |
| quantidade | inteiro | Unidades do item |
| preco_unitario | número | Preço efetivamente praticado por unidade |
| desconto | número | Desconto total do item, em reais |
| status | texto | concluida ou cancelada |

Fórmula: `valor_liquido = quantidade * preco_unitario - desconto`.

Não substitua o preço da venda pelo preço atual do cadastro. Para SQL, trate os valores monetários como `DECIMAL(18,2)`, conforme o dialeto do engine. Não use ponto flutuante para agregar moeda.

### Passo 2 — Gerar uma base fixa

O arquivo `gerar_dados.py` usa `random.Random(42)`: uma semente fixa torna os valores reproduzíveis, em vez de gerar novas vendas em cada chamada.

Foram criados 30 produtos, três categorias, três marcas e 500 pedidos com dois itens cada, entre 01/04/2026 e 30/09/2026. Cada décimo pedido é cancelado. Os preços das vendas são próprios das transações; não são copiados do preço atual do cadastro.

Os descontos são calculados com `Decimal` e arredondados para centavos antes da exportação. O gerador usa o arredondamento padrão de `Decimal` (meio para par).

### Passo 3 — Inserir problemas de qualidade controlados

| Situação | Onde encontrar | Tratamento proposto |
|---|---|---|
| Categoria com espaços | Produto 2: ` eletrônicos ` | TRIM e padronização de capitalização |
| Categoria em maiúsculas | Produto 5: `ELETRÔNICOS` | Mesma padronização |
| Item sem produto cadastrado | Venda V00001, item 1: produto 999 | Separar em rejeições, com motivo |
| Duplicata exata | Venda V00005, item 2, copiada no final | Deduplicar pela chave de negócio |
| Cancelamentos | 50 pedidos, 100 itens | Preservar na Silver; filtrar na fato do case |

A inconsistência do produto 999 está em uma venda concluída. Os casos não se sobrepõem para facilitar a conferência.

### Passo 4 — Salvar os dados de origem

O gerador grava JSON, CSV e gabarito em `dados/`. O JSON é a fonte servida pela API. O CSV é apoio caso seja necessário demonstrar a ingestão de arquivos.

Para recriar os arquivos, pare o servidor e execute:

```bat
py gerar_dados.py
py app.py
```

A API carrega os arquivos ao iniciar. Se você editar JSON com o servidor aberto, reinicie para aplicar as alterações. Não há banco de dados nem operações de gravação via API.

### Passo 5 — Criar o servidor HTTP

Em `app.py`, `ThreadingHTTPServer` recebe as chamadas HTTP e `Handler.do_GET` escolhe a rota. O servidor:

1. Identifica o caminho solicitado.
2. Lê e valida os parâmetros.
3. Filtra as vendas quando solicitado.
4. Separa a página de registros.
5. Devolve um objeto JSON com a lista `dados` e metadados de paginação.

As rotas disponíveis são `/produtos`, `/vendas`, `/health` e `/docs`. Não há autenticação, pois o exercício usa apenas dados fictícios. É um servidor pequeno para demonstração, sem estrutura de operação de uma API de produção.

### Passo 6 — Testar o comportamento

Na pasta do projeto:

```bat
py -m unittest discover -s tests -v
```

Os seis testes verificam: disponibilidade/documentação; paginação sem perdas; filtros preservados entre páginas; parâmetros inválidos e rota inexistente; determinismo e chamadas repetidas; consistência da base e do gabarito. Eles fazem requisições HTTP reais em um servidor local temporário.

## 3. Consumir a API

### Carga completa para começar

Use `tamanho=2000`: os 1.001 registros cabem em uma única chamada. Isso permite concentrar a demonstração inicial no SQL.

```text
GET /produtos?tamanho=2000
GET /vendas?tamanho=2000
```

Não filtre o status na ingestão inicial: queremos manter as canceladas na Bronze e discutir a regra depois.

### Paginação para um segundo momento

```text
GET /vendas?pagina=1&tamanho=100
```

Resposta, com a lista abreviada apenas nesta explicação:

```json
{
  "versao_dataset": "workshop-v1",
  "dados": [],
  "pagina": 1,
  "tamanho": 100,
  "total_registros": 1001,
  "total_paginas": 11,
  "proxima_pagina": "/vendas?pagina=2&tamanho=100"
}
```

Na chamada real, `dados` contém os registros da página. `proxima_pagina` é um caminho relativo: concatene com o host. Quando for `null`, encerre o loop. `tamanho` aceita 1 a 2000; padrão 100. `pagina` começa em 1. Páginas além do final devolvem lista vazia. Uma busca vazia tem zero páginas.

### Filtro por período

```text
GET /vendas?data_inicio=2026-05-01&data_fim=2026-05-31&tamanho=2000
```

As datas inicial e final são inclusivas. Também pode usar `status=concluida` ou `status=cancelada`. Parâmetros incorretos retornam HTTP 400 com `erro`; rota inexistente retorna 404.

Esse filtro permite demonstrar cargas por período. Ele não é captura incremental de alterações: a API não possui `updated_at`, cursor de mudanças ou CDC.

## 4. Publicar para obter uma URL HTTPS

`localhost` funciona apenas no computador em que o processo está executando. Uma chamada feita pelo Skyone na nuvem não alcança o seu `localhost`. Para essa integração, publique a API em uma hospedagem acessível ao ambiente deles.

Exemplo com Render, seguindo a documentação oficial consultada em 27/10/2026:

1. Crie um repositório no GitHub e envie o conteúdo da pasta do projeto. `app.py`, `Dockerfile` e `dados/` devem ficar na raiz desse repositório. Se enviar a pasta inteira como subpasta, configure-a como diretório raiz no serviço.
2. Entre em https://render.com/ e escolha **New > Web Service**.
3. Conecte `anacpais/repos-ana-pais` e selecione a branch `main`. Deixe o diretório raiz vazio: o Dockerfile está na raiz.
4. Selecione o runtime **Docker**. O pacote já contém o `Dockerfile`; não precisa definir um comando de build Python.
5. Escolha um nome e uma modalidade de serviço apropriada. Confira as condições e eventuais custos antes de contratar.
6. Se houver configuração de health check, use `/health`.
7. Inicie a criação do serviço e aguarde o deploy.
8. Copie a URL HTTPS que o provedor atribuir. A URL pública será atribuída somente após publicar o serviço.
9. Teste `SUA_URL/health`, `SUA_URL/produtos?tamanho=2000` e `SUA_URL/vendas?tamanho=2000`.

O código já escuta em `0.0.0.0` e lê a variável `PORT` fornecida pela hospedagem. Os JSON ficam dentro da imagem Docker e continuam iguais após reiniciar o serviço. Nenhuma instalação adicional é necessária. A publicação não foi executada nesta entrega.

Se preferir executar via Docker local:

```sh
docker build -t api-workshop .
docker run --rm -p 8000:8000 api-workshop
```

O Dockerfile foi fornecido como configuração; os testes desta entrega foram executados diretamente com Python.

## 5. Conectar no Skyone Studio

A documentação oficial prevê módulos REST com JSON e operações GET. A sequência abaixo descreve a configuração pretendida; a tela e o mapeamento exato devem ser validados no ambiente deles. Esta entrega não executou chamadas dentro de uma conta Skyone.

1. Crie um módulo com conectividade REST.
2. Configure a conta/conexão com o host HTTPS obtido na publicação. Como nossa API é aberta, use a opção disponível de acesso sem autenticação.
3. Crie a operação de produtos com método GET e endpoint `/produtos`, usando `tamanho=2000` como parâmetro de query.
4. Crie a operação de vendas com método GET e endpoint `/vendas`, também com `tamanho=2000`.
5. Configure o cabeçalho `Accept: application/json`, se solicitado. Não há corpo de requisição para esses GETs.
6. Execute o teste de cada operação. A lista de registros é o campo `dados` da resposta. Os demais campos são metadados; não são linhas de venda.
7. Defina a estrutura de saída usando a resposta real do teste e os campos do dicionário acima.
8. No fluxo, conecte as operações à etapa de gravação disponível no ambiente. Para começar, preserve cada resposta original como JSON na Bronze, junto com instante da ingestão, lote e endpoint de origem. Se optar por uma Bronze tabular, mantenha os valores de origem e preserve também o payload original para rastreabilidade.
9. A partir da Bronze, execute as transformações SQL para Silver e Gold no engine configurado. A leitura/expansão de JSON, o DDL e o método de carga dependem desse engine; não suponha sintaxe de outro banco.

Atenção ao host: a documentação Skyone informa que o host da conexão é concatenado com a configuração da operação. Evite duplicar o domínio no endpoint.

Para o primeiro workshop, use uma única página por endpoint. Se depois demonstrar paginação, configure o loop para seguir `proxima_pagina` até `null`, preservando os filtros. Verifique no ambiente como a saída do REST e os loops são mapeados.

## 6. Roteiro sugerido para as camadas

| Camada | Objetos | Regra |
|---|---|---|
| Bronze | bronze_produtos, bronze_vendas | Conteúdo original + metadados de ingestão |
| Silver | silver_produtos | Tipar, normalizar categoria e garantir unicidade por id_produto |
| Silver | silver_vendas | Tipar, deduplicar por id_venda/numero_item e validar referência de produto |
| Silver | rejeicoes_vendas | Separar item com produto inexistente e registrar o motivo |
| Gold | dim_produto | Uma linha por produto, com chave substituta e atributos de categoria/marca |
| Gold | dim_data | Uma linha por data, com ano, mês e trimestre |
| Gold | fato_vendas | Um item de venda concluída e válida, ligado às duas dimensões |

Uma extração integral tem 1.001 linhas de vendas. Após deduplicar: 1.000. Separe a rejeição: 999 itens válidos na Silver, incluindo 100 cancelados. Filtrando os cancelados, a fato terá 899 itens.

Categoria e marca são atributos de `dim_produto`. Não crie dimensões adicionais para elas neste exercício. `id_venda` fica na fato como identificador do pedido, e não como uma dimensão com uma linha por pedido.

A API responde a mesma coisa quando chamada novamente. Isso facilita conferir o resultado, mas a idempotência da carga precisa ser implementada no pipeline: reprocessar não deve duplicar linhas na Silver/Gold. A Bronze pode guardar diferentes lotes de uma mesma extração para auditoria, desde que isso não multiplique a fato. Para simplificar a primeira demonstração, pode reconstruir integralmente as tabelas derivadas; depois discutir MERGE/UPSERT conforme o engine.

## 7. Gabarito para conferir no SQL

| Indicador | Esperado |
|---|---:|
| Produtos | 30 |
| Registros de venda na extração completa | 1.001 |
| Itens após deduplicação | 1.000 |
| Duplicatas removidas | 1 |
| Item sem produto cadastrado | 1 |
| Itens cancelados | 100 |
| Itens na fato | 899 |
| Pedidos distintos na fato | 450 |
| Quantidade vendida na fato | 2.666 |
| Receita líquida na fato | R$ 1.112.252,39 |

Um pedido continua na fato com seu segundo item mesmo quando o primeiro item é rejeitado. Por isso, permanecem 450 pedidos distintos.

| Mês | Receita líquida |
|---|---:|
| Abril/2026 | R$ 193.774,47 |
| Maio/2026 | R$ 157.288,00 |
| Junho/2026 | R$ 174.072,81 |
| Julho/2026 | R$ 182.912,52 |
| Agosto/2026 | R$ 234.717,85 |
| Setembro/2026 | R$ 169.486,74 |

O mesmo gabarito está em `dados/gabarito.json`. Os totais foram calculados com `Decimal`.

## 8. Arquivos do pacote

- `app.py`: servidor e validação das rotas.
- `gerar_dados.py`: geração dos dados e cálculo do gabarito.
- `docs.html`: documentação servida em `/docs`.
- `iniciar_windows.bat`: atalho para iniciar no Windows.
- `Dockerfile`: configuração para execução em contêiner.
- `tests/test_api.py`: testes HTTP e de consistência.
- `dados/*.json`: base usada pela API e gabarito.
- `dados/*.csv`: cópias da base para exercícios com arquivos.

## Referências oficiais

- Skyone — conectividade REST: https://docs.skyone.cloud/skyone-studio/modulos/configuracoes-and-operacoes/configuracoes-de-modulos/conectividade-rest
- Skyone — operações: https://docs.skyone.cloud/skyone-studio/modulos/configuracoes-and-operacoes/operacoes-de-modulos
- Skyone — Data Warehouse: https://docs.skyone.cloud/skyone-studio/data-warehouse
- Render — Web Services: https://render.com/docs/web-services
- Render — Docker: https://render.com/docs/docker

## Verificação da publicação e automação

Após obter a URL pública no Render, execute:

```sh
python scripts/verificar_api.py https://SEU-SERVICO.onrender.com
```

O comando verifica saúde, 30 produtos e 1.001 vendas. A pasta `.github/workflows/` configura os testes e o build Docker no GitHub Actions. O Blueprint `render.yaml` configura a publicação a partir de `main`. A publicação depende de conectar o GitHub na sua conta Render e confirmar a criação do serviço.

Este projeto é uma API pública de demonstração com dados fictícios e servidor HTTP da biblioteca padrão. Para dados reais ou uso em produção, adote servidor adequado, autenticação e limites de requisição. O HTTPS público é fornecido pelo Render.
