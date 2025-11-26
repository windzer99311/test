import streamlit as st
from pytubefix import YouTube

def main():
    st.title("YouTube URL Extractor")

    url = st.text_input("Enter YouTube URL")
    click = st.button("Get URL")

    if url and click:
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=False)

        # Try to get a stable (non-cipher) streaming URL
        stream = yt.streams.filter(progressive=True, file_extension="mp4").first()

        if stream:
            st.write(stream.url)   # print the URL
        else:
            st.write("No stable streaming URL available for this video.")

main()
