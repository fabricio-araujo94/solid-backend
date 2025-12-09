from typing import Protocol, Tuple, runtime_checkable
import os
import uuid

@runtime_checkable
class IFileStorage(Protocol):
    def save(self, file_bytes: bytes, original_filename: str, directory: str, prefix: str = "") -> Tuple[str, str]:
        """
        Saves a file and returns (physical_path, access_url)
        """
        ...

class LocalFileStorage:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def save(self, file_bytes: bytes, original_filename: str, directory: str, prefix: str = "") -> Tuple[str, str]:
        os.makedirs(directory, exist_ok=True)
        filename_parts = original_filename.split('.')
        file_extension = filename_parts[-1] if len(filename_parts) > 1 else "bin"
        
        if prefix:
            unique_filename = f"{prefix}_{uuid.uuid4()}.{file_extension}"
        else:
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
        file_path = os.path.join(directory, unique_filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        path_for_url = os.path.join(directory, unique_filename).replace(os.sep, "/")
        return file_path, f"{self.base_url}/{path_for_url}"
