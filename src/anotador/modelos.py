from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

# Cores em BGR (ordem do OpenCV)
CORES_BGR: dict[int, tuple[int, int, int]] = {
    0: (0, 255, 0),  # verde
    1: (0, 0, 255),  # vermelho
}
ESPESSURA = 2


@dataclass(frozen=True)
class Deteccao:
    classe_id: int
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    def esta_dentro_dos_limites(self, largura: int, altura: int) -> bool:
        """Verifica 0 <= x_min < x_max < largura e 0 <= y_min < y_max < altura."""
        return 0 <= self.x_min < self.x_max < largura and 0 <= self.y_min < self.y_max < altura

    def desenhar(self, imagem: np.ndarray) -> None:
        if self.classe_id not in CORES_BGR:
            raise ValueError(f"Classe sem cor definida: {self.classe_id}")
        cv2.rectangle(
            imagem,
            (self.x_min, self.y_min),
            (self.x_max, self.y_max),
            CORES_BGR[self.classe_id],
            ESPESSURA,
        )


@dataclass
class ImagemAnotada:
    caminho: Path
    deteccoes: list[Deteccao] = field(default_factory=list[Deteccao])

    def adicionar_deteccao(self, deteccao: Deteccao) -> None:
        self.deteccoes.append(deteccao)

    def gerar_imagem(self) -> np.ndarray:
        imagem = cv2.imread(str(self.caminho))
        if imagem is None:
            raise FileNotFoundError(f"Não foi possível abrir a imagem: {self.caminho}")

        altura, largura = imagem.shape[:2]
        for deteccao in self.deteccoes:
            if not deteccao.esta_dentro_dos_limites(largura, altura):
                raise ValueError(
                    f"{self.caminho.name}: caixa fora dos limites da imagem "
                    f"({largura}x{altura}): {deteccao}"
                )

        for deteccao in self.deteccoes:
            deteccao.desenhar(imagem)
        return imagem
