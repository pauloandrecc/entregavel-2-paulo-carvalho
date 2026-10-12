# Anotador de Imagens

![CI](https://github.com/pauloandrecc/entregavel-2-paulo-carvalho/actions/workflows/ci.yml/badge.svg)

Programa em Python que lê bounding boxes de um arquivo CSV e as desenha sobre as imagens correspondentes usando OpenCV.

> **Status:** em desenvolvimento.

## Objetivo

- Ler `dados/anotacoes.csv` e agrupar as caixas pelo nome da imagem.
- Desenhar as caixas em cada imagem de `imagens/`, com cores por classe, identificação da imagem e legenda.
- Salvar as imagens anotadas em `resultados/`, mantendo nome e resolução originais.
- Exibir uma imagem por vez: `espaço` avança, `q` encerra.

## Dependências
 
| Pacote | Uso |
| --- | --- |
| Python >= 3.10 | linguagem |
| `opencv-python` (>=4.8, <5) | leitura, desenho e exibição das imagens (traz o NumPy junto) |
| `pytest` (dev) | testes automatizados |
| `pytest-cov` (dev) | relatório de cobertura de testes |
| `ruff` (dev) | lint e formatação |
| `poethepoet` (dev) | atalhos para os comandos de desenvolvimento (`poe`) |

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```
## Atalhos de desenvolvimento (Poe)
 
Os comandos mais usados estão definidos em `[tool.poe.tasks]` no `pyproject.toml` e
funcionam com o ambiente virtual ativo:
 
| Comando | O que faz | Equivalente |
| --- | --- | --- |
| `poe run` | executa o programa | `python -m anotador` |
| `poe test` | roda os testes | `pytest` |
| `poe cov` | roda os testes com cobertura | `pytest --cov=anotador --cov-report=term-missing` |
| `poe lint` | verifica o código com o ruff | `ruff check .` |
| `poe fmt-check` | verifica a formatação | `ruff format --check .` |
| `poe check` | lint, formatação e testes em sequência | os três acima |
 
Para listar as tarefas disponíveis: `poe --help`.

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

## Classes
 
As classes ficam em `src/anotador/modelos.py`.
 
### `Deteccao`
 
Representa uma bounding box. Guarda `classe_id`, `x_min`, `y_min`, `x_max` e `y_max`
e é imutável (`dataclass` com `frozen=True`). O método `desenhar(imagem)` desenha a
própria caixa na imagem recebida, usando a cor da classe definida em `CORES_BGR`
(classe 0 em verde, classe 1 em vermelho, no formato BGR do OpenCV). Uma classe sem
cor definida levanta `ValueError`.
 
### `ImagemAnotada`
 
Associa uma imagem às suas detecções. Guarda o `caminho` do arquivo e a lista
`deteccoes`. O método `adicionar_deteccao(deteccao)` inclui uma caixa na lista, e
`gerar_imagem()` lê o arquivo e devolve uma cópia com todas as caixas desenhadas,
chamando `desenhar` de cada detecção. O arquivo de entrada não é alterado e a
resolução original é mantida.

## Testes
 
```bash
poe test               # ou: python -m pytest
poe cov                # testes com cobertura no terminal
```
 
Para um relatório de cobertura em HTML (abra `htmlcov/index.html` no navegador):
 
```bash
pytest --cov=anotador --cov-report=html
```

Os testes ficam em `tests/`. O arquivo `tests/test_modelos.py` cobre `modelos.py` usando
imagens sintéticas (NumPy) e arquivos temporários (`tmp_path`), sem abrir janelas:
 
- `Deteccao`: valores armazenados, imutabilidade, cor da borda por classe, interior e área
  externa intactos, `shape` preservado e erro para classe sem cor.
- `ImagemAnotada`: lista de detecções independente por instância, ordem das detecções,
  todas as caixas desenhadas, resolução original, arquivo de entrada intacto e erro para
  caminho inexistente.

## Qualidade de código
 
```bash
poe lint               # ruff check .
poe fmt-check          # ruff format --check .
poe check              # lint + formatação + testes
```
 
O CI (GitHub Actions) roda lint, verificação de formatação e testes a cada push e pull request.