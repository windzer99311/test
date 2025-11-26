import requests, streamlit as st, os, time
from pytubefix import YouTube

def main():
    st.title("YouTube Video Downloader")
    url = st.text_input("Enter YouTube URL")
    click = st.button("Download Video")

    if url:
        if click:
            yt = YouTube(url)
            stream = yt.streams.get_lowest_resolution()

            # Unique filename to avoid Windows lock
            filename = f"video_{int(time.time())}.mp4"

            stream.download(filename=filename)

            st.success("Video downloaded!")

            with open(filename, "rb") as f:
                st.download_button(
                    label="Save to device",
                    data=f,
                    file_name=filename,
                    mime="video/mp4"
                )

    else:
        st.write("Enter YouTube URL")

main()
