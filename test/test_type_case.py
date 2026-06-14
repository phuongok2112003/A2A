import sounddevice as sd
from typecast import Typecast
from typecast.models import TTSRequestStream, OutputStream, LanguageCode

# Initialize client with API key
client = Typecast(api_key="__plt3FqV7xago2D26eGbaLksvYgXRnJkNtdjToGBnPb3")

request = TTSRequestStream(
    text="Tôi yêu bạn, và tôi yêu tất cả các em.",
    model="ssfm-v30",
    voice_id="tc_672c5f5ce59fac2a48faeaee",
    output=OutputStream(audio_format="wav"),
    language=LanguageCode.VIE,
)

# Instead of playing directly, save the streamed audio to a file
output_filename = "streamed_output.wav"
with open(output_filename, "wb") as f:
    for chunk in client.text_to_speech_stream(request):
        f.write(chunk)

print(f"Streamed audio saved to {output_filename}")