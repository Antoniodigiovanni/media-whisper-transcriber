from pytubefix import YouTube
import logging, io

def download_mp3_from_youtube(youtube_url: str, save_file=False, filename=None) -> bytes:
    logging.getLogger("pytube").setLevel(logging.INFO)
    yt = YouTube(youtube_url)
    video = yt.streams.filter(only_audio=True).first()
    buffer = io.BytesIO()
    video.stream_to_buffer(buffer)
    buffer.seek(0)
    if save_file:
        if filename is None:
            filename = yt.title + ".mp3"
        with open(filename, "wb") as f:
            f.write(buffer.read())
            buffer.close()
            logging.log(logging.INFO, f"Saved {filename}")
    else:
        logging.log(logging.INFO, f"Downloaded {yt.title} to buffer")
        return buffer.read()

def download_captions_from_youtube(youtube_url: str, captions_format='txt', save_path=None, language=None):
    assert captions_format in ['txt', 'srt'], f"Invalid captions format. Possible values are 'txt' or 'srt', got {captions_format}"
    
    yt = YouTube(youtube_url)
    if language is None:
        language = list(yt.captions.keys())[0]

    if captions_format == 'txt':
        caption = yt.captions[language].generate_txt_captions()
    elif captions_format == 'srt':
        caption = yt.captions[language].generate_srt_captions()

    if save_path is not None:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(caption)

    return caption

def download_podcast_from_podcastindex_url():
    #TODO
    pass

