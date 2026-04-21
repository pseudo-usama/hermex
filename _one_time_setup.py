from janus import ChatGPTScraper, GeminiScraper


try:
    scraper_obj = GeminiScraper()
    scraper_obj.open_url()
    scraper_obj.sleep(10)

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"An error occurred: {e}")

finally:
    input("Press Enter to close the browser...")
    scraper_obj.close()
