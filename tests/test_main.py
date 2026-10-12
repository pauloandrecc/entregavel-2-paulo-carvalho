from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pytest

import anotador.main as principal
from anotador.main import Acao, criar_parser, executar, interpretar_tecla, main
from anotador.modelos import CORES_BGR

ALTURA = 60
LARGURA = 80
CINZA = 128


@dataclass
class Projeto:
    csv: Path
    imagens: Path
    resultados: Path

    @property
    def argv(self) -> list[str]:
        return [
            "--csv",
            str(self.csv),
            "--imagens",
            str(self.imagens),
            "--resultados",
            str(self.resultados),
        ]


class ExibidorFalso:
    """Substitui a janela do OpenCV: registra o que seria mostrado e devolve ações prontas.

    Depois de esgotar as ações informadas, devolve sempre `Acao.AVANCAR`.
    """

    def __init__(self, *acoes: Acao) -> None:
        self._acoes = iter(acoes)
        self.titulos: list[str] = []
        self.imagens: dict[str, np.ndarray] = {}

    def __call__(self, titulo: str, imagem: np.ndarray) -> Acao:
        self.titulos.append(titulo)
        self.imagens[titulo] = imagem
        return next(self._acoes, Acao.AVANCAR)


@pytest.fixture
def projeto(tmp_path: Path) -> Projeto:
    """Três imagens (criadas fora de ordem) e um CSV com linhas da imagem `a` separadas.

    `a.png` tem 2 caixas (classes 0 e 1), `b.png` não tem nenhuma e `c.png` tem 1.
    """
    imagens = tmp_path / "imagens"
    imagens.mkdir()
    for nome in ["c.png", "a.png", "b.png"]:
        cinza = np.full((ALTURA, LARGURA, 3), CINZA, dtype=np.uint8)
        assert cv2.imwrite(str(imagens / nome), cinza)

    csv = tmp_path / "anotacoes.csv"
    csv.write_text(
        "imagem,classe_id,x_min,y_min,x_max,y_max\n"
        "a.png,0,10,10,40,30\n"
        "c.png,1,5,5,30,30\n"
        "a.png,1,50,5,70,50\n",
        encoding="utf-8",
    )
    return Projeto(csv=csv, imagens=imagens, resultados=tmp_path / "resultados")


def ler_imagem(caminho: Path) -> np.ndarray:
    imagem = cv2.imread(str(caminho))
    assert imagem is not None
    return imagem


def pixel(imagem: np.ndarray, x: int, y: int) -> tuple[int, int, int]:
    b, g, r = imagem[y, x]
    return int(b), int(g), int(r)


# --- interpretar_tecla ------------------------------------------------------


def test_espaco_avanca() -> None:
    assert interpretar_tecla(ord(" ")) is Acao.AVANCAR


def test_q_encerra() -> None:
    assert interpretar_tecla(ord("q")) is Acao.SAIR


@pytest.mark.parametrize("tecla", [ord("a"), ord("Q"), 13, 27, -1])
def test_outras_teclas_mantem_a_imagem_atual(tecla: int) -> None:
    assert interpretar_tecla(tecla) is Acao.MANTER


def test_ignora_bits_extras_do_codigo_da_tecla() -> None:
    assert interpretar_tecla(0x100000 | ord("q")) is Acao.SAIR
    assert interpretar_tecla(0x100000 | ord(" ")) is Acao.AVANCAR


# --- executar ---------------------------------------------------------------


def test_percorre_as_imagens_em_ordem_alfabetica(projeto: Projeto) -> None:
    exibidor = ExibidorFalso()

    total = executar(projeto.csv, projeto.imagens, projeto.resultados, exibidor)

    assert total == 3
    assert exibidor.titulos == ["a.png", "b.png", "c.png"]


def test_salva_uma_imagem_por_entrada_com_mesmo_nome_e_resolucao(projeto: Projeto) -> None:
    executar(projeto.csv, projeto.imagens, projeto.resultados, ExibidorFalso())

    assert sorted(p.name for p in projeto.resultados.iterdir()) == ["a.png", "b.png", "c.png"]
    for nome in ["a.png", "b.png", "c.png"]:
        assert ler_imagem(projeto.resultados / nome).shape == (ALTURA, LARGURA, 3)


def test_imagem_salva_tem_as_caixas_com_a_cor_de_cada_classe(projeto: Projeto) -> None:
    executar(projeto.csv, projeto.imagens, projeto.resultados, ExibidorFalso())

    salva = ler_imagem(projeto.resultados / "a.png")
    assert pixel(salva, 10, 10) == CORES_BGR[0]
    assert pixel(salva, 50, 5) == CORES_BGR[1]


def test_imagem_sem_anotacao_e_salva_sem_alteracoes(projeto: Projeto) -> None:
    executar(projeto.csv, projeto.imagens, projeto.resultados, ExibidorFalso())

    salva = ler_imagem(projeto.resultados / "b.png")
    assert np.array_equal(salva, np.full((ALTURA, LARGURA, 3), CINZA, dtype=np.uint8))


