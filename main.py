from generate_imgs import generate_imgs_with_initial_prompt

if __name__ == "__main__":
    # Example usage
    initial_prompt = "Create a series of images depicting a futuristic city."
    num_frames = 5
    initial_url = "https://chatgpt.com"

    chat_url, result_imgs = generate_imgs_with_initial_prompt(
        initial_prompt, num_frames, initial_url
    )
