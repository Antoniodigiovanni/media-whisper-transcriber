from pytubefix import YouTube
import logging, io
import requests
import xml.etree.ElementTree as ET
import os
from urllib.parse import urlparse

from src.utils.utils import get_safe_file_name

def download_mp3_from_youtube(youtube_url: str, save_file=False, download_dir='downloads', filename=None) -> bytes:
    logging.getLogger("pytube").setLevel(logging.INFO)
    yt = YouTube(youtube_url)
    video = yt.streams.filter(only_audio=True).first()
    buffer = io.BytesIO()
    video.stream_to_buffer(buffer)
    buffer.seek(0)
    if save_file:
        if filename is None:
            filename = get_safe_file_name(yt.title + ".mp3")
            file_path = download_dir + '/' + filename
        with open(file_path, "wb") as f:
            f.write(buffer.read())
            buffer.close()
            logging.log(logging.INFO, f"Saved {filename}")
            return file_path
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

def download_podcast_from_podcastindex_url(feed_url, media_type="audio/mpeg", download_dir=None, selected_indices=None):
    """
    Downloads podcast audio files of a specified media type from an RSS feed URL.
    
    Args:
        feed_url (str): The URL of the podcast RSS feed
        media_type (str): The media type to download (e.g., "audio/mpeg")
        download_dir (str): Directory to save downloaded files
        selected_indices (list): List of episode indices to download (None means user will be prompted)
        
    Returns:
        tuple: (list of episode info, downloaded files info)
    """
    # Create download directory if specified and it doesn't exist
    if download_dir and not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Fetch the RSS feed
    try:
        response = requests.get(feed_url)
        response.raise_for_status()  # Raise exception for bad status codes
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching RSS feed: {e}")
        return [], []
    
    # Parse XML content
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        st.error(f"Error parsing XML: {e}")
        return [], []
    
    # Find channel element (typical RSS feed structure)
    channel = root.find("channel") if root.tag == "rss" else root
    
    # Get podcast title for display
    podcast_title_elem = channel.find("title")
    podcast_title = podcast_title_elem.text if podcast_title_elem is not None else "Podcast"
    
    # Build list of episodes
    episodes = []
    for i, item in enumerate(channel.findall("item")):
        title_elem = item.find("title")
        title = title_elem.text if title_elem is not None else f"Episode {i+1}"
        
        # Find the enclosure with the specified media type
        enclosure = item.find("enclosure")
        if enclosure is not None and (media_type is None or enclosure.get("type") == media_type):
            episodes.append({
                "index": i,
                "title": title,
                "url": enclosure.get("url")
            })
    
    # Reverse the episode numbering
    total_episodes = len(episodes)
    for episode in episodes:
        episode["index"] = total_episodes - episode["index"] - 1
    
    if not episodes:
        st.warning(f"No episodes found with media type: {media_type}")
        return [], []
    
    # If no indices are provided, they will be selected in the Streamlit UI
    if selected_indices is None:
        return episodes, []
    
    # Process selected episodes
    selected_episodes = [ep for ep in episodes if ep["index"] in selected_indices]
    
    # Download selected episodes
    downloaded = []
    for episode in selected_episodes:
        # safe_title = re.sub(r'[^\w\-_.]', '_', episode['title'])
        safe_title = get_safe_file_name(episode['title'])
        
        # Extract filename from URL or use the safe title
        url_path = urlparse(episode['url']).path
        file_extension = os.path.splitext(url_path)[1] if url_path else ".mp3"
        if not file_extension:
            file_extension = ".mp3"  # Default extension for audio/mpeg
            
        filename = f"{safe_title}{file_extension}"
        
        # Use either specified download directory or temporary directory
        if download_dir:
            filepath = os.path.join(download_dir, filename)
        else:
            temp_dir = tempfile.mkdtemp()
            filepath = os.path.join(temp_dir, filename)
        
        with st.status(f"Downloading: {episode['title']}", expanded=True) as status:
            try:
                # Stream download to handle large files
                with requests.get(episode['url'], stream=True) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    
                    with open(filepath, 'wb') as f:
                        downloaded_size = 0
                        chunk_size = 8192
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # Update progress
                                if total_size > 0:
                                    percent = (downloaded_size / total_size) * 100
                                    status.update(label=f"Downloading: {episode['title']} - {percent:.1f}%")
                    
                    status.update(label=f"Downloaded: {episode['title']}", state="complete")
                    downloaded.append({
                        "title": episode['title'],
                        "path": filepath,
                        "size": total_size
                    })
            except requests.exceptions.RequestException as e:
                status.update(label=f"Error downloading {episode['title']}: {e}", state="error")
    
    return episodes, downloaded
