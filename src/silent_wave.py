from pathlib import Path
import logging
import wave

_logger = logging.getLogger(__name__)

SAMPLERATE = 48000


def write_silent_wav(path: Path, channels: int,
                     tempo: float, beats: float):
    if tempo <= 0.0:
        _logger.error(
            f'Can not write a silent file with this tempo: {tempo}')
        return
    n_frames = round((60.0 / tempo) * SAMPLERATE * beats)
    
    try:
        with wave.open(str(path), 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(1)
            wav_file.setframerate(SAMPLERATE)
            wav_file.writeframes(
                bytes([0 for i in range(n_frames * channels)]))
    
    except BaseException as e:
        _logger.warning(f'Failed to write silent wav file\n{str(e)}')
