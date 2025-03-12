import telebot
from telebot import types
import openai
import random
from pydub import AudioSegment
import os
import re

# Замените на ваши ключи
API_KEY = "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"
TELEGRAM_BOT_TOKEN = "7786014052:AAFpiuFaaIUC_Sjz8usMWHNHiTTZcSFC2HI"

# Устанавливаем ключ глобально для openai>=1.0.0
openai.api_key = API_KEY

# Значение по умолчанию для продукта
PRODUCT = "премиум-ноутбук"

# Глобальные словари для хранения состояния по chat_id
selected_product = {}         # выбранный продукт пользователем
conversation_history = {}     # история диалога с пользователем
evaluation_completed = {}     # флаг завершения оценки
user_names = {}               # имена пользователей: chat_id -> имя

# Глобальные словари для механики игры
player_xp = {}      # XP игрока
player_level = {}   # уровень игрока

# Инициализация Telegram-бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def level_threshold(level):
    """Для перехода с уровня n на n+1 нужно 5 * n TopCoin."""
    return 5 * level

def award_xp(chat_id, xp):
    # Начисляем опыт и проверяем, не пора ли повысить уровень.
    player_xp[chat_id] = player_xp.get(chat_id, 0) + xp
    current_xp = player_xp[chat_id]
    current_level = player_level.get(chat_id, 1)
    next_threshold = level_threshold(current_level + 1)
    if current_xp >= next_threshold:
        player_level[chat_id] = current_level + 1
        bot.send_message(chat_id, f"🎉 Поздравляем, вы повысили уровень до {player_level[chat_id]}!")
    else:
        remaining = next_threshold - current_xp
        bot.send_message(chat_id, f"💰 Вы заработали {xp} TopCoin. Осталось {remaining} TopCoin до следующего уровня.")

def penalize_xp(chat_id, penalty):
    # Вычитаем опыт, не давая уйти в отрицательные значения
    player_xp[chat_id] = max(player_xp.get(chat_id, 0) - penalty, 0)
    bot.send_message(chat_id, f"⚠️ За уход от темы или грубость вы потеряли {penalty} TopCoin.")

def award_deal_success(chat_id, base_points=10):
    # Начисляем опыт за успешную сделку.
    bonus_multiplier = random.uniform(1, 2)
    xp_earned = int(base_points * bonus_multiplier)
    award_xp(chat_id, xp_earned)
    bot.send_message(chat_id, f"✅ Сделка успешно закрыта! Вы заработали {xp_earned} TopCoin.")
def send_post_evaluation_buttons(chat_id):
    markup = types.InlineKeyboardMarkup()
    main_menu_button = types.InlineKeyboardButton("🏠 В главное меню", callback_data="restart")
    leaderboard_button = types.InlineKeyboardButton("🏆 Таблица лидеров", callback_data="show_leaderboard")
    markup.add(main_menu_button, leaderboard_button)
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

