from scraper.chatgpt import ChatGPTScraper
from scraper.config import selenium_download_dir, generated_imgs_dir


def generate_imgs_with_initial_prompt(initial_prompt,
                                      num_frames,
                                      delay_between_messages=5*60,
                                      initial_url="https://chatgpt.com",
                                      headless=False):
    if selenium_download_dir.exists() and any(selenium_download_dir.iterdir()):
        print(f"Directory {selenium_download_dir} already exists and is not empty.")
        return
    selenium_download_dir.mkdir(parents=True, exist_ok=True)
    generated_imgs_dir.mkdir(parents=True, exist_ok=True)

    chatgpt = ChatGPTScraper(
        download_dir=selenium_download_dir,
        headless=headless
    )
    chat_url = None
    downloaded_imgs = []

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
                img = list(selenium_download_dir.iterdir())[0]
                img = img.rename(generated_imgs_dir / img.name)
                downloaded_imgs.append(img)
                print(f"Image {i+1} downloaded successfully.")
            except Exception as e:
                downloaded_imgs.append(None)
                print(f"Error downloading image {i+1}: {e}")

            if i < num_frames - 1:
                chatgpt.refresh_page()
                chatgpt.human_like_delay(delay_between_messages)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        chatgpt.close()

    return chat_url, downloaded_imgs


def generate_imgs_with_n_prompts(prompts,
                                 delay_between_messages=5*60,
                                 initial_url="https://chatgpt.com",
                                 headless=False):
    if selenium_download_dir.exists() and any(selenium_download_dir.iterdir()):
        print(f"Directory {selenium_download_dir} already exists and is not empty.")
        return
    selenium_download_dir.mkdir(parents=True, exist_ok=True)
    generated_imgs_dir.mkdir(parents=True, exist_ok=True)

    chatgpt = ChatGPTScraper(
        download_dir=selenium_download_dir,
        headless=headless
    )
    chat_url = None
    downloaded_imgs = []

    try:
        chatgpt.initialize_driver()
        chatgpt.open_url(url=initial_url)
        chatgpt.human_like_delay(7)

        for i, prompt in enumerate(prompts):
            print("Generating image ", i+1)
            chatgpt.type_message(prompt)
            chatgpt.human_like_delay(delay_between_messages)

            try:
                chatgpt.download_last_generated_image()
                chatgpt.human_like_delay(7)
                img = list(selenium_download_dir.iterdir())[0]
                img = img.rename(generated_imgs_dir / img.name)
                downloaded_imgs.append(img)
                print(f"Image {i+1} downloaded successfully.")
            except Exception as e:
                downloaded_imgs.append(None)
                print(f"Error downloading image {i+1}: {e}")

            if i < len(prompts) - 1:
                chatgpt.refresh_page()
                chatgpt.human_like_delay(delay_between_messages)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        chatgpt.close()

    return chat_url, downloaded_imgs
