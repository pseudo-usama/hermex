from scraper import ChatGPTScraper
from scraper import generated_imgs_dir


def generate_imgs_with_initial_prompt(initial_prompt,
                                      num_frames,
                                      delay_between_messages=5*60,
                                      initial_url="https://chatgpt.com",
                                      headless=False):
    chatgpt = ChatGPTScraper(
        download_dir=generated_imgs_dir,
        headless=headless
    )
    chat_url = None
    responses = []

    try:
        chatgpt.open_url(url=initial_url)
        chatgpt.sleep(7)

        print(f"Sending initial system prompt")
        chatgpt.type_message(initial_prompt)
        chatgpt.sleep(delay_between_messages)

        chat_url = chatgpt.get_current_url(only_base=True)

        for i in range(num_frames):
            chatgpt.sleep(7)

            print(f"Generating image", i+1)
            chatgpt.type_message(f"good, now generate image no. {i+1}")
            chatgpt.sleep(delay_between_messages)

            text, img = chatgpt.get_last_response()
            responses.append({"text": text, "img": img})
            print(f"Response {i+1}: ",
                  "img," if img else "no image,",
                  "text" if text else "no text")

            if i < num_frames - 1:
                chatgpt.refresh_page()
                chatgpt.sleep(delay_between_messages)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        chatgpt.close()

    return chat_url, responses


def generate_imgs_with_initial_prompt_and_n_prompts(initial_prompt,
                                                    prompts,
                                                    delay_between_messages=5*60,
                                                    initial_url="https://chatgpt.com",
                                                    headless=False):
    chatgpt = ChatGPTScraper(
        download_dir=generated_imgs_dir,
        headless=headless
    )
    chat_url = None
    responses = []

    try:
        chatgpt.open_url(url=initial_url)
        chatgpt.sleep(7)

        print(f"Sending initial system prompt")
        chatgpt.type_message(initial_prompt)
        chatgpt.sleep(delay_between_messages)

        chat_url = chatgpt.get_current_url(only_base=True)

        for i, prompt in enumerate(prompts):
            chatgpt.sleep(7)

            print(f"Generating image", i+1)
            chatgpt.type_message(prompt)
            chatgpt.sleep(delay_between_messages)

            text, img = chatgpt.get_last_response()
            responses.append({"text": text, "img": img})
            print(f"Response {i+1}: ",
                  "img," if img else "no image,",
                  "text" if text else "no text")

            if i < len(prompts) - 1:
                chatgpt.refresh_page()
                chatgpt.sleep(delay_between_messages)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        chatgpt.close()

    return chat_url, responses
    


def generate_imgs_with_n_prompts(prompts,
                                 delay_between_messages=5*60,
                                 initial_url="https://chatgpt.com",
                                 headless=False):
    chatgpt = ChatGPTScraper(
        download_dir=generated_imgs_dir,
        headless=headless
    )
    chat_url = None
    responses = []

    try:
        chatgpt.open_url(url=initial_url)
        chatgpt.sleep(7)

        chat_url = chatgpt.get_current_url(only_base=True)

        for i, prompt in enumerate(prompts):
            print("Generating image", i+1)
            chatgpt.type_message(prompt)
            chatgpt.sleep(delay_between_messages)

            text, img = chatgpt.get_last_response()
            responses.append({"text": text, "img": img})
            print(f"Response {i+1}: ",
                  "img," if img else "no image,",
                  "text" if text else "no text")

            if i < len(prompts) - 1:
                chatgpt.refresh_page()
                chatgpt.sleep(delay_between_messages)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        chatgpt.close()

    return chat_url, responses
