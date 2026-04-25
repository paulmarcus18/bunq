from __future__ import annotations

import io
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


_WHISPER_MODEL = None


def _get_model():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is not None:
        return _WHISPER_MODEL

    from faster_whisper import WhisperModel

    model_size = os.getenv("WHISPER_MODEL_SIZE", "base.en")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    logger.info("Loading faster-whisper model %s (%s)", model_size, compute_type)
    _WHISPER_MODEL = WhisperModel(model_size, device="cpu", compute_type=compute_type)
    return _WHISPER_MODEL


def transcribe_audio(file_bytes: bytes, filename: Optional[str] = None) -> str:
    if not file_bytes:
        return ""

    model = _get_model()
    audio_buffer = io.BytesIO(file_bytes)
    segments, _info = model.transcribe(
        audio_buffer,
        language="en",
        vad_filter=True,
        beam_size=1,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()
