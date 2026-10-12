import numpy as np
import pytest

from anotador.desenho import (
    desenhar_identificacao,
    desenhar_legenda,
    montar_imagem_de_exibicao,
    reduzir_para_caber,
)
from anotador.modelos import CORES_BGR

CINZA = 128


@pytest.fixture
def base() -> np.ndarray:
    """Imagem cinza 400x600: nenhuma cor de classe nem o preto/branco do texto."""
    return np.full((400, 600, 3), CINZA, dtype=np.uint8)


def alterados(depois: np.ndarray, antes: np.ndarray) -> np.ndarray:
    """Máscara (altura x largura) dos pixels que mudaram."""
    return np.any(depois != antes, axis=2)


def tem_cor(imagem: np.ndarray, cor: tuple[int, int, int]) -> bool:
    return bool(np.any(np.all(imagem == cor, axis=2)))


def linha_media_da_cor(imagem: np.ndarray, cor: tuple[int, int, int]) -> float:
    linhas, _ = np.nonzero(np.all(imagem == cor, axis=2))
    return float(linhas.mean())


# --- desenhar_identificacao -------------------------------------------------


def test_identificacao_altera_apenas_o_canto_superior_esquerdo(base: np.ndarray) -> None:
    original = base.copy()

    desenhar_identificacao(base, "foto01.jpg")

    mascara = alterados(base, original)
    assert mascara.any()
    linhas, colunas = np.nonzero(mascara)
    assert linhas.max() < 40
    assert colunas.max() < 150


def test_identificacao_mantem_shape_e_dtype(base: np.ndarray) -> None:
    desenhar_identificacao(base, "foto01.jpg")

    assert base.shape == (400, 600, 3)
    assert base.dtype == np.uint8


def test_identificacao_cresce_com_a_resolucao(base: np.ndarray) -> None:
    grande = np.full((1600, 2400, 3), CINZA, dtype=np.uint8)

    desenhar_identificacao(base, "foto01.jpg")
    desenhar_identificacao(grande, "foto01.jpg")

    pequena_alterada = np.count_nonzero(alterados(base, np.full_like(base, CINZA)))
    grande_alterada = np.count_nonzero(alterados(grande, np.full_like(grande, CINZA)))
    assert grande_alterada > 4 * pequena_alterada


# --- desenhar_legenda -------------------------------------------------------


def test_legenda_mostra_a_cor_de_cada_classe_por_padrao(base: np.ndarray) -> None:
    desenhar_legenda(base)

    assert tem_cor(base, CORES_BGR[0])
    assert tem_cor(base, CORES_BGR[1])


def test_legenda_altera_apenas_o_canto_inferior_esquerdo(base: np.ndarray) -> None:
    original = base.copy()

    desenhar_legenda(base)

    linhas, colunas = np.nonzero(alterados(base, original))
    assert linhas.min() > 300
    assert colunas.max() < 150


def test_legenda_usa_as_cores_recebidas_em_ordem_crescente_de_id(base: np.ndarray) -> None:
    cores = {9: (70, 80, 90), 0: (10, 20, 30), 5: (40, 50, 60)}

    desenhar_legenda(base, cores)

    for cor in cores.values():
        assert tem_cor(base, cor)
    assert (
        linha_media_da_cor(base, cores[0])
        < linha_media_da_cor(base, cores[5])
        < linha_media_da_cor(base, cores[9])
    )


def test_legenda_sem_cores_nao_altera_a_imagem(base: np.ndarray) -> None:
    original = base.copy()

    desenhar_legenda(base, {})

    assert np.array_equal(base, original)


def test_legenda_mantem_shape_e_dtype(base: np.ndarray) -> None:
    desenhar_legenda(base)

    assert base.shape == (400, 600, 3)
    assert base.dtype == np.uint8


# --- reduzir_para_caber ----------------------------------------------------


def test_reduzir_nao_altera_imagem_que_ja_cabe(base: np.ndarray) -> None:
    resultado = reduzir_para_caber(base, 600, 400)

    assert resultado is not base
    assert np.array_equal(resultado, base)


@pytest.mark.parametrize(
    ("forma", "esperada"),
    [((1050, 1400, 3), (720, 960, 3)), ((540, 1920, 3), (360, 1280, 3))],
    ids=["limitada_pela_altura", "limitada_pela_largura"],
)
def test_reduzir_mantem_a_proporcao(
    forma: tuple[int, int, int], esperada: tuple[int, int, int]
) -> None:
    grande = np.full(forma, CINZA, dtype=np.uint8)

    resultado = reduzir_para_caber(grande, 1280, 720)

    assert resultado.shape == esperada
    assert grande.shape == forma  # a original não é alterada


# --- montar_imagem_de_exibicao ----------------------------------------------


def test_exibicao_nao_altera_a_imagem_recebida(base: np.ndarray) -> None:
    original = base.copy()

    resultado = montar_imagem_de_exibicao(base, "foto01.jpg")

    assert resultado is not base
    assert np.array_equal(base, original)


def test_exibicao_mantem_a_resolucao_de_imagem_que_cabe_na_tela(base: np.ndarray) -> None:
    resultado = montar_imagem_de_exibicao(base, "foto01.jpg")

    assert resultado.shape == base.shape
    assert resultado.dtype == base.dtype


def test_exibicao_tem_identificacao_e_legenda_e_mais_nada(base: np.ndarray) -> None:
    resultado = montar_imagem_de_exibicao(base, "foto01.jpg")

    mascara = alterados(resultado, base)
    assert mascara[:40, :150].any()  # identificação
    assert mascara[300:, :150].any()  # legenda
    assert not mascara[40:300, :].any()  # nada no meio
    assert not mascara[:, 150:].any()  # nada à direita
    assert tem_cor(resultado, CORES_BGR[0])
    assert tem_cor(resultado, CORES_BGR[1])


def test_exibicao_preserva_caixas_ja_desenhadas(base: np.ndarray) -> None:
    base[200, 300] = CORES_BGR[1]

    resultado = montar_imagem_de_exibicao(base, "foto01.jpg")

    assert tuple(int(v) for v in resultado[200, 300]) == CORES_BGR[1]


def test_imagem_pequena_nao_gera_erro() -> None:
    pequena = np.full((20, 30, 3), CINZA, dtype=np.uint8)

    resultado = montar_imagem_de_exibicao(pequena, "uma_imagem_com_nome_bem_longo.jpg")

    assert resultado.shape == (20, 30, 3)


def test_exibicao_reduz_imagem_maior_que_a_tela_sem_alterar_a_original() -> None:
    grande = np.full((1050, 1400, 3), CINZA, dtype=np.uint8)

    resultado = montar_imagem_de_exibicao(grande, "foto01.jpg")

    assert resultado.shape == (720, 960, 3)
    assert grande.shape == (1050, 1400, 3)
    assert np.all(grande == CINZA)
