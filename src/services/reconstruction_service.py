# reconstruction_service.py
from abc import ABC, abstractmethod
from typing import Union

import cv2
import numpy as np
import trimesh
from skimage import measure
from rembg import remove

import os
import uuid
import tempfile


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, 'uploads', 'models')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Abstraction
class ReconstructionStrategy(ABC):
    @abstractmethod
    def reconstruct(self, front_input: Union[str, bytes], side_input: Union[str, bytes], filename_prefix: str, identifier: int) -> str:
        """
        Abstract method to generate a 3D model from images.
        Returns the path to the saved model file.
        """
        pass

# 2. Concrete Implementation (Silhouette Based)
class SilhouetteReconstructionStrategy(ReconstructionStrategy):
    def reconstruct(self, front_input: Union[str, bytes], side_input: Union[str, bytes], filename_prefix: str, identifier: int) -> str:
        # 1. Image Loading (path or bytes)
        print(f"Loading images")
        def load_image(inp):
            if isinstance(inp, (bytes, bytearray)):
                img = cv2.imdecode(np.frombuffer(inp, np.uint8), cv2.IMREAD_COLOR)
            else:
                img = cv2.imread(inp, cv2.IMREAD_COLOR)
            return img

        img_frontal = load_image(front_input)
        img_lateral = load_image(side_input)

        if img_frontal is None or img_lateral is None:
            raise ValueError("Falha ao decodificar imagens enviadas.")

        print(f"[{filename_prefix}_{identifier}] Iniciando segmentação (rembg)...")

        def get_mask(img):
            # Use rembg to remove background and obtain alpha mask
            is_success, buffer = cv2.imencode(".png", img)
            if not is_success:
                raise ValueError("Falha ao codificar imagem para rembg.")

            input_bytes = buffer.tobytes()
            try:
                output_bytes = remove(input_bytes)
            except Exception as e:
                raise Exception(f"Erro na rembg: {e}")

            img_array = np.frombuffer(output_bytes, np.uint8)
            result = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
            if result is None:
                raise ValueError("Falha ao decodificar imagem retornada pelo rembg.")

            # Extract alpha channel as mask, or fallback to threshold
            if result.ndim == 3 and result.shape[2] == 4:
                mask = result[:, :, 3]
            elif result.ndim == 2:
                mask = result
            else:
                gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
                _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

            _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
            return binary

        mascara_frontal = get_mask(img_frontal)
        mascara_lateral = get_mask(img_lateral)

        print(f"[{filename_prefix}_{identifier}] Processando geometria...")

        def recortar_silhueta(mascara):
            contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contornos: return mascara # Retorna original se falhar
            maior_contorno = max(contornos, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(maior_contorno)
            return mascara[y:y+h, x:x+w]

        mf_recortada = recortar_silhueta(mascara_frontal)
        ml_recortada = recortar_silhueta(mascara_lateral)

        mf_recortada = np.pad(mf_recortada, 1, mode='constant', constant_values=0)
        ml_recortada = np.pad(ml_recortada, 1, mode='constant', constant_values=0)


        MAX_RESOLUTION = 300
        altura_alvo = min(max(mf_recortada.shape[0], ml_recortada.shape[0]), MAX_RESOLUTION)
        
        def redimensionar(mascara, h_alvo):
            h, w = mascara.shape
            if h == h_alvo: return mascara
            ratio = h_alvo / h
            w_novo = int(w * ratio)
            return cv2.resize(mascara, (w_novo, h_alvo), interpolation=cv2.INTER_NEAREST)

        mf_final = redimensionar(mf_recortada, altura_alvo)
        ml_final = redimensionar(ml_recortada, altura_alvo)

        mf_norm = (mf_final / 255.0).astype(np.uint8)
        ml_norm = (ml_final / 255.0).astype(np.uint8)

        grid_frontal = mf_norm[:, :, np.newaxis]
        grid_lateral = ml_norm[:, np.newaxis, :]
        
        voxels = (grid_frontal & grid_lateral).astype(np.uint8)

        # Using level 0.5 for Marching Cubes
        verts, faces, normals, values = measure.marching_cubes(voxels, level=0.5)
        
        mesh = trimesh.Trimesh(vertices=verts, faces=faces)
        
        filename = f"{filename_prefix}_{identifier}.stl"
        file_path = os.path.join(OUTPUT_DIR, filename)
        
        mesh.export(file_path)
        print(f"[{filename_prefix}_{identifier}] Modelo salvo em: {file_path}")
        
        return file_path

# 3. Manager/Facade -> Service with DI
class ReconstructionService:
    def __init__(self, strategy: ReconstructionStrategy):
        self.strategy = strategy

    def process(self, front_input: str, side_input: str, filename_prefix: str, identifier: int) -> str:
        return self.strategy.reconstruct(front_input, side_input, filename_prefix, identifier)

def process_images_to_3d(front_image_bytes: bytes, side_image_bytes: bytes, filename_prefix: str, identifier: int) -> str:
    # Uses the default strategy. This can be extended to select strategy via factory.
    strategy = SilhouetteReconstructionStrategy()
    service = ReconstructionService(strategy)
    return service.process(front_image_bytes, side_image_bytes, filename_prefix, identifier)