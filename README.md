# AI Anime Tribute Video Generator

## 1. Overview

This project is an AI-powered web application that automatically generates short, motivational anime tribute videos. The application takes a script provided by the user, sources relevant video clips, generates a voiceover using voice cloning, and combines everything into a final video ready for upload. It also features an iterative refinement process and direct integration with YouTube for uploading the main video and creating shorts.

## 2. Features

- **Automated Video Sourcing:** Searches the internet for anime clips based on character names.
- **AI Voice Cloning:** Uses the VoxCPM model to clone a character's voice from a reference audio clip and make it speak a new script.
- **Dynamic Video Generation:** Combines video clips, a voiceover, background music, and synchronized text overlays into a single video file.
- **Web-Based UI:** A simple, user-friendly interface built with Flask for providing input and managing the generation process.
- **YouTube Integration:** Directly uploads the final video and automatically generated 50-second shorts to a specified YouTube channel.

## 3. Setup and Installation

Follow these steps to get the application running on your local machine (Debian/Ubuntu-based systems).

### Step 3.1: Install System Dependencies

These are required for video processing, image manipulation, and library compilation. Open your terminal and run:

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg imagemagick libjpeg-dev
```

### Step 3.2: Download the Font

The video generator uses a custom font for the text overlays.

1.  **[Click here to download the "1942 Report" font from Font Squirrel](https://www.fontsquirrel.com/fonts/download/1942-report)**.
2.  Create a new directory named `assets` in the root of the project.
3.  The download will be a `zip` file. Unzip it, find the `1942.ttf` file, and place it inside the `assets` directory. The final path should be `assets/1942.ttf`.

### Step 3.3: Clone the Repository & Set Up Python

```bash
# Clone this project
git clone <repository_url>
cd <repository_directory>

# We recommend using a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all required Python libraries
pip install -r requirements.txt
```

**Note:** The first time you run the application, it will download the AI models for voice cloning (`VoxCPM`), which are very large (several gigabytes). This will take a significant amount of time and disk space.

## 4. Configuration: YouTube API

To allow the application to upload videos to your YouTube channel, you need to configure your Google Cloud project and get API credentials.

1.  **Create a Google Cloud Project:**
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Click the project drop-down and select **New Project**.
    - Give your project a name and click **Create**.

2.  **Enable the YouTube Data API v3:**
    - In your new project, navigate to **APIs & Services > Library**.
    - Search for "YouTube Data API v3" and click on it.
    - Click the **Enable** button.

3.  **Create OAuth 2.0 Credentials:**
    - Go to **APIs & Services > Credentials**.
    - Click **Create Credentials** and select **OAuth client ID**.
    - If prompted, you may need to configure the **OAuth consent screen** first. Choose **External** and fill in the required app name, user support email, and developer contact information. You can leave most fields blank.
    - For the application type, select **Desktop app**.
    - Give the client ID a name (e.g., "AI Video Gen Client").
    - Click **Create**. A window will pop up with your credentials.

4.  **Download the Credentials File:**
    - In the credentials list, find the client ID you just created and click the **Download JSON** icon.
    - **Rename the downloaded file to `client_secret.json`**.
    - **Place this `client_secret.json` file in the root directory of this project.**

## 5. Running the Application

### Step 5.1: Start the Web Server

Once all dependencies are installed and the `client_secret.json` is in place, run the following command from the project's root directory:

```bash
python app.py
```

This will start the Flask web server. Open your web browser and navigate to `http://127.0.0.1:8080`.

### Step 5.2: First-Time YouTube Authentication

The first time you try to upload a video, the application needs your permission to access your YouTube account.
1.  Generate a video using the web interface.
2.  On the result page, click the **Upload to YouTube** button.
3.  A new tab will open in your browser, prompting you to log in to your Google account and grant the application the permissions it requested.
4.  After you grant permission, the tab will close, and the application will save your credentials in a `youtube_credentials.pkl` file for future use. The upload will then proceed.

## 6. Known Limitations

- **YouTube Sourcing:** The `video_sourcing.py` module may be blocked by YouTube in some network environments (like cloud servers). If you experience issues, you may need to run this on a home network.
- **Hinglish Voice Quality:** The VoxCPM voice cloning model is officially trained on English and Chinese. Its performance on Hinglish is not guaranteed, and the accent or pronunciation may be imperfect.
- **Processing Time:** The AI models for voice cloning and the video generation process are computationally intensive. Generating a video can take a significant amount of time and resources.
- **Error Handling:** This is a proof-of-concept application. While it handles some errors, it may not be robust against all possible invalid inputs or edge cases.
