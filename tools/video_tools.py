from urllib.parse import urlparse
# import yt_dlp
import google.generativeai as genai
# from smolagents import tool
from langchain_core.tools import tool
from langchain_community.document_loaders import YoutubeLoader
import tempfile
import os


@tool
def analyze_youtube_video(url: str) -> str:
    """
    Analyze YouTube video content using metadata and subtitles.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Analysis of the video content
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return "Please provide a valid video URL with http:// or https:// prefix."

        if 'youtube.com' not in url and 'youtu.be' not in url:
            return "Only YouTube videos are supported at this time."

        with tempfile.TemporaryDirectory() as tmpdir:
            subtitle_path = None

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return "Could not extract video information."

                video_id = info.get("id")
                title = info.get("title", "Unknown")
                description = info.get("description", "")
                duration = info.get("duration", 0)
                view_count = info.get("view_count", 0)
                upload_date = info.get("upload_date", "")

                if upload_date:
                    upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

                # Look for subtitle file
                subtitle_file = Path(tmpdir) / f"{video_id}.en.vtt"
                subtitle_text = ""
                if subtitle_file.exists():
                    try:
                        import webvtt
                        for caption in webvtt.read(str(subtitle_file)):
                            subtitle_text += caption.text + " "
                        subtitle_text = subtitle_text.strip()
                    except Exception as e:
                        subtitle_text = "(Failed to parse subtitles)"
                else:
                    subtitle_text = "(No subtitles found for this video)"

                # Construct prompt
                prompt = f"""Please analyze this YouTube video:
Title: {title}
URL: {url}
Duration: {duration} seconds
Upload Date: {upload_date}
Views: {view_count:,}
Description: {description}

Subtitles:
{subtitle_text}

Please provide a detailed analysis focusing on:
1. Main topic and key points
2. Expected visual elements and scenes
3. Overall message or purpose
4. Target audience
5. Key information from the description and subtitles
6. Any notable statistics or facts
"""

                response = genai.generate_content(prompt)
                return response.text

    except Exception as e:
        return f"Error analyzing video: {str(e)}"



# @tool
# def youtube_transcript(url: str) -> str:
#     """Download a transcript of a YouTube video.
#     Args:
#         url: URL of the YouTube video."""
#     print("\n-------------------- Tool (YouTube Transcript) has been called --------------------\n")
#     loader = YoutubeLoader.from_youtube_url(
#         url, add_video_info=False
#     )
#     docs = loader.load()
#     transcript = "\n\n".join(
#         (f"\nContent:\n{doc.page_content}")
#         for doc in docs
#     )
#     return {"youtube_transcript": transcript}
        