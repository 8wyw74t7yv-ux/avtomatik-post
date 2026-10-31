import os
from pydub import AudioSegment
import librosa
import soundfile as sf
import numpy as np

class AudioProcessor:
    def __init__(self, input_path):
        self.input_path = input_path
        self.audio = AudioSegment.from_file(input_path)

    def cut_audio(self, start_ms, end_ms, output_path):
        """Audio kesish (millisekundlarda)"""
        processed = self.audio[start_ms:end_ms]
        processed.export(output_path, format="mp3")
        return output_path

    def change_volume(self, db_change, output_path):
        """Ovoz balandligini o'zgartirish (+dB yoki -dB)"""
        processed = self.audio + db_change
        processed.export(output_path, format="mp3")
        return output_path

    def reverse_audio(self, output_path):
        """Musiqani orqaga aylantirish (Reverse)"""
        processed = self.audio.reverse()
        processed.export(output_path, format="mp3")
        return output_path

    def change_tempo(self, output_path, speed_factor=1.2):
        """Pitch'ni buzmasdan tezlikni o'zgartirish (DJ Style Tempo)"""
        y, sr = librosa.load(self.input_path, sr=None)
        y_fast = librosa.effects.time_stretch(y, rate=speed_factor)
        sf.write(output_path, y_fast, sr)
        return output_path

    def add_fade(self, output_path, fade_in_ms=3000, fade_out_ms=3000):
        """Boshlanish va oxiriga Fade In / Fade Out qo'shish"""
        processed = self.audio.fade_in(fade_in_ms).fade_out(fade_out_ms)
        processed.export(output_path, format="mp3")
        return output_path
