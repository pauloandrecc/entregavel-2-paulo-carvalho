from pathlib import Path

import cv2
import numpy as np
import pytest

from anotador.arquivos import listar_imagens, salvar_resultado


def criar_imagem(altura: int = 100, largura: int = 200) -> np.ndarray:
    """Imagem com um padrão de pixels variado, para detectar qualquer alteração."""
    valores = np.arange(altura * largura * 3) % 256
    return valores.astype(np.uint8).reshape(altura, largura, 3)


def gravar(caminho: Path, imagem: np.ndarray) -> None:
    assert cv2.imwrite(str(caminho), imagem)


# --- listar_imagens ---------------------------------------------------------


def test_lista_imagens_em_ordem_alfabetica(tmp_path: Path) -> None:
    for nome in ["c.png", "a.png", "b.png"]:
        (tmp_path / nome).touch()

    assert [c.name for c in listar_imagens(tmp_path)] == ["a.png", "b.png", "c.png"]


def test_ordem_nao_diferencia_maiusculas_de_minusculas(tmp_path: Path) -> None:
    for nome in ["c.png", "B.png", "a.png"]:
        (tmp_path / nome).touch()

    assert [c.name for c in listar_imagens(tmp_path)] == ["a.png", "B.png", "c.png"]


def test_devolve_caminhos_dentro_da_pasta(tmp_path: Path) -> None:
    (tmp_path / "a.png").touch()

    assert listar_imagens(tmp_path) == [tmp_path / "a.png"]


def test_ignora_arquivos_que_nao_sao_imagens(tmp_path: Path) -> None:
    for nome in ["a.png", "notas.txt", "anotacoes.csv", "sem_extensao", "b.jpg"]:
        (tmp_path / nome).touch()

    assert [c.name for c in listar_imagens(tmp_path)] == ["a.png", "b.jpg"]


def test_aceita_extensoes_em_maiusculas(tmp_path: Path) -> None:
    for nome in ["a.JPG", "b.Png", "c.jpeg", "d.bmp"]:
        (tmp_path / nome).touch()

    assert [c.name for c in listar_imagens(tmp_path)] == ["a.JPG", "b.Png", "c.jpeg", "d.bmp"]


def test_ignora_subpastas_mesmo_com_nome_de_imagem(tmp_path: Path) -> None:
    (tmp_path / "pasta.png").mkdir()
    (tmp_path / "a.png").touch()

    assert [c.name for c in listar_imagens(tmp_path)] == ["a.png"]


def test_pasta_vazia_devolve_lista_vazia(tmp_path: Path) -> None:
    assert listar_imagens(tmp_path) == []


def test_pasta_inexistente_levanta_erro(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="nao_existe"):
        listar_imagens(tmp_path / "nao_existe")


# --- salvar_resultado -------------------------------------------------------


def test_salva_com_o_mesmo_nome_do_arquivo_de_origem(tmp_path: Path) -> None:
    origem = tmp_path / "imagens" / "foto01.png"
    origem.parent.mkdir()
    resultados = tmp_path / "resultados"

    destino = salvar_resultado(criar_imagem(), origem, resultados)

    assert destino == resultados / "foto01.png"
    assert destino.is_file()


def test_cria_a_pasta_de_resultados_se_nao_existir(tmp_path: Path) -> None:
    resultados = tmp_path / "saida" / "resultados"

    salvar_resultado(criar_imagem(), tmp_path / "foto01.png", resultados)

    assert (resultados / "foto01.png").is_file()


def test_mantem_resolucao_e_conteudo_da_imagem(tmp_path: Path) -> None:
    imagem = criar_imagem(altura=123, largura=457)

    destino = salvar_resultado(imagem, tmp_path / "foto01.png", tmp_path / "resultados")

    lida = cv2.imread(str(destino))
    assert lida is not None
    assert lida.shape == (123, 457, 3)
    assert np.array_equal(lida, imagem)


def test_salva_imagem_jpg_com_a_mesma_resolucao(tmp_path: Path) -> None:
    destino = salvar_resultado(
        criar_imagem(altura=64, largura=96), tmp_path / "foto01.jpg", tmp_path / "resultados"
    )

    lida = cv2.imread(str(destino))
    assert lida is not None
    assert lida.shape == (64, 96, 3)


def test_substitui_resultado_anterior_com_o_mesmo_nome(tmp_path: Path) -> None:
    resultados = tmp_path / "resultados"
    origem = tmp_path / "foto01.png"
    segunda = np.full((100, 200, 3), 7, dtype=np.uint8)

    salvar_resultado(criar_imagem(), origem, resultados)
    destino = salvar_resultado(segunda, origem, resultados)

    lida = cv2.imread(str(destino))
    assert lida is not None
    assert np.array_equal(lida, segunda)


def test_nao_sobrescreve_a_imagem_de_entrada(tmp_path: Path) -> None:
    entrada = tmp_path / "imagens" / "foto01.png"
    entrada.parent.mkdir()
    gravar(entrada, criar_imagem())
    conteudo_antes = entrada.read_bytes()

    with pytest.raises(ValueError, match="sobrescreveria"):
        salvar_resultado(np.zeros((100, 200, 3), dtype=np.uint8), entrada, entrada.parent)

    assert entrada.read_bytes() == conteudo_antes


def test_salvar_nao_altera_o_arquivo_de_entrada(tmp_path: Path) -> None:
    entrada = tmp_path / "imagens" / "foto01.png"
    entrada.parent.mkdir()
    gravar(entrada, criar_imagem())
    conteudo_antes = entrada.read_bytes()

    salvar_resultado(np.zeros((100, 200, 3), dtype=np.uint8), entrada, tmp_path / "resultados")

    assert entrada.read_bytes() == conteudo_antes


def test_erro_quando_a_gravacao_falha(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def imwrite_que_falha(*_args: object, **_kwargs: object) -> bool:
        return False

    monkeypatch.setattr(cv2, "imwrite", imwrite_que_falha)

    with pytest.raises(OSError, match="foto01.png"):
        salvar_resultado(criar_imagem(), tmp_path / "foto01.png", tmp_path / "resultados")