def test_exibicao_tem_identificacao_e_legenda_mas_o_arquivo_salvo_nao(projeto: Projeto) -> None:
    exibidor = ExibidorFalso()

    executar(projeto.csv, projeto.imagens, projeto.resultados, exibidor)

    exibida = exibidor.imagens["b.png"]
    salva = ler_imagem(projeto.resultados / "b.png")
    assert exibida.shape == salva.shape
    assert np.any(exibida != salva)


def test_nao_altera_as_imagens_de_entrada(projeto: Projeto) -> None:
    antes = {p.name: p.read_bytes() for p in projeto.imagens.iterdir()}

    executar(projeto.csv, projeto.imagens, projeto.resultados, ExibidorFalso())

    assert {p.name: p.read_bytes() for p in projeto.imagens.iterdir()} == antes


def test_mostra_no_terminal_o_nome_e_a_quantidade_de_caixas(
    projeto: Projeto, capsys: pytest.CaptureFixture[str]
) -> None:
    executar(projeto.csv, projeto.imagens, projeto.resultados, ExibidorFalso())

    assert capsys.readouterr().out.splitlines() == [
        "a.png - caixas desenhadas: 2",
        "b.png - caixas desenhadas: 0",
        "c.png - caixas desenhadas: 1",
    ]


def test_sair_interrompe_o_percurso_mas_mantem_o_que_ja_foi_salvo(projeto: Projeto) -> None:
    exibidor = ExibidorFalso(Acao.AVANCAR, Acao.SAIR)

    total = executar(projeto.csv, projeto.imagens, projeto.resultados, exibidor)

    assert total == 2
    assert exibidor.titulos == ["a.png", "b.png"]
    assert sorted(p.name for p in projeto.resultados.iterdir()) == ["a.png", "b.png"]


def test_avisa_sobre_imagens_do_csv_que_nao_existem_na_pasta(
    projeto: Projeto, capsys: pytest.CaptureFixture[str]
) -> None:
    conteudo = projeto.csv.read_text(encoding="utf-8")
    projeto.csv.write_text(conteudo + "fantasma.png,0,1,1,2,2\n", encoding="utf-8")

    total = executar(projeto.csv, projeto.imagens, projeto.resultados, ExibidorFalso())

    assert total == 3
    assert "fantasma.png" in capsys.readouterr().err


def test_pasta_sem_imagens_nao_exibe_nada(tmp_path: Path) -> None:
    csv = tmp_path / "anotacoes.csv"
    csv.write_text("imagem,classe_id,x_min,y_min,x_max,y_max\n", encoding="utf-8")
    imagens = tmp_path / "imagens"
    imagens.mkdir()
    exibidor = ExibidorFalso()

    total = executar(csv, imagens, tmp_path / "resultados", exibidor)

    assert total == 0
    assert exibidor.titulos == []


def test_csv_inexistente_levanta_erro(projeto: Projeto) -> None:
    projeto.csv.unlink()

    with pytest.raises(FileNotFoundError):
        executar(projeto.csv, projeto.imagens, projeto.resultados, ExibidorFalso())


# --- criar_parser e main ----------------------------------------------------


def test_parser_usa_caminhos_padrao_relativos_a_pasta_atual() -> None:
    args = criar_parser().parse_args([])

    assert args.csv == Path("dados/anotacoes.csv")
    assert args.imagens == Path("imagens")
    assert args.resultados == Path("resultados")


def test_parser_aceita_caminhos_personalizados() -> None:
    args = criar_parser().parse_args(["--csv", "x.csv", "--imagens", "i", "--resultados", "r"])

    assert (args.csv, args.imagens, args.resultados) == (Path("x.csv"), Path("i"), Path("r"))


def test_main_executa_o_fluxo_completo_e_fecha_as_janelas(
    projeto: Projeto, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fechadas: list[bool] = []

    def fechar_janelas() -> None:
        fechadas.append(True)

    monkeypatch.setattr(principal, "mostrar_e_esperar", ExibidorFalso())
    monkeypatch.setattr(cv2, "destroyAllWindows", fechar_janelas)

    codigo = main(projeto.argv)

    assert codigo == 0
    assert fechadas == [True]
    assert sorted(p.name for p in projeto.resultados.iterdir()) == ["a.png", "b.png", "c.png"]
    assert "3 imagens processadas" in capsys.readouterr().out


def test_main_devolve_1_e_fecha_as_janelas_quando_ha_erro(
    projeto: Projeto, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fechadas: list[bool] = []

    def fechar_janelas() -> None:
        fechadas.append(True)

    monkeypatch.setattr(principal, "mostrar_e_esperar", ExibidorFalso())
    monkeypatch.setattr(cv2, "destroyAllWindows", fechar_janelas)
    projeto.csv.unlink()

    codigo = main(projeto.argv)

    assert codigo == 1
    assert fechadas == [True]
    assert "Erro" in capsys.readouterr().err
