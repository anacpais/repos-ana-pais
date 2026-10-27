"""Valide a publicação: python scripts/verificar_api.py https://seu-servico.onrender.com"""
import json
import sys
from urllib.parse import urlsplit
from urllib.request import urlopen


def verificar(base):
    base = base.rstrip('/')
    url = urlsplit(base)
    if url.scheme not in ('http', 'https') or not url.netloc or url.query or url.fragment:
        raise ValueError('Informe a URL base da API, sem query ou fragmento.')
    for caminho, chave, esperado in (
        ('/health', 'status', 'ok'),
        ('/produtos?tamanho=2000', 'total_registros', 30),
        ('/vendas?tamanho=2000', 'total_registros', 1001),
    ):
        with urlopen(base + caminho, timeout=90) as resposta:
            dados = json.load(resposta)
            if resposta.status != 200 or dados.get(chave) != esperado:
                raise RuntimeError(f'Resposta inesperada em {caminho}')
            if 'dados' in dados and len(dados['dados']) != esperado:
                raise RuntimeError(f'Lista incompleta em {caminho}')
        print(f'OK {caminho}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Uso: python scripts/verificar_api.py https://seu-servico.onrender.com')
    verificar(sys.argv[1])
