# product_states.py
from enum import Enum

class ProductState(Enum):
    """Упрощенные состояния создания товара"""
    WAITING_BASIC_INFO = "waiting_basic_info"  # Название, категория, доступность
    WAITING_DETAILS = "waiting_details"        # Описание, единица измерения, количество, цена, оплата
    CONFIRMATION = "confirmation"              # Подтверждение
    #PHOTO_MANAGEMENT = "photo_management"
    PHOTO_QUESTION = "photo_question"        # Новое: вопрос о фото
    ADDING_PHOTOS = "adding_photos"       # Управление фото


# from enum import Enum

# class ProductState(Enum):
#     WAITING_NAME = "waiting_name"                   # 1. Название
#     WAITING_CATEGORY = "waiting_category"           # 2. Категория
#     WAITING_AVAILABILITY = "waiting_availability"   # 3. Доступность
#     WAITING_DESCRIPTION = "waiting_description"     # 4. Описание
#     WAITING_MEASUREMENT_UNIT = "waiting_measurement_unit"  # 5. Единица измерения
#     WAITING_QUANTITY = "waiting_quantity"           # 6. Количество
#     WAITING_PRICE = "waiting_price"                 # 7. Цена
#     WAITING_PREPAYMENT = "waiting_prepayment"       # 8. Оплата
#     CONFIRMATION = "confirmation"                   # 9. Подтверждение
#     ASKING_FOR_PHOTOS = "asking_for_photos"         # 10. Спросить про фото
#     WAITING_MAIN_PHOTO = "waiting_main_photo"       # 11. Основное фото
#     WAITING_ADDITIONAL_PHOTOS = "waiting_additional_photos"  # 12. Доп. фото
#     SELECTING_MAIN_PHOTO = "selecting_main_photo"   # 13. Выбор главного фото
    