"""Species dossier media — re-exports shared plate helpers."""
from __future__ import annotations

from .dossier_media import (  # noqa: F401
    DEFAULT_PROFILE,
    PROFILE_FILE,
    PROFILE_FORMAT,
    PROFILE_HEIGHT,
    PROFILE_WIDTH,
    browse_image_path,
    clear_profile_image,
    copy_profile_image,
    has_custom_profile_image,
    ingest_profile_image,
    open_image_external,
    profile_image_path,
    profile_status_label,
    resize_to_profile_plate,
    resolve_profile_image,
    validate_image_file,
    write_profile_image,
)

PROFILE_MIME = "image/png"
