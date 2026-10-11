# Anotador de Imagens

![CI](https://github.com/pauloandrecc/entregavel-2-paulo-carvalho/actions/workflows/ci.yml/badge.svg)

Programa em Python que lê bounding boxes de um arquivo CSV e as desenha sobre as imagens correspondentes usando OpenCV.

> **Status:** em desenvolvimento.

## Objetivo

- Ler `dados/anotacoes.csv` e agrupar as caixas pelo nome da imagem.
- Desenhar as caixas em cada imagem de `imagens/`, com cores por classe, identificação da imagem e legenda.
- Salvar as imagens anotadas em `resultados/`, mantendo nome e resolução originais.
- Exibir uma imagem por vez: `espaço` avança, `q` encerra.

## Requisitos

- Python 3.10 ou superior

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Desenvolvimento

```bash
ruff check .             # lint
ruff format --check .    # formatação
pytest                   # testes
```

O CI (GitHub Actions) roda esses mesmos comandos a cada push e pull request.

## Estrutura

```
.
├── dados/          # anotacoes.csv
├── imagens/        # imagens de entrada (não são modificadas)
├── resultados/     # imagens anotadas geradas pelo programa
├── src/anotador/   # código-fonte
├── tests/          # testes automatizados
└── pyproject.toml
```