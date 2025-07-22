from chatgpt import ChatGPTScraper

try:
    gpt = ChatGPTScraper()
    gpt.open_url()
    gpt.sleep(10)

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"An error occurred: {e}")

finally:
    input("Press Enter to close the browser...")
    gpt.close()
