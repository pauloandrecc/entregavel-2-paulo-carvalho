from dataclasses import FrozenInstanceError
from pathlib import Path

import cv2
import numpy as np
import pytest

from anotador.modelos import CORES_BGR, Deteccao, ImagemAnotada

ALTURA = 100
LARGURA = 200


def pixel(imagem: np.ndarray, x: int, y: int) -> tuple[int, int, int]:
    """Devolve o pixel (x, y) como tupla BGR de ints."""
    b, g, r = imagem[y, x]
    return int(b), int(g), int(r)


@pytest.fixture
def imagem_preta() -> np.ndarray:
    return np.zeros((ALTURA, LARGURA, 3), dtype=np.uint8)


@pytest.fixture
def caminho_imagem(tmp_path: Path, imagem_preta: np.ndarray) -> Path:
    caminho = tmp_path / "foto.png"
    assert cv2.imwrite(str(caminho), imagem_preta)
    return caminho


# --- Deteccao ---------------------------------------------------------------


def test_deteccao_armazena_valores() -> None:
    d = Deteccao(classe_id=1, x_min=10, y_min=20, x_max=30, y_max=40)

    assert (d.classe_id, d.x_min, d.y_min, d.x_max, d.y_max) == (1, 10, 20, 30, 40)


def test_deteccao_e_imutavel() -> None:
    d = Deteccao(0, 10, 20, 30, 40)

    with pytest.raises(FrozenInstanceError):
        d.x_min = 99  # type: ignore[misc]


@pytest.mark.parametrize("classe_id", [0, 1])
def test_desenhar_pinta_borda_com_cor_da_classe(imagem_preta: np.ndarray, classe_id: int) -> None:
    d = Deteccao(classe_id, x_min=20, y_min=30, x_max=120, y_max=80)

    d.desenhar(imagem_preta)

    cor = CORES_BGR[classe_id]
    assert pixel(imagem_preta, 20, 30) == cor  # canto superior esquerdo
    assert pixel(imagem_preta, 120, 80) == cor  # canto inferior direito
    assert pixel(imagem_preta, 70, 30) == cor  # meio da borda superior
    assert pixel(imagem_preta, 20, 55) == cor  # meio da borda esquerda


def test_desenhar_nao_pinta_fora_nem_dentro_da_caixa(imagem_preta: np.ndarray) -> None:
    d = Deteccao(0, x_min=20, y_min=30, x_max=120, y_max=80)

    d.desenhar(imagem_preta)

    assert pixel(imagem_preta, 150, 90) == (0, 0, 0)  # fora
    assert pixel(imagem_preta, 70, 55) == (0, 0, 0)  # interior (caixa não é preenchida)


def test_desenhar_mantem_shape_e_dtype(imagem_preta: np.ndarray) -> None:
    Deteccao(0, 20, 30, 120, 80).desenhar(imagem_preta)

    assert imagem_preta.shape == (ALTURA, LARGURA, 3)
    assert imagem_preta.dtype == np.uint8


def test_classes_diferentes_usam_cores_diferentes() -> None:
    assert CORES_BGR[0] != CORES_BGR[1]


def test_desenhar_classe_sem_cor_levanta_erro(imagem_preta: np.ndarray) -> None:
    d = Deteccao(classe_id=7, x_min=20, y_min=30, x_max=120, y_max=80)

    with pytest.raises(ValueError, match="7"):
        d.desenhar(imagem_preta)


# --- ImagemAnotada ----------------------------------------------------------


def test_imagem_anotada_comeca_sem_deteccoes(caminho_imagem: Path) -> None:
    assert ImagemAnotada(caminho_imagem).deteccoes == []


def test_instancias_nao_compartilham_a_lista_de_deteccoes(caminho_imagem: Path) -> None:
    a = ImagemAnotada(caminho_imagem)
    b = ImagemAnotada(caminho_imagem)

    a.adicionar_deteccao(Deteccao(0, 1, 1, 5, 5))

    assert len(a.deteccoes) == 1
    assert b.deteccoes == []


def test_adicionar_deteccao_preserva_ordem(caminho_imagem: Path) -> None:
    primeira = Deteccao(0, 1, 1, 5, 5)
    segunda = Deteccao(1, 10, 10, 20, 20)
    imagem = ImagemAnotada(caminho_imagem)

    imagem.adicionar_deteccao(primeira)
    imagem.adicionar_deteccao(segunda)

    assert imagem.deteccoes == [primeira, segunda]


def test_gerar_imagem_desenha_todas_as_caixas(caminho_imagem: Path) -> None:
    imagem = ImagemAnotada(caminho_imagem)
    imagem.adicionar_deteccao(Deteccao(0, 10, 10, 50, 50))
    imagem.adicionar_deteccao(Deteccao(1, 100, 40, 180, 90))

    resultado = imagem.gerar_imagem()

    assert pixel(resultado, 10, 10) == CORES_BGR[0]
    assert pixel(resultado, 180, 90) == CORES_BGR[1]


def test_gerar_imagem_sem_deteccoes_devolve_imagem_original(
    caminho_imagem: Path, imagem_preta: np.ndarray
) -> None:
    resultado = ImagemAnotada(caminho_imagem).gerar_imagem()

    assert np.array_equal(resultado, imagem_preta)


def test_gerar_imagem_mantem_resolucao_original(caminho_imagem: Path) -> None:
    imagem = ImagemAnotada(caminho_imagem)
    imagem.adicionar_deteccao(Deteccao(0, 10, 10, 50, 50))

    assert imagem.gerar_imagem().shape == (ALTURA, LARGURA, 3)


def test_gerar_imagem_nao_altera_arquivo_de_entrada(caminho_imagem: Path) -> None:
    conteudo_antes = caminho_imagem.read_bytes()
    imagem = ImagemAnotada(caminho_imagem)
    imagem.adicionar_deteccao(Deteccao(0, 10, 10, 50, 50))

    imagem.gerar_imagem()

    assert caminho_imagem.read_bytes() == conteudo_antes


def test_gerar_imagem_devolve_copia_independente_a_cada_chamada(caminho_imagem: Path) -> None:
    imagem = ImagemAnotada(caminho_imagem)
    imagem.adicionar_deteccao(Deteccao(0, 10, 10, 50, 50))

    primeira = imagem.gerar_imagem()
    primeira[:] = 255  # alterar o resultado não pode afetar chamadas futuras
    segunda = imagem.gerar_imagem()

    assert pixel(segunda, 70, 70) == (0, 0, 0)
    assert pixel(segunda, 10, 10) == CORES_BGR[0]


def test_gerar_imagem_com_caminho_inexistente_levanta_erro(tmp_path: Path) -> None:
    imagem = ImagemAnotada(tmp_path / "nao_existe.png")

    with pytest.raises(FileNotFoundError, match="nao_existe.png"):
        imagem.gerar_imagem()