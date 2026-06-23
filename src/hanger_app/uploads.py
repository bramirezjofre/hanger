import io
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


@dataclass(frozen=True)
class SavedUpload:
    stored_name: str
    original_name: str
    mime_type: str
    size: int


class UploadService:
    FORMATS = {"PNG": "png", "JPEG": "jpg", "GIF": "gif", "WEBP": "webp"}

    def __init__(self, directory: Path, max_bytes: int):
        self.directory = Path(directory)
        self.max_bytes = max_bytes
        self.directory.mkdir(parents=True, exist_ok=True)

    def save_image(self, upload: FileStorage) -> SavedUpload:
        original_name = secure_filename(upload.filename or "")
        if not original_name:
            raise ValueError("An image filename is required")
        content = upload.stream.read(self.max_bytes + 1)
        if not content or len(content) > self.max_bytes:
            raise ValueError("Image is empty or exceeds the upload limit")
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
                image_format = image.format
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError("Uploaded file is not a valid image") from error
        extension = self.FORMATS.get(image_format or "")
        if extension is None:
            raise ValueError("Unsupported image format")
        stored_name = f"{uuid.uuid4().hex}.{extension}"
        (self.directory / stored_name).write_bytes(content)
        return SavedUpload(
            stored_name=stored_name,
            original_name=original_name,
            mime_type=f"image/{'jpeg' if extension == 'jpg' else extension}",
            size=len(content),
        )
