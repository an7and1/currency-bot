from vkbottle import Callback, Keyboard, KeyboardButtonColor, Text


def reply_main_menu() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text("Конвертировать"), color=KeyboardButtonColor.PRIMARY)
    kb.add(Text("Курсы валют"), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("Моя пара"), color=KeyboardButtonColor.SECONDARY)
    kb.add(Text("Мои конвертации"), color=KeyboardButtonColor.SECONDARY)
    kb.row()
    kb.add(Text("Помощь"), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def inline_quick_amounts() -> str:
    kb = Keyboard(one_time=False, inline=True)
    kb.add(Callback("100 USD RUB", {"cmd": "quick", "text": "100 USD RUB"}))
    kb.add(Callback("500 USD RUB", {"cmd": "quick", "text": "500 USD RUB"}))
    kb.row()
    kb.add(Callback("100 EUR RUB", {"cmd": "quick", "text": "100 EUR RUB"}))
    kb.add(Callback("Меню", {"cmd": "menu"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def inline_after_result() -> str:
    kb = Keyboard(one_time=False, inline=True)
    kb.add(Callback("Ещё конвертация", {"cmd": "ask_convert"}), color=KeyboardButtonColor.PRIMARY)
    kb.add(Callback("В меню", {"cmd": "menu"}), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()