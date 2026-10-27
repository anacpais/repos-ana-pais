import json
import threading
import unittest
from decimal import Decimal
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen
from pathlib import Path
from app import Handler, PRODUTOS, VENDAS
from gerar_dados import conferir, gerar

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
    def get(self, path):
        with urlopen(self.base + path, timeout=5) as r:
            return json.load(r)
    def test_health_and_docs(self):
        self.assertEqual(self.get('/health')['status'], 'ok')
        with urlopen(self.base + '/docs') as r:
            self.assertIn(b'/produtos', r.read())
    def test_paginacao_sem_perdas(self):
        path, dados = '/vendas?tamanho=73', []
        while path:
            resposta = self.get(path)
            dados.extend(resposta['dados'])
            path = resposta['proxima_pagina']
        self.assertEqual(dados, VENDAS)
        self.assertEqual(self.get('/vendas?pagina=100')['dados'], [])
    def test_filtros_e_preservacao_na_paginacao(self):
        path = '/vendas?data_inicio=2026-05-01&data_fim=2026-05-31&status=concluida&tamanho=7'
        dados = []
        while path:
            resposta = self.get(path)
            dados.extend(resposta['dados'])
            path = resposta['proxima_pagina']
        esperado = [v for v in VENDAS if '2026-05-01' <= v['data_venda'] <= '2026-05-31' and v['status']=='concluida']
        self.assertEqual(dados, esperado)
        self.assertEqual(self.get('/vendas?data_inicio=2030-01-01')['total_registros'], 0)
    def test_erros(self):
        for path in ['/vendas?pagina=0', '/vendas?tamanho=2001', '/vendas?pagina=x',
                     '/vendas?data_inicio=2026-02-30', '/vendas?status=errado',
                     '/vendas?data_inicio=2026-06-01&data_fim=2026-05-01',
                     '/produtos?status=concluida', '/vendas?pagina=1&pagina=2', '/vendas?data_inicio=']:
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as erro:
                    self.get(path)
                self.assertEqual(erro.exception.code, 400)
        with self.assertRaises(HTTPError) as erro:
            self.get('/inexistente')
        self.assertEqual(erro.exception.code, 404)
    def test_determinismo_e_requisicoes_repetidas(self):
        p, v = gerar()
        self.assertEqual(p, PRODUTOS)
        self.assertEqual(v, VENDAS)
        self.assertEqual(self.get('/vendas?tamanho=2000'), self.get('/vendas?tamanho=2000'))
    def test_cenario_e_gabarito(self):
        salvo = json.loads((Path(__file__).resolve().parents[1] / 'dados/gabarito.json').read_text())
        self.assertEqual(conferir(PRODUTOS, VENDAS), salvo)
        self.assertEqual(len(PRODUTOS), 30)
        self.assertEqual(len(VENDAS), 1001)
        self.assertEqual(len({(v['id_venda'],v['numero_item']) for v in VENDAS}), 1000)
        ids = {p['id_produto'] for p in PRODUTOS}
        self.assertEqual(sum(v['id_produto'] not in ids for v in VENDAS), 1)
        for v in VENDAS:
            self.assertLessEqual(Decimal(str(v['desconto'])), Decimal(str(v['preco_unitario'])) * v['quantidade'])
if __name__ == '__main__':
    unittest.main()
