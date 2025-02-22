import asyncio
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from googletrans import Translator

BASE_URL = "https://parasol.vmguest.uni-jena.de/grac_crystal/#wordlist?corpname=grac18&tab=advanced&wlattr=lc&itemsPerPage=500&showresults=1"


def get_words_from_page(driver, url):
    driver.get(url)

    time.sleep(10)
    WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "._t.word"))
    )

    attempts = 3
    for _ in range(attempts):
        try:
            words_from_page = driver.find_elements(By.CSS_SELECTOR, "._t.word")
            if words_from_page is not None:
                print(word.text.strip() for word in words_from_page if word.text.strip() and word.text.strip() != "Word")
                return [word.text.strip() for word in words_from_page if word.text.strip() and word.text.strip() != "Word"]
        except StaleElementReferenceException:
            print("Attempting to re-fetch items...")

    return []


def get_ukrainian_word():
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")  
    driver = webdriver.Chrome(options=options)
    words = []
    for i in range(1, 41):
        try:
            if i == 1:
                words_from_page = get_words_from_page(driver, BASE_URL)
            else:
                next_url = f"https://parasol.vmguest.uni-jena.de/grac_crystal/#wordlist?corpname=grac18&tab=advanced&wlattr=lc&page={i}&itemsPerPage=500&showresults=1"
                words_from_page = get_words_from_page(driver, next_url)
        except Exception as e:
            print(e)
            continue
        finally:
            print(f"Page: {i}")
            words.extend(words_from_page)
    driver.quit()
    return words


async def translation_into_given_language(language_of_translation, count_of_translated_words, ukrainian_words):
    attempts = 10
    translated_dictionary = {}

    translator = Translator()

    try:
        for i, word in enumerate(ukrainian_words[count_of_translated_words:], start=count_of_translated_words):

            if i % 100 == 0:
                print(f"Reinitializing Translator after {i} words")
                translator = Translator()

            translated_word = await translator.translate(word, src="uk", dest=language_of_translation)
            if translated_word == None:
                for _ in range(attempts):
                    translated_word = await translator.translate(word, src="uk", dest=language_of_translation)
                    if translated_word is not None:
                        break
            if translated_word:
                translated_dictionary[word] = translated_word.text.lower()
                print(f"translated word {i+1} - {word}")
            else:
                print(f"Failed to translate word: {word}")
            
    except Exception as e:
        print(e)
    finally:
        return translated_dictionary


def writte_word_into_file(translated_dictionary):
    with open("en-dictionary.txt", "w", encoding="utf-8") as file:
        for word, translated_word in translated_dictionary.items():
            text_file_string = f"{word} - {translated_word}\n"
            file.write(text_file_string)


if __name__ =="__main__":
    count_of_translated_words = 0
    translated_dictionary = {}
    words = get_ukrainian_word()

    print(len(words))
    print(count_of_translated_words)

    while(count_of_translated_words < len(words)):
        print("start translate words")
        new_translation = asyncio.run(translation_into_given_language("en",count_of_translated_words, words))
        translated_dictionary.update(new_translation)
        
        count_of_translated_words = len(translated_dictionary)

    writte_word_into_file(translated_dictionary)
