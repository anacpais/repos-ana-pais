# Publicar a API e conectar ao Skyone Studio

Repositório: https://github.com/anacpais/repos-ana-pais

Branch para implantação: **`main`**.

O GitHub guarda os arquivos. O Render executará a API e fornecerá uma URL HTTPS. A conexão GitHub do ChatGPT não autoriza automaticamente o Render; essa conexão será feita na sua conta Render.

## 1. Conferir o repositório

Depois de enviar o pacote, os arquivos da API devem ficar na raiz: `app.py`, `Dockerfile`, `docs.html`, `gerar_dados.py`, `dados/`, `tests/` e os guias. Não precisa enviá-los manualmente se já aparecem no GitHub.

Os arquivos deste pacote estão na raiz da branch `main`. Não é necessário excluir arquivos antigos nem fazer upload manual. O histórico Git preserva as versões anteriores.

### Publicação usando o Blueprint

1. Envie os arquivos para a branch `main` no GitHub.
2. No Render, selecione **New > Blueprint** e conecte este repositório.
3. Selecione `main` e confira o serviço definido em `render.yaml`.
4. O arquivo solicita o plano gratuito; confira a disponibilidade e as condições na sua conta antes de confirmar. Serviços gratuitos podem suspender por inatividade.
5. Confirme a criação e aguarde o deploy. O Render fornecerá a URL HTTPS.

O Blueprint já configura Docker, porta 10000 e health check `/health`. Não precisa de banco, token ou chave da Skyone. Como alternativa, configure manualmente conforme a próxima seção.

## 2. Publicar no Render

1. Acesse https://dashboard.render.com/ e entre ou crie sua conta.
2. Clique em **New > Web Service**.
3. Escolha **Git Provider**, conecte o GitHub e autorize acesso ao repositório `repos-ana-pais`.
4. Selecione `anacpais/repos-ana-pais`.
5. Preencha os campos abaixo.

| Campo | Valor |
|---|---|
| Name | `api-workshop-vendas-ana` ou outro disponível |
| Branch | `main` |
| Language / Runtime | **Docker** |
| Root Directory | Deixe vazio |
| Dockerfile Path | `./Dockerfile`, se solicitado |
| Docker Command | Deixe vazio; o Dockerfile já define o comando |
| Health Check Path | `/health`, se disponível |

6. Escolha a região e a modalidade de serviço, verificando as condições e eventuais custos antes de contratar.
7. Não precisa criar banco de dados, disco persistente ou variáveis de senha. Não há dependências pip para instalar.
8. Clique no botão de criação/Deploy e aguarde o serviço ficar ativo.
9. Copie a URL HTTPS exibida no painel. O nome acima é uma sugestão, não uma URL já criada.

O código escuta em `0.0.0.0` e usa a variável `PORT` da hospedagem. Os dados JSON ficam dentro da imagem e permanecem iguais após reiniciar.

## 3. Testar o endereço público

Substitua `SUA_URL` pela URL real, sem barra no final, e abra no navegador:

| Endereço | Esperado |
|---|---|
| `SUA_URL/health` | JSON com `status: ok` |
| `SUA_URL/docs` | Documentação da API |
| `SUA_URL/produtos?tamanho=2000` | `total_registros: 30` |
| `SUA_URL/vendas?tamanho=2000` | `total_registros: 1001` |

A API publicada independe do seu computador ligado. O serviço de hospedagem precisa estar ativo; conforme a modalidade, a primeira chamada após inatividade pode demorar.

Não use o endereço do repositório, o painel de logs do Render ou `localhost` como host do Skyone. Use a URL pública HTTPS da API.

## 4. Configurar o módulo REST no Skyone

Os nomes seguem a documentação oficial; valide as telas disponíveis na conta.

1. Crie um módulo chamado **API Workshop Vendas**.
2. Em **Configurações**, escolha conectividade **REST**.
3. Em autenticação, escolha **No Auth**. A API não pede token ou senha.
4. Em **Conta conectada > Adicionar conta conectada**, use a URL HTTPS como Host, seguindo os campos da tela.
5. Salve as configurações para habilitar as operações.

O Host da conexão é concatenado com o endpoint da operação: informe o domínio uma única vez.

