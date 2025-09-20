import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# --- Configuration ---
# The user MUST provide this file. It is obtained from the Google Cloud Console.
CLIENT_SECRETS_FILE = "client_secret.json"
# This file will be created automatically after the first successful authentication.
CREDENTIALS_PICKLE_FILE = "youtube_credentials.pkl"
# This defines the scopes of access we are requesting.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
# --- End Configuration ---

def get_authenticated_service():
    """
    Handles the OAuth 2.0 flow and returns an authenticated YouTube API service object.
    """
    credentials = None

    # Check if we have saved credentials
    if os.path.exists(CREDENTIALS_PICKLE_FILE):
        with open(CREDENTIALS_PICKLE_FILE, "rb") as f:
            credentials = pickle.load(f)

    # If we don't have valid credentials, start the OAuth flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing access token...")
            credentials.refresh(Request())
        else:
            # This is the part that requires user interaction in a browser.
            # The user will need to run this part from their local machine one time.
            print("Starting OAuth 2.0 flow. Please follow the browser instructions.")
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"ERROR: The client secrets file ('{CLIENT_SECRETS_FILE}') was not found.")
                print("Please download it from your Google Cloud project and place it in the root directory.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            # This will start a local server and open a browser window for the user to authorize the app.
            credentials = flow.run_local_server(port=8080)

        # Save the new credentials for the next run
        with open(CREDENTIALS_PICKLE_FILE, "wb") as f:
            pickle.dump(credentials, f)
            print("Credentials saved successfully.")

    try:
        return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    except Exception as e:
        print(f"Failed to build YouTube service: {e}")
        return None

def upload_video(
    youtube_service,
    file_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "private" # Can be "public", "private", or "unlisted"
) -> str | None:
    """
    Uploads a video to YouTube.

    Args:
        youtube_service: The authenticated YouTube API service object.
        file_path (str): The path to the video file.
        title (str): The title of the video.
        description (str): The description of the video.
        tags (list[str]): A list of tags for the video.
        privacy_status (str): The privacy status of the video.

    Returns:
        str | None: The ID of the uploaded video, or None if an error occurred.
    """
    if not os.path.exists(file_path):
        print(f"Error: Video file not found at {file_path}")
        return None

    try:
        print(f"Uploading video '{title}'...")
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "24" # 24 is "Entertainment" category
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube_service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        response = request.execute()
        print(f"Video uploaded successfully! Video ID: {response['id']}")
        return response['id']

    except Exception as e:
        print(f"An error occurred during video upload: {e}")
        return None


if __name__ == '__main__':
    # --- Instructions for Manual Testing ---
    # 1. Go to the Google Cloud Console (https://console.cloud.google.com/).
    # 2. Create a new project.
    # 3. Enable the "YouTube Data API v3".
    # 4. Create OAuth 2.0 credentials for a "Desktop application".
    # 5. Download the credentials JSON file and save it as "client_secret.json" in this directory.
    # 6. Create a dummy video file to upload, e.g., "outputs/final_test_video.mp4".
    # 7. Run this script: `python src/youtube_uploader.py`
    # 8. Your web browser will open, asking you to log in and authorize the application.
    # 9. After authorization, the script will proceed with the upload.

    print("--- YouTube Uploader Module Test ---")

    # Authenticate
    # This will fail in this sandboxed environment because it can't open a browser.
    # The code is here to be complete.
    try:
        youtube = get_authenticated_service()

        if youtube:
            print("Successfully authenticated with YouTube API.")

            # Example upload
            video_to_upload = "outputs/final_test_video.mp4" # Assumes this file exists
            if os.path.exists(video_to_upload):
                upload_video(
                    youtube_service=youtube,
                    file_path=video_to_upload,
                    title="AI Generated Tribute Video (Test)",
                    description="This is a test video uploaded by the AI generator.",
                    tags=["ai", "anime", "test"]
                )
            else:
                print(f"Test video not found at '{video_to_upload}'. Skipping upload test.")
        else:
            print("Could not get authenticated YouTube service. This is expected in an environment without a browser.")

    except Exception as e:
        print(f"Test failed as expected in this environment: {e}")

    print("--- End of Test ---")
