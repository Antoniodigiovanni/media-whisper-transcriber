import streamlit as st
import os
import tempfile
import torch
import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import urlparse
from io import BytesIO
from dotenv import load_dotenv

# Import your modules
from src.transcription.api_model import ApiModel
from src.transcription.local_model import Model
from src.downloader.downloader import download_mp3_from_youtube, download_podcast_from_podcastindex_url

load_dotenv()

# Create folder if it doesn't exist
if not os.path.exists('./downloads'):
    os.makedirs('./downloads')

st.set_page_config(page_title="Whisper AI - Media Transcriber", layout="wide")

def main():
    st.title("Whisper Audio Transcriber")
    st.subheader("Download & Transcribe YouTube Videos or Podcasts")

    # Sidebar for model selection
    st.sidebar.header("Settings")
    transcription_method = st.sidebar.radio(
        "Transcription Method",
        options=["API (Groq)", "Local (Whisper)"]
    )
    
    if transcription_method == "API (Groq)":
        api_key = os.getenv("GROQ_API_KEY")

        # # Useful for custom Gro API key written by the user
        # api_key = st.sidebar.text_input("Enter Groq API Key", type="password")
        # if api_key:
            # os.environ["GROQ_API_KEY"] = api_key

        model_name = st.sidebar.selectbox(
            "Select Model",
            options=["whisper-large-v3", "whisper-medium", "whisper-small"],
            index=0
        )
        language = st.sidebar.selectbox(
            "Language",
            options=[None, "en", "it", "fr", "es", "de"],
            index=0,
            format_func=lambda x: "Auto-detect" if x is None else x
        )
        return_text_only = st.sidebar.checkbox("Return Text Only", value=True)
    else:
        model_name = st.sidebar.selectbox(
            "Select Model",
            options=["openai/whisper-large-v3", "openai/whisper-medium", "openai/whisper-small"],
            index=0
        )
        st.sidebar.info("Using local Whisper model requires GPU for optimal performance.")
        
    # Tabs for different input methods
    tab1, tab2, tab3, tab4 = st.tabs(["YouTube URL", "Podcast RSS", "Upload Audio", "Saved Files"])
    
    # YouTube URL tab
    with tab1:
        st.header("Transcribe from YouTube")
        youtube_url = st.text_input("Enter YouTube URL")
        
        col1, col2 = st.columns(2)
        with col1:
            download_btn = st.button("Download & Transcribe", key="youtube_download")
        with col2:
            save_audio = st.checkbox("Save audio file", value=False)
            
        if download_btn and youtube_url:
            with st.spinner("Downloading audio from YouTube..."):
                try:
                    if save_audio:
                        # filename = f"downloaded_audio_{hash(youtube_url)}.mp3"
                        # download_mp3_from_youtube(youtube_url, save_file=True, filename=filename)
                        audio_file = download_mp3_from_youtube(youtube_url, save_file=True)
                        file_name = audio_file.split('/')[-1]
                        st.success(f"Audio saved as {file_name}")
                    else:
                        audio_bytes = download_mp3_from_youtube(youtube_url)
                        # Save to temporary file
                        temp_dir = tempfile.mkdtemp()
                        temp_path = os.path.join(temp_dir, "audio.mp3")
                        with open(temp_path, "wb") as f:
                            f.write(audio_bytes)
                        audio_file = temp_path
                        st.success("Download complete!")
                    
                    transcribe_file(audio_file, transcription_method, model_name, language, return_text_only)
                    
                except Exception as e:
                    st.error(f"Error downloading from YouTube: {str(e)}")
    
    # Podcast RSS tab
    with tab2:
        st.header("Download & Transcribe Podcast")
        st.markdown('### Search Podcasts RSS links [here](https://podcastindex.org)')
        feed_url = st.text_input("Enter podcast RSS feed URL")
        
        if feed_url:
            # Display a loading message while fetching podcast data
            with st.spinner("Fetching podcast feed..."):
                episodes, _ = download_podcast_from_podcastindex_url(feed_url)
            
            if episodes:
                st.success(f"Found {len(episodes)} episodes")
                
                # Let user select episodes
                episode_options = {f"Episode {ep['index']+1}: {ep['title']}": ep['index'] for ep in episodes}
                selected_episodes = st.multiselect(
                    "Select episodes to download",
                    options=list(episode_options.keys())
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    save_podcast_audio = st.checkbox("Save podcast audio files", value=False)
                with col2:
                    transcribe_after_download = st.checkbox("Transcribe after download", value=True)
                
                download_dir = "downloads" if save_podcast_audio else None
                
                if st.button("Download Selected Episodes", key="podcast_download"):
                    if not selected_episodes:
                        st.warning("Please select at least one episode")
                    else:
                        selected_indices = [episode_options[ep] for ep in selected_episodes]
                        
                        # Download selected episodes
                        _, downloaded_files = download_podcast_from_podcastindex_url(
                            feed_url, 
                            download_dir=download_dir,
                            selected_indices=selected_indices
                        )
                        
                        if downloaded_files:
                            st.success(f"Successfully downloaded {len(downloaded_files)} episodes")
                            
                            # Display downloaded files
                            for i, file_info in enumerate(downloaded_files):
                                with st.expander(f"{i+1}. {file_info['title']}"):
                                    st.write(f"File path: {file_info['path']}")
                                    st.write(f"Size: {file_info['size'] / (1024*1024):.2f} MB")
                                
                                # Transcribe if option selected
                                if transcribe_after_download:
                                    with st.expander(f"Transcription - {file_info['title']}"):
                                        transcribe_file(
                                            file_info['path'], 
                                            transcription_method, 
                                            model_name, 
                                            language, 
                                            return_text_only
                                        )
                        else:
                            st.error("Failed to download any episodes")

    # Upload audio tab
    with tab3:
        st.header("Upload Audio File")
        uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "flac"])
        save_uploaded_audio = st.checkbox("Keep file in local storage", value=False)


        if uploaded_file is not None:
            if not save_uploaded_audio:
                # Save the uploaded file to a temporary location
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                audio_file_path = temp_path
            else:
                default_path = f'./downloads/{uploaded_file.name}'
                with open(default_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    audio_file_path = default_path                 
                    st.success(f"Audio saved as {uploaded_file.name}")

            st.audio(uploaded_file)

            if st.button("Transcribe Uploaded Audio"):
                transcribe_file(audio_file_path, transcription_method, model_name, language, return_text_only)

    with tab4:

        def file_selector(folder_path='./downloads'):
            filenames = os.listdir(folder_path)
            selected_filename = st.selectbox('Select a file', filenames, index=None)
            if selected_filename is not None:
                return os.path.join(folder_path, selected_filename)

        filename = file_selector()
        if filename is not None:
            st.audio(filename)
            st.button('Transcribe', on_click= transcribe_file, args=(filename, transcription_method, model_name, language, return_text_only))


def transcribe_file(audio_path, transcription_method, model_name, language=None, return_text_only=True):
    try:
        with st.spinner("Transcribing audio..."):
            if transcription_method == "API (Groq)":
                
                if "GROQ_API_KEY" not in os.environ:
                    st.error("Please enter your Groq API key in the .env file or set GROQ_API_KEY environment variable.")
                    return
                    
                transcriber = ApiModel(
                    model_name=model_name,
                    language=language,
                    return_text_only=return_text_only
                )
                result = transcriber.transcribe(audio_path)
                
            else:
                # Initialize and load the model
                transcriber = Model(model_name)
                with st.spinner("Loading Whisper model... This may take a couple of minutes"):
                    transcriber.load_model()
                
                result = transcriber.transcribe([audio_path])
            
            # Display results
            st.success("Transcription complete!")
            
            if transcription_method == "API (Groq)" and not return_text_only:
                st.json(result)
            else:
                st.header("Transcription:")
                st.write(result)
                
                # Download button for transcription
                st.download_button(
                    label="Download Transcription",
                    data=result if isinstance(result, str) else str(result),
                    file_name="transcription.txt",
                    mime="text/plain"
                )
    
    except Exception as e:
        st.error(f"Error during transcription: {str(e)}")
        st.info("If using the local model, make sure you have sufficient GPU memory.")

if __name__ == "__main__":
    main()