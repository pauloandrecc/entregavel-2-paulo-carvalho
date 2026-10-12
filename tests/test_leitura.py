from pathlib import Path

import pytest

from anotador.leitura import ler_anotacoes

CABECALHO = "imagem,classe_id,x_min,y_min,x_max,y_max"


def escrever_csv(
    tmp_path: Path,
    *linhas: str,
    cabecalho: str = CABECALHO,
    encoding: str = "utf-8",
) -> Path:
    caminho = tmp_path / "anotacoes.csv"
    caminho.write_text("\n".join([cabecalho, *linhas]) + "\n", encoding=encoding)
    return caminho


def test_le_linha_valida_e_converte_campos_numericos_para_int(tmp_path: Path) -> None:
    caminho = escrever_csv(tmp_path, "foto01.jpg,1,10,20,30,40")

    resultado = ler_anotacoes(caminho)

    assert resultado == [
        {"imagem": "foto01.jpg", "classe_id": 1, "x_min": 10, "y_min": 20, "x_max": 30, "y_max": 40}
    ]
    linha = resultado[0]
    for campo in ("classe_id", "x_min", "y_min", "x_max", "y_max"):
        assert type(linha[campo]) is int  # type: ignore[literal-required]


def test_preserva_ordem_e_nao_agrupa_linhas(tmp_path: Path) -> None:
    caminho = escrever_csv(
        tmp_path,
        "b.jpg,0,1,1,5,5",
        "a.jpg,1,2,2,6,6",
        "b.jpg,1,3,3,7,7",
    )

    resultado = ler_anotacoes(caminho)

    assert [linha["imagem"] for linha in resultado] == ["b.jpg", "a.jpg", "b.jpg"]
    assert [linha["x_min"] for linha in resultado] == [1, 2, 3]


def test_somente_cabecalho_devolve_lista_vazia(tmp_path: Path) -> None:
    caminho = escrever_csv(tmp_path)

    assert ler_anotacoes(caminho) == []


def test_aceita_colunas_em_outra_ordem(tmp_path: Path) -> None:
    caminho = escrever_csv(
        tmp_path,
        "1,foto01.jpg,40,30,20,10",
        cabecalho="classe_id,imagem,y_max,x_max,y_min,x_min",
    )

    (linha,) = ler_anotacoes(caminho)

    assert linha == {
        "imagem": "foto01.jpg",
        "classe_id": 1,
        "x_min": 10,
        "y_min": 20,
        "x_max": 30,
        "y_max": 40,
    }


def test_ignora_espacos_ao_redor_dos_valores(tmp_path: Path) -> None:
    caminho = escrever_csv(tmp_path, " foto01.jpg , 1 , 10 , 20 , 30 , 40 ")

    (linha,) = ler_anotacoes(caminho)

    assert linha["imagem"] == "foto01.jpg"
    assert (linha["classe_id"], linha["x_min"], linha["y_max"]) == (1, 10, 40)


def test_aceita_csv_com_bom_utf8(tmp_path: Path) -> None:
    caminho = escrever_csv(tmp_path, "foto01.jpg,0,1,2,3,4", encoding="utf-8-sig")

    (linha,) = ler_anotacoes(caminho)

    assert linha["imagem"] == "foto01.jpg"


def test_arquivo_vazio_levanta_erro_de_colunas(tmp_path: Path) -> None:
    caminho = tmp_path / "anotacoes.csv"
    caminho.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="colunas ausentes"):
        ler_anotacoes(caminho)


def test_coluna_faltando_levanta_erro_citando_a_coluna(tmp_path: Path) -> None:
    caminho = escrever_csv(
        tmp_path,
        "foto01.jpg,1,10,20,30",
        cabecalho="imagem,classe_id,x_min,y_min,x_max",
    )

    with pytest.raises(ValueError, match="y_max"):
        ler_anotacoes(caminho)


@pytest.mark.parametrize("valor", ["abc", "12.5", ""], ids=["texto", "decimal", "vazio"])
def test_valor_numerico_invalido_levanta_erro_com_numero_da_linha(
    tmp_path: Path, valor: str
) -> None:
    caminho = escrever_csv(
        tmp_path,
        "foto01.jpg,0,1,2,3,4",
        f"foto02.jpg,1,{valor},2,3,4",
    )

    with pytest.raises(ValueError, match="linha 3"):
        ler_anotacoes(caminho)


def test_linha_com_campos_faltando_levanta_erro(tmp_path: Path) -> None:
    caminho = escrever_csv(tmp_path, "foto01.jpg,0,1,2")

    with pytest.raises(ValueError, match="linha 2"):
        ler_anotacoes(caminho)


@pytest.mark.parametrize("classe", ["2", "-1"])
def test_classe_invalida_levanta_erro_com_numero_da_linha(tmp_path: Path, classe: str) -> None:
    caminho = escrever_csv(
        tmp_path,
        "foto01.jpg,0,1,2,3,4",
        f"foto02.jpg,{classe},1,2,3,4",
    )

    with pytest.raises(ValueError, match=f"linha 3: classe_id {classe} inválido"):
        ler_anotacoes(caminho)


def test_nome_da_imagem_vazio_levanta_erro_com_numero_da_linha(tmp_path: Path) -> None:
    caminho = escrever_csv(tmp_path, "foto01.jpg,0,1,2,3,4", "  ,0,1,2,3,4")

    with pytest.raises(ValueError, match="linha 3: nome da imagem vazio"):
        ler_anotacoes(caminho)


def test_arquivo_inexistente_levanta_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ler_anotacoes(tmp_path / "nao_existe.csv")