## 5. Criar duas operações

Clique em **Nova operação** e configure:

| Campo | Produtos | Vendas |
|---|---|---|
| Nome | Listar produtos | Listar vendas |
| Método | GET | GET |
| Caminho relativo / PATH | `/produtos` | `/vendas` |
| Parâmetro de query | `tamanho=2000` | `tamanho=2000` |
| Corpo | Nenhum | Nenhum |
| Coleção de saída | `dados` | `dados` |

Se necessário, declare o parâmetro `tamanho` como inteiro na etapa de parâmetros e informe 2000 ao testar/executar. Confira que a URL final seja `SUA_URL/produtos?tamanho=2000` ou `SUA_URL/vendas?tamanho=2000`.

O cabeçalho `Accept: application/json` pode ser informado. Execute o teste e configure a estrutura de saída a partir do JSON real, selecionando a lista `dados`. Os outros campos são metadados de paginação.

A opção **FULL URL** permite informar o endereço completo, se esse for o formato preferido na conta. Evite duplicar o domínio na concatenação.

Não filtre `status` na carga inicial: queremos preservar as canceladas na Bronze. O padrão de tamanho é 100; sem `tamanho=2000`, você receberá só a primeira página de vendas. A base inteira cabe em uma chamada com tamanho 2000.

## 6. Gravar e transformar

1. Crie um fluxo com um gatilho de execução disponível no ambiente e inclua as duas operações REST.
2. Confira 30 produtos e 1.001 registros de venda nas respostas.
3. Encaminhe a saída para a gravação disponível no Data Lake/Data Warehouse configurado. Uma operação REST não cria tabelas automaticamente.
4. Preserve o JSON original na Bronze com lote, origem e instante de ingestão. Se a Bronze for tabular, expanda `dados` e preserve também o payload para rastreabilidade.
5. Use SQL na Silver para tipar campos, normalizar categorias e deduplicar itens por `id_venda` + `numero_item`. Separe o produto inexistente em rejeições.
6. Na Gold, crie `dim_produto`, `dim_data` e `fato_vendas`, incluindo na fato apenas itens válidos de vendas concluídas.

O mapeamento da saída, a gravação e a sintaxe SQL dependem dos recursos e do engine da conta Skyone. O teste autenticado nessa conta não foi executado nesta preparação.

## 7. Conferir os totais

| Indicador | Esperado |
|---|---:|
| Produtos | 30 |
| Registros recebidos de vendas | 1.001 |
| Itens após deduplicar | 1.000 |
| Rejeitados por produto inexistente | 1 |
| Itens válidos na Silver, incluindo cancelados | 999 |
| Itens cancelados | 100 |
| Itens na fato | 899 |
| Pedidos distintos na fato | 450 |
| Receita líquida | R$ 1.112.252,39 |

Receita líquida = quantidade × preço unitário da venda − desconto total do item. Use DECIMAL para moeda. O detalhamento está em `dados/gabarito.json` e no README.

Repetir a chamada devolve os mesmos dados. A carga SQL deve evitar duplicações na Silver e Gold; a resposta fixa não implementa idempotência no pipeline.

## Problemas comuns

| Problema | Conferir |
|---|---|
| Dockerfile não encontrado | Branch correta, Root Directory vazio e caminho `./Dockerfile` |
| Pedido de requirements.txt | Selecione Docker como runtime |
| Skyone não conecta | Teste a URL pública em `/health` |
| Só chegam 100 vendas | Use tamanho 2000 ou implemente paginação |
| HTTP 404 | Confira `/produtos` e `/vendas` |
| HTTP 400 | Verifique os parâmetros; datas devem usar AAAA-MM-DD |
| Faturamento multiplicado | Revise deduplicação, joins e reprocessamento |

## Referências oficiais

Consultadas em 27/10/2026:

- https://render.com/docs/web-services
- https://render.com/docs/docker
- https://docs.skyone.cloud/skyone-studio/modulos/configuracoes-and-operacoes/configuracoes-de-modulos/conectividade-rest
- https://docs.skyone.cloud/skyone-studio/modulos/configuracoes-and-operacoes/operacoes-de-modulos
