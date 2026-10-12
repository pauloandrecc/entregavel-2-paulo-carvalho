import csv
from pathlib import Path
from typing import TypedDict

from anotador.modelos import CORES_BGR

COLUNA_IMAGEM = "imagem"
COLUNAS_INTEIRAS = ("classe_id", "x_min", "y_min", "x_max", "y_max")
COLUNAS_OBRIGATORIAS = (COLUNA_IMAGEM, *COLUNAS_INTEIRAS)


class LinhaAnotacao(TypedDict):
    imagem: str
    classe_id: int
    x_min: int
    y_min: int
    x_max: int
    y_max: int


def ler_anotacoes(caminho: Path) -> list[LinhaAnotacao]:
    # utf-8-sig descarta o BOM que o Excel costuma adicionar ao salvar CSV.
    with caminho.open(newline="", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo)

        colunas = leitor.fieldnames or []
        faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in colunas]
        if faltando:
            raise ValueError(f"{caminho}: colunas ausentes no cabeçalho: {', '.join(faltando)}")

        linhas: list[LinhaAnotacao] = []
        for linha in leitor:
            prefixo = f"{caminho}: linha {leitor.line_num}"
            try:
                anotacao = LinhaAnotacao(
                    imagem=linha[COLUNA_IMAGEM].strip(),
                    classe_id=int(linha["classe_id"]),
                    x_min=int(linha["x_min"]),
                    y_min=int(linha["y_min"]),
                    x_max=int(linha["x_max"]),
                    y_max=int(linha["y_max"]),
                )
            except (ValueError, TypeError, AttributeError) as erro:
                raise ValueError(f"{prefixo}: valor inválido ou campo ausente") from erro

            if not anotacao["imagem"]:
                raise ValueError(f"{prefixo}: nome da imagem vazio")
            if anotacao["classe_id"] not in CORES_BGR:
                validas = ", ".join(str(c) for c in sorted(CORES_BGR))
                raise ValueError(
                    f"{prefixo}: classe_id {anotacao['classe_id']} inválido (esperado: {validas})"
                )
            linhas.append(anotacao)

    return linhas
