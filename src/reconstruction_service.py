# reconstruction_service.py
import cv2
import numpy as np
import trimesh
from skimage import measure
from rembg import remove
import os
import uuid

OUTPUT_DIR = "uploads/models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_images_to_3d(front_image_bytes: bytes, side_image_bytes: bytes, filename_prefix: str, identifier: int) -> str:
    """
    Recebe os bytes das imagens, aplica segmentação via IA, 
    reconstrói o modelo 3D e retorna o caminho do arquivo salvo.
    """
    
    # 1. Decodificar bytes para Imagem OpenCV
    front_nparr = np.frombuffer(front_image_bytes, np.uint8)
    side_nparr = np.frombuffer(side_image_bytes, np.uint8)
    
    img_frontal = cv2.imdecode(front_nparr, cv2.IMREAD_COLOR)
    img_lateral = cv2.imdecode(side_nparr, cv2.IMREAD_COLOR)

    if img_frontal is None or img_lateral is None:
        raise ValueError("Falha ao decodificar imagens enviadas.")

    print(f"[{filename_prefix}_{identifier}] Iniciando segmentação IA...")
    
    def get_mask(img):
        result = remove(img)
        mask = result[:, :, 3]
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

    altura_alvo = max(mf_recortada.shape[0], ml_recortada.shape[0])
    
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

    verts, faces, normals, values = measure.marching_cubes(voxels, level=0.5)
    
    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    
    filename = f"{filename_prefix}_{identifier}.stl"
    file_path = os.path.join(OUTPUT_DIR, filename)
    
    mesh.export(file_path)
    print(f"[{filename_prefix}_{identifier}] Modelo salvo em: {file_path}")
    
    return file_path