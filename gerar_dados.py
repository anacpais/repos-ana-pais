"""Base sintética reproduzível: Python 3.10+, somente biblioteca padrão."""
import csv
import json
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

PASTA = Path(__file__).parent / 'dados'

def gerar():
    rng = random.Random(42)
    produtos = []
    grupos = [('Eletrônicos', 'Aurora', ['Fone', 'Teclado', 'Mouse', 'Monitor', 'Webcam']),
              ('Casa', 'Lar Vivo', ['Luminária', 'Cadeira', 'Mesa', 'Organizador', 'Almofada']),
              ('Esporte', 'Movimento', ['Tapete', 'Garrafa', 'Halter', 'Bola', 'Mochila'])]
    for i in range(1, 31):
        categoria, marca, nomes = grupos[(i - 1) // 10]
        nome = nomes[(i - 1) % 5] + (' Essencial' if (i - 1) % 10 < 5 else ' Plus')
        produtos.append(dict(id_produto=i, nome=nome, categoria=categoria, marca=marca,
                             descricao=f'{nome} da marca {marca}', preco_atual=round(rng.randint(2500, 90000) / 100, 2)))
    produtos[1]['categoria'] = ' eletrônicos '
    produtos[4]['categoria'] = 'ELETRÔNICOS'
    vendas = []
    for n in range(1, 501):
        data_venda = date(2026, 4, 1) + timedelta(days=rng.randrange(183))
        status = 'cancelada' if n % 10 == 0 else 'concluida'
        for item in (1, 2):
            produto = rng.choice(produtos)
            preco = Decimal(rng.randint(2000, 85000)) / 100
            quantidade = rng.randint(1, 5)
            desconto = (preco * quantidade * Decimal(rng.choice(['0', '0.05', '0.10']))).quantize(Decimal('0.01'))
            vendas.append(dict(id_venda=f'V{n:05}', numero_item=item, data_venda=data_venda.isoformat(),
                               id_produto=produto['id_produto'], quantidade=quantidade,
                               preco_unitario=float(preco), desconto=float(desconto), status=status))
    vendas[0]['id_produto'] = 999  # concluída, cadastro inexistente
    vendas.append(dict(vendas[9]))  # cópia exata de V00005/item 2
    return produtos, vendas


def conferir(produtos, vendas):
    ids = {p['id_produto'] for p in produtos}
    unicas = {(v['id_venda'], v['numero_item']): v for v in vendas}
    validas = [v for v in unicas.values() if v['id_produto'] in ids and v['status'] == 'concluida']
    def liquido(v):
        return Decimal(str(v['preco_unitario'])) * v['quantidade'] - Decimal(str(v['desconto']))
    por_mes = {}
    for v in validas:
        mes = v['data_venda'][:7]
        por_mes[mes] = por_mes.get(mes, Decimal('0')) + liquido(v)
    return dict(produtos=len(produtos), registros_bronze_vendas=len(vendas),
                itens_apos_deduplicacao=len(unicas), duplicatas_removidas=len(vendas)-len(unicas),
                itens_produto_inexistente=sum(v['id_produto'] not in ids for v in unicas.values()),
                itens_cancelados=sum(v['status']=='cancelada' for v in unicas.values()),
                itens_fato_vendas=len(validas), pedidos_fato_vendas=len({v['id_venda'] for v in validas}),
                quantidade_total=sum(v['quantidade'] for v in validas),
                receita_liquida=f'{sum((liquido(v) for v in validas), Decimal(0)):.2f}',
                receita_por_mes={k: f'{v:.2f}' for k, v in sorted(por_mes.items())})

if __name__ == '__main__':
    PASTA.mkdir(exist_ok=True)
    produtos, vendas = gerar()
    for nome, dados in [('produtos', produtos), ('vendas', vendas)]:
        (PASTA / f'{nome}.json').write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
        with (PASTA / f'{nome}.csv').open('w', newline='', encoding='utf-8-sig') as arquivo:
            writer = csv.DictWriter(arquivo, fieldnames=list(dados[0]))
            writer.writeheader()
            writer.writerows(dados)
    (PASTA / 'gabarito.json').write_text(json.dumps(conferir(produtos, vendas), ensure_ascii=False, indent=2), encoding='utf-8')
    print('Arquivos criados em dados/.')
