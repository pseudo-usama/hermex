from scraper.chatgpt import ChatGPTScraper
from scraper.config import download_dir
from scraper.utils import list_and_sort_dir


def generate_imgs_with_scraper(initial_prompt,
                               num_frames,
                               delay_between_messages=5*60,
                               initial_url="https://chatgpt.com"):
    if download_dir.exists() and any(download_dir.iterdir()):
        print(f"Directory {download_dir} already exists and is not empty.")
        return
    download_dir.mkdir(parents=True, exist_ok=True)

    chatgpt = ChatGPTScraper()
    chat_url = None
    download_status = [False] * num_frames

    try:
        chatgpt.initialize_driver()
        chatgpt.open_url(url=initial_url)

        chatgpt.human_like_delay(7)
        print(f"Sending initial system prompt")
        chatgpt.type_message(initial_prompt)
        chatgpt.human_like_delay(delay_between_messages)

        chat_url = chatgpt.get_current_url(only_base=True)
        chatgpt.open_url(chat_url+"?model=gpt-4o")
        chatgpt.human_like_delay(7)

        for i in range(num_frames):
            chatgpt.human_like_delay(7)

            print(f"Generating image", i+1)
            chatgpt.type_message(f"good, now generate image no. {i+1}")
            chatgpt.human_like_delay(delay_between_messages)

            try:
                chatgpt.download_last_generated_image()
                chatgpt.human_like_delay(7)
                print(f"Image {i+1} downloaded successfully.")
                download_status[i] = True
            except Exception as e:
                print(f"Error downloading image {i+1}: {e}")

            if i < num_frames - 1:
                chatgpt.refresh_page()
                chatgpt.human_like_delay(5)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        chatgpt.close()

    # Map downloaded files to their positions or None for failures
    files = iter(list_and_sort_dir(download_dir))
    result_imgs = [next(files, None) if status else None for status in download_status]
    
    return chat_url, result_imgs
