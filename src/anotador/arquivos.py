from pathlib import Path

import cv2
import numpy as np

EXTENSOES_IMAGEM = frozenset({".jpg", ".jpeg", ".png", ".bmp"})


def listar_imagens(diretorio: Path) -> list[Path]:
    if not diretorio.is_dir():
        raise FileNotFoundError(f"Pasta de imagens não encontrada: {diretorio}")

    imagens = [
        caminho
        for caminho in diretorio.iterdir()
        if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_IMAGEM
    ]
    return sorted(imagens, key=lambda caminho: (caminho.name.lower(), caminho.name))


def salvar_resultado(imagem: np.ndarray, caminho_origem: Path, diretorio_resultados: Path) -> Path:
    destino = diretorio_resultados / caminho_origem.name
    if destino.resolve() == caminho_origem.resolve():
        raise ValueError(f"O resultado sobrescreveria a imagem de entrada: {caminho_origem}")

    diretorio_resultados.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destino), imagem):
        raise OSError(f"Não foi possível salvar a imagem: {destino}")
    return destino
