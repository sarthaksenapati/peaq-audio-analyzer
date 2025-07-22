# models/recording_session.py

from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class RecordingSession:
    file: str
    start_time: datetime = field(default_factory=datetime.now)
    duration_sec: float = 0.0
    clean_duration_sec: float = 0.0
    interruptions: int = 0
