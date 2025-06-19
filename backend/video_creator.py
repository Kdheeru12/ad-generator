from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
from PIL import ImageDraw, ImageFont, Image
import numpy as np
import re
import tempfile
import os
from gtts import gTTS


def remove_emojis(text):
    text = text.replace("*", "")
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002700-\U000027bf"
        "\U0001f900-\U0001f9ff"
        "\U00002600-\U000026ff"
        "\u2022"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


def add_pil_text_overlay(img, text, video_size, fontsize=60):
    img = img.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except Exception:
        font = ImageFont.load_default()

    text = remove_emojis(text.replace("*", ""))
    lines = text.split("\n")
    total_height = sum([draw.textsize(line, font=font)[1] + 10 for line in lines])
    y_text = (video_size[1] - total_height) // 2

    for line in lines:
        try:
            text_width, text_height = draw.textsize(line, font=font)
            x = (video_size[0] - text_width) / 2
            padding = 20
            draw.rectangle(
                [(x - padding, y_text - padding), (x + text_width + padding, y_text + text_height + padding)],
                fill="black",
            )
            draw.text((x, y_text), line, font=font, fill="yellow")
            y_text += text_height + 20
        except UnicodeEncodeError:
            continue

    return img


def generate_voice(text, filename):
    text = text.strip()
    if not text:
        return
    try:
        tts = gTTS(text)
        tts.save(filename)
    except Exception as e:
        print("Voice generation failed:", e)


def create_ad_video(image_list, bullets, title, price, output="product_video.mp4", aspect_ratio="16:9"):
    video_size = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)  # Full HD
    clips = []
    audio_segments = []

    for i, img in enumerate(image_list[: len(bullets) + 1]):
        try:
            # Resize using high-quality filter
            img = img.resize(video_size, Image.LANCZOS)
            text = f"{title}. {price}" if i == 0 else bullets[i - 1]

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                generate_voice(text, tmp_audio.name)
                audio = AudioFileClip(tmp_audio.name).audio_fadein(0.2).audio_fadeout(0.2)
                duration = audio.duration + 0.5

                img_with_text = add_pil_text_overlay(img, text, video_size)
                frame = np.array(img_with_text)

                clip = (
                    ImageClip(frame)
                    .set_duration(duration)
                    .resize(lambda t: 1.0 + 0.004 * t)  # very light zoom
                    .fadein(0.5)
                    .fadeout(0.5)
                    .set_audio(audio)
                )

                clips.append(clip)
                audio_segments.append(tmp_audio.name)

        except Exception as e:
            print(f"Image {i+1} failed: {e}")

    if not clips:
        raise ValueError("No clips to render.")

    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(output, fps=24, audio_codec="aac")

    for path in audio_segments:
        try:
            os.remove(path)
        except Exception:
            pass


# from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
# from PIL import ImageDraw, ImageFont
# import numpy as np
# import re
# import tempfile
# import os
# from gtts import gTTS


# def remove_emojis(text):
#     text.replace("*", "")
#     emoji_pattern = re.compile(
#         "["
#         "\U0001f600-\U0001f64f"  # emoticons
#         "\U0001f300-\U0001f5ff"  # symbols & pictographs
#         "\U0001f680-\U0001f6ff"  # transport & map symbols
#         "\U0001f1e0-\U0001f1ff"  # flags (iOS)
#         "\U00002700-\U000027bf"  # Dingbats
#         "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
#         "\U00002600-\U000026ff"  # Misc symbols
#         "\u2022"
#         "]+",
#         flags=re.UNICODE,
#     )
#     return emoji_pattern.sub(r"", text)


# def add_pil_text_overlay(img, text, video_size, fontsize=50):
#     img = img.copy()
#     draw = ImageDraw.Draw(img)
#     try:
#         font = ImageFont.truetype("arial.ttf", fontsize)
#     except Exception:
#         font = ImageFont.load_default()

#     text = remove_emojis(text.replace("*", ""))

#     lines = text.split("\n")
#     total_height = sum([draw.textsize(line, font=font)[1] + 10 for line in lines])
#     y_text = (video_size[1] - total_height) // 2

#     for line in lines:
#         try:
#             text_width, text_height = draw.textsize(line, font=font)
#             x = (video_size[0] - text_width) / 2

#             padding = 20
#             draw.rectangle(
#                 [(x - padding, y_text - padding), (x + text_width + padding, y_text + text_height + padding)],
#                 fill="black",
#             )
#             draw.text((x, y_text), line, font=font, fill="yellow")
#             y_text += text_height + 20
#         except UnicodeEncodeError as e:
#             print(f"⚠️ Skipping line due to encoding issue: {line}")
#             continue

#     return img


# def generate_voice(text, filename):
#     text = text.strip()
#     if not text:
#         return
#     try:
#         tts = gTTS(text)
#         tts.save(filename)
#     except Exception as e:
#         print("Voice generation failed:", e)


# def create_ad_video(image_list, bullets, title, price, output="product_video.mp4", aspect_ratio="16:9"):
#     video_size = (1280, 720) if aspect_ratio == "16:9" else (720, 1280)
#     clips = []
#     audio_segments = []

#     for i, img in enumerate(image_list[: len(bullets) + 1]):
#         try:
#             img = img.resize(video_size)
#             text = bullets[i - 1]
#             if i == 0:
#                 text = f"{title}. {price}"
#             else:
#                 text = bullets[i - 1]

#             # Generate voice and get actual duration of audio
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
#                 generate_voice(text, tmp_audio.name)
#                 audio = AudioFileClip(tmp_audio.name)
#                 duration = audio.duration + 0.5  # Add half a second buffer

#                 img_with_text = add_pil_text_overlay(img, text, video_size)
#                 frame = np.array(img_with_text)
#                 clip = ImageClip(frame).set_duration(duration).fadein(0.5).fadeout(0.5)
#                 clip = clip.set_audio(audio)

#                 clips.append(clip)
#                 audio_segments.append(tmp_audio.name)

#         except Exception as e:
#             print(f"Image {i+1} failed: {e}")

#     if not clips:
#         raise ValueError("No clips to render.")

#     final_video = concatenate_videoclips(clips, method="compose")
#     final_video.write_videofile(output, fps=24)

#     # Clean up temporary audio files
#     for path in audio_segments:
#         try:
#             os.remove(path)
#         except:
#             pass
