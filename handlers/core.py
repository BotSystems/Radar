import json
import os
import urllib.request
from math import sin, cos, sqrt, atan2, radians

from telegram import ParseMode, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from handlers.messages import get_message_by_key
from handlers.models import Place
from handlers.place_types import places
from models import Chanel

SELECTED_LANGUAGE = os.getenv('LANGUAGE', 'EN')
DIRECTION_URL = 'https://www.google.com/maps/dir/?api=1&origin={},{}&destination={},{}'
GET_NEARBY_PLACES_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={},{}&radius={}&rankBy=distance&type={}&key={}'


def get_direction(lat1, lng1, lat2, lng2):
    return DIRECTION_URL.format(lat1, lng1, lat2, lng2)


def get_distance(lat1, lng1, lat2, lng2):
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lng1)
    lat2 = radians(lat2)
    lon2 = radians(lng2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return int(R * c * 1000)


def render_result(result_data_json):
    return result_data_json['results'][:10]


def get_nearby_places(lat, lng, token, place_type, radius):
    url = GET_NEARBY_PLACES_URL.format(lat, lng, radius, place_type, token)

    response = urllib.request.urlopen(url)
    result = json.loads(response.read())

    if 'results' in result:
        return result['results']
    return []


def build_places(places, currentLat, currentLng):
    placesList = []

    for place in places:
        placeCoordinateLat = place['geometry']['location']['lat']
        placeCoordinateLng = place['geometry']['location']['lng']

        name = place['name'] if 'name' in place else get_message_by_key('not_indicated')
        location = place['vicinity'] if 'vicinity' in place else get_message_by_key('not_indicated')
        rating = place['rating'] if 'rating' in place else get_message_by_key('not_indicated')
        distance = get_distance(currentLat, currentLng, placeCoordinateLat, placeCoordinateLng)
        direction = get_direction(currentLat, currentLng, placeCoordinateLat, placeCoordinateLng)

        placesList.append(Place(name, location, direction, distance, rating))

    return placesList


def order_places(placeList):
    placeList.sort(key=lambda obj: obj.distance, reverse=True)
    return placeList


def build_keyboard():
    search_key = [KeyboardButton(get_message_by_key('search'), None, True)]
    return ReplyKeyboardMarkup([search_key], True)


def build_inline_keyboard_categories(lang='RU'):
    all_places = places[lang]
    buttons = []

    for k, v in all_places.items():
        buttons.append([InlineKeyboardButton(v.capitalize(), None, k)])

    return InlineKeyboardMarkup(buttons)


def send_categories(bot, update):
    try:
        if not update.message.location:
            return update.message.reply_text(get_message_by_key('coordinates_are_required'))

        lat, lng = update.message.location.latitude, update.message.location.longitude

        chanel = find_chanel(update.message.chat.id)
        chanel.set_coordinates(lat, lng)

        keyboard = build_inline_keyboard_categories(SELECTED_LANGUAGE)
        update.message.reply_text(get_message_by_key('places_and_establishments'), reply_markup=keyboard)
    except Exception as ex:
        print(ex)


def send_places(bot, update, places):
    if (places):
        try:
            for place in places:
                bot.send_message(update.callback_query.message.chat.id, place.build_answer(), parse_mode=ParseMode.HTML)
        except Exception as ex:
            print(ex)
    else:
        not_found_message = get_message_by_key('not_found')
        bot.send_message(update.callback_query.message.chat.id, not_found_message, parse_mode=ParseMode.HTML)


def take_by_limit(places, limit):
    return places[:limit]


def find_chanel(update_id):
    return Chanel.get(Chanel.chanel_id == update_id)


if __name__ == '__main__':
    latitude, longitude = 49.2316962, 28.4554234

    GOOGLE_PLACE_LIMIT = os.getenv('GOOGLE_PLACE_LIMIT')
    GOOGLE_PLACES_TOKEN = os.getenv('GOOGLE_PLACE_TOKEN')
    GOOGLE_PLACES_TYPE = os.getenv('GOOGLE_PLACE_TYPE')
    GOOGLE_PLACES_GOOGLE_PLACE_DISTANCE = os.getenv('GOOGLE_PLACE_DISTANCE')

    nearby_places = get_nearby_places(latitude, longitude, GOOGLE_PLACES_TOKEN, GOOGLE_PLACES_TYPE,
                                      GOOGLE_PLACES_GOOGLE_PLACE_DISTANCE)
    places_objects = take_by_limit(order_places(build_places(nearby_places, latitude, longitude)), GOOGLE_PLACE_LIMIT)

    print(places_objects)
