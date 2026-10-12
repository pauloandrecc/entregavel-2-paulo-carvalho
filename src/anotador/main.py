import argparse
import contextlib
import sys
from collections.abc import Callable, Sequence
from enum import Enum, auto
from pathlib import Path

import cv2
import numpy as np

from anotador.agrupamento import agrupar_por_imagem
from anotador.arquivos import listar_imagens, salvar_resultado
from anotador.desenho import montar_imagem_de_exibicao
from anotador.leitura import ler_anotacoes
from anotador.modelos import ImagemAnotada

NOME_JANELA = "Anotador de Imagens"
INTERVALO_MS = 50
TECLA_AVANCAR = ord(" ")
TECLA_SAIR = ord("q")


class Acao(Enum):
    AVANCAR = auto()
    SAIR = auto()
    MANTER = auto()


# Recebe o nome da imagem e a imagem a exibir; só devolve quando o usuário decidir
# avançar ou sair. Na execução real é `mostrar_e_esperar`; nos testes, um substituto.
Exibidor = Callable[[str, np.ndarray], Acao]


def interpretar_tecla(tecla: int) -> Acao:
    """Traduz o código devolvido por `cv2.waitKey`: espaço avança, `q` sai, o resto mantém."""
    codigo = tecla & 0xFF  # alguns backends devolvem bits extras (modificadores)
    if codigo == TECLA_AVANCAR:
        return Acao.AVANCAR
    if codigo == TECLA_SAIR:
        return Acao.SAIR
    return Acao.MANTER


def _janela_fechada() -> bool:  # pragma: no cover
    try:
        return cv2.getWindowProperty(NOME_JANELA, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True


def mostrar_e_esperar(titulo: str, imagem: np.ndarray) -> Acao:  # pragma: no cover
    """Mostra a imagem na janela do OpenCV e espera espaço ou `q`.

    Qualquer outra tecla mantém a imagem atual. Fechar a janela equivale a sair.
    """
    cv2.namedWindow(NOME_JANELA, cv2.WINDOW_NORMAL)
    cv2.imshow(NOME_JANELA, imagem)
    with contextlib.suppress(cv2.error):  # nem todos os backends permitem mudar o título
        cv2.setWindowTitle(NOME_JANELA, f"{NOME_JANELA} - {titulo}")

    while True:
        acao = interpretar_tecla(cv2.waitKey(INTERVALO_MS))
        if acao is not Acao.MANTER:
            return acao
        if _janela_fechada():
            return Acao.SAIR


def executar(
    arquivo_csv: Path,
    diretorio_imagens: Path,
    diretorio_resultados: Path,
    exibir: Exibidor,
) -> int:
    """Percorre as imagens em ordem alfabética, anota, salva e exibe cada uma.

    Para cada imagem: desenha as caixas, salva o resultado, mostra no terminal o nome e a
    quantidade de caixas e exibe a imagem (com identificação e legenda) até o usuário
    avançar ou sair. Imagens sem anotação também são salvas, com zero caixas.

    Devolve quantas imagens foram processadas.

    Raises:
        FileNotFoundError, ValueError, OSError: erros de leitura do CSV, das imagens ou
            de gravação dos resultados.
    """
    linhas = ler_anotacoes(arquivo_csv)
    grupos = agrupar_por_imagem(linhas, diretorio_imagens)
    imagens = listar_imagens(diretorio_imagens)

    ausentes = sorted(set(grupos) - {caminho.name for caminho in imagens})
    if ausentes:
        print(
            f"Aviso: o CSV cita imagens que não estão em {diretorio_imagens}: "
            f"{', '.join(ausentes)}",
            file=sys.stderr,
        )

    processadas = 0
    for caminho in imagens:
        anotada = grupos.get(caminho.name)
        if anotada is None:
            anotada = ImagemAnotada(caminho)

        imagem = anotada.gerar_imagem()
        salvar_resultado(imagem, caminho, diretorio_resultados)
        print(f"{caminho.name} - caixas desenhadas: {len(anotada.deteccoes)}")
        processadas += 1

        exibicao = montar_imagem_de_exibicao(imagem, caminho.name)
        if exibir(caminho.name, exibicao) is Acao.SAIR:
            break

    return processadas


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anotador",
        description="Desenha as bounding boxes de um CSV sobre as imagens e mostra o resultado.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("dados/anotacoes.csv"),
        help="arquivo de anotações (padrão: %(default)s)",
    )
    parser.add_argument(
        "--imagens",
        type=Path,
        default=Path("imagens"),
        help="pasta das imagens de entrada (padrão: %(default)s)",
    )
    parser.add_argument(
        "--resultados",
        type=Path,
        default=Path("resultados"),
        help="pasta das imagens anotadas (padrão: %(default)s)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = criar_parser().parse_args(argv)
    try:
        total = executar(args.csv, args.imagens, args.resultados, mostrar_e_esperar)
    except (OSError, ValueError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    finally:
        cv2.destroyAllWindows()

    print(f"{total} imagens processadas; resultados em {args.resultados}")
    return 0
