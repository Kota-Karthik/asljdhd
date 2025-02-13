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

def get_twitter_auth():
    """Initialize OAuth1 authentication for Twitter login."""
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, callback="oob")
    try:
        redirect_url = auth.get_authorization_url()
        st.session_state["request_token"] = auth.request_token
        return redirect_url
    except tweepy.TweepyException as e:
        st.error(f"Failed to get authorization URL: {e}")
        return None

def authenticate_user(oauth_verifier):
    """Exchange the verifier PIN for user access tokens."""
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    auth = tweepy.OAuth1UserHandler(api_key, api_secret)
    request_token = st.session_state.get("request_token", {})
    auth.request_token = request_token
    
    try:
        access_token, access_secret = auth.get_access_token(oauth_verifier)
        st.session_state["access_token"] = access_token
        st.session_state["access_secret"] = access_secret
        st.success("Authentication successful! You can now post to Twitter.")
        st.rerun()  # Force UI refresh
    except tweepy.TweepyException as e:
        st.error(f"Failed to get access token: {e}")

# def upload_to_twitter(images):
#     """Uploads images to Twitter and posts a tweet."""
#     if "access_token" not in st.session_state or "access_secret" not in st.session_state:
#         st.error("You must authenticate first!")
#         return
    
#     api_key = os.getenv("X_API_KEY")
#     api_secret = os.getenv("X_API_SECRET")
#     access_token = st.session_state["access_token"]
#     access_secret = st.session_state["access_secret"]
    
#     auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
#     api = tweepy.API(auth)
    
#     media_ids = []
#     for img in images:
#         byte_io = io.BytesIO()
#         img.save(byte_io, format='PNG')
#         byte_io.seek(0)

#         media_res = api.media_upload(filename="image.png", file=byte_io)
#         media_ids.append(media_res.media_id_string)

#     api.update_status(status="Here are your resized images!", media_ids=media_ids)
#     st.success("Images posted to Twitter!")

def upload_to_twitter(images):
    """Uploads images to Twitter and posts a tweet using API v2."""
    if "access_token" not in st.session_state or "access_secret" not in st.session_state:
        st.error("You must authenticate first!")
        return
    
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = st.session_state["access_token"]
    access_secret = st.session_state["access_secret"]
    bearer_token = os.getenv("BEARER_TOKEN")  # Needed for API v2

    # Authenticate with Tweepy Client (API v2)
    client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_secret)

    media_ids = []
    for img in images:
        byte_io = io.BytesIO()
        img.save(byte_io, format='PNG')
        byte_io.seek(0)

        # Use API v1.1 for media upload (since API v2 does not support it yet)
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        api = tweepy.API(auth)
        media_res = api.media_upload(filename="image.png", file=byte_io)
        media_ids.append(media_res.media_id_string)

    # Post Tweet with media using API v2
    client.create_tweet(text="Here are your resized images!", media_ids=media_ids)
    st.success("Images posted to Twitter!")


# Streamlit UI
st.title("Image Resizer and Twitter Uploader")

if "access_token" not in st.session_state:
    st.subheader("Login to Twitter")
    if st.button("Authenticate with Twitter"):
        auth_url = get_twitter_auth()
        if auth_url:
            st.write("[Click here to authorize]({})".format(auth_url))
    verifier = st.text_input("Enter the PIN from Twitter")
    if st.button("Verify and Authenticate") and verifier:
        authenticate_user(verifier)
else:
    st.success("You are logged in!")
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Image", use_container_width=True)
        resized_images = [resize_image(image, size) for size in IMAGE_SIZES]
        
        for img, size in zip(resized_images, IMAGE_SIZES):
            st.image(img, caption=f"{size[0]}x{size[1]}", use_container_width=True)
        
        if st.button("Post to Twitter"):
            upload_to_twitter(resized_images)