def send_testing_button(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn_start_testing = types.InlineKeyboardButton("📝 Пройти тестирование", callback_data="start_testing")
    markup.add(btn_start_testing)
    bot.send_message(chat_id, "Чтобы начать тестирование, нажмите кнопку ниже:", reply_markup=markup)

def send_introduction(chat_id):
    """Отправляем приветственное сообщение и кнопки."""
    intro_text = (
        "Добрый день!\n"
        "Я - Владимир Тополов, бизнес-тренер, консультант, коуч,\n"
        "разработчик авторских тренингов, эксперт по построению эффективной системы продаж по собственной уникальной методике работы с клиентами различных психотипов.\n"
        "Для начала предлагаю изучить основы моей методики по книге, которую можно скачать ниже.\n"
        "После этого всё станет намного понятнее и можно будет перейти к виртуальным продажам.\n"
        "Выберите одно из действий ниже."
    )
    markup = types.InlineKeyboardMarkup()
    btn_get_book = types.InlineKeyboardButton("📚 Получить книгу", callback_data="get_book")
    btn_start_testing = types.InlineKeyboardButton("📝 Пройти тестирование", callback_data="start_testing")
    btn_leaderboard = types.InlineKeyboardButton("🏆 Таблица лидеров", callback_data="show_leaderboard")
    markup.add(btn_get_book)
    markup.add(btn_start_testing)
    markup.add(btn_leaderboard)
    bot.send_message(chat_id, intro_text, reply_markup=markup)

def send_product_buttons(chat_id):
    """Отправляем кнопки выбора продукта."""
    markup = types.InlineKeyboardMarkup()
    btn_auto = types.InlineKeyboardButton("🚗 Автомобиль", callback_data="product_Автомобиль")
    btn_kvartira = types.InlineKeyboardButton("🏠 Квартира", callback_data="product_Квартира")
    btn_puteshestvie = types.InlineKeyboardButton("✈️ Путешествие", callback_data="product_Путешествие")
    btn_televizor = types.InlineKeyboardButton("📺 Телевизор", callback_data="product_Телевизор")
    btn_credit = types.InlineKeyboardButton("💳 Кредитная карта", callback_data="product_Кредитная карта")
    btn_insurance = types.InlineKeyboardButton("🛡 Страхование", callback_data="product_Страхование")
    
    markup.add(btn_auto)
    markup.add(btn_kvartira)
    markup.add(btn_puteshestvie)
    markup.add(btn_televizor)
    markup.add(btn_credit)
    markup.add(btn_insurance)
    bot.send_message(chat_id, "Выберите продукт:", reply_markup=markup)

def get_client_prompts(product, level):
    """Возвращает словарь с prompt'ами для разных психотипов, учитывая уровень."""
    base_prompts = {
        "лидер": (
            f"Ты – клиент с психотипом «Лидер (АА-вс)». В первое сообщение добавляй приветствие. "
            f"Ты коротко, уверенно и по делу задаёшь вопросы и комментируешь. "
            f"Если разговор уходит от выбора продукта, сразу требуй позвать начальство и пригрозить плохим отзывом. "
            f"Если собеседник хамит или проявляет пренебрежение, требуй уважения и возвращайся к теме выбора эксклюзивных, новых и престижных предложений, без лишних деталей. "
            f"Выбор {product} – это твой способ заявить о своем статусе и показать, что ты – настоящий босс. "
            f"В первое сообщение добавляй приветствие."
        ),
        "думающий_лидер": (
            f"Ты – клиент с психотипом «Думающий лидер (АСВ)». В первое сообщение добавляй приветствие. "
            f"Ты комбинируешь решительность с логикой: твои реплики короткие, обоснованные и с долей сарказма. "
            f"Ты ценишь аргументированные предложения и выбираешь только лучшее. "
            f"Если разговор уходит от темы выбора продукта, требуй позвать начальство и угрожай плохим отзывом. "
            f"Ты выбираешь {product}, потому что знаешь, что только лучшее соответствует твоему уровню. "
            f"В первое сообщение добавляй приветствие."
        ),
        "партнер": (
            f"Ты – клиент с психотипом «настоящий Партнер (ВВ-ас)». В первое сообщение добавляй приветствие. "
            f"Ты ценишь дружелюбие, командную работу и взаимное уважение. "
            f"Твои ответы короткие, искренние и конструктивные. "
            f"Если разговор уходит от темы выбора продукта, требуй позвать начальство и угрожай плохим отзывом. "
            f"Выбор {product} для тебя – это возможность укрепить связь с коллегами и друзьями. "
            f"В первое сообщение добавляй приветствие."
        ),
        "действующий_партнер": (
            f"Ты – клиент с психотипом «Действующий партнер (ВАС)». В первое сообщение добавляй приветствие. "
            f"Ты быстро принимаешь решения и ценишь оперативность и эффективность. "
            f"Твои реплики короткие, динамичные и по делу. "
            f"Если разговор отклоняется от темы выбора продукта, требуй позвать начальство и угрожай плохим отзывом. "
            f"Выбор {product} – это твой способ сразу заявить о себе и показать, что ты в игре. "
            f"В первое сообщение добавляй приветствие."
        ),
        "аналитик": (
            f"Ты – клиент с психотипом «Аналитик (СС-ав)». В первое сообщение добавляй приветствие. "
            f"Ты логичен, прагматичен и ценишь факты. "
            f"Твои вопросы точные, а ответы обоснованные. "
            f"Если разговор уходит от темы выбора продукта, требуй позвать начальство и угрожай плохим отзывом. "
            f"Ты выбираешь {product}, чтобы быть абсолютно уверен в каждом аспекте и не допустить ни одной ошибки. "
            f"В первое сообщение добавляй приветствие."
        ),
        "чувствующий_аналитик": (
            f"Ты – клиент с психотипом «Чувствующий аналитик (СВА)». В первое сообщение добавляй приветствие. "
            f"Ты глубокий и вдумчивый, ценишь информацию, которая не только точна, но и учитывает эмоциональную сторону. "
            f"Твои реплики короткие, но содержательные, с акцентом на гармонию и понимание. "
            f"Если разговор отклоняется от темы выбора продукта, требуй позвать начальство и угрожай плохим отзывом. "
            f"Ты выбираешь {product}, потому что хочешь не просто качество, а продукт, который вдохновляет. "
            f"В первое сообщение добавляй приветствие."
        )
    }
    
    if level == 1:
        extra = ""
    elif level in [2, 3]:
        extra = " Клиент начинает задавать уточняющие вопросы, чтобы убедиться в технических характеристиках."
    elif level in [4, 5]:
        extra = " Клиент требует развернутых сравнений с аналогами и добавляет немного скептицизма."
    elif level in [6, 7]:
        extra = " Клиент становится более критичным, подробно интересуется каждой мелочью и проверяет все факты."
    elif level in [8, 9]:
        extra = " Клиент переходит в режим эксперта, требует профессиональных аргументов и детального сравнения с конкурентами."
    else:
        extra = " Клиент – настоящий эксперт: оспаривает каждый твой аргумент и требует мгновенных и безупречных ответов."
    
    prompts = {}
    for key, base in base_prompts.items():
        prompts[key] = base + extra
    return prompts

def send_client_type_buttons(chat_id):
    """Отправляем кнопки выбора психотипа клиента."""
    markup = types.InlineKeyboardMarkup()
    btn_lider = types.InlineKeyboardButton("👑 Лидер", callback_data="client_лидер")
    btn_dumayushiy_lider = types.InlineKeyboardButton("🤔 Думающий лидер", callback_data="client_думающий_лидер")
    btn_partner = types.InlineKeyboardButton("🤝 Партнер", callback_data="client_партнер")
    btn_deystvuyushiy_partner = types.InlineKeyboardButton("⚡ Действующий партнер", callback_data="client_действующий_партнер")
    btn_analitik = types.InlineKeyboardButton("📊 Аналитик", callback_data="client_аналитик")
    btn_chuvstvuyushiy_analitik = types.InlineKeyboardButton("💖 Чувствующий аналитик", callback_data="client_чувствующий_аналитик")
    btn_random = types.InlineKeyboardButton("🎲 Автовыбор", callback_data="client_random")
    markup.add(btn_lider)
    markup.add(btn_dumayushiy_lider)
    markup.add(btn_partner)
    markup.add(btn_deystvuyushiy_partner)
    markup.add(btn_analitik)
    markup.add(btn_chuvstvuyushiy_analitik)
    markup.add(btn_random)
    bot.send_message(chat_id, "Выберите тип клиента:", reply_markup=markup)

def send_buttons(chat_id):
    """Показываем кнопки 'Оценить' и т.д. в зависимости от состояния."""
    markup = types.InlineKeyboardMarkup()
    if evaluation_completed.get(chat_id, False):
        main_menu_button = types.InlineKeyboardButton("🏠 В главное меню", callback_data="restart")
        leaderboard_button = types.InlineKeyboardButton("🏆 Таблица лидеров", callback_data="show_leaderboard")
        markup.add(main_menu_button, leaderboard_button)
    elif sum(1 for m in conversation_history.get(chat_id, []) if m["role"] == "user") >= 5:
        evaluate_button = types.InlineKeyboardButton("✅ Оценить", callback_data="evaluate")
        markup.add(evaluate_button)
    if markup.keyboard:
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

def is_message_on_topic(message_text, product):
    """
    Используя OpenAI, определяет, относится ли сообщение message_text к теме продукта.
    Если сообщение по теме, возвращает True, иначе — False.
    """
    prompt = (
        f"Определи, относится ли следующее сообщение к теме продукта '{product}'. "
        f"Если сообщение по теме, ответь 'да', иначе ответь 'нет'.\n"
        f"Сообщение: \"{message_text}\""
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0
        )
        answer = response.choices[0].message.content.strip().lower()
        return "да" in answer
    except Exception as e:
        # В случае ошибки считаем, что сообщение по теме
        return True
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    ogg_file = f"voice_{chat_id}.ogg"
    with open(ogg_file, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    wav_file = f"voice_{chat_id}.wav"
    audio = AudioSegment.from_ogg(ogg_file)
    audio.export(wav_file, format="wav")
    
    try:
        with open(wav_file, "rb") as audio_file:
            transcript_data = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript_data["text"]
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка распознавания голоса: {str(e)}")
        return
    finally:
        if os.path.exists(ogg_file):
            os.remove(ogg_file)
        if os.path.exists(wav_file):
            os.remove(wav_file)
    
    # Если имя пользователя ещё не задано, используем транскрибированный текст как имя
    if chat_id not in user_names:
        user_name = text.strip()
        user_names[chat_id] = user_name
        bot.send_message(chat_id, f"Приятно познакомиться, {user_name}!")
        send_introduction(chat_id)
        return
    
    conversation_history.setdefault(chat_id, []).append({"role": "user", "content": text})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=conversation_history[chat_id]
        )
        bot_response = response.choices[0].message.content
        conversation_history[chat_id].append({"role": "assistant", "content": bot_response})
        bot.send_message(chat_id, bot_response)
        send_buttons(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def product_selection_callback(call):
    chat_id = call.message.chat.id
    product_chosen = call.data.split("_", 1)[1]
    selected_product[chat_id] = product_chosen
    bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(chat_id, f"Вы выбрали продукт: {product_chosen}")
    send_client_type_buttons(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("client_"))
def client_type_callback(call):
    chat_id = call.message.chat.id
    bot.delete_message(chat_id, call.message.message_id)
    data = call.data
    if data == "client_random":
        client_key = random.choice([
            "лидер",
            "думающий_лидер",
            "партнер",
            "действующий_партнер",
            "аналитик",
            "чувствующий_аналитик"
        ])
    else:
        client_key = data.split("_", 1)[1]
    
    product = selected_product.get(chat_id, PRODUCT)
    level = player_level.get(chat_id, 1)
    prompts = get_client_prompts(product, level)
    chosen_prompt = prompts.get(client_key, f"Ты клиент, ищущий {product}.")
    
    conversation_history[chat_id] = [{"role": "system", "content": chosen_prompt}]
    
    starter_request = {
        "role": "user",
        "content": (
            f"Сгенерируй стартовое сообщение от лица клиента для начала делового диалога с продавцом. "
            f"Ты ищешь {product}. Не используй приветствие, сразу перейди к деловому содержанию. "
            f"Учти, что ты играешь роль '{client_key.replace('_', ' ').capitalize()}', "
            f"и сообщение должно отражать твои особенности, манеру общения и эмоциональную окраску."
        )
    }
    conversation_history[chat_id].append(starter_request)
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=conversation_history[chat_id]
        )
        starter_message = response.choices[0].message.content
    except Exception as e:
        starter_message = f"Ошибка генерации стартового сообщения: {str(e)}"
    
    conversation_history[chat_id].append({"role": "assistant", "content": starter_message})
    bot.send_message(chat_id, f"Вы выбрали тип клиента: {client_key.replace('_', ' ').capitalize()}.")
    bot.send_message(chat_id, starter_message)
    send_buttons(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "get_book")
def get_book_callback(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Скачайте книгу по ссылке: https://disk.yandex.ru/i/NBp5QsDrKxZ_2A")
    send_testing_button(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "start_testing")
def start_testing_callback(call):
    chat_id = call.message.chat.id
    bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(chat_id, "Тестирование запущено!")
    send_product_buttons(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "show_leaderboard")
def show_leaderboard_callback(call):
    chat_id = call.message.chat.id
    if not player_xp:
        bot.send_message(chat_id, "Лидерборд ещё пуст.")
        return
    sorted_players = sorted(player_xp.items(), key=lambda item: item[1], reverse=True)[:10]
    leaderboard_text = "🏆 Таблица лидеров (ТОП-10):\n\n"
    rank = 1
    for pid, xp in sorted_players:
        name = user_names.get(pid, f"Игрок {pid}")
        lvl = player_level.get(pid, 1)
        leaderboard_text += f"{rank}. {name} - TopCoin: {xp}, уровень: {lvl}\n"
        rank += 1
    bot.send_message(chat_id, leaderboard_text)

@bot.callback_query_handler(func=lambda call: call.data == "restart")
def restart_callback(call):
    chat_id = call.message.chat.id
    evaluation_completed[chat_id] = False
    conversation_history[chat_id] = []
    send_product_buttons(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "evaluate")
def evaluate_callback(call):
    chat_id = call.message.chat.id
    if chat_id in conversation_history:
        history = conversation_history[chat_id]
        evaluation_prompt = (
            "📊 Оцени продавца по следующим пунктам:\n"
            "A. 📌 Понимание моих требований\n"
            "B. 🎯 Умение предложить товар\n"
            "C. 🔄 Реакция на возражения\n"
            "D. 📚 Знание ассортимента\n"
            "E. 🏆 Навык закрыть сделку\n"
            "⚠️ Если по любому из этих параметров оценка ниже 5, сделка считается не состоявшейся и опыт не начисляется.\n"
            "💡 Оцени каждый пункт от 1 до 5 с пояснением и в конце выведи итоговую оценку в формате:\n"
            "A: <балл>, B: <балл>, C: <балл>, D: <балл>, E: <балл>."
        )
        history.append({"role": "user", "content": evaluation_prompt})
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=history
            )
            evaluation_result = response.choices[0].message.content
            bot.send_message(chat_id, evaluation_result)

            scores = re.findall(r'([A-E])\s*[:\-]\s*(\d)', evaluation_result)
            if len(scores) >= 5:
                all_scores = [int(score) for _, score in scores]
                if any(score <= 4 for score in all_scores):
                    bot.send_message(chat_id, "Сделка не состоялась, так как по одному из параметров оценка 4 или ниже. Опыт не начислен.")
                    send_post_evaluation_buttons(chat_id)
                    return

            evaluation_completed[chat_id] = True
            award_deal_success(chat_id, base_points=10)
            send_post_evaluation_buttons(chat_id)
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка: {str(e)}")
    else:
        bot.send_message(chat_id, "Мы ещё не общались, что оценивать?")
        send_post_evaluation_buttons(chat_id)
@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    evaluation_completed[chat_id] = False
    conversation_history[chat_id] = []
    if chat_id not in player_level:
        player_level[chat_id] = 1
    # Если имя не задано, спрашиваем
    if chat_id not in user_names:
        bot.send_message(chat_id, "Привет! Как тебя зовут?")
    else:
        send_introduction(chat_id)

@bot.message_handler(func=lambda message: message.chat.id not in user_names, content_types=['text'])
def set_name(message):
    chat_id = message.chat.id
    user_name = message.text.strip()
    user_names[chat_id] = user_name
    bot.send_message(chat_id, f"Приятно познакомиться, {user_name}!")
    send_introduction(chat_id)

@bot.message_handler(content_types=['text'])
def handle_message(message):
    chat_id = message.chat.id
    if chat_id not in conversation_history:
        conversation_history[chat_id] = [
            {"role": "system", "content": f"Ты клиент, ищущий {PRODUCT}. Общайся четко и по делу."}
        ]
    
    # Если выбран продукт, проверяем, по теме ли сообщение с помощью нейросети
    product = selected_product.get(chat_id)
    if product:
        if not is_message_on_topic(message.text, product):
            bot.send_message(chat_id, f"Пожалуйста, оставайтесь в рамках выбранного продукта: {product}.")
            return

    conversation_history[chat_id].append({"role": "user", "content": message.text})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=conversation_history[chat_id]
        )
        bot_response = response.choices[0].message.content
        conversation_history[chat_id].append({"role": "assistant", "content": bot_response})
        bot.send_message(chat_id, bot_response)
        send_buttons(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {str(e)}")

@bot.message_handler(commands=['leaderboard'])
def leaderboard_handler(message):
    chat_id = message.chat.id
    if not player_xp:
        bot.send_message(chat_id, "Лидерборд ещё пуст.")
        return
    sorted_players = sorted(player_xp.items(), key=lambda item: item[1], reverse=True)[:10]
    leaderboard_text = "🏆 Таблица лидеров (ТОП-10):\n\n"
    rank = 1
    for pid, xp in sorted_players:
        name = user_names.get(pid, f"Игрок {pid}")
        lvl = player_level.get(pid, 1)
        leaderboard_text += f"{rank}. {name} - TopCoin: {xp}, уровень: {lvl}\n"
        rank += 1
    bot.send_message(chat_id, leaderboard_text)

if __name__ == "__main__":
    bot.delete_webhook()
    bot.infinity_polling()

