import logging

from vkbottle import GroupEventType
from vkbottle.bot import Bot, Message, MessageEvent

from app.bot import keyboards
from app.bot.deps import get_session
from app.bot.states import BotStates
from app.db import repository
from app.domain import scenario, texts
from app.services.external_api import ExternalAPI
from app.services.validators import parse_conversion_input

logger = logging.getLogger(__name__)

MENU_COMMANDS = [
    "/start", "start",
    "Начать", "начать",
    "Меню", "меню",
    "Назад", "назад",
]


async def _send_menu(bot: Bot, peer_id: int, text: str) -> None:
    await bot.state_dispenser.set(peer_id, BotStates.MENU)
    await bot.api.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=0,
        keyboard=keyboards.reply_main_menu(),
    )


async def _snackbar(event: MessageEvent, text: str) -> None:
    try:
        await event.show_snackbar(text)
    except Exception as exc:
        logger.debug("snackbar failed: %s", exc)


async def _do_convert(bot: Bot, peer_id: int, user_id: int, user_input: str) -> None:
    try:
        amount, from_cur, to_cur = parse_conversion_input(user_input)
    except ValueError as exc:
        await bot.api.messages.send(
            peer_id=peer_id, message=str(exc), random_id=0,
            keyboard=keyboards.inline_quick_amounts(),
        )
        return

    await bot.api.messages.send(
        peer_id=peer_id, message=texts.TXT_LOADING, random_id=0,
    )

    api = ExternalAPI()
    try:
        text = await scenario.handle_convert(api, amount, from_cur, to_cur)
    except Exception as exc:
        logger.error("Ошибка при конвертации: %s", exc)
        await bot.api.messages.send(
            peer_id=peer_id, message=texts.TXT_API_ERROR, random_id=0,
            keyboard=keyboards.reply_main_menu(),
        )
        return
    finally:
        await api.close()

    async with get_session() as session:
        await repository.set_favorite_pair(session, user_id, f"{from_cur}->{to_cur}")
        await repository.add_history(session, user_id, user_input, text)

    await bot.state_dispenser.set(peer_id, BotStates.MENU)
    await bot.api.messages.send(
        peer_id=peer_id, message=text, random_id=0,
        keyboard=keyboards.inline_after_result(),
    )


def register_handlers(bot: Bot) -> None:

    @bot.on.message(text=MENU_COMMANDS)
    async def start_handler(message: Message) -> None:
        await _send_menu(bot, message.peer_id, texts.TXT_WELCOME)

    @bot.on.message(text=["Конвертировать", "Перевести", "/convert"])
    async def convert_prompt_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.WAITING_CONVERSION)
        await message.answer(texts.TXT_ASK_CONVERSION, keyboard=keyboards.inline_quick_amounts())

    @bot.on.message(text=["Курсы валют", "Курсы", "/rates"])
    async def rates_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        await message.answer(texts.TXT_LOADING)
        api = ExternalAPI()
        try:
            text = await scenario.handle_rates(api)
        except Exception as exc:
            logger.error("Ошибка при запросе курсов: %s", exc)
            text = texts.TXT_API_ERROR
        finally:
            await api.close()
        await message.answer(text, keyboard=keyboards.reply_main_menu())

    @bot.on.message(text=["Моя пара", "Избранное", "/my_pair"])
    async def my_pair_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        async with get_session() as session:
            pair = await repository.get_favorite_pair(session, message.from_id)
        if not pair:
            text = texts.TXT_NO_PAIR
        else:
            from_cur, to_cur = pair.split("->", 1)
            text = texts.TXT_SAVED_PAIR.format(from_cur=from_cur, to_cur=to_cur)
        await message.answer(text, keyboard=keyboards.reply_main_menu())

    @bot.on.message(text=["Мои конвертации", "История", "/history"])
    async def history_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        async with get_session() as session:
            items = await repository.get_recent_history(session, message.from_id, limit=5)
        if not items:
            await message.answer(texts.TXT_HISTORY_EMPTY, keyboard=keyboards.reply_main_menu())
            return
        lines = [texts.TXT_HISTORY_HEADER, ""]
        for item in items:
            ts = item.created_at.strftime("%d.%m %H:%M")
            lines.append(f"• {ts} — {item.query}")
        await message.answer("\n".join(lines), keyboard=keyboards.reply_main_menu())

    @bot.on.message(text=["Помощь", "/help"])
    async def help_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        await message.answer(texts.TXT_HELP, keyboard=keyboards.reply_main_menu())

    @bot.on.message(state=BotStates.WAITING_CONVERSION)
    async def conversion_input_handler(message: Message) -> None:
        await _do_convert(bot, message.peer_id, message.from_id, (message.text or "").strip())

    @bot.on.message()
    async def fallback_handler(message: Message) -> None:
        await bot.state_dispenser.set(message.peer_id, BotStates.MENU)
        await message.answer(texts.TXT_FALLBACK, keyboard=keyboards.reply_main_menu())

    @bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
    async def callback_handler(event: MessageEvent) -> None:
        payload = event.payload or {}
        cmd = payload.get("cmd")
        peer_id = event.peer_id
        user_id = event.user_id

        if cmd == "menu":
            await _snackbar(event, texts.TXT_MAIN_MENU)
            await _send_menu(bot, peer_id, texts.TXT_WELCOME)

        elif cmd == "ask_convert":
            await _snackbar(event, texts.TXT_ASK_CONVERSION)
            await bot.state_dispenser.set(peer_id, BotStates.WAITING_CONVERSION)
            await bot.api.messages.send(
                peer_id=peer_id, message=texts.TXT_ASK_CONVERSION, random_id=0,
                keyboard=keyboards.inline_quick_amounts(),
            )

        elif cmd == "quick":
            query = payload.get("text", "")
            await _snackbar(event, f"Отправлено: {query}")
            await bot.api.messages.send(peer_id=peer_id, message=query, random_id=0)
            await _do_convert(bot, peer_id, user_id, query)
