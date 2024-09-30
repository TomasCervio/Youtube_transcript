import streamlit as st
import yt_dlp
import whisper
import os
import re
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """
    Extrae el ID del video de una URL de YouTube.

    Parámetros:
        url (str): La URL de YouTube.

    Retorna:
        str: El ID del video si se encuentra, de lo contrario, None.
    """
    # Expresiones regulares para diferentes formatos de URL
    regex_patterns = [
        r'(?:https?://)?(?:www\.)?youtu\.be/(?P<id>[^?&/]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/(?P<id>[^?&/]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/(?P<id>[^?&/]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=(?P<id>[^?&/]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?.*?&v=(?P<id>[^?&/]+)',
    ]

    for pattern in regex_patterns:
        match = re.match(pattern, url)
        if match:
            return match.group('id')
    
    # Si no coincide con ninguna expresión regular, intentar con urlparse
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            query_params = parse_qs(parsed_url.query)
            return query_params.get('v', [None])[0]
        elif parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        elif parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
    
    return None

def download_audio(video_url, output_dir='audios', filename='audio.mp3'):
    """
    Descarga el audio de un video de YouTube y lo guarda en el directorio especificado.

    Parámetros:
        video_url (str): La URL completa del video de YouTube.
        output_dir (str): Directorio donde se guardará el audio.
        filename (str): Nombre del archivo de audio.
    """
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, filename),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,  # Cambiar a False para ver más detalles en la descarga
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def transcribe_audio(audio_path, model_name='base', language='es'):
    """
    Transcribe el audio utilizando el modelo Whisper.

    Parámetros:
        audio_path (str): Ruta al archivo de audio.
        model_name (str): Nombre del modelo Whisper a usar ('tiny', 'base', 'small', 'medium', 'large').
        language (str): Código de idioma para la transcripción.

    Retorna:
        str: Texto transcrito del audio.
    """
    try:
        # Cargar el modelo Whisper
        model = whisper.load_model(model_name)
        
        # Transcribir el audio
        result = model.transcribe(audio_path, language=language)
        
        return result['text']
    except Exception as e:
        return f"Error durante la transcripción: {e}"

def main():
    st.title("Transcriptor de Videos de YouTube 🎥📝")
    st.write("Ingresa el enlace de un video de YouTube y obtén la transcripción del audio.")
    
    # Entrada del usuario
    youtube_url = st.text_input("URL de YouTube:", "")
    
    # Selección del idioma
    language = st.selectbox(
        "Selecciona el idioma del audio:",
        ("es", "en", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh")
    )
    
    # Selección del modelo Whisper
    model_name = st.selectbox(
        "Selecciona el modelo de transcripción:",
        ("tiny", "base", "small", "medium", "large")
    )
    
    if st.button("Transcribir"):
        if youtube_url:
            video_id = extract_video_id(youtube_url)
            if video_id:
                st.success(f"ID del Video: `{video_id}`")
                
                # Mostrar el video
                st.video(f"https://www.youtube.com/watch?v={video_id}")
                
                # Descargar el audio
                with st.spinner("Descargando el audio..."):
                    audio_filename = f"{video_id}.mp3"
                    download_audio(youtube_url, output_dir='audios', filename=audio_filename)
                
                audio_path = os.path.join('audios', audio_filename)
                
                if os.path.exists(audio_path):
                    st.success("Audio descargado correctamente.")
                    
                    # Transcribir el audio
                    with st.spinner("Transcribiendo el audio..."):
                        transcription = transcribe_audio(audio_path, model_name=model_name, language=language)
                    
                    # Mostrar la transcripción
                    if "Error durante la transcripción" not in transcription:
                        st.subheader("Transcripción:")
                        st.write(transcription)
                        
                        # Descargar la transcripción como archivo de texto
                        st.download_button(
                            label="Descargar Transcripción",
                            data=transcription,
                            file_name=f"{video_id}_transcription.txt",
                            mime="text/plain",
                        )
                    else:
                        st.error(transcription)
                else:
                    st.error("No se pudo descargar el audio. Verifica la URL y vuelve a intentarlo.")
            else:
                st.error("No se pudo extraer el ID del video. Por favor, verifica la URL ingresada.")
        else:
            st.warning("Por favor, ingresa una URL de YouTube.")

if __name__ == "__main__":
    main()

