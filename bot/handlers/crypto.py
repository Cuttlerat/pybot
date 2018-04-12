from services.crypto_compare import CryptoCompare


def crypto(bot, update):
    current_rate = CryptoCompare.get_rate(["BTC", "BCH", "ETH", "XMR", "XMO"], ["USD"])
    message = "```\n"
    for crypt, rates in sorted(current_rate.items()):
        message += "1 " + str(crypt) + " = $" + str(round(rates['USD'], 2))
        message += "\n"
    message += "```"
    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     parse_mode="markdown")
