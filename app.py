import os
import telebot

BOT_TOKEN = os.environ.get("9268470292:AAE077lR2Ew5qoVmxsVopKcdDZrN-QZukZU")

if BOT_TOKEN:
    bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

    @bot.message_handler(commands=["start"])
    def start_cmd(m):
        bot.reply_to(m, "Формат: /find Название | Фон\nПример: /find Plush Pepe | Midnight Blue")

    @bot.message_handler(commands=["find"])
    def find_cmd(m):
        args = m.text.partition(" ")[2]
        if "|" not in args:
            return bot.reply_to(m, "Формат: /find Название | Фон")
        name, backdrop = [x.strip() for x in args.split("|", 1)]
        slug = re.sub(r"[^A-Za-z0-9]", "", name)
        wait = bot.reply_to(m, f"Ищу {name} с фоном {backdrop}…")

        def work():
            if slug not in jobs:
                threading.Thread(target=scan, args=(slug,), daemon=True).start()
                time.sleep(1)
            deadline = time.time() + 600
            while not jobs.get(slug, {}).get("done") and time.time() < deadline:
                time.sleep(3)
            found = [g for g in list(cache.get(slug, {}).values())
                     if g["backdrop"].lower() == backdrop.lower()]
            if not found:
                text = "Ничего не найдено. Проверь написание названия и фона (по-английски)."
            else:
                lines = [f"https://t.me/nft/{slug}-{g['num']} | {g['model']} | {g['owner'] or 'владелец скрыт'}"
                         for g in found[:30]]
                text = f"Найдено: {len(found)}\n\n" + "\n".join(lines)
            bot.edit_message_text(text, m.chat.id, wait.message_id, disable_web_page_preview=True)

        threading.Thread(target=work, daemon=True).start()

    threading.Thread(target=bot.infinity_polling, daemon=True).start()
