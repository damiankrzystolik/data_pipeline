import os
import magic
from django.core.exceptions import ValidationError

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'application/pdf'}


def validate_file_extension(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f'Niedozwolone rozszerzenie pliku: {ext}')
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(f'Niedozwolony typ pliku: {mime}')


def validate_file_size(file, max_size_mb=10):
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Plik przekracza limit {max_size_mb}MB.')