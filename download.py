import requests , streamlit as st
from pytubefix import YouTube


def main():
    st.title("YouTube Video Downloader")
    url = st.text_input("Enter YouTube URL")
    click = st.button("Download Video")

    if url:
        if click:
            yt = YouTube(url)
            streaming_url = yt.streams.get_lowest_resolution().url

            st.write(streaming_url)
    else:
        st.write("Enter YouTube URL")

main()
