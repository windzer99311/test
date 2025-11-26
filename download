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

            response = requests.get(streaming_url)
            filename = "test.mp4"

            with open(filename, "wb") as f:
                f.write(response.content)

            st.success("Video downloaded!")

            # ⭐ ADDING ONLY THE SAVE BUTTON (download_button)
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
