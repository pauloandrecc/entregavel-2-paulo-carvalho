from collections.abc import Iterable
from pathlib import Path

from anotador.leitura import LinhaAnotacao
from anotador.modelos import Deteccao, ImagemAnotada


def agrupar_por_imagem(
    linhas: Iterable[LinhaAnotacao], diretorio_imagens: Path
) -> dict[str, ImagemAnotada]:
    grupos: dict[str, ImagemAnotada] = {}

    for linha in linhas:
        nome = linha["imagem"]
        if nome not in grupos:
            grupos[nome] = ImagemAnotada(diretorio_imagens / nome)
        grupos[nome].adicionar_deteccao(
            Deteccao(
                classe_id=linha["classe_id"],
                x_min=linha["x_min"],
                y_min=linha["y_min"],
                x_max=linha["x_max"],
                y_max=linha["y_max"],
            )
        )

    return grupos
