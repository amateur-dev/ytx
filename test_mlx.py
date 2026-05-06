import mlx_whisper

# Create a dummy audio file using ffmpeg
import subprocess
subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=2', 'test.wav'], capture_output=True)

res = mlx_whisper.transcribe('test.wav', path_or_hf_repo='mlx-community/whisper-tiny')
print(res.keys())
if 'segments' in res and len(res['segments']) > 0:
    print(res['segments'][0].keys())
print("Language:", res.get('language'))
