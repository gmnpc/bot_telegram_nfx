import logging
import configparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class NetflixLocationUpdate:
    _config: configparser.ConfigParser
    _driver: webdriver.Chrome
    _mail: object  # Tipo específico de IMAP o conexión de correo
    _mailbox_name: str
    _move_to_mailbox: bool
    _move_to_mailbox_name: str

    def __init__(self, config_path: str):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        if 'EMAIL' not in self._config:
            raise ValueError(f'EMAIL section does not exist in {config_path} file.')

        self._mailbox_name = self._config.get('EMAIL', 'Mailbox', fallback='INBOX')
        self._move_to_mailbox = self._config.getboolean('GENERAL', 'MoveEmailsToMailbox', fallback=False)
        self._move_to_mailbox_name = self._config.get('GENERAL', 'MailboxName', fallback='Netflix')

        # Email config
        imap_server = self._config.get('EMAIL', 'ImapServer')
        imap_port = self._config.getint('EMAIL', 'ImapPort')
        imap_username = self._config.get('EMAIL', 'Username')
        imap_password = self._config.get('EMAIL', 'Password')

        # Inicializar WebDriver correctamente utilizando webdriver_manager para obtener ChromeDriver
        self._driver = self.__init_webdriver()

    @staticmethod
    def __init_webdriver() -> webdriver.Chrome:
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Usar ChromeService y ChromeDriverManager para inicializar el WebDriver correctamente
            service = ChromeService(executable_path=ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        except Exception as e:
            logging.error(f"Error al inicializar WebDriver: {str(e)}")
            return None

    def close(self):
        # Apagar WebDriver y cerrar el servicio de correo
        if self._driver:
            self._driver.quit()
        if self._mail:
            self._mail.logout()
        logging.info('Conexión cerrada correctamente.')

    def __del__(self):
        # Cerrar WebDriver solo si está inicializado
        if hasattr(self, '_driver') and self._driver:
            self._driver.quit()

    def process_netflix_for_user(self, user_email):
        # Aquí es donde procesarías la lógica de Netflix para el usuario
        # Placeholder para el procesamiento
        logging.info(f"Procesando solicitud para el usuario: {user_email}")
        # Simular la lógica de procesamiento de Netflix...
        # Al finalizar, cerrar la conexión
        self.close()
