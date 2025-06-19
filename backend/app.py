import os
import uuid
import asyncio

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models
import schemas

from scraper import scrape_product_data
from overlay_generator import generate_overlay_text
from video_creator import create_ad_video

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Directory for temporary video storage ---
TEMP_VIDEO_DIR = "temp_videos"
os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Health Check Endpoint ---
@app.get("/")
async def read_root():
    """health check endpoint."""
    return {"message": "AI Video Ad Generator Backend is running!"}


@app.post("/generate-ad-video/", response_model=schemas.Video)
async def generate_ad_video_endpoint(
    input_data: schemas.URLInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Accepts a product URL, scrapes data, generates ad copy, and queues video creation.
    Saves video metadata to the database.
    """
    url = str(input_data.url)

    video_filepath = None  # Initialize to None for error handling
    new_video_db_entry = None  # Initialize db entry for update

    try:
        print(f"🔍 Scraping product data for URL: {url}")
        try:
            product_data, image_bytes_list = scrape_product_data(url)
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to scrape product data or images.")

        if not product_data or not image_bytes_list:
            raise HTTPException(status_code=500, detail="Failed to scrape product data or images.")

        # Create initial DB entry with "processing" status
        new_video_db_entry = models.Video(
            original_url=url,
            product_title=product_data.get("title", "Untitled Product"),
            video_filename="",  # Will be updated after UUID is generated
            status="processing",
        )
        db.add(new_video_db_entry)
        db.commit()
        db.refresh(new_video_db_entry)

        print("🤖 Generating overlay text from LM Studio...")
        overlay_bullets = generate_overlay_text(product_data, len(image_bytes_list))

        if not overlay_bullets:
            raise HTTPException(status_code=500, detail="Failed to generate ad copy.")

        if len(overlay_bullets) != len(image_bytes_list):
            print(
                f"⚠️ Warning: Mismatch between number of images ({len(image_bytes_list)}) "
                f"and overlay bullets ({len(overlay_bullets)}). Adjusting to minimum count."
            )
            min_count = min(len(image_bytes_list), len(overlay_bullets))
            image_bytes_list = image_bytes_list[:min_count]
            overlay_bullets = overlay_bullets[:min_count]
            if not image_bytes_list or not overlay_bullets:
                raise HTTPException(status_code=500, detail="Insufficient data after image/bullet count adjustment.")

        unique_filename = f"ad_video_{uuid.uuid4()}.mp4"
        video_filepath = os.path.join(TEMP_VIDEO_DIR, unique_filename)

        # Update DB entry with generated filename
        new_video_db_entry.video_filename = unique_filename
        db.add(new_video_db_entry)
        db.commit()
        db.refresh(new_video_db_entry)

        print(f"🎬 Queueing video creation: {video_filepath}")
        # Pass the DB session and entry ID to the background task for status updates
        background_tasks.add_task(
            create_video_and_update_db,
            db_session_factory=SessionLocal,
            video_id=new_video_db_entry.id,
            image_bytes_list=image_bytes_list,
            overlay_bullets=overlay_bullets,
            title=product_data["title"],
            price=product_data["price"],
            output_filepath=video_filepath,
        )

        return new_video_db_entry

    except HTTPException as e:
        # If an HTTPException occurs, update DB status to "failed" if entry exists
        if new_video_db_entry:
            new_video_db_entry.status = "failed"
            db.add(new_video_db_entry)
            db.commit()
        raise e
    except Exception as e:
        print(f"🚨 An unexpected error occurred during video generation request: {e}")
        # Clean up any partial video file if an error occurred during its creation
        if video_filepath and os.path.exists(video_filepath):
            os.remove(video_filepath)
        # Update DB status to "failed" for unexpected errors
        if new_video_db_entry:
            new_video_db_entry.status = "failed"
            db.add(new_video_db_entry)
            db.commit()
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


async def create_video_and_update_db(
    db_session_factory, video_id: int, image_bytes_list, overlay_bullets, title, price, output_filepath
):
    """
    Background task to create the video and update its status in the database.
    Receives a db_session_factory to create its own session, as DB sessions are not thread-safe.
    """
    db = db_session_factory()
    try:

        video_entry = db.query(models.Video).filter(models.Video.id == video_id).first()
        if not video_entry:
            print(f"Error: Video entry with ID {video_id} not found in DB for background task.")
            return

        print(f"Starting background video creation for ID: {video_id} - {output_filepath}")
        # Call the actual video creation function
        create_ad_video(
            image_list=image_bytes_list,
            bullets=overlay_bullets,
            title=title,
            price=price,
            output=output_filepath,
            # aspect_ratio="9:16",
        )
        print(f"Video creation completed for ID: {video_id}")
        video_entry.status = "completed"
        db.add(video_entry)
        db.commit()
    except Exception as e:
        print(f"🚨 Error in background video creation for ID {video_id}: {e}")

        if video_entry:
            video_entry.status = "failed"
            db.add(video_entry)
            db.commit()

        if os.path.exists(output_filepath):
            os.remove(output_filepath)
    finally:
        db.close()


async def delete_file_after_delay(filepath: str):
    """Deletes a file after a short delay."""
    await asyncio.sleep(600)  # Wait 10 minutes (600 seconds) to ensure file is streamed and user downloads it
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"Cleaned up temporary file: {filepath}")
        except Exception as e:
            print(f"Error cleaning up file {filepath}: {e}")


@app.get("/get-video/{video_filename}")
async def get_video_file(video_filename: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Serves the generated video file.
    Includes a background task to delete the file after it's sent.
    """
    file_path = os.path.join(TEMP_VIDEO_DIR, video_filename)

    video_entry = db.query(models.Video).filter(models.Video.video_filename == video_filename).first()
    if not video_entry or video_entry.status not in [
        "completed",
        "processing",
    ]:  # Allow fetching processing if needed
        raise HTTPException(status_code=404, detail="Video not found or is in an invalid state.")

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, detail="Video file not found on server disk. It might have been cleaned up."
        )

    # FileResponse handles streaming (Content-Range) automatically for browsers
    response = FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=video_filename,
    )

    # background_tasks.add_task(delete_file_after_delay, file_path)

    return response


@app.get("/videos/", response_model=list[schemas.VideoList])  # Response model is a list of VideoList schemas
async def list_videos(db: Session = Depends(get_db)):
    """
    Returns a list of all generated videos with their titles and statuses.
    """
    videos = db.query(models.Video).order_by(models.Video.created_at.desc()).all()
    return videos


@app.delete("/videos/{video_id}", status_code=200)
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """
    Deletes a video record from the database and its corresponding file from disk.
    """
    video_entry = db.query(models.Video).filter(models.Video.id == video_id).first()

    if not video_entry:
        raise HTTPException(status_code=404, detail="Video not found.")

    video_filename = video_entry.video_filename
    file_path = os.path.join(TEMP_VIDEO_DIR, video_filename)

    # Delete from database
    db.delete(video_entry)
    db.commit()

    # Delete file from disk
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Deleted video file from disk: {file_path}")
        except OSError as e:
            print(f"Error deleting video file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete video file from disk: {e}")
    else:
        print(f"Video file not found on disk, but DB entry was deleted: {file_path}")

    return {"message": f"Video with ID {video_id} and file '{video_filename}' deleted successfully."}
