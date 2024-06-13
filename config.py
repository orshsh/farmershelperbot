from enum import Enum

TOKEN = '7031526897:AAFYlRWeqRWyb425xJBXExje2CX0Zff5BjA'
OWNERID = '1171930676'
NOSUPTYPES = ["audio", "document", "photo", "sticker", "video", "video_note", "voice", "location", "contact"]

class Stages(Enum): # Сомнительно, но окэй
    S_START = 0  # Начальное состояние
    S_1Q = 1
    S_2Q = 2
    S_3Q = 3
    S_FB = -1 # Оставить отзыв

KEYS = [2, 1, 3]
CODES = ['SKIDKA5', 'SKIDKA10', 'SKIDKA20', 'SKIDKA30']