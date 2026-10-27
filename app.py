"""API didática somente leitura. Inicie com: python app.py"""
import json
import os
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

PASTA = Path(__file__).parent
PRODUTOS = json.loads((PASTA / 'dados/produtos.json').read_text(encoding='utf-8'))
VENDAS = json.loads((PASTA / 'dados/vendas.json').read_text(encoding='utf-8'))
VERSAO = 'workshop-v1'

class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, dados, tipo='application/json; charset=utf-8'):
        corpo = (json.dumps(dados, ensure_ascii=False) if tipo.startswith('application/json') else dados).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(len(corpo)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        url = urlsplit(self.path)
        caminho = url.path.rstrip('/') or '/'
        if caminho in ('/', '/docs'):
            self.responder(200, (PASTA / 'docs.html').read_text(encoding='utf-8'), 'text/html; charset=utf-8')
            return
        if caminho == '/health':
            self.responder(200, {'status': 'ok', 'versao_dataset': VERSAO})
            return
        if caminho not in ('/produtos', '/vendas'):
            self.responder(404, {'erro': 'Rota inexistente. Consulte /docs.'})
            return
        params = parse_qs(url.query, keep_blank_values=True)
        permitidos = {'pagina', 'tamanho'} | ({'data_inicio', 'data_fim', 'status'} if caminho == '/vendas' else set())
        try:
            if set(params) - permitidos or any(len(v) != 1 for v in params.values()):
                raise ValueError('Parâmetro desconhecido ou repetido.')
            pagina = int(params.get('pagina', ['1'])[0])
            tamanho = int(params.get('tamanho', ['100'])[0])
            if pagina < 1 or not 1 <= tamanho <= 2000:
                raise ValueError('pagina deve ser >= 1; tamanho deve estar entre 1 e 2000.')
            inicio = params.get('data_inicio', [None])[0]
            fim = params.get('data_fim', [None])[0]
            for data in (inicio, fim):
                if data is not None and date.fromisoformat(data).isoformat() != data:
                    raise ValueError('Use datas no formato AAAA-MM-DD.')
            if inicio and fim and inicio > fim:
                raise ValueError('data_inicio deve ser menor ou igual a data_fim.')
            status = params.get('status', [None])[0]
            if status is not None and status not in ('concluida', 'cancelada'):
                raise ValueError('status deve ser concluida ou cancelada.')
        except ValueError as erro:
            self.responder(400, {'erro': str(erro)})
            return
        registros = PRODUTOS if caminho == '/produtos' else VENDAS
        if caminho == '/vendas':
            registros = [v for v in registros if (not inicio or v['data_venda'] >= inicio)
                         and (not fim or v['data_venda'] <= fim)
                         and (not status or v['status'] == status)]
        total = len(registros)
        paginas = (total + tamanho - 1) // tamanho
        proxima = None
        if pagina < paginas:
            consulta = {k: v[0] for k, v in params.items()}
            consulta.update(pagina=pagina + 1, tamanho=tamanho)
            proxima = caminho + '?' + urlencode(consulta)
        offset = (pagina - 1) * tamanho
        self.responder(200, dict(versao_dataset=VERSAO, dados=registros[offset:offset+tamanho],
                                pagina=pagina, tamanho=tamanho, total_registros=total,
                                total_paginas=paginas, proxima_pagina=proxima))

if __name__ == '__main__':
    host, port = os.environ.get('HOST', '0.0.0.0'), int(os.environ.get('PORT', '8000'))
    print(f'API iniciada na porta {port}. Local: http://localhost:{port}/docs', flush=True)
    try:
        ThreadingHTTPServer((host, port), Handler).serve_forever()
    except KeyboardInterrupt:
        print('\nAPI encerrada.')
