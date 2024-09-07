import logging
import configparser
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import asyncio
from gmail_handler import GmailHandler
from selenium_handler import NetflixLocationUpdate
from message_handler import log_info, log_error

# Leer la configuración desde el archivo ini
config = configparser.ConfigParser()
config.read('config.ini')
telegram_token = config.get('TELEGRAM', 'TelegramToken')
whatsapp_link = "https://wa.me/message/CNIIAESNO45BN1"  # Nuevo enlace de WhatsApp

# Configurar logging
logging.basicConfig(
    filename='status.log',           # Archivo de log
    encoding='utf-8',                # Codificación
    level=logging.INFO,              # Nivel de logging
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del log
    datefmt='%Y-%m-%d %H:%M:%S'      # Formato de fecha y hora
)

# Expresión regular para validar el formato de correo electrónico
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# Función para mostrar el menú principal
async def show_main_menu(update_or_query: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🎬 Consulta tu código Netflix", callback_data='consulta_netflix'),
            InlineKeyboardButton("🛒 Comprar una cuenta aquí", url=whatsapp_link)  # Redirigir al nuevo enlace de WhatsApp
        ],
        [
            InlineKeyboardButton("💬 WhatsApp", url=whatsapp_link),  # Redirigir al nuevo enlace de WhatsApp
            InlineKeyboardButton("ℹ️ Ayuda", callback_data='ayuda')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Si es un mensaje normal
    if update_or_query.message:
        await update_or_query.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)
    # Si es un callback query
    elif update_or_query.callback_query:
        await update_or_query.callback_query.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)

# Manejador del comando /start
async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    await update.message.reply_text(f"👋 ¡Hola {user.first_name}! Bienvenido al bot de verificación de correos de Netflix.")
    await show_main_menu(update, context)

# Función para manejar los botones interactivos
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "consulta_netflix":
        await query.edit_message_text(text="🔎 Por favor, ingresa tu correo para consultar tu código Netflix.")
        context.user_data["waiting_for_email"] = True  # Establecer la espera del correo
        # Iniciar el tiempo de espera de 30 segundos
        asyncio.create_task(wait_for_email_timeout(update, context))
    elif query.data == "ayuda":
        await show_help(query, context)

# Función para manejar el tiempo de espera de 30 segundos
async def wait_for_email_timeout(update: Update, context: CallbackContext) -> None:
    await asyncio.sleep(30)  # Esperar 30 segundos
    if context.user_data.get("waiting_for_email", False):  # Verificar si aún estamos esperando un correo
        # Verificar si el contexto es un mensaje o una callback query y enviar la respuesta adecuada
        if update.message:
            await update.message.reply_text("⏳ No se recibió ningún correo válido en los últimos 30 segundos.")
        elif update.callback_query:
            await update.callback_query.message.reply_text("⏳ No se recibió ningún correo válido en los últimos 30 segundos.")
        
        context.user_data["waiting_for_email"] = False  # Terminar la espera
        await show_main_menu(update, context)

# Función para mostrar la ayuda
async def show_help(query: Update, context: CallbackContext) -> None:
    # Mensaje de ayuda actualizado
    help_text = (
        "ℹ️ **Ayuda del Bot de Netflix**\n\n"
        "📌 Para obtener tu código de verificación de Netflix, sigue estos pasos:\n"
        "1️⃣ Usa el botón *Consulta tu código Netflix*.\n"
        "2️⃣ Ingresa un correo electrónico con el formato correcto: *correo@dominio.com*.\n"
        "3️⃣ Si el correo está registrado, el bot lo verificará y te proporcionará el enlace correspondiente.\n\n"
        "⚠️ Si no recibimos un correo en los próximos 30 segundos, el proceso se cancelará y volverás al menú principal.\n\n"
        "💬 Para más asistencia, también puedes contactarnos a través de WhatsApp."
    )
    await query.edit_message_text(help_text)

    # Esperar 5 segundos y luego regresar automáticamente al menú principal
    await asyncio.sleep(5)
    await show_main_menu(query, context)

# Función para manejar el correo electrónico
async def handle_email(update: Update, context: CallbackContext) -> None:
    # Verificar si el bot está esperando un correo
    if "waiting_for_email" not in context.user_data or not context.user_data["waiting_for_email"]:
        # Si no estamos esperando un correo, se muestra un mensaje de error
        await update.message.reply_text("⚠️ No se está esperando un correo en este momento. Usa el menú para seleccionar una opción.")
        await show_main_menu(update, context)
        return

    user_email = update.message.text

    # Verificación del formato de correo electrónico
    if not re.match(EMAIL_REGEX, user_email):
        await update.message.reply_text("❌ El correo ingresado no es válido. Por favor, ingresa un correo con el formato correcto (correo@dominio.com).")
        return  # Volver a solicitar el correo

    gmail_handler = GmailHandler(config_path='config.ini')

    # Verificación del correo electrónico
    if gmail_handler.fetch_emails_for_user(user_email):
        await update.message.reply_text(f"📧 Recibimos tu correo {user_email}. Procesando tu solicitud, por favor espera unos momentos...")
        # Si el correo es válido, proceder con la cuenta de Netflix correspondiente
        netflix_updater = NetflixLocationUpdate(config_path='config.ini')
        netflix_updater.process_netflix_for_user(user_email)
        await update.message.reply_text("✔️ Verificación completada con éxito.")
    else:
        # Si el correo no es válido, mostramos un mensaje de error y regresamos al menú principal
        await update.message.reply_text("❌ El correo proporcionado no está registrado. Por favor, verifica que está correctamente escrito.")
    
    context.user_data["waiting_for_email"] = False  # Ya no estamos esperando un correo
    await show_main_menu(update, context)

# Manejador de errores
async def error_handler(update: Update, context: CallbackContext) -> None:
    log_error(context.error)
    if update.message:
        await update.message.reply_text("⚠️ Ocurrió un error. Por favor, inténtalo más tarde.")

# Iniciar el bot
if __name__ == '__main__':
    # Usar ApplicationBuilder en lugar de Updater
    application = ApplicationBuilder().token(telegram_token).build()

    # Registro de los manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email))
    application.add_error_handler(error_handler)

    # Iniciar el bot
    application.run_polling()
