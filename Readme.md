# Chima Ad Generator: AI Video Ad Platform

## Project Overview
This project is an AI-powered platform designed to automatically transform any product page URL into compelling video advertisements. Inspired by Creatify.ai, it focuses on the core "URL to Video" feature, providing a seamless experience for generating dynamic ad content.

## Features
* **URL Input & Scraping:** Accepts product page URLs (primarily tested with Amazon.in) and extracts key product information like images, titles, descriptions, and prices.
* **AI-Powered Content Generation:** Utilizes a configurable Large Language Model (LLM) – either a local LM Studio instance or OpenAI API – to generate concise, catchy ad copy and bullet points.
* **Dynamic Video Creation:**
    * **Image Handling:** Resizes and crops images intelligently to fit video dimensions while maintaining aspect ratio, and applies the "Ken Burns" (pan and zoom) effect for visual dynamism.
    * **Animated Text Overlays:** Integrates professional-looking text animations (fade-in, slide-in) for product details and ad copy.
    * **Text-to-Speech Voiceovers:** Generates natural-sounding audio for all textual content using gTTS, synced with on-screen visuals.
    * **Structured Output:** Produces videos with an intro slide (title/price), content slides (image + bullet), and an outro (call-to-action).
    * **Output Quality:** Renders high-quality MP4 videos (H.264 video, AAC audio) with a flexible aspect ratio (default 16:9).
* **User Interface:**
    * Simple, intuitive dashboard for URL input.
    * In-browser video preview.
    * Option to download generated videos.
    * Lists all previously generated videos with their status (processing, completed, failed).
    * Allows deletion of videos (from database and disk).
* **Robust Backend:** Built with FastAPI, featuring asynchronous processing for video generation, database persistence (SQLite) for video metadata, and dynamic environment configuration.

## Technical Stack

* **Frontend:**
    * **React.js:** For building a responsive and interactive user interface.
    * **CSS:** Custom CSS for styling (no external frameworks like Tailwind used directly in components).
* **Backend:**
    * **Python:** The core language for server-side logic.
    * **FastAPI:** A modern, fast (high-performance) web framework for building the API.
    * **SQLAlchemy:** Python SQL toolkit and Object Relational Mapper (ORM) for interacting with the SQLite database.
    * **Pydantic:** Used with FastAPI for data validation and settings management.
    * **Web Scraping:** `requests` and `BeautifulSoup4` for parsing product pages.
    * **Video Processing:** `MoviePy` (Python library for video editing) which relies on `FFmpeg`.
    * **Text-to-Speech:** `gTTS` (Google Text-to-Speech) for voiceovers.
    * **Image Processing:** `Pillow` (PIL fork) for handling image manipulation.
* **AI/ML Services (Configurable):**
    * **LM Studio:** For running local Large Language Models (LLMs) (e.g., Llama 3) for ad copy generation.
    * **OpenAI API:** Alternative cloud-based LLM for ad copy generation (requires API key).
* **Containerization:**
    * **Docker:** For building isolated and portable environments for both frontend and backend.
    * **Docker Compose:** For defining and running multi-container Docker applications with ease.

## Getting Started

Follow these steps to set up and run the Chima Ad Generator locally using Docker Compose.

### Prerequisites

