import math
import os
import random
import struct
import tempfile
import wave
from PySide6.QtCore import QObject, QUrl, Signal
from .state import resource_path

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
    HAS_MULTIMEDIA = True
except Exception:
    HAS_MULTIMEDIA = False


class NativeAudioEngine(QObject):
    """Pure Native Qt6 Audio Engine for Offline Sahaba Poems & Music-Free Natural Ambiance."""

    poem_progress = Signal(int, int)  # position_ms, duration_ms
    poem_state = Signal(bool)         # is_playing

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ambiance_enabled = False
        self.ambiance_mode = "desert"
        self._temp_wavs = {}

        self._poem_player = None
        self._poem_out = None
        self._amb_player = None
        self._amb_out = None

        if HAS_MULTIMEDIA:
            try:
                self._poem_player = QMediaPlayer(self)
                self._poem_out = QAudioOutput(self)
                self._poem_out.setVolume(0.92)
                self._poem_player.setAudioOutput(self._poem_out)
                self._poem_player.positionChanged.connect(self._on_pos)
                self._poem_player.durationChanged.connect(self._on_dur)
                self._poem_player.playbackStateChanged.connect(self._on_state)

                self._amb_player = QMediaPlayer(self)
                self._amb_out = QAudioOutput(self)
                self._amb_out.setVolume(0.22)
                self._amb_player.setAudioOutput(self._amb_out)
                self._amb_player.setLoops(QMediaPlayer.Loops.Infinite)
            except Exception:
                self._poem_player = None
                self._amb_player = None

    def _on_pos(self, pos: int):
        dur = self._poem_player.duration() if self._poem_player else 0
        self.poem_progress.emit(pos, dur)

    def _on_dur(self, dur: int):
        pos = self._poem_player.position() if self._poem_player else 0
        self.poem_progress.emit(pos, dur)

    def _on_state(self, state):
        if not self._poem_player:
            return
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.poem_state.emit(playing)

    # ---------- Sahaba Poems Offline Playback ----------
    def load_and_play_poem(self, rel_audio_src: str, speed: float = 1.0):
        if not self._poem_player:
            return False
        full_path = resource_path(rel_audio_src)
        if not os.path.exists(full_path):
            return False
        current = self._poem_player.source().toLocalFile()
        if os.path.abspath(current) != os.path.abspath(full_path):
            self._poem_player.setSource(QUrl.fromLocalFile(full_path))
        self._poem_player.setPlaybackRate(speed)
        self._poem_player.play()
        return True

    def toggle_poem(self, rel_audio_src: str, speed: float = 1.0) -> bool:
        if not self._poem_player:
            return False
        if self._poem_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._poem_player.pause()
            return False
        return self.load_and_play_poem(rel_audio_src, speed)

    def stop_poem(self):
        if self._poem_player:
            self._poem_player.stop()

    def seek_poem_ratio(self, ratio: float):
        if self._poem_player and self._poem_player.duration() > 0:
            target = int(max(0.0, min(1.0, ratio)) * self._poem_player.duration())
            self._poem_player.setPosition(target)

    def set_poem_speed(self, speed: float):
        if self._poem_player:
            self._poem_player.setPlaybackRate(speed)

    # ---------- Music-Free Synthesized Natural Soundscapes ----------
    def _ensure_ambiance_wav(self, mode: str) -> str:
        if mode in self._temp_wavs and os.path.exists(self._temp_wavs[mode]):
            return self._temp_wavs[mode]

        sr = 22050
        seconds = 6
        total_samples = sr * seconds
        fd, path = tempfile.mkstemp(prefix=f"sirag_amb_{mode}_", suffix=".wav")
        os.close(fd)

        rng = random.Random(42 if mode == "desert" else (99 if mode == "rain" else 7))
        prev = 0.0
        prev2 = 0.0
        buf = bytearray()

        alpha = 0.04 if mode == "desert" else (0.28 if mode == "rain" else 0.09)
        for i in range(total_samples):
            white = rng.uniform(-1.0, 1.0)
            prev = prev + alpha * (white - prev)
            prev2 = prev2 + (alpha * 0.6) * (prev - prev2)
            # Gentle natural breath envelope with seamless loop edges
            t = i / total_samples
            env = 0.65 + 0.35 * math.sin(2.0 * math.pi * t * 2.0)
            sample = prev2 * env * (0.45 if mode != "rain" else 0.30)
            if mode == "rain" and rng.random() < 0.0025:
                sample += rng.uniform(-0.22, 0.22)
            val = max(-32767, min(32767, int(sample * 32767)))
            buf += struct.pack("<h", val)

        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(bytes(buf))

        self._temp_wavs[mode] = path
        return path

    def toggle_ambiance(self, mode: str = None) -> bool:
        if mode:
            self.ambiance_mode = mode
        self.ambiance_enabled = not self.ambiance_enabled
        self._apply_ambiance()
        return self.ambiance_enabled

    def set_ambiance_mode(self, mode: str):
        self.ambiance_mode = mode
        if self.ambiance_enabled:
            self._apply_ambiance()

    def _apply_ambiance(self):
        if not self._amb_player:
            return
        if not self.ambiance_enabled:
            self._amb_player.stop()
            return
        wav_path = self._ensure_ambiance_wav(self.ambiance_mode)
        self._amb_player.setSource(QUrl.fromLocalFile(wav_path))
        self._amb_player.play()
