import os
import uuid

BASE_URL = "https://special-rotary-phone-pvwjvqvv95c99jp-8000.app.github.dev"

def save_file_to_disk(file_bytes: bytes, original_filename: str, directory: str, prefix: str = "") -> tuple[str, str]:
    """
    Saves bytes to disk with a unique name.
    Returns:
        tuple: (file_path_on_disk, web_url)
    """
    os.makedirs(directory, exist_ok=True)
    # Simple extension extraction
    filename_parts = original_filename.split('.')
    file_extension = filename_parts[-1] if len(filename_parts) > 1 else "bin"
    
    if prefix:
        unique_filename = f"{prefix}_{uuid.uuid4()}.{file_extension}"
    else:
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
    file_path = os.path.join(directory, unique_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
        
    # Convert backslashes to slashes for URL
    path_for_url = os.path.join(directory, unique_filename).replace(os.sep, "/")
    return file_path, f"{BASE_URL}/{path_for_url}"
