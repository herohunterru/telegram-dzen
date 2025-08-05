import os
import requests
import google.generativeai as genai

# --- Получаем секреты из переменных окружения GitHub ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
UNSPLASH_KEY = os.getenv('UNSPLASH_ACCESS_KEY')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# --- Проверка, что все секреты на месте ---
if not all([TELEGRAM_TOKEN, CHANNEL_ID, UNSPLASH_KEY, GEMINI_KEY]):
    print("Ошибка: Один или несколько секретов не найдены. Проверьте настройки репозитория.")
    exit(1)

# --- Функция для генерации текста с помощью Gemini ---
def generate_text_with_gemini(api_key, prompt_text):
    try:
        genai.configure(api_key=api_key)
        # Используем модель 1.5 Flash - она быстрая и экономичная
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("Отправляю запрос в Gemini API...")
        response = model.generate_content(prompt_text)
        generated_text = response.text.strip()
        print("Текст успешно сгенерирован.")
        return generated_text
    except Exception as e:
        print(f"Ошибка при генерации текста через Gemini API: {e}")
        return None

# --- Функция для получения случайного фото с Unsplash ---
def get_random_office_photo(api_key):
    url = "https://api.unsplash.com/photos/random"
    params = {
        "client_id": api_key,
        "query": "office, business, workplace, team, meeting",
        "orientation": "landscape"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        image_url = data['urls']['regular']
        author_name = data['user']['name']
        author_url = data['user']['links']['html']
        attribution = f'Фото от <a href="{author_url}?utm_source=telegram_poster&utm_medium=referral">{author_name}</a> на <a href="https://unsplash.com/?utm_source=telegram_poster&utm_medium=referral">Unsplash</a>'
        print(f"Найдено фото от {author_name}.")
        return image_url, attribution
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Unsplash API: {e}")
        return None, None

# --- Функция для отправки поста в Telegram ---
def send_to_telegram(text, image_url, attribution):
    full_caption = f"{text}\n\n{attribution}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHANNEL_ID,
        "photo": image_url,
        "caption": full_caption,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Пост успешно отправлен в Telegram!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке в Telegram: {e}")
        print(f"Ответ от сервера: {response.text}")

# --- Основной блок выполнения ---
if __name__ == "__main__":
    print("Начинаю процесс публикации...")
    
    # Читаем промпт из файла
    try:
        with open("prompt.txt", 'r', encoding='utf-8') as f:
            prompt = f.read()
    except FileNotFoundError:
        print("Ошибка: Файл prompt.txt не найден.")
        exit(1)

    # Генерируем текст
    generated_text = generate_text_with_gemini(GEMINI_KEY, prompt)
    
    # Получаем фото
    photo_url, photo_attribution = get_random_office_photo(UNSPLASH_KEY)
    
    if generated_text and photo_url:
        send_to_telegram(generated_text, photo_url, photo_attribution)
    else:
        print("Не удалось получить текст или фото. Публикация отменена.")
