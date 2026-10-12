from collections.abc import Mapping

import cv2
import numpy as np

from anotador.modelos import CORES_BGR

Cor = tuple[int, int, int]

FONTE = cv2.FONT_HERSHEY_SIMPLEX
COR_TEXTO: Cor = (255, 255, 255)
COR_FUNDO: Cor = (0, 0, 0)

# Imagens com o menor lado de 800 px usam fonte de escala 1.0; as maiores crescem
# proporcionalmente e as menores não ficam abaixo da escala mínima.
LADO_REFERENCIA = 800
ESCALA_MINIMA = 0.5

# Tamanho máximo da imagem na janela. Imagens maiores são reduzidas só na exibição.
LARGURA_MAXIMA_EXIBICAO = 1280
ALTURA_MAXIMA_EXIBICAO = 720


def _escala(imagem: np.ndarray) -> float:
    menor_lado = min(imagem.shape[0], imagem.shape[1])
    return max(ESCALA_MINIMA, menor_lado / LADO_REFERENCIA)


def _medir(texto: str, escala: float) -> tuple[int, int, int, int]:
    """Devolve (largura, altura, base, espessura) do texto na escala dada."""
    espessura = max(1, round(escala * 2))
    (largura, altura), base = cv2.getTextSize(texto, FONTE, escala, espessura)
    return largura, altura, base, espessura


def desenhar_identificacao(imagem: np.ndarray, texto: str) -> None:
    """Escreve `texto` no canto superior esquerdo, sobre um fundo escuro (modifica o array)."""
    escala = _escala(imagem)
    largura, altura, base, espessura = _medir(texto, escala)
    margem = round(10 * escala)
    pad = round(4 * escala)

    cv2.rectangle(
        imagem,
        (margem, margem),
        (margem + largura + 2 * pad, margem + altura + base + 2 * pad),
        COR_FUNDO,
        cv2.FILLED,
    )
    cv2.putText(
        imagem,
        texto,
        (margem + pad, margem + pad + altura),
        FONTE,
        escala,
        COR_TEXTO,
        espessura,
        cv2.LINE_AA,
    )


def desenhar_legenda(imagem: np.ndarray, cores: Mapping[int, Cor] = CORES_BGR) -> None:
    if not cores:
        return

    escala = _escala(imagem)
    margem = round(10 * escala)
    pad = round(4 * escala)

    rotulos = [(classe_id, f"Classe {classe_id}") for classe_id in sorted(cores)]
    medidas = [_medir(rotulo, escala) for _, rotulo in rotulos]
    altura_texto = max(m[1] for m in medidas)
    base = max(m[2] for m in medidas)
    espessura = medidas[0][3]

    lado = altura_texto
    altura_linha = altura_texto + base + 2 * pad
    y = imagem.shape[0] - margem - altura_linha * len(rotulos)

    for (classe_id, rotulo), (largura, *_) in zip(rotulos, medidas, strict=True):
        largura_linha = pad + lado + pad + largura + pad
        cv2.rectangle(
            imagem, (margem, y), (margem + largura_linha, y + altura_linha), COR_FUNDO, cv2.FILLED
        )
        cv2.rectangle(
            imagem,
            (margem + pad, y + pad),
            (margem + pad + lado, y + pad + lado),
            cores[classe_id],
            cv2.FILLED,
        )
        cv2.putText(
            imagem,
            rotulo,
            (margem + 2 * pad + lado, y + pad + altura_texto),
            FONTE,
            escala,
            COR_TEXTO,
            espessura,
            cv2.LINE_AA,
        )
        y += altura_linha


def reduzir_para_caber(
    imagem: np.ndarray,
    largura_maxima: int = LARGURA_MAXIMA_EXIBICAO,
    altura_maxima: int = ALTURA_MAXIMA_EXIBICAO,
) -> np.ndarray:
    altura, largura = imagem.shape[:2]
    fator = min(largura_maxima / largura, altura_maxima / altura)
    if fator >= 1:
        return imagem.copy()
    tamanho = (max(1, round(largura * fator)), max(1, round(altura * fator)))
    return cv2.resize(imagem, tamanho, interpolation=cv2.INTER_AREA)


def montar_imagem_de_exibicao(
    imagem: np.ndarray, nome_imagem: str, cores: Mapping[int, Cor] = CORES_BGR
) -> np.ndarray:
    exibicao = reduzir_para_caber(imagem)
    desenhar_identificacao(exibicao, nome_imagem)
    desenhar_legenda(exibicao, cores)
    return exibicao
