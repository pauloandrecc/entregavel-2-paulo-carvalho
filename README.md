# Anotador de Imagens

![CI](https://github.com/pauloandrecc/entregavel-2-paulo-carvalho/actions/workflows/ci.yml/badge.svg)

**Autor:** Paulo André Cardoso Carvalho

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
| `poe cov-html` | gera o relatório de cobertura em `htmlcov/` | `pytest --cov=anotador --cov-report=html` |
| `poe lint` | verifica o código com o ruff | `ruff check .` |
| `poe fmt-check` | verifica a formatação | `ruff format --check .` |
| `poe check` | lint, formatação e testes em sequência | os três acima |
| `poe fix` | aplica as correções automáticas do lint | `ruff check --fix .` |
| `poe format` | formata o código | `ruff format .` |
| `poe fmt` | `fix` e depois `format` | os dois acima |

Para listar as tarefas disponíveis: `poe --help`.

## Execução

Com o ambiente virtual ativado, na raiz do projeto:

```bash
poe run                # ou: python -m anotador
```

Uma execução completa gera dez imagens anotadas em `resultados/`.

Sem argumentos, o programa usa caminhos relativos à pasta atual, por isso deve ser executado
na raiz do projeto. As opções abaixo são todas opcionais:

| Opção | Padrão | Descrição |
| --- | --- | --- |
| `--csv` | `dados/anotacoes.csv` | arquivo de anotações |
| `--imagens` | `imagens` | pasta das imagens de entrada |
| `--resultados` | `resultados` | pasta das imagens anotadas |

```bash
python -m anotador --imagens outras_imagens --resultados saida
```

Para cada imagem, o terminal mostra o nome e a quantidade de caixas desenhadas, e no final
o total de imagens processadas:

```
a.png - caixas desenhadas: 2
b.png - caixas desenhadas: 0
c.png - caixas desenhadas: 1
3 imagens processadas; resultados em resultados
```

## Controles do visualizador

| Tecla | Ação |
| --- | --- |
| `Espaço` | avança para a próxima imagem |
| `q` | encerra o programa |
| qualquer outra | mantém a imagem atual |

Fechar a janela no botão de fechar do sistema também encerra o programa. Ao chegar à
última imagem, as janelas são fechadas.

## Leitura do CSV

O módulo `src/anotador/leitura.py` lê `dados/anotacoes.csv` com o módulo `csv` da
biblioteca padrão. O arquivo deve ter o cabeçalho:

```csv
imagem,classe_id,x_min,y_min,x_max,y_max
```

A função `ler_anotacoes(caminho)` devolve uma lista de `LinhaAnotacao` (um `TypedDict`),
uma por linha do arquivo e na mesma ordem, com `classe_id`, `x_min`, `y_min`, `x_max` e
`y_max` convertidos para `int`. As colunas podem estar em qualquer ordem.

Erros:

- `FileNotFoundError`, se o arquivo não existir;
- `ValueError`, se faltar alguma coluna no cabeçalho ou se um valor numérico for inválido
  (texto, decimal ou vazio). A mensagem informa o número da linha com problema.

## Agrupamento por imagem

O módulo `src/anotador/agrupamento.py` transforma as linhas lidas do CSV em objetos e
agrupa as caixas pela imagem a que pertencem.

A função `agrupar_por_imagem(linhas, diretorio_imagens)` devolve um dicionário que associa
o nome de cada imagem a um `ImagemAnotada`, cujo caminho é `diretorio_imagens / nome`. Cada
linha vira uma `Deteccao` adicionada à imagem correspondente.

- Funciona mesmo que as linhas de uma imagem estejam separadas ou fora de ordem no CSV.
- As chaves seguem a ordem da primeira aparição no arquivo e as detecções de cada imagem
  seguem a ordem das linhas. A ordem alfabética das imagens é aplicada na hora de percorrê-las.
- Imagens sem nenhuma linha no CSV não aparecem no dicionário.
- A função não acessa o disco; a existência dos arquivos só é verificada ao gerar a imagem.

## Estrutura

```
.
├── dados/
│   └── anotacoes.csv   # uma bounding box por linha
├── imagens/            # imagens de entrada (não são modificadas)
├── resultados/         # imagens anotadas geradas pelo programa
├── src/anotador/
│   ├── __init__.py
│   ├── __main__.py     # permite executar com python -m anotador
│   ├── agrupamento.py  # agrupamento das caixas por imagem
│   ├── arquivos.py     # listagem ordenada e salvamento das imagens
│   ├── desenho.py      # identificação e legenda para a janela de exibição
│   ├── leitura.py      # leitura do CSV e conversão para inteiros
│   ├── main.py         # loop de exibição e execução principal
│   └── modelos.py      # Deteccao e ImagemAnotada
├── tests/
│   ├── test_agrupamento.py
│   ├── test_arquivos.py
│   ├── test_desenho.py
│   ├── test_leitura.py
│   ├── test_main.py
│   └── test_modelos.py
└── pyproject.toml
```

## Desenho

As caixas são desenhadas por `Deteccao.desenhar` (ver [Classes](#classes)). O módulo
`src/anotador/desenho.py` acrescenta, para a janela de exibição, a identificação da imagem
e a legenda das cores:

- `desenhar_identificacao(imagem, texto)`: escreve o nome da imagem no canto superior
  esquerdo, sobre um fundo escuro para ficar legível.
- `desenhar_legenda(imagem, cores)`: desenha no canto inferior esquerdo uma linha por
  classe, com a amostra da cor e o id (`Classe 0`, `Classe 1`), em ordem crescente de id.
  Por padrão usa `CORES_BGR`, o mesmo dicionário usado para desenhar as caixas, então as
  cores da legenda sempre correspondem às das caixas.
- `montar_imagem_de_exibicao(imagem, nome_imagem)`: devolve uma **cópia** da imagem com a
  identificação e a legenda, sem alterar a original e mantendo a resolução.
O tamanho do texto cresce proporcionalmente à resolução da imagem (referência de 800 px no
menor lado), para continuar legível em imagens grandes.

A identificação e a legenda aparecem só na janela. As imagens salvas em `resultados/`
contêm apenas as caixas, com a resolução original.

## Listagem e salvamento das imagens

O módulo `src/anotador/arquivos.py` cuida dos arquivos de imagem.

`listar_imagens(diretorio)` devolve os caminhos das imagens da pasta em ordem alfabética,
sem diferenciar maiúsculas de minúsculas. Só entram arquivos `.jpg`, `.jpeg`, `.png` e
`.bmp` (em qualquer caixa); subpastas e outros tipos de arquivo são ignorados. A ordem é
alfabética simples, não "natural": `img10.png` vem antes de `img2.png`, então use zeros à
esquerda nos nomes (`img_01`, `img_02`, ...). Se a pasta não existir, levanta
`FileNotFoundError`.

`salvar_resultado(imagem, caminho_origem, diretorio_resultados)` grava a imagem anotada em
`resultados/` com o mesmo nome do arquivo de origem e sem redimensionar. A pasta é criada se
não existir, um resultado anterior com o mesmo nome é substituído e o caminho salvo é
devolvido.

- As imagens de entrada nunca são sobrescritas: se o destino for o próprio arquivo de
  origem (por exemplo, pasta de resultados igual à de imagens), levanta `ValueError`.
- Se a gravação falhar, levanta `OSError`.
- Imagens JPG são recodificadas ao salvar: a resolução se mantém, mas os valores dos pixels
  mudam um pouco. Em PNG a cópia é exata.

## Execução principal

O módulo `src/anotador/main.py` junta as etapas anteriores.

`executar(arquivo_csv, diretorio_imagens, diretorio_resultados, exibir)` lê o CSV, agrupa as
caixas, lista as imagens em ordem alfabética e, para cada uma:

1. desenha as caixas e salva o resultado em `resultados/`;
2. mostra no terminal o nome da imagem e a quantidade de caixas desenhadas;
3. exibe a imagem, com identificação e legenda, até o usuário avançar ou sair.
Devolve quantas imagens foram processadas.

- A imagem é salva **antes** de ser exibida. Se o usuário sair com `q` na terceira imagem,
  as três primeiras já estão em `resultados/`; as demais não são processadas. Para gerar as
  dez, é preciso avançar até o fim.
- Imagens sem nenhuma anotação também são processadas e salvas, com zero caixas.
- Se o CSV citar imagens que não existem na pasta, um aviso é mostrado no `stderr`.
- A função de exibição é recebida como parâmetro (`exibir`). Na execução real é
  `mostrar_e_esperar`; nos testes, um substituto sem janela.
`interpretar_tecla(tecla)` traduz o código devolvido por `cv2.waitKey`: espaço avança, `q`
encerra e qualquer outra tecla mantém a imagem atual.

`mostrar_e_esperar(titulo, imagem)` abre uma janela redimensionável do OpenCV, mostra a
imagem e espera uma tecla (espaço ou `q`) ou o fechamento da janela. A janela é redimensionável
apenas na tela: o arquivo salvo mantém a resolução original.

`main(argv)` lê as opções da linha de comando, chama `executar` e fecha todas as janelas ao
final, mesmo em caso de erro. Devolve 0 em caso de sucesso e 1 se ocorrer um erro.

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

O arquivo `tests/test_leitura.py` cobre `leitura.py` com CSVs temporários (`tmp_path`):
conversão para `int`, ordem preservada, colunas em outra ordem, espaços e BOM UTF-8,
arquivo vazio ou só com cabeçalho, coluna faltando, valor numérico inválido (com o número
da linha no erro) e arquivo inexistente.

O arquivo `tests/test_agrupamento.py` cobre `agrupamento.py`: entrada vazia, linhas
consecutivas e separadas da mesma imagem, imagens que não se misturam, valores copiados
para a `Deteccao`, ordem das detecções e das chaves, caminho da imagem, entrada como
iterável e um teste que lê um CSV embaralhado e agrupa o resultado.

O arquivo `tests/test_desenho.py` cobre `desenho.py` com imagens sintéticas: a identificação
fica no canto superior esquerdo e a legenda no inferior esquerdo, as cores correspondem às
das classes e aparecem em ordem crescente de id, a imagem original não é alterada, a
resolução é mantida, o texto cresce com a resolução e imagens muito pequenas não geram erro.

O arquivo `tests/test_arquivos.py` cobre `arquivos.py` com pastas temporárias (`tmp_path`):
ordem alfabética (com arquivos criados fora de ordem e sem diferenciar maiúsculas), filtro
de extensões, subpastas ignoradas, pasta vazia ou inexistente, nome preservado ao salvar,
pasta de resultados criada, resolução e conteúdo mantidos, resultado anterior substituído,
imagem de entrada intacta (inclusive quando a pasta de saída é a mesma da entrada) e erro
quando a gravação falha.

O arquivo `tests/test_main.py` cobre `main.py` usando um exibidor falso no lugar da janela:
interpretação das teclas, ordem alfabética, uma imagem salva por entrada com nome e resolução
originais, cores das caixas no arquivo salvo, imagem sem anotação, identificação e legenda só
na exibição, entradas intactas, saída do terminal, `q` interrompendo o percurso, aviso de
imagens ausentes, pasta sem imagens, CSV inexistente, opções da linha de comando e a função
`main` (código 0 em caso de sucesso, código 1 em caso de erro e janelas sempre fechadas).

As funções `mostrar_e_esperar` e `_janela_fechada` usam a janela real do OpenCV. Por isso
ficam fora dos testes automatizados e da medição de cobertura (`# pragma: no cover`) e devem
ser verificadas manualmente:

1. rode `poe run` na raiz do projeto;
2. avance com `espaço` e confira que o terminal mostra o nome e a quantidade de caixas;
3. aperte outras teclas e confira que a imagem não muda;
4. saia com `q` em uma execução e feche a janela no botão de fechar em outra;
5. numa execução completa, confira que `resultados/` tem as dez imagens, com a resolução
   original, e que as imagens de `imagens/` não foram alteradas.

## Qualidade de código

```bash
poe lint               # ruff check .
poe fmt-check          # ruff format --check .
poe check              # lint + formatação + testes
poe fmt                # corrige o lint (o que for automático) e formata o código
```

O CI (GitHub Actions) roda lint, verificação de formatação e testes a cada push e pull request.
