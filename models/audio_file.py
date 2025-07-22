# models/audio_file.py
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AudioFile:
    path: str

    @property
    def name(self):
        return Path(self.path).stem

    @property
    def extension(self):
        return Path(self.path).suffix.lower()
