import logging

# Configuración básica de logging
logging.basicConfig(
    filename='status.log',           # El archivo donde se almacenarán los logs
    encoding='utf-8',                # Codificación del archivo
    level=logging.INFO,              # Nivel de log (INFO, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato de los mensajes de log
    datefmt='%Y-%m-%d %H:%M:%S'      # Formato de la fecha y hora
)

def send_welcome_message():
    print("👋 ¡Hola! Bienvenido al bot de verificación de correos de Netflix.")

def log_info(message):
    logging.info(message)

def log_error(e):
    logging.error(f"Error: {str(e)}")
    print("😓 Hubo un problema, revisa los logs para más detalles.")

def send_invalid_email_message(user_email):
    """
    Envia un mensaje indicando que el correo proporcionado no está registrado.
    """
    print(f"📧 El correo {user_email} no está registrado en nuestra plataforma. Por favor, verifica tu correo.")
