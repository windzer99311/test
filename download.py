import os
import requests
import streamlit as st
from pytubefix import YouTube

def download_video(stream_url, filename):
    response = requests.get(stream_url, stream=True)
    total = int(response.headers.get("content-length", 0))

    with open(filename, "wb") as file, st.progress(0) as progress_bar:
        downloaded = 0
        for data in response.iter_content(chunk_size=1024 * 256):  # 256 KB chunks
            file.write(data)
            downloaded += len(data)
            if total > 0:
                progress_bar.progress(downloaded / total)

def main():
    st.title("YouTube Video Downloader")

    url = st.text_input("Enter YouTube URL")
    click = st.button("Download Video")

    if click:
        if url.strip():
            try:
                yt = YouTube(url)
                st.write("🎬 **Title:**", yt.title)

                stream = yt.streams.get_lowest_resolution()
                streaming_url = stream.url

                st.write("🔗 **Direct Video URL Found!**")

                filename = "downloaded_video.mp4"
                st.info("Downloading video... Please wait.")

                download_video(streaming_url, filename)

                st.success("Download Completed!")

                # Show download button
                with open(filename, "rb") as f:
                    st.download_button(
                        label="⬇️ Download File",
                        data=f,
                        file_name=filename,
                        mime="video/mp4"
                    )

            except Exception as e:
                st.error(f"Error: {e}")

        else:
            st.warning("Please enter a YouTube URL.")

if __name__ == "__main__":
    main()
