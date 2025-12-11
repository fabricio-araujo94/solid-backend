# reconstruction_service.py
from abc import ABC, abstractmethod
import cv2
import numpy as np
import trimesh
from skimage import measure
import requests

import os
import uuid
import tempfile

OUTPUT_DIR = tempfile.gettempdir()
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Abstraction
class ReconstructionStrategy(ABC):
    @abstractmethod
    def reconstruct(self, front_input: str, side_input: str, filename_prefix: str, identifier: int) -> str:
        """
        Abstract method to generate a 3D model from images.
        Returns the path to the saved model file.
        """
        pass

# 2. Concrete Implementation (Silhouette Based)
class SilhouetteReconstructionStrategy(ReconstructionStrategy):
    def reconstruct(self, front_input: str, side_input: str, filename_prefix: str, identifier: int) -> str:
        # 1. Image Loading (from Path)
        print(f"Loading images from: {front_input} and {side_input}")
        img_frontal = cv2.imread(front_input, cv2.IMREAD_COLOR)
        img_lateral = cv2.imread(side_input, cv2.IMREAD_COLOR)

        if img_frontal is None or img_lateral is None:
            raise ValueError("Falha ao decodificar imagens enviadas.")

        print(f"[{filename_prefix}_{identifier}] Iniciando segmentação IA...")

        def get_mask(img):
            api_key = os.environ.get("CLIPDROP_API_KEY")
            if not api_key:
                raise ValueError("CLIPDROP_API_KEY não encontrada nas variáveis de ambiente.")

            # Encode image to bytes for API
            is_success, buffer = cv2.imencode(".jpg", img)
            if not is_success:
                 raise ValueError("Falha ao codificar imagem para API.")
            
            headers = {
                'x-api-key': api_key,
            }
            files = {
                'image_file': ('image.jpg', buffer.tobytes(), 'image/jpeg')
            }

            response = requests.post('https://clipdrop-api.co/remove-background/v1', headers=headers, files=files) 

            if response.status_code == 200:
                # Decode response image
                img_array = np.frombuffer(response.content, np.uint8)
                result = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
                
                # Extract alpha channel as mask
                if result.shape[2] == 4:
                    mask = result[:, :, 3]
                else:
                    # Fallback if no alpha channel returned (unexpected from remove-bg)
                    mask = result 
                
                _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
                return binary
            else:
                raise Exception(f"Erro na API Clipdrop: {response.status_code} - {response.text}")

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