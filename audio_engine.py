import subprocess
import os

class ProAudioEngine:
    @staticmethod
    def run_ffmpeg(cmd: list):
        """FFmpeg buyrug'ini xavfsiz bajarish va xatoliklarni ushlash"""
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg xatoligi: {process.stderr.decode('utf-8')}")

    @classmethod
    def apply_bass_boost(cls, input_path: str, output_path: str, gain_db: int = 15):
        """Professional Bass Kuchaytirgich (Low-shelf filter)"""
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-af', f'equalizer=f=90:width_type=o:width=2:g={gain_db}',
            output_path
        ]
        cls.run_ffmpeg(cmd)
        return output_path

    @classmethod
    def change_speed_and_pitch(cls, input_path: str, output_path: str, tempo: float = 1.2):
        """Vokalni buzmasdan tempni o'zgartirish (DJ Tempo Shift)"""
        # atempo 0.5 dan 2.0 gacha ishlaydi
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-af', f'atempo={tempo}',
            output_path
        ]
        cls.run_ffmpeg(cmd)
        return output_path

    @classmethod
    def apply_radio_filter(cls, input_path: str, output_path: str):
        """Radio / Telefon ovozi effekti (Bandpass filter)"""
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-af', 'highpass=f=300, lowpass=f=3000',
            output_path
        ]
        cls.run_ffmpeg(cmd)
        return output_path

    @classmethod
    def reverse_audio(cls, input_path: str, output_path: str):
        """Musiqani to'liq orqaga aylantirish (Reverse)"""
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-af', 'areverse',
            output_path
        ]
        cls.run_ffmpeg(cmd)
        return output_path

    @classmethod
    def apply_reverb(cls, input_path: str, output_path: str):
        """Akustik Xona / Reverb (Echo) effekti"""
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-af', 'aecho=0.8:0.88:60|150:0.4|0.2',
            output_path
        ]
        cls.run_ffmpeg(cmd)
        return output_path