* **Git:** For cloning the repository.
* **Docker Desktop:** Essential for running the application via Docker Compose (includes Docker Engine).
* **LM Studio (Optional, but default LLM):**
    1.  Download and install LM Studio from [lmstudio.ai](https://lmstudio.ai/).
    2.  Open LM Studio, navigate to the "Discover" or "Chat" tab.
    3.  Download a suitable local LLM model (e.g., `tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf` or any other compatible `GGUF` model).
    4.  Go to the "Local Inference Server" tab (usually the `->` icon on the left sidebar).
    5.  Load the downloaded model into the server.
    6.  **Crucially, click "Start Server"**. Ensure it's running on `http://localhost:1234`. The Docker containers will access this via `host.docker.internal`.

### Setup and Running the Application (Using Docker Compose)

This is the **recommended** way to run the project. It sets up both frontend and backend with all dependencies and proper communication.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Kdheeru12/ad-generator.git
    cd chima-ad-generator
    ```
    *Ensure your `backend` and `frontend` folders are directly inside `chima_ad_generator` as shown in the project structure above.*

2.  **Configure LLM Provider (Optional):**
    * Open `docker-compose.yml` in your project root.
    * Locate the `backend` service's `environment` section.
    * By default, `LLM_PROVIDER` is set to `lm_studio` and `LM_STUDIO_URL` points to `http://host.docker.internal:1234`. Make sure LM Studio is running on your host machine as described in Prerequisites.
    * **To use OpenAI instead:**
        * Change `LLM_PROVIDER: lm_studio` to `LLM_PROVIDER: openai`.
        * **Uncomment** the `OPENAI_API_KEY` line and replace `your_openai_api_key_here` with your actual OpenAI API key.
        * You can comment out or remove the `LM_STUDIO_URL` line if you're not using LM Studio.

    *Example (for OpenAI):*
    ```yaml
        environment:
          LLM_PROVIDER: openai
          # LM_STUDIO_URL: [http://host.docker.internal:1234](http://host.docker.internal:1234) # Comment this out
          OPENAI_API_KEY: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx # Your actual key
    ```

3.  **Build and Run Services:**
    Navigate to the root directory of the `chima_ad_generator` project (where `docker-compose.yml` is located) in your terminal and run:
    ```bash
    docker-compose up --build
    ```
    * `--build`: This flag ensures that Docker images for your `backend` and `frontend` services are built (or rebuilt if their `Dockerfile`s or source code changed). This is crucial for the first run and after any dependency or code modifications.
    * Docker Compose will:
        * Build the backend image (`Dockerfile.backend`).
        * Build the frontend image (`Dockerfile.frontend`).
        * Start the FastAPI backend service (accessible on host `localhost:8000`).
        * Start the React development server (accessible on host `localhost:3000`).
        * Mount your local source code into the containers, enabling **hot-reloading** for both frontend and backend during development.
        * Create a named Docker volume `generated_videos` to store your generated video files persistently in the root project directory, even if containers are stopped or removed.

4.  **Access the Application:**
    Once both services are up and running (you'll see verbose logs from both frontend and backend in your terminal), open your web browser and navigate to:
    `http://localhost:3000`

    The React frontend will automatically communicate with the FastAPI backend service running internally within the Docker network.

5.  **Stop the Services:**
    To stop and remove the containers, networks, and volumes created by `docker-compose up`:
    ```bash
    docker-compose down
    ```
    To stop the services without removing them (useful if you want to restart quickly later):
    ```bash
    docker-compose stop
    ```

### Manual Setup (for Advanced Development / Debugging)

If you prefer to run services manually without Docker Compose:

1.  **Backend Manual Setup:**
    * Navigate to `chima_ad_generator/backend`.
    * `python -m venv venv`
    * `source venv/bin/activate` (Windows: `.\venv\Scripts\activate`)
    * `pip install -r requirements.txt`
    * **Set environment variables for LLM:**
        * **For LM Studio:** (Optional) `export LM_STUDIO_URL="http://localhost:1234"` if LM Studio is on a non-default host/port.
        * **For OpenAI:** `export LLM_PROVIDER="openai"` and `export OPENAI_API_KEY="your_key_here"`.
    * `uvicorn app:app --reload --host 0.0.0.0 --port 8000`
    * Access at `http://localhost:8000`.

2.  **Frontend Manual Setup:**
    * Navigate to `chima_ad_generator/frontend`.
    * `npm install`
    * **Set environment variable for Backend URL:**
        * `export REACT_APP_BACKEND_URL="http://localhost:8000"` (Windows: `$env:REACT_APP_BACKEND_URL="http://localhost:8000"`)
    * `npm start`
    * Access at `http://localhost:3000`.

## Usage

1.  Open your web browser and navigate to the frontend URL (`http://localhost:3000`).
2.  In the "Product Page URL" input, enter a valid URL (e.g., from Amazon India).
3.  Click "Generate Video Ad".
4.  The system will initiate the video generation. A new entry will appear in the "Generated Videos" list with a "processing" status.
5.  Wait for the status to change to "completed" (the list updates automatically every few seconds).
6.  Once "completed", you can:
    * Click "Preview" to watch the video directly in the browser player.
    * Click "Download" to save the MP4 video file to your local machine.
    * Click "Delete" to remove the video entry from the database and its corresponding file from the server. This also works for "failed" videos.

## Contributing

We welcome contributions! Please open issues for bugs or feature requests, and feel free to submit pull requests.

## License

This project is licensed under the MIT License.

## Contact

For any questions or support, please open an issue in this repository.
