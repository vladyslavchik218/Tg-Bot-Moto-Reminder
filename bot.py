import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from database import Database

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
MILEAGE, MAINTENANCE_TYPE, MAINTENANCE_MILEAGE, MAINTENANCE_NOTES, MAINTENANCE_PRICE = range(5)
INTERVAL_TYPE, INTERVAL_KM, INTERVAL_DAYS = range(3)
KNOWLEDGE_TITLE, KNOWLEDGE_URL, KNOWLEDGE_DESC, KNOWLEDGE_CATEGORY = range(4)

# Initialize database
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        db.add_user(user_id)

        welcome_message = """
🏍️ Вітаю в Боті-щоденнику обслуговування для мотоцикла!

Я допоможу тобі відстежувати обслуговування.
    """

        # Create main menu keyboard
        keyboard = [
            [
                InlineKeyboardButton("📊 Пробіг", callback_data='menu_mileage'),
                InlineKeyboardButton("🔧 Обслуговування", callback_data='menu_maintenance')
            ],
            [
                InlineKeyboardButton(" Статистика", callback_data='menu_stats'),
                InlineKeyboardButton("⚙️ Налаштування", callback_data='menu_settings')
            ],
            [
                InlineKeyboardButton("📋 Історія", callback_data='menu_history'),
                InlineKeyboardButton("🔗 Ланцюг", callback_data='menu_chain')
            ],
            [
                InlineKeyboardButton("🏍️ Мотоцикли", callback_data='menu_motorcycles'),
                InlineKeyboardButton("📚 База знань", callback_data='menu_knowledge')
            ],
            [
                InlineKeyboardButton("🔍 Техогляд", callback_data='menu_mot'),
                InlineKeyboardButton("📦 Запчастини", callback_data='menu_parts')
            ],
            [
                InlineKeyboardButton("🛣️ Поїздки", callback_data='menu_trips')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("Виникла помилка. Спробуйте пізніше.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📋 Використовуйте кнопки меню для навігації:

📊 Пробіг - оновити поточний пробіг
🔧 Обслуговування - додати запис про обслуговування
 Статистика - перегляд статистики та звітів
⚙️ Налаштування - налаштування інтервалів обслуговування
📋 Історія - історія обслуговування
🔗 Ланцюг - швидке записування змащення ланцюга

Бот автоматично нагадуватиме про обслуговування!
    """
    
    # Return to main menu
    keyboard = [
        [
            InlineKeyboardButton("🔙 Головне меню", callback_data='main_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup)

async def chain_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_mileage = db.get_current_mileage(user_id)
    
    if current_mileage is None:
        await update.message.reply_text(
            "Спочатку вкажіть поточний пробіг через /mileage"
        )
        return
    
    db.add_maintenance_record(user_id, 'chain', current_mileage, 'Змащення ланцюга')
    db.update_reminder(user_id, 'chain', current_mileage, datetime.now().isoformat())
    
    keyboard = [[InlineKeyboardButton("🔙 Головне меню", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Змащення ланцюга записано!\n"
        f"Пробіг: {current_mileage} км\n"
        f"Наступне нагадування через 500 км.",
        reply_markup=reply_markup
    )

# Menu button handlers
async def menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    callback_data = query.data

    if callback_data == 'main_menu':
        keyboard = [
            [
                InlineKeyboardButton("📊 Пробіг", callback_data='menu_mileage'),
                InlineKeyboardButton("🔧 Обслуговування", callback_data='menu_maintenance')
            ],
            [
                InlineKeyboardButton(" Статистика", callback_data='menu_stats'),
                InlineKeyboardButton("⚙️ Налаштування", callback_data='menu_settings')
            ],
            [
                InlineKeyboardButton("📋 Історія", callback_data='menu_history'),
                InlineKeyboardButton("🔗 Ланцюг", callback_data='menu_chain')
            ],
            [
                InlineKeyboardButton("🏍️ Мотоцикли", callback_data='menu_motorcycles'),
                InlineKeyboardButton("📚 База знань", callback_data='menu_knowledge')
            ],
            [
                InlineKeyboardButton("🔍 Техогляд", callback_data='menu_mot'),
                InlineKeyboardButton("📦 Запчастини", callback_data='menu_parts')
            ],
            [
                InlineKeyboardButton("🛣️ Поїздки", callback_data='menu_trips')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🏍️ Головне меню:", reply_markup=reply_markup)
    
    elif callback_data == 'menu_mileage':
        await query.edit_message_text("Введіть поточний пробіг мотоцикла (в км):")
        context.user_data['awaiting_mileage'] = True
    
    elif callback_data == 'menu_maintenance':
        keyboard = [
            [InlineKeyboardButton("🛢️ Заміна масла", callback_data='maint_oil')],
            [InlineKeyboardButton("🔧 Фільтри", callback_data='maint_filter')],
            [InlineKeyboardButton("⚙️ Клапани", callback_data='maint_valve')],
            [InlineKeyboardButton("🔌 Інше", callback_data='maint_other')],
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Оберіть тип обслуговування:", reply_markup=reply_markup)
    
    elif callback_data == 'menu_stats':
        stats = db.get_statistics(user_id)

        message = "📈 Статистика\n\n"
        message += f"Поточний пробіг: {stats['current_mileage'] or 0} км\n"
        message += f"Всього записів: {stats['total_records']}\n"
        message += f"💰 Загальні витрати: {stats['total_cost']:.2f} грн\n\n"
        message += "За типом обслуговування:\n"

        type_names = {
            'oil': '🛢️ Заміна масла',
            'filter': '🔧 Фільтри',
            'valve': '⚙️ Клапани',
            'chain': '🔗 Ланцюг',
            'other': '🔌 Інше'
        }

        for maint_type, count in stats['type_counts'].items():
            cost = stats['type_costs'].get(maint_type, 0)
            message += f"• {type_names.get(maint_type, maint_type)}: {count} ({cost:.2f} грн)\n"

        keyboard = [
            [InlineKeyboardButton("📤 Експорт в CSV", callback_data='export_csv')],
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif callback_data == 'menu_settings':
        intervals = db.get_all_intervals(user_id)
        
        if not intervals:
            message = "⚙️ Налаштування\n\nНалаштуйте інтервали для нагадувань про обслуговування."
        else:
            message = "⚙️ Налаштування інтервалів\n\n"
            for interval in intervals:
                type_names = {
                    'oil': 'Заміна масла',
                    'filter': 'Фільтри',
                    'valve': 'Клапани',
                    'chain': 'Ланцюг'
                }
                name = type_names.get(interval['maintenance_type'], interval['maintenance_type'])
                message += f"• {name}: кожні {interval['interval_km']} км\n"
        
        keyboard = [
            [InlineKeyboardButton("🛢️ Масло", callback_data='set_interval_oil')],
            [InlineKeyboardButton("🔧 Фільтри", callback_data='set_interval_filter')],
            [InlineKeyboardButton("⚙️ Клапани", callback_data='set_interval_valve')],
            [InlineKeyboardButton("🍂 Сезонні нагадування", callback_data='menu_seasonal')],
            [InlineKeyboardButton("� Резервне копіювання", callback_data='menu_backup')],
            [InlineKeyboardButton("� Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif callback_data == 'menu_history':
        records = db.get_maintenance_records(user_id)

        if not records:
            message = "📋 Історія обслуговування\n\nПоки немає записів."
        else:
            message = "📋 Історія обслуговування\n\n"
            type_names = {
                'oil': '🛢️ Заміна масла',
                'filter': '🔧 Фільтри',
                'valve': '⚙️ Клапани',
                'chain': '🔗 Ланцюг',
                'other': '🔌 Інше'
            }

            for record in records[:10]:
                date_str = datetime.fromisoformat(record['date']).strftime('%d.%m.%Y')
                message += f"{type_names.get(record['type'], record['type'])}\n"
                message += f"📅 {date_str} | 🛣️ {record['mileage']} км\n"
                if record['notes']:
                    message += f"📝 {record['notes']}\n"
                price = record.get('price', 0) or 0
                if price > 0:
                    message += f"💰 {price:.2f} грн\n"
                message += "---\n"

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif callback_data == 'menu_chain':
        current_mileage = db.get_current_mileage(user_id)
        
        if current_mileage is None:
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Спочатку вкажіть поточний пробіг.", reply_markup=reply_markup)
            return
        
        db.add_maintenance_record(user_id, 'chain', current_mileage, 'Змащення ланцюга')
        db.update_reminder(user_id, 'chain', current_mileage, datetime.now().isoformat())
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"✅ Змащення ланцюга записано!\n"
            f"Пробіг: {current_mileage} км\n"
            f"Наступне нагадування через 500 км.",
            reply_markup=reply_markup
        )
    
    elif callback_data.startswith('maint_'):
        maint_type = callback_data.replace('maint_', '')
        context.user_data['maintenance_type'] = maint_type
        await query.edit_message_text(f"Введіть пробіг на момент обслуговування (км):")
        context.user_data['awaiting_maintenance_mileage'] = True
    
    elif callback_data.startswith('set_interval_'):
        interval_type = callback_data.replace('set_interval_', '')
        context.user_data['interval_type'] = interval_type
        await query.edit_message_text(f"Введіть інтервал в км для {interval_type}:")
        context.user_data['awaiting_interval_km'] = True

    elif callback_data == 'menu_knowledge':
        keyboard = [
            [InlineKeyboardButton("➕ Додати статтю", callback_data='knowledge_add')],
            [InlineKeyboardButton("🔍 Пошук", callback_data='knowledge_search')],
            [InlineKeyboardButton("📋 Всі статті", callback_data='knowledge_list')],
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📚 База знань\n\nЗберігайте корисні посилання, статті та відео про мотоцикли.", reply_markup=reply_markup)

    elif callback_data == 'knowledge_add':
        await query.edit_message_text("Введіть назву статті:")
        context.user_data['awaiting_knowledge_title'] = True

    elif callback_data == 'knowledge_search':
        await query.edit_message_text("Введіть ключове слово для пошуку:")
        context.user_data['awaiting_knowledge_search'] = True

    elif callback_data == 'knowledge_list':
        items = db.get_all_knowledge_items(user_id)

        if not items:
            message = "📋 Всі статті\n\nБаза знань порожня."
        else:
            message = "📋 Всі статті\n\n"
            for item in items[:10]:
                message += f"📌 {item['title']}\n"
                message += f"🔗 {item['url']}\n"
                if item['description']:
                    message += f"📝 {item['description']}\n"
                if item['category']:
                    message += f"📂 Категорія: {item['category']}\n"
                message += "---\n"

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_knowledge')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif callback_data == 'export_csv':
        await export_csv(update, context)

    elif callback_data == 'menu_seasonal':
        reminders = db.get_all_seasonal_reminders(user_id)

        message = "🍂 Сезонні нагадування\n\n"
        if not reminders:
            message += "Налаштуйте нагадування для сезонного обслуговування."
        else:
            type_names = {
                'spring_prep': '🌸 Підготовка до весни',
                'winter_prep': '❄️ Підготовка до зими',
                'summer_prep': '☀️ Підготовка до літа',
                'autumn_prep': '🍂 Підготовка до осені'
            }
            for reminder in reminders:
                status = "✅ Ввімкнено" if reminder['enabled'] else "❌ Вимкнено"
                message += f"{type_names.get(reminder['reminder_type'], reminder['reminder_type'])}: {status}\n"
                if reminder['reminder_date']:
                    message += f"   Дата: {reminder['reminder_date']}\n"

        keyboard = [
            [InlineKeyboardButton("🌸 Весна", callback_data='seasonal_spring')],
            [InlineKeyboardButton("❄️ Зима", callback_data='seasonal_winter')],
            [InlineKeyboardButton("🔙 Назад", callback_data='menu_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif callback_data.startswith('seasonal_'):
        season_type = callback_data.replace('seasonal_', '')
        type_names = {
            'spring': 'spring_prep',
            'winter': 'winter_prep'
        }
        season_name = {
            'spring': '🌸 Підготовка до весни',
            'winter': '❄️ Підготовка до зими'
        }

        reminder = db.get_seasonal_reminder(user_id, type_names[season_type])
        status = "Ввімкнено" if reminder and reminder['enabled'] else "Вимкнено"

        keyboard = [
            [InlineKeyboardButton(f"🔔 Нагадування: {status}", callback_data=f'toggle_seasonal_{season_type}')],
            [InlineKeyboardButton("🔙 Назад", callback_data='menu_seasonal')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"{season_name[season_type]}\n\n"
            f"Налаштуйте нагадування для сезонного обслуговування.",
            reply_markup=reply_markup
        )

    elif callback_data.startswith('toggle_seasonal_'):
        season_type = callback_data.replace('toggle_seasonal_', '')
        type_names = {
            'spring': 'spring_prep',
            'winter': 'winter_prep'
        }
        season_name = {
            'spring': '🌸 Підготовка до весни',
            'winter': '❄️ Підготовка до зими'
        }

        reminder = db.get_seasonal_reminder(user_id, type_names[season_type])
        new_status = not (reminder and reminder['enabled'])
        db.set_seasonal_reminder(user_id, type_names[season_type], None, new_status)

        status = "Ввімкнено" if new_status else "Вимкнено"

        keyboard = [
            [InlineKeyboardButton(f"🔔 Нагадування: {status}", callback_data=f'toggle_seasonal_{season_type}')],
            [InlineKeyboardButton("🔙 Назад", callback_data='menu_seasonal')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"{season_name[season_type]}\n\n"
            f"Нагадування {status.lower()}!",
            reply_markup=reply_markup
        )

    elif callback_data == 'menu_motorcycles':
        motorcycles = db.get_motorcycles(user_id)
        current_moto = db.get_current_motorcycle(user_id)

        message = "🏍️ Мої мотоцикли\n\n"
        if not motorcycles:
            message += "Немає мотоциклів."
        else:
            for moto in motorcycles:
                is_current = "✅ " if current_moto and moto['id'] == current_moto['id'] else ""
                message += f"{is_current}{moto['name']}"
                if moto['model']:
                    message += f" ({moto['model']}"
                    if moto['year']:
                        message += f", {moto['year']}"
                    message += ")"
                message += f" - {moto['current_mileage']} км\n"

        keyboard = []
        for moto in motorcycles:
            is_current = current_moto and moto['id'] == current_moto['id']
            if not is_current:
                keyboard.append([InlineKeyboardButton(f"🔄 {moto['name']}", callback_data=f'switch_moto_{moto["id"]}')])

        keyboard.append([InlineKeyboardButton("➕ Додати мотоцикл", callback_data='add_moto')])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='main_menu')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif callback_data.startswith('switch_moto_'):
        motorcycle_id = int(callback_data.replace('switch_moto_', ''))
        db.set_current_motorcycle(user_id, motorcycle_id)

        motorcycles = db.get_motorcycles(user_id)
        current_moto = db.get_current_motorcycle(user_id)

        message = "🏍️ Мої мотоцикли\n\n"
        for moto in motorcycles:
            is_current = "✅ " if current_moto and moto['id'] == current_moto['id'] else ""
            message += f"{is_current}{moto['name']}"
            if moto['model']:
                message += f" ({moto['model']}"
                if moto['year']:
                    message += f", {moto['year']}"
                message += ")"
            message += f" - {moto['current_mileage']} км\n"

        keyboard = []
        for moto in motorcycles:
            is_current = current_moto and moto['id'] == current_moto['id']
            if not is_current:
                keyboard.append([InlineKeyboardButton(f"🔄 {moto['name']}", callback_data=f'switch_moto_{moto["id"]}')])

        keyboard.append([InlineKeyboardButton("➕ Додати мотоцикл", callback_data='add_moto')])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='main_menu')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("✅ Мотоцикл змінено!", reply_markup=reply_markup)

    elif callback_data == 'add_moto':
        await query.edit_message_text("Введіть назву мотоцикла:")
        context.user_data['awaiting_moto_name'] = True

    elif callback_data == 'menu_mot':
        mot_records = db.get_mot_records(user_id)
        next_mot = db.get_next_mot_reminder(user_id)

        message = "🔍 Техогляд (MOT)\n\n"
        if next_mot:
            message += f"📅 Наступний техогляд: {next_mot['next_inspection_date']}\n\n"

        if not mot_records:
            message += "Історія техогляду порожня."
        else:
            message += "Історія техоглядів:\n\n"
            for record in mot_records[:5]:
                message += f"📅 Пройдено: {record['inspection_date']}\n"
                message += f"📅 Наступний: {record['next_inspection_date']}\n"
                if record['notes']:
                    message += f"📝 {record['notes']}\n"
                message += "---\n"

        keyboard = [
            [InlineKeyboardButton("➕ Додати запис", callback_data='add_mot')],
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif callback_data == 'add_mot':
        await query.edit_message_text("Введіть дату проходження техогляду (формат: DD.MM.YYYY):")
        context.user_data['awaiting_mot_inspection_date'] = True

    elif callback_data == 'menu_parts':
        parts = db.get_parts(user_id)

        if not parts:
            message = "📦 Запчастини та інвентар\n\nСписок порожній."
        else:
            message = "📦 Запчастини та інвентар\n\n"
            for part in parts[:10]:
                message += f"📌 {part['name']}\n"
                if part['part_number']:
                    message += f"🔢 Артикул: {part['part_number']}\n"
                message += f"📦 Кількість: {part['quantity']}\n"
                if part['purchase_date']:
                    message += f"📅 Куплено: {part['purchase_date']}\n"
                if part['expiry_date']:
                    message += f"⏰ Термін: {part['expiry_date']}\n"
                if part['notes']:
                    message += f"📝 {part['notes']}\n"
                message += "---\n"

        keyboard = [
            [InlineKeyboardButton("➕ Додати запчастину", callback_data='add_part')],
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif callback_data == 'add_part':
        await query.edit_message_text("Введіть назву запчастини:")
        context.user_data['awaiting_part_name'] = True

    elif callback_data == 'menu_trips':
        trips = db.get_trips(user_id)
        stats = db.get_trip_statistics(user_id)

        message = "🛣️ Поїздки\n\n"
        message += f"📊 Статистика:\n"
        message += f"• Всього поїздок: {stats['total_trips']}\n"
        message += f"• Загальна відстань: {stats['total_distance']:.1f} км\n"
        if stats['total_duration'] > 0:
            hours = stats['total_duration'] // 60
            minutes = stats['total_duration'] % 60
            message += f"• Загальний час: {hours} год {minutes} хв\n"
        message += "\n"

        if not trips:
            message += "Історія поїздок порожня."
        else:
            message += "Останні поїздки:\n\n"
            for trip in trips[:5]:
                message += f"📅 {trip['date']}\n"
                if trip['start_location'] and trip['end_location']:
                    message += f"📍 {trip['start_location']} → {trip['end_location']}\n"
                message += f"🛣️ {trip['distance_km']:.1f} км\n"
                if trip['duration_minutes']:
                    message += f"⏱️ {trip['duration_minutes']} хв\n"
                if trip['notes']:
                    message += f"📝 {trip['notes']}\n"
                message += "---\n"

        keyboard = [
            [InlineKeyboardButton("➕ Додати поїздку", callback_data='add_trip')],
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)

    elif callback_data == 'add_trip':
        await query.edit_message_text("Введіть місце відправлення:")
        context.user_data['awaiting_trip_start'] = True

    elif callback_data == 'menu_backup':
        keyboard = [
            [InlineKeyboardButton("📤 Експорт в JSON", callback_data='export_json')],
            [InlineKeyboardButton("📥 Імпорт з JSON", callback_data='import_json')],
            [InlineKeyboardButton("🔙 Назад", callback_data='menu_settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💾 Резервне копіювання\n\nЕкспортуйте або імпортуйте дані бота.", reply_markup=reply_markup)

    elif callback_data == 'export_json':
        json_data = db.export_to_json(user_id)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_backup')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📤 Експорт даних (JSON)\n\n"
            "Скопіюйте дані нижче та збережіть їх у файл:\n\n"
            f"```json\n{json_data}\n```",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif callback_data == 'import_json':
        await query.edit_message_text("📥 Вставте JSON дані для імпорту:")
        context.user_data['awaiting_import_json'] = True

# Handle text messages for menu interactions
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check if user is in any awaiting state
    is_awaiting = (
        context.user_data.get('awaiting_mileage') or
        context.user_data.get('awaiting_maintenance_mileage') or
        context.user_data.get('awaiting_maintenance_notes') or
        context.user_data.get('awaiting_maintenance_price') or
        context.user_data.get('awaiting_interval_km') or
        context.user_data.get('awaiting_knowledge_title') or
        context.user_data.get('awaiting_knowledge_url') or
        context.user_data.get('awaiting_knowledge_search') or
        context.user_data.get('awaiting_moto_name') or
        context.user_data.get('awaiting_mot_inspection_date') or
        context.user_data.get('awaiting_mot_next_date') or
        context.user_data.get('awaiting_part_name') or
        context.user_data.get('awaiting_part_number') or
        context.user_data.get('awaiting_part_quantity') or
        context.user_data.get('awaiting_part_expiry') or
        context.user_data.get('awaiting_part_notes') or
        context.user_data.get('awaiting_trip_start') or
        context.user_data.get('awaiting_trip_end') or
        context.user_data.get('awaiting_trip_distance') or
        context.user_data.get('awaiting_trip_date') or
        context.user_data.get('awaiting_trip_duration') or
        context.user_data.get('awaiting_trip_notes') or
        context.user_data.get('awaiting_import_json')
    )
    
    # If not awaiting anything, ignore the message
    if not is_awaiting:
        return
    
    # Handle mileage input
    if context.user_data.get('awaiting_mileage'):
        try:
            mileage = int(text)
            if mileage < 0:
                await update.message.reply_text("Пробіг не може бути від'ємним.")
                return
            
            db.update_mileage(user_id, mileage)
            context.user_data['awaiting_mileage'] = False
            
            # Check chain reminder
            last_chain = db.get_last_maintenance(user_id, 'chain')
            if last_chain:
                km_since_chain = mileage - last_chain['mileage']
                if km_since_chain >= 500:
                    await update.message.reply_text(
                        f"⚠️ Привіт, пора перевірити ланцюг! "
                        f"Ти проїхав {km_since_chain} км після останнього змащування."
                    )
            
            keyboard = [[InlineKeyboardButton("🔙 Головне меню", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"✅ Пробіг оновлено: {mileage} км", reply_markup=reply_markup)
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть число (км):")
    
    # Handle maintenance mileage input
    elif context.user_data.get('awaiting_maintenance_mileage'):
        try:
            mileage = int(text)
            if mileage < 0:
                await update.message.reply_text("Пробіг не може бути від'ємним.")
                return

            context.user_data['maintenance_mileage'] = mileage
            context.user_data['awaiting_maintenance_mileage'] = False
            context.user_data['awaiting_maintenance_notes'] = True

            await update.message.reply_text("Додайте нотатку (необов'язково, натисніть /skip щоб пропустити):")
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть число (км):")
    
    # Handle maintenance notes input
    elif context.user_data.get('awaiting_maintenance_notes'):
        context.user_data['maintenance_notes'] = text
        context.user_data['awaiting_maintenance_notes'] = False
        context.user_data['awaiting_maintenance_price'] = True

        await update.message.reply_text("Введіть вартість обслуговування в грн (необов'язково, натисніть /skip щоб пропустити):")

    # Handle maintenance price input
    elif context.user_data.get('awaiting_maintenance_price'):
        try:
            price = float(text)
            if price < 0:
                await update.message.reply_text("Вартість не може бути від'ємною.")
                return

            context.user_data['maintenance_price'] = price
            context.user_data['awaiting_maintenance_price'] = False

            user_id = update.effective_user.id
            maintenance_type = context.user_data['maintenance_type']
            mileage = context.user_data['maintenance_mileage']
            notes = context.user_data['maintenance_notes']
            price = context.user_data['maintenance_price']

            record_id = db.add_maintenance_record(user_id, maintenance_type, mileage, notes, price)

            # Update current mileage if this is higher
            current_mileage = db.get_current_mileage(user_id)
            if current_mileage is None or mileage > current_mileage:
                db.update_mileage(user_id, mileage)

            context.user_data['last_record_id'] = record_id

            type_names = {
                'oil': 'Заміна масла',
                'filter': 'Фільтри',
                'valve': 'Клапани',
                'chain': 'Ланцюг',
                'other': 'Інше'
            }

            keyboard = [
                [InlineKeyboardButton(" Головне меню", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ Запис додано!\n"
                f"Тип: {type_names.get(maintenance_type, maintenance_type)}\n"
                f"Пробіг: {mileage} км\n"
                f"Нотатка: {notes}\n"
                f"Вартість: {price:.2f} грн",
                reply_markup=reply_markup
            )
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть число (грн):")
    
    # Handle interval km input
    elif context.user_data.get('awaiting_interval_km'):
        try:
            interval_km = int(text)
            if interval_km <= 0:
                await update.message.reply_text("Інтервал має бути більше 0.")
                return
            
            interval_type = context.user_data['interval_type']
            db.set_maintenance_interval(user_id, interval_type, interval_km)
            context.user_data['awaiting_interval_km'] = False
            
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_settings')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            type_names = {
                'oil': 'Заміна масла',
                'filter': 'Фільтри',
                'valve': 'Клапани'
            }
            
            await update.message.reply_text(
                f"✅ Інтервал налаштовано!\n"
                f"{type_names.get(interval_type, interval_type)}: кожні {interval_km} км",
                reply_markup=reply_markup
            )
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть число (км):")

    # Handle knowledge title input
    elif context.user_data.get('awaiting_knowledge_title'):
        context.user_data['knowledge_title'] = text
        context.user_data['awaiting_knowledge_title'] = False
        context.user_data['awaiting_knowledge_url'] = True

        await update.message.reply_text("Введіть URL посилання:")

    # Handle knowledge URL input
    elif context.user_data.get('awaiting_knowledge_url'):
        context.user_data['knowledge_url'] = text
        context.user_data['awaiting_knowledge_url'] = False
        context.user_data['awaiting_knowledge_desc'] = True

        await update.message.reply_text("Введіть опис (необов'язково, натисніть /skip щоб пропустити):")

    # Handle knowledge description input
    elif context.user_data.get('awaiting_knowledge_desc'):
        context.user_data['knowledge_desc'] = text
        context.user_data['awaiting_knowledge_desc'] = False
        context.user_data['awaiting_knowledge_category'] = True

        await update.message.reply_text("Введіть категорію (необов'язково, натисніть /skip щоб пропустити):")

    # Handle knowledge category input
    elif context.user_data.get('awaiting_knowledge_category'):
        context.user_data['knowledge_category'] = text
        context.user_data['awaiting_knowledge_category'] = False

        user_id = update.effective_user.id
        title = context.user_data['knowledge_title']
        url = context.user_data['knowledge_url']
        desc = context.user_data['knowledge_desc']
        category = context.user_data['knowledge_category']

        db.add_knowledge_item(user_id, title, url, desc, None, category)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_knowledge')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Статтю додано!\n📌 {title}\n🔗 {url}",
            reply_markup=reply_markup
        )

    # Handle knowledge search input
    elif context.user_data.get('awaiting_knowledge_search'):
        context.user_data['awaiting_knowledge_search'] = False

        user_id = update.effective_user.id
        query = text
        items = db.search_knowledge_base(user_id, query)

        if not items:
            message = f"🔍 Результати пошуку: '{query}'\n\nНічого не знайдено."
        else:
            message = f"🔍 Результати пошуку: '{query}'\n\n"
            for item in items[:10]:
                message += f"📌 {item['title']}\n"
                message += f"🔗 {item['url']}\n"
                if item['description']:
                    message += f"📝 {item['description']}\n"
                if item['category']:
                    message += f"📂 Категорія: {item['category']}\n"
                message += "---\n"

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_knowledge')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

    # Handle motorcycle name input
    elif context.user_data.get('awaiting_moto_name'):
        context.user_data['moto_name'] = text
        context.user_data['awaiting_moto_name'] = False
        context.user_data['awaiting_moto_model'] = True

        await update.message.reply_text("Введіть модель (необов'язково, натисніть /skip щоб пропустити):")

    # Handle motorcycle model input
    elif context.user_data.get('awaiting_moto_model'):
        context.user_data['moto_model'] = text
        context.user_data['awaiting_moto_model'] = False
        context.user_data['awaiting_moto_year'] = True

        await update.message.reply_text("Введіть рік (необов'язково, натисніть /skip щоб пропустити):")

    # Handle motorcycle year input
    elif context.user_data.get('awaiting_moto_year'):
        try:
            year = int(text)
            context.user_data['moto_year'] = year
        except ValueError:
            context.user_data['moto_year'] = None

        context.user_data['awaiting_moto_year'] = False

        user_id = update.effective_user.id
        name = context.user_data['moto_name']
        model = context.user_data.get('moto_model')
        year = context.user_data.get('moto_year')

        db.add_motorcycle(user_id, name, model, year)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_motorcycles')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Мотоцикл додано!\n🏍️ {name}",
            reply_markup=reply_markup
        )

    # Handle MOT inspection date input
    elif context.user_data.get('awaiting_mot_inspection_date'):
        context.user_data['mot_inspection_date'] = text
        context.user_data['awaiting_mot_inspection_date'] = False
        context.user_data['awaiting_mot_next_date'] = True

        await update.message.reply_text("Введіть дату наступного техогляду (формат: DD.MM.YYYY):")

    # Handle MOT next inspection date input
    elif context.user_data.get('awaiting_mot_next_date'):
        context.user_data['mot_next_date'] = text
        context.user_data['awaiting_mot_next_date'] = False
        context.user_data['awaiting_mot_notes'] = True

        await update.message.reply_text("Додайте нотатку (необов'язково, натисніть /skip щоб пропустити):")

    # Handle MOT notes input
    elif context.user_data.get('awaiting_mot_notes'):
        context.user_data['mot_notes'] = text
        context.user_data['awaiting_mot_notes'] = False

        user_id = update.effective_user.id
        inspection_date = context.user_data['mot_inspection_date']
        next_date = context.user_data['mot_next_date']
        notes = context.user_data['mot_notes']

        db.add_mot_record(user_id, inspection_date, next_date, notes)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_mot')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Запис техогляду додано!\n"
            f"📅 Пройдено: {inspection_date}\n"
            f"📅 Наступний: {next_date}",
            reply_markup=reply_markup
        )

    # Handle part name input
    elif context.user_data.get('awaiting_part_name'):
        context.user_data['part_name'] = text
        context.user_data['awaiting_part_name'] = False
        context.user_data['awaiting_part_number'] = True

        await update.message.reply_text("Введіть артикул (необов'язково, натисніть /skip щоб пропустити):")

    # Handle part number input
    elif context.user_data.get('awaiting_part_number'):
        context.user_data['part_number'] = text
        context.user_data['awaiting_part_number'] = False
        context.user_data['awaiting_part_quantity'] = True

        await update.message.reply_text("Введіть кількість:")

    # Handle part quantity input
    elif context.user_data.get('awaiting_part_quantity'):
        try:
            quantity = int(text)
            if quantity < 1:
                await update.message.reply_text("Кількість має бути більше 0.")
                return
            context.user_data['part_quantity'] = quantity
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть число:")
            return

        context.user_data['awaiting_part_quantity'] = False
        context.user_data['awaiting_part_expiry'] = True

        await update.message.reply_text("Введіть термін придатності (формат: DD.MM.YYYY, необов'язково, натисніть /skip щоб пропустити):")

    # Handle part expiry date input
    elif context.user_data.get('awaiting_part_expiry'):
        context.user_data['part_expiry'] = text
        context.user_data['awaiting_part_expiry'] = False
        context.user_data['awaiting_part_notes'] = True

        await update.message.reply_text("Додайте нотатку (необов'язково, натисніть /skip щоб пропустити):")

    # Handle part notes input
    elif context.user_data.get('awaiting_part_notes'):
        context.user_data['part_notes'] = text
        context.user_data['awaiting_part_notes'] = False

        user_id = update.effective_user.id
        name = context.user_data['part_name']
        part_number = context.user_data.get('part_number')
        quantity = context.user_data['part_quantity']
        expiry_date = context.user_data['part_expiry']
        notes = context.user_data['part_notes']

        db.add_part(user_id, name, part_number, quantity, None, expiry_date, notes)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_parts')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Запчастину додано!\n📌 {name}\n📦 Кількість: {quantity}",
            reply_markup=reply_markup
        )

    # Handle trip start location input
    elif context.user_data.get('awaiting_trip_start'):
        context.user_data['trip_start'] = text
        context.user_data['awaiting_trip_start'] = False
        context.user_data['awaiting_trip_end'] = True

        await update.message.reply_text("Введіть місце призначення:")

    # Handle trip end location input
    elif context.user_data.get('awaiting_trip_end'):
        context.user_data['trip_end'] = text
        context.user_data['awaiting_trip_end'] = False
        context.user_data['awaiting_trip_distance'] = True

        await update.message.reply_text("Введіть відстань в км:")

    # Handle trip distance input
    elif context.user_data.get('awaiting_trip_distance'):
        try:
            distance = float(text)
            if distance <= 0:
                await update.message.reply_text("Відстань має бути більше 0.")
                return
            context.user_data['trip_distance'] = distance
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть число:")
            return

        context.user_data['awaiting_trip_distance'] = False
        context.user_data['awaiting_trip_date'] = True

        await update.message.reply_text("Введіть дату поїздки (формат: DD.MM.YYYY):")

    # Handle trip date input
    elif context.user_data.get('awaiting_trip_date'):
        context.user_data['trip_date'] = text
        context.user_data['awaiting_trip_date'] = False
        context.user_data['awaiting_trip_duration'] = True

        await update.message.reply_text("Введіть тривалість в хвилинах (необов'язково, натисніть /skip щоб пропустити):")

    # Handle trip duration input
    elif context.user_data.get('awaiting_trip_duration'):
        try:
            duration = int(text)
            if duration < 0:
                await update.message.reply_text("Тривалість не може бути від'ємною.")
                return
            context.user_data['trip_duration'] = duration
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть число:")
            return

        context.user_data['awaiting_trip_duration'] = False
        context.user_data['awaiting_trip_notes'] = True

        await update.message.reply_text("Додайте нотатку (необов'язково, натисніть /skip щоб пропустити):")

    # Handle trip notes input
    elif context.user_data.get('awaiting_trip_notes'):
        context.user_data['trip_notes'] = text
        context.user_data['awaiting_trip_notes'] = False

        user_id = update.effective_user.id
        start_location = context.user_data['trip_start']
        end_location = context.user_data['trip_end']
        distance = context.user_data['trip_distance']
        date = context.user_data['trip_date']
        duration = context.user_data.get('trip_duration')
        notes = context.user_data['trip_notes']

        db.add_trip(user_id, start_location, end_location, distance, date, duration, notes)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_trips')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Поїздку додано!\n"
            f"📍 {start_location} → {end_location}\n"
            f"🛣️ {distance:.1f} км\n"
            f"📅 {date}",
            reply_markup=reply_markup
        )

    # Handle JSON import
    elif context.user_data.get('awaiting_import_json'):
        context.user_data['awaiting_import_json'] = False

        try:
            db.import_from_json(user_id, text)

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_backup')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "✅ Дані успішно імпортовано!",
                reply_markup=reply_markup
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Помилка імпорту: {str(e)}")

# Skip command handler
async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_maintenance_notes'):
        context.user_data['maintenance_notes'] = None
        context.user_data['awaiting_maintenance_notes'] = False
        context.user_data['awaiting_maintenance_price'] = True

        await update.message.reply_text("Введіть вартість обслуговування в грн (необов'язково, натисніть /skip щоб пропустити):")

    elif context.user_data.get('awaiting_maintenance_price'):
        context.user_data['maintenance_price'] = 0
        context.user_data['awaiting_maintenance_price'] = False

        user_id = update.effective_user.id
        maintenance_type = context.user_data['maintenance_type']
        mileage = context.user_data['maintenance_mileage']
        notes = context.user_data['maintenance_notes']
        price = context.user_data['maintenance_price']

        db.add_maintenance_record(user_id, maintenance_type, mileage, notes, price)

        # Update current mileage if this is higher
        current_mileage = db.get_current_mileage(user_id)
        if current_mileage is None or mileage > current_mileage:
            db.update_mileage(user_id, mileage)

        type_names = {
            'oil': 'Заміна масла',
            'filter': 'Фільтри',
            'valve': 'Клапани',
            'chain': 'Ланцюг',
            'other': 'Інше'
        }

        keyboard = [
            [InlineKeyboardButton(" Головне меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Запис додано!\n"
            f"Тип: {type_names.get(maintenance_type, maintenance_type)}\n"
            f"Пробіг: {mileage} км\n"
            f"Нотатка: {notes}\n"
            f"Вартість: 0.00 грн",
            reply_markup=reply_markup
        )

    elif context.user_data.get('awaiting_knowledge_desc'):
        context.user_data['knowledge_desc'] = None
        context.user_data['awaiting_knowledge_desc'] = False
        context.user_data['awaiting_knowledge_category'] = True

        await update.message.reply_text("Введіть категорію (необов'язково, натисніть /skip щоб пропустити):")

    elif context.user_data.get('awaiting_knowledge_category'):
        context.user_data['knowledge_category'] = None
        context.user_data['awaiting_knowledge_category'] = False

        user_id = update.effective_user.id
        title = context.user_data['knowledge_title']
        url = context.user_data['knowledge_url']
        desc = context.user_data['knowledge_desc']
        category = context.user_data['knowledge_category']

        db.add_knowledge_item(user_id, title, url, desc, None, category)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_knowledge')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Статтю додано!\n📌 {title}\n🔗 {url}",
            reply_markup=reply_markup
        )

    elif context.user_data.get('awaiting_moto_model'):
        context.user_data['moto_model'] = None
        context.user_data['awaiting_moto_model'] = False
        context.user_data['awaiting_moto_year'] = True

        await update.message.reply_text("Введіть рік (необов'язково, натисніть /skip щоб пропустити):")

    elif context.user_data.get('awaiting_moto_year'):
        context.user_data['moto_year'] = None
        context.user_data['awaiting_moto_year'] = False

        user_id = update.effective_user.id
        name = context.user_data['moto_name']
        model = context.user_data.get('moto_model')
        year = context.user_data.get('moto_year')

        db.add_motorcycle(user_id, name, model, year)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_motorcycles')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Мотоцикл додано!\n🏍️ {name}",
            reply_markup=reply_markup
        )

    elif context.user_data.get('awaiting_mot_notes'):
        context.user_data['mot_notes'] = None
        context.user_data['awaiting_mot_notes'] = False

        user_id = update.effective_user.id
        inspection_date = context.user_data['mot_inspection_date']
        next_date = context.user_data['mot_next_date']
        notes = context.user_data['mot_notes']

        db.add_mot_record(user_id, inspection_date, next_date, notes)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_mot')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Запис техогляду додано!\n"
            f"📅 Пройдено: {inspection_date}\n"
            f"📅 Наступний: {next_date}",
            reply_markup=reply_markup
        )

    elif context.user_data.get('awaiting_part_number'):
        context.user_data['part_number'] = None
        context.user_data['awaiting_part_number'] = False
        context.user_data['awaiting_part_quantity'] = True

        await update.message.reply_text("Введіть кількість:")

    elif context.user_data.get('awaiting_part_expiry'):
        context.user_data['part_expiry'] = None
        context.user_data['awaiting_part_expiry'] = False
        context.user_data['awaiting_part_notes'] = True

        await update.message.reply_text("Додайте нотатку (необов'язково, натисніть /skip щоб пропустити):")

    elif context.user_data.get('awaiting_part_notes'):
        context.user_data['part_notes'] = None
        context.user_data['awaiting_part_notes'] = False

        user_id = update.effective_user.id
        name = context.user_data['part_name']
        part_number = context.user_data.get('part_number')
        quantity = context.user_data['part_quantity']
        expiry_date = context.user_data.get('part_expiry')
        notes = context.user_data['part_notes']

        db.add_part(user_id, name, part_number, quantity, None, expiry_date, notes)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_parts')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Запчастину додано!\n📌 {name}\n📦 Кількість: {quantity}",
            reply_markup=reply_markup
        )

    elif context.user_data.get('awaiting_trip_duration'):
        context.user_data['trip_duration'] = None
        context.user_data['awaiting_trip_duration'] = False
        context.user_data['awaiting_trip_notes'] = True

        await update.message.reply_text("Додайте нотатку (необов'язково, натисніть /skip щоб пропустити):")

    elif context.user_data.get('awaiting_trip_notes'):
        context.user_data['trip_notes'] = None
        context.user_data['awaiting_trip_notes'] = False

        user_id = update.effective_user.id
        start_location = context.user_data['trip_start']
        end_location = context.user_data['trip_end']
        distance = context.user_data['trip_distance']
        date = context.user_data['trip_date']
        duration = context.user_data.get('trip_duration')
        notes = context.user_data['trip_notes']

        db.add_trip(user_id, start_location, end_location, distance, date, duration, notes)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='menu_trips')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Поїздку додано!\n"
            f"📍 {start_location} → {end_location}\n"
            f"🛣️ {distance:.1f} км\n"
            f"📅 {date}",
            reply_markup=reply_markup
        )

# CSV Export
async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    records = db.get_maintenance_records(user_id)
    
    if not records:
        query = update.callback_query
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Немає даних для експорту.", reply_markup=reply_markup)
        return
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Дата', 'Тип', 'Пробіг (км)', 'Нотатка', 'Вартість (грн)'])

    for record in records:
        date_str = datetime.fromisoformat(record['date']).strftime('%d.%m.%Y')
        writer.writerow([
            date_str,
            record['type'],
            record['mileage'],
            record['notes'] or '',
            record.get('price', 0) or 0
        ])
    
    output.seek(0)
    
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📤 Експорт даних:\n\n" + output.getvalue() + "\n\nСкопіюйте дані та збережіть в CSV файл.",
        reply_markup=reply_markup
    )

# Reminder functions
async def send_weekly_mileage_reminder(context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_users()
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="📊 Привіт! Не забудь оновити поточний пробіг твого мотоцикла через /mileage"
            )
        except Exception as e:
            logger.error(f"Error sending reminder to user {user_id}: {e}")

async def check_chain_reminders(context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_users()
    for user_id in users:
        current_mileage = db.get_current_mileage(user_id)
        if current_mileage is None:
            continue

        last_chain = db.get_last_maintenance(user_id, 'chain')
        if last_chain:
            km_since_chain = current_mileage - last_chain['mileage']
            if km_since_chain >= 500:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"⚠️ Привіт, пора перевірити ланцюг! "
                             f"Ти проїхав {km_since_chain} км після останнього змащування."
                    )
                except Exception as e:
                    logger.error(f"Error sending chain reminder to user {user_id}: {e}")

async def check_seasonal_reminders(context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime
    current_month = datetime.now().month

    users = db.get_all_users()
    for user_id in users:
        reminders = db.get_all_seasonal_reminders(user_id)

        for reminder in reminders:
            if not reminder['enabled']:
                continue

            message = None
            if reminder['reminder_type'] == 'spring_prep' and current_month == 2:
                message = "🌸 Привіт! Скоро настане весна - час підготувати мотоцикл до сезону!"
            elif reminder['reminder_type'] == 'winter_prep' and current_month == 10:
                message = "❄️ Привіт! Скоро настане зима - час підготувати мотоцикл до зберігання!"

            if message:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message
                    )
                except Exception as e:
                    logger.error(f"Error sending seasonal reminder to user {user_id}: {e}")

async def check_mot_reminders(context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime, timedelta

    users = db.get_all_users()
    for user_id in users:
        next_mot = db.get_next_mot_reminder(user_id)
        if not next_mot:
            continue

        try:
            next_date = datetime.strptime(next_mot['next_inspection_date'], '%d.%m.%Y')
            today = datetime.now()
            days_until = (next_date - today).days

            if days_until <= 30 and days_until > 0:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🔍 Нагадування: Техогляд через {days_until} днів ({next_mot['next_inspection_date']})"
                    )
                except Exception as e:
                    logger.error(f"Error sending MOT reminder to user {user_id}: {e}")
            elif days_until <= 0:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"⚠️ Термін техогляду настав або пройшов! ({next_mot['next_inspection_date']})"
                    )
                except Exception as e:
                    logger.error(f"Error sending MOT reminder to user {user_id}: {e}")
        except ValueError:
            logger.error(f"Invalid date format for MOT reminder: {next_mot['next_inspection_date']}")

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('chain', chain_start))
    application.add_handler(CommandHandler('skip', skip_command))
    
    # Menu button handler
    application.add_handler(CallbackQueryHandler(menu_button_handler))
    
    # Text message handler for menu interactions
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Setup job queue for reminders
    job_queue = application.job_queue
    
    # Weekly mileage reminder
    job_queue.run_repeating(
        send_weekly_mileage_reminder,
        interval=timedelta(weeks=1),
        first=datetime.now() + timedelta(seconds=10)
    )
    
    # Chain reminder check every 6 hours
    job_queue.run_repeating(
        check_chain_reminders,
        interval=timedelta(hours=6),
        first=datetime.now() + timedelta(seconds=30)
    )

    # Seasonal reminder check every day
    job_queue.run_repeating(
        check_seasonal_reminders,
        interval=timedelta(days=1),
        first=datetime.now() + timedelta(seconds=60)
    )

    # MOT reminder check every day
    job_queue.run_repeating(
        check_mot_reminders,
        interval=timedelta(days=1),
        first=datetime.now() + timedelta(seconds=90)
    )
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
