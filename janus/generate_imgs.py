from janus import ChatGPT, Gemini


def _identify_scraper(initial_url):
    if "chatgpt" in initial_url:
        return ChatGPT
    elif "gemini" in initial_url:
        return Gemini
    else:
        raise ValueError("Unsupported URL for scraper identification.")


def generate_imgs_with_initial_prompt(
    initial_prompt,
    num_frames,
    delay_between_messages=5 * 60,
    initial_url="https://chatgpt.com",
    headless=False,
):
    ScraperClass = _identify_scraper(initial_url)

    scraper: ChatGPT | Gemini = ScraperClass(headless=headless)
    chat_url = None
    responses = []

    try:
        scraper.open_url(url=initial_url)
        scraper.sleep(7)

        print(f"Sending initial system prompt")
        scraper.send_message(initial_prompt)
        scraper.sleep(delay_between_messages)

        chat_url = scraper.get_current_url(only_base=True)
        if ScraperClass == Gemini:
            scraper.select_nano_banana()

        for i in range(num_frames):
            scraper.sleep(7)

            print(f"Generating image", i + 1)
            scraper.send_message(f"good, now generate image no. {i + 1}")
            scraper.sleep(delay_between_messages)

            response = scraper.get_last_response()
            responses.append(response)
            print(
                f"Response {i + 1}: ",
                "img," if response.image else "no image,",
                "text" if response.text else "no text",
            )

            if i < num_frames - 1:
                scraper.refresh_page()
                scraper.sleep(delay_between_messages)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

    return chat_url, responses


def generate_imgs_with_initial_prompt_and_n_prompts(
    initial_prompt,
    prompts,
    delay_between_messages=5 * 60,
    initial_url="https://chatgpt.com",
    headless=False,
):
    ScraperClass = _identify_scraper(initial_url)

    scraper: ChatGPT | Gemini = ScraperClass(headless=headless)
    chat_url = None
    responses = []

    try:
        scraper.open_url(url=initial_url)
        scraper.sleep(7)

        print(f"Sending initial system prompt")
        scraper.send_message(initial_prompt)
        scraper.sleep(delay_between_messages)

        chat_url = scraper.get_current_url(only_base=True)
        if ScraperClass == Gemini:
            scraper.select_nano_banana()

        for i, prompt in enumerate(prompts):
            scraper.sleep(7)

            print("Generating image", i + 1)
            scraper.send_message(prompt)
            scraper.sleep(delay_between_messages)

            response = scraper.get_last_response()
            responses.append(response)
            print(
                f"Response {i + 1}: ",
                "img," if response.image else "no image,",
                "text" if response.text else "no text",
            )

            if i < len(prompts) - 1:
                scraper.refresh_page()
                scraper.sleep(delay_between_messages)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

    return chat_url, responses


# TODO: I guess it's already in scraper_base.py as n_prompts?
def generate_imgs_with_n_prompts(
    prompts,
    delay_between_messages=5 * 60,
    initial_url="https://chatgpt.com",
    headless=False,
):
    chatgpt = ChatGPT(headless=headless)
    chat_url = None
    responses = []

    try:
        chatgpt.open_url(url=initial_url)
        chatgpt.sleep(7)

        chat_url = chatgpt.get_current_url(only_base=True)

        for i, prompt in enumerate(prompts):
            print("Generating image", i + 1)
            chatgpt.send_message(prompt)
            chatgpt.sleep(delay_between_messages)

            response = chatgpt.get_last_response()
            responses.append(response)
            print(
                f"Response {i + 1}: ",
                "img," if response.image else "no image,",
                "text" if response.text else "no text",
            )

            if i < len(prompts) - 1:
                chatgpt.refresh_page()
                chatgpt.sleep(delay_between_messages)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        chatgpt.close()

    return chat_url, responses
