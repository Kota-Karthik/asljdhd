from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from PIL import Image
import io
import tweepy
import os

app = FastAPI()

# Use a secret key for session middleware (for testing only)
app.add_middleware(SessionMiddleware, secret_key="!secret")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the /static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint to serve index.html
@app.get("/")
def read_index(request: Request):
    return FileResponse("static/index.html")

# Hardcoded Twitter credentials (replace with your own values)
TWITTER_API_KEY = "YOUR_TWITTER_API_KEY_HERE"
TWITTER_API_SECRET = "YOUR_TWITTER_API_SECRET_HERE"

# Callback URL for Twitter OAuth (adjust if needed)
CALLBACK_URL = "http://127.0.0.1:8000/auth/callback/"

# Twitter OAuth login endpoint
@app.get("/login/")
async def login(request: Request):
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET, callback=CALLBACK_URL)
    try:
        redirect_url = auth.get_authorization_url()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # Save the request token in session for later use
    request.session["request_token"] = auth.request_token
    return RedirectResponse(redirect_url)

# Callback endpoint for Twitter OAuth
@app.get("/auth/callback/")
async def twitter_callback(request: Request, oauth_token: str, oauth_verifier: str):
    request_token = request.session.get("request_token")
    if not request_token:
        raise HTTPException(status_code=400, detail="Missing request token in session.")
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET, callback=CALLBACK_URL)
    auth.request_token = request_token
    try:
        access_token, access_token_secret = auth.get_access_token(oauth_verifier)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # Save access tokens in the session
    request.session["access_token"] = access_token
    request.session["access_token_secret"] = access_token_secret
    # Redirect back to the home page
    return RedirectResponse(url="/")

# Default image sizes
DEFAULT_IMAGE_SIZES = [(300, 250), (728, 90), (160, 600), (300, 600)]

def resize_image(image: Image, sizes: list):
    resized_images = {}
    for size in sizes:
        img_resized = image.resize(size)
        img_io = io.BytesIO()
        img_resized.save(img_io, format='PNG')
        img_io.seek(0)
        resized_images[size] = img_io.read()
    return resized_images

def post_to_twitter(image_data, size, access_token, access_token_secret):
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    img_io = io.BytesIO(image_data)
    img_io.seek(0)
    media = api.media_upload(filename=f"image_{size[0]}x{size[1]}.png", file=img_io)
    api.update_status(status=f"Here is your resized image: {size}", media_ids=[media.media_id])
    return {"message": f"Image {size} posted successfully"}

@app.post("/process/")
async def process_image(
    request: Request,
    file: UploadFile = File(...),
    sizes: str = Form(None),
    post: bool = Form(False)
):
    # Check if the user is authenticated via Twitter
    if "access_token" not in request.session or "access_token_secret" not in request.session:
        # Not authenticated: redirect to login
        return JSONResponse(status_code=401, content={"detail": "Not authenticated. Please login."})
    
    try:
        # Open the uploaded image
        image = Image.open(io.BytesIO(await file.read()))
        
        # Determine sizes: if sizes provided, parse them; otherwise, use defaults.
        if sizes:
            sizes_list = [tuple(map(int, size.strip().split("x"))) for size in sizes.split(",") if "x" in size]
        else:
            sizes_list = DEFAULT_IMAGE_SIZES
        
        # Resize the image
        resized_images = resize_image(image, sizes_list)
        twitter_responses = []
        if post:
            for size, image_data in resized_images.items():
                response = post_to_twitter(
                    image_data, size,
                    request.session["access_token"],
                    request.session["access_token_secret"]
                )
                twitter_responses.append(response)
        return JSONResponse(
            content={
                "message": "Processing completed successfully",
                "sizes": list(resized_images.keys()),
                "twitter": twitter_responses,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# To run the server, use: uvicorn main:app --reload
