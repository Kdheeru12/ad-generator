import os
import requests
import re

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lm_studio").lower()


LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_COMPLETIONS_URL = "https://api.openai.com/v1/completions"


def generate_overlay_text(product_data: dict, num_images: int) -> list[str]:
    prompt = f"""
        You are a professional ad copywriter. Create exactly {num_images} short, catchy lines for a video ad based on the product below.

        PRODUCT DETAILS:
        Title: {product_data['title']}
        Price: {product_data['price']}
        Description: {product_data['description']}

        REQUIREMENTS:
        - Write exactly {num_images} lines (no more, no less)
        - Each line must be 4–7 words only
        - Use clean, benefit-focused, persuasive language
        - DO NOT use emojis, punctuation, asterisks, or symbols
        - DO NOT use numbering or list formatting (e.g., 1., 2., •)
        - DO NOT include quotation marks, headings, or extra text
        - Return each line on a separate new line
        - Final output must be raw plain text only

        FORMAT EXAMPLE:
        High Strength Durable Materials
        Perfect Fit With Adjustable Design
        Waterproof And Lightweight For Travel
        Great Value Two Pack Combo

        Begin your response immediately with the first line.
        """  # noqa

    headers = {"Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "max_tokens": 250,
        "temperature": 0.7,
        "stop": ["\n\n"],  # Stop sequence to help with clean output
    }

    raw_response_text = ""

    try:
        if LLM_PROVIDER == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set for OpenAI provider.")
            headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
            payload["model"] = "gpt-3.5-turbo-instruct"  # A good text completion model for OpenAI
            print("Calling OpenAI API (v1/completions)...")
            response = requests.post(OPENAI_COMPLETIONS_URL, headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            raw_response_text = response.json()["choices"][0]["text"]

        elif LLM_PROVIDER == "lm_studio":
            print("Calling LM Studio API (v1/completions)...")
            response = requests.post(f"{LM_STUDIO_URL}/v1/completions", headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            raw_response_text = response.json()["choices"][0]["text"]

        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Please choose 'lm_studio' or 'openai'.")

        raw_lines = raw_response_text.strip().split("\n")
        print(f"Raw lines from LLM: {raw_lines}")

        # Clean lines: remove numbering, bullets, asterisks
        clean_lines = []
        for line in raw_lines:
            line = line.strip()
            # Remove "1. ", "1) ", "- ", "* ", etc. at the beginning of the line
            line = re.sub(r"^(?:\s*[\d]+[.)\-•*]?\s*)", "", line)
            # Remove any stray leading/trailing quotes if the LLM adds them
            line = line.strip('"')
            if line:  # Only add non-empty lines
                clean_lines.append(line)

        return clean_lines

    except requests.exceptions.ConnectionError as e:
        print(f"Connection error to LLM server ({LLM_PROVIDER}): {e}.")
        print("Please ensure the LLM server is running and the URL/API key is correct.")
        return []
    except requests.exceptions.Timeout as e:
        print(f"LLM request timed out ({LLM_PROVIDER}): {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API ({LLM_PROVIDER}): {e}")
        if e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
        return []
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred in generate_overlay_text: {e}")
        return []


# import requests
# import re


# def generate_overlay_text(product_data, num_images):
#     prompt = f"""
#         You are a professional ad copywriter. Create exactly {num_images} short, catchy lines for a video ad based on the product below.

#         PRODUCT DETAILS:
#         Title: {product_data['title']}
#         Price: {product_data['price']}
#         Description: {product_data['description']}

#         REQUIREMENTS:
#         - Write exactly {num_images} lines (no more, no less)
#         - Each line must be 4–7 words only
#         - Use clean, benefit-focused, persuasive language
#         - DO NOT use emojis, punctuation, asterisks, or symbols
#         - DO NOT use numbering or list formatting (e.g., 1., 2., •)
#         - DO NOT include quotation marks, headings, or extra text
#         - Return each line on a separate new line
#         - Final output must be raw plain text only

#         FORMAT EXAMPLE:
#         High Strength Durable Materials
#         Perfect Fit With Adjustable Design
#         Waterproof And Lightweight For Travel
#         Great Value Two Pack Combo

#         Begin your response immediately with the first line.
#         """  # noqa

#     response = requests.post(
#         "http://localhost:1234/v1/completions",
#         json={
#             "prompt": prompt,
#             "max_tokens": 250,
#             "temperature": 0.7,
#             "stop": ["\n\n"],
#         },
#     )

#     raw_lines = response.json()["choices"][0]["text"].strip().split("\n")
#     print(raw_lines)

#     # Clean lines: remove numbering, bullets, asterisks

#     clean_lines = []
#     for line in raw_lines:
#         line = line.strip()
#         line = re.sub(r"^(?:\s*[\d]+[.)\-•*]?\s*)", "", line)  # Remove "1. ", "1) ", "- ", "* ", etc.
#         if line:
#             clean_lines.append(line)


#     return clean_lines
