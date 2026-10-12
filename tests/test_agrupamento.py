from pathlib import Path

from anotador.agrupamento import agrupar_por_imagem
from anotador.leitura import LinhaAnotacao, ler_anotacoes
from anotador.modelos import Deteccao

DIRETORIO = Path("imagens")


def linha(
    imagem: str,
    classe_id: int = 0,
    x_min: int = 1,
    y_min: int = 2,
    x_max: int = 3,
    y_max: int = 4,
) -> LinhaAnotacao:
    return LinhaAnotacao(
        imagem=imagem,
        classe_id=classe_id,
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
    )


def test_entrada_vazia_devolve_dicionario_vazio() -> None:
    assert agrupar_por_imagem([], DIRETORIO) == {}


def test_agrupa_linhas_consecutivas_da_mesma_imagem() -> None:
    linhas = [linha("a.jpg"), linha("a.jpg"), linha("a.jpg")]

    grupos = agrupar_por_imagem(linhas, DIRETORIO)

    assert list(grupos) == ["a.jpg"]
    assert len(grupos["a.jpg"].deteccoes) == 3


def test_agrupa_linhas_da_mesma_imagem_separadas_no_csv() -> None:
    linhas = [linha("a.jpg"), linha("b.jpg"), linha("a.jpg"), linha("c.jpg"), linha("a.jpg")]

    grupos = agrupar_por_imagem(linhas, DIRETORIO)

    assert len(grupos["a.jpg"].deteccoes) == 3
    assert len(grupos["b.jpg"].deteccoes) == 1
    assert len(grupos["c.jpg"].deteccoes) == 1


def test_imagens_diferentes_nao_se_misturam() -> None:
    linhas = [
        linha("a.jpg", classe_id=0, x_min=10),
        linha("b.jpg", classe_id=1, x_min=20),
    ]

    grupos = agrupar_por_imagem(linhas, DIRETORIO)

    assert [d.x_min for d in grupos["a.jpg"].deteccoes] == [10]
    assert [d.x_min for d in grupos["b.jpg"].deteccoes] == [20]


def test_converte_cada_linha_em_deteccao_com_os_mesmos_valores() -> None:
    grupos = agrupar_por_imagem(
        [linha("a.jpg", classe_id=1, x_min=10, y_min=20, x_max=30, y_max=40)], DIRETORIO
    )

    assert grupos["a.jpg"].deteccoes == [Deteccao(1, 10, 20, 30, 40)]


def test_deteccoes_de_uma_imagem_seguem_a_ordem_das_linhas() -> None:
    linhas = [
        linha("a.jpg", x_min=1),
        linha("b.jpg", x_min=9),
        linha("a.jpg", x_min=2),
        linha("a.jpg", x_min=3),
    ]

    grupos = agrupar_por_imagem(linhas, DIRETORIO)

    assert [d.x_min for d in grupos["a.jpg"].deteccoes] == [1, 2, 3]


def test_chaves_seguem_a_ordem_da_primeira_aparicao() -> None:
    linhas = [linha("c.jpg"), linha("a.jpg"), linha("c.jpg"), linha("b.jpg")]

    grupos = agrupar_por_imagem(linhas, DIRETORIO)

    assert list(grupos) == ["c.jpg", "a.jpg", "b.jpg"]


def test_caminho_da_imagem_e_diretorio_mais_nome() -> None:
    grupos = agrupar_por_imagem([linha("a.jpg")], DIRETORIO)

    assert grupos["a.jpg"].caminho == DIRETORIO / "a.jpg"


def test_aceita_qualquer_iteravel_de_linhas() -> None:
    linhas = (linha(nome) for nome in ["a.jpg", "b.jpg", "a.jpg"])

    grupos = agrupar_por_imagem(linhas, DIRETORIO)

    assert {nome: len(g.deteccoes) for nome, g in grupos.items()} == {"a.jpg": 2, "b.jpg": 1}


def test_agrupa_a_partir_de_um_csv_com_linhas_embaralhadas(tmp_path: Path) -> None:
    csv = tmp_path / "anotacoes.csv"
    csv.write_text(
        "imagem,classe_id,x_min,y_min,x_max,y_max\n"
        "b.jpg,1,5,5,50,50\n"
        "a.jpg,0,1,1,10,10\n"
        "b.jpg,0,6,6,60,60\n"
        "a.jpg,1,2,2,20,20\n"
        "c.jpg,0,7,7,70,70\n",
        encoding="utf-8",
    )

    grupos = agrupar_por_imagem(ler_anotacoes(csv), tmp_path / "imagens")

    assert {nome: len(g.deteccoes) for nome, g in grupos.items()} == {
        "b.jpg": 2,
        "a.jpg": 2,
        "c.jpg": 1,
    }
    assert [d.classe_id for d in grupos["a.jpg"].deteccoes] == [0, 1]
