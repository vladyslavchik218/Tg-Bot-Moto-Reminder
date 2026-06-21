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
MILEAGE, MAINTENANCE_TYPE, MAINTENANCE_MILEAGE, MAINTENANCE_NOTES = range(4)
INTERVAL_TYPE, INTERVAL_KM, INTERVAL_DAYS = range(3)

# Initialize database
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

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
                InlineKeyboardButton("� Статистика", callback_data='menu_stats'),
                InlineKeyboardButton("⚙️ Налаштування", callback_data='menu_settings')
            ],
            [
                InlineKeyboardButton("📋 Історія", callback_data='menu_history'),
                InlineKeyboardButton("🔗 Ланцюг", callback_data='menu_chain')
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
        message += f"Всього записів: {stats['total_records']}\n\n"
        message += "За типом обслуговування:\n"
        
        type_names = {
            'oil': '🛢️ Заміна масла',
            'filter': '🔧 Фільтри',
            'valve': '⚙️ Клапани',
            'chain': '🔗 Ланцюг',
            'other': '🔌 Інше'
        }
        
        for maint_type, count in stats['type_counts'].items():
            message += f"• {type_names.get(maint_type, maint_type)}: {count}\n"
        
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
            [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
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
    
    elif callback_data == 'export_csv':
        await export_csv(update, context)

# Handle text messages for menu interactions
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check if user is in any awaiting state
    is_awaiting = (
        context.user_data.get('awaiting_mileage') or
        context.user_data.get('awaiting_maintenance_mileage') or
        context.user_data.get('awaiting_maintenance_notes') or
        context.user_data.get('awaiting_interval_km')
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
        
        user_id = update.effective_user.id
        maintenance_type = context.user_data['maintenance_type']
        mileage = context.user_data['maintenance_mileage']
        notes = context.user_data['maintenance_notes']
        
        record_id = db.add_maintenance_record(user_id, maintenance_type, mileage, notes)
        
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
            f"Нотатка: {notes}",
            reply_markup=reply_markup
        )
    
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

# Skip command handler
async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_maintenance_notes'):
        context.user_data['maintenance_notes'] = None
        context.user_data['awaiting_maintenance_notes'] = False
        
        user_id = update.effective_user.id
        maintenance_type = context.user_data['maintenance_type']
        mileage = context.user_data['maintenance_mileage']
        
        db.add_maintenance_record(user_id, maintenance_type, mileage, None)
        
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
            f"Пробіг: {mileage} км",
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
    
    writer.writerow(['Дата', 'Тип', 'Пробіг (км)', 'Нотатка'])
    
    for record in records:
        date_str = datetime.fromisoformat(record['date']).strftime('%d.%m.%Y')
        writer.writerow([
            date_str,
            record['type'],
            record['mileage'],
            record['notes'] or ''
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
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
