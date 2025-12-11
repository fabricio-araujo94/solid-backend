import os
import uuid
from typing import Protocol, Tuple, runtime_checkable, BinaryIO
import shutil
import cloudinary
import cloudinary.uploader

@runtime_checkable
class IFileStorage(Protocol):
    def save(self, file_bytes: bytes, original_filename: str, directory: str, prefix: str = "") -> Tuple[str, str]:
        """
        Saves a file and returns (physical_path_or_id, access_url)
        """
        ...
        
    def save_stream(self, file_stream: BinaryIO, original_filename: str, directory: str, prefix: str = "") -> Tuple[str, str]:
        """
        Saves a file from a stream and returns (physical_path_or_id, access_url)
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
        
    def save_stream(self, file_stream: BinaryIO, original_filename: str, directory: str, prefix: str = "") -> Tuple[str, str]:
        os.makedirs(directory, exist_ok=True)
        filename_parts = original_filename.split('.')
        file_extension = filename_parts[-1] if len(filename_parts) > 1 else "bin"
        
        if prefix:
            unique_filename = f"{prefix}_{uuid.uuid4()}.{file_extension}"
        else:
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
        file_path = os.path.join(directory, unique_filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file_stream, f)
            
        path_for_url = os.path.join(directory, unique_filename).replace(os.sep, "/")
        return file_path, f"{self.base_url}/{path_for_url}"

class CloudinaryFileStorage:
    def __init__(self):
        # Configuration is handled via CLOUDINARY_URL env var or parameters
        pass

    def save(self, file_bytes: bytes, original_filename: str, directory: str, prefix: str = "") -> Tuple[str, str]:
        # Using directory as 'folder' in Cloudinary
        filename_parts = original_filename.split('.')
        public_id = filename_parts[0]
        if prefix:
             public_id = f"{prefix}_{public_id}_{uuid.uuid4()}"
        else:
             public_id = f"{public_id}_{uuid.uuid4()}"

        result = cloudinary.uploader.upload(
            file_bytes, 
            folder=directory,
            public_id=public_id,
            resource_type="auto"
        )
        return result['public_id'], result['secure_url']

    def save_stream(self, file_stream: BinaryIO, original_filename: str, directory: str, prefix: str = "") -> Tuple[str, str]:
        filename_parts = original_filename.split('.')
        public_id = filename_parts[0]
        if prefix:
             public_id = f"{prefix}_{public_id}_{uuid.uuid4()}"
        else:
             public_id = f"{public_id}_{uuid.uuid4()}"
             
        result = cloudinary.uploader.upload(
            file_stream,
            folder=directory,
            public_id=public_id,
            resource_type="auto"
        )
        return result['public_id'], result['secure_url']
