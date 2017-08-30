# -*- coding: utf-8 -*-
import os

from telegram.ext import MessageHandler, CallbackQueryHandler, CommandHandler

from handlers.core import send_places, get_nearby_places, take_by_limit, order_places, build_places, send_categories, \
    find_chanel, build_keyboard
from handlers.decorators import save_chanel_decorator
from handlers.messages import get_message_by_key

GOOGLE_PLACE_LIMIT = os.getenv('GOOGLE_PLACE_LIMIT')
GOOGLE_PLACE_TOKEN = os.getenv('GOOGLE_PLACE_TOKEN')
GOOGLE_PLACE_DISTANCE = os.getenv('GOOGLE_PLACE_DISTANCE')


@save_chanel_decorator
def intro(bot, update):
    intro_message = get_message_by_key('intro')
    keyboard = build_keyboard()
    bot.send_message(update.message.chat.id, intro_message, reply_markup=keyboard)


@save_chanel_decorator
def handle_coordinate(bot, update):
    searching_place = update.callback_query.data

    chanel = find_chanel(update.callback_query.message.chat.id)
    lat, lng = chanel.lat, chanel.lng

    nearby_places = get_nearby_places(lat, lng, GOOGLE_PLACE_TOKEN, searching_place, GOOGLE_PLACE_DISTANCE)
    places_objects = take_by_limit(order_places(build_places(nearby_places, lat, lng)), int(GOOGLE_PLACE_LIMIT))

    return send_places(bot, update, places_objects)


def init_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler('start', intro))
    dispatcher.add_handler(MessageHandler(None, send_categories))
    dispatcher.add_handler(CallbackQueryHandler(handle_coordinate))
    return dispatcher
