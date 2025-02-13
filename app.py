import streamlit as st
import requests
from PIL import Image
import io
import tweepy
import os
from dotenv import load_dotenv
load_dotenv()


IMAGE_SIZES = [(300, 250), (728, 90), (160, 600), (300, 600)]

def resize_image(image, size):
    return image.resize(size, Image.LANCZOS)


def upload_to_twitter(images):
    """Uploads images to Twitter (X) using API v1.1 for media upload and API v2 for tweeting."""
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_SECRET")
    bearer_token = os.getenv("X_BEARER_TOKEN")

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api = tweepy.API(auth)

    client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_secret)

    media_ids = []
    for img in images:
        byte_io = io.BytesIO()
        img.save(byte_io, format='PNG')
        byte_io.seek(0)

        media_res = api.media_upload(filename="image.png", file=byte_io)
        media_ids.append(media_res.media_id_string)

    client.create_tweet(text="Here are your resized images!", media_ids=media_ids)
    st.success("Images posted to Twitter!")



# Streamlit UI
st.title("Image Resizer and Twitter Uploader")
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Original Image", use_container_width=True)
    
    resized_images = [resize_image(image, size) for size in IMAGE_SIZES]
    
    for img, size in zip(resized_images, IMAGE_SIZES):
        st.image(img, caption=f"{size[0]}x{size[1]}", use_container_width=True)
    
    if st.button("Post to Twitter"):
        upload_to_twitter(resized_images)