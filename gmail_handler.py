import imaplib
import email
import quopri  # Importamos quopri para manejar quoted-printable encoding
import configparser
from message_handler import log_info, log_error, send_invalid_email_message

class GmailHandler:
    def __init__(self, config_path='config.ini'):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self.imap_server = self._config.get('EMAIL', 'ImapServer')
        self.imap_port = self._config.getint('EMAIL', 'ImapPort')
        self.mailbox_name = self._config.get('EMAIL', 'Mailbox', fallback='INBOX')

    def __init_mails(self, username, password):
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(username, password)
            log_info(f"Conexión exitosa al servidor IMAP {self.imap_server} con el usuario {username}")
            return mail
        except Exception as e:
            log_error(f"Error en la conexión IMAP para el usuario {username}: {str(e)}")
            return None

    def fetch_emails_for_user(self, user_email):
        # Verificar si el correo proporcionado corresponde a alguna cuenta precargada
        i = 1
        while True:
            username_key = f'Username{i}'
            password_key = f'Password{i}'

            # Verificar si las claves existen en el archivo config
            if not self._config.has_option('EMAIL', username_key) or not self._config.has_option('EMAIL', password_key):
                log_info(f"No se encontró {username_key} en la configuración. Finalizando la búsqueda de cuentas.")
                break

            username = self._config.get('EMAIL', username_key)
            password = self._config.get('EMAIL', password_key)

            if username == user_email:  # Verifica si el correo proporcionado corresponde
                log_info(f"Procesando correos para el usuario {user_email}...")
                mail = self.__init_mails(username, password)

                if mail:
                    try:
                        mail.select(self.mailbox_name)
                        search_criteria = '(FROM "info@account.netflix.com")'
                        result, data = mail.search(None, search_criteria)
                        email_ids = data[0].split()

                        if not email_ids:
                            log_info(f"No se encontraron correos de Netflix en la cuenta {username}.")
                            return

                        for email_id in reversed(email_ids):
                            result, data = mail.fetch(email_id, '(RFC822)')
                            raw_email = data[0][1]
                            parsed_email = email.message_from_bytes(raw_email)

                            for part in parsed_email.walk():
                                if part.get_content_type() == "text/plain":
                                    # Decodificar el contenido quoted-printable
                                    body = quopri.decodestring(part.get_payload()).decode('utf-8')
                                    log_info(f"Correo procesado, ID: {email_id}, cuenta: {username}")
                                    if "netflix" in body.lower():
                                        link = self.extract_link(body)
                                        log_info(f"Enlace de Netflix encontrado para {username}: {link}")
                                        return link  # Detener el bucle al encontrar el correo

                    except Exception as e:
                        log_error(f"Error al procesar los correos para {username}: {str(e)}")
                return True

            i += 1  # Incrementar el índice para la siguiente cuenta

        # Si no se encuentra el correo en la lista precargada
        send_invalid_email_message(user_email)
        return False

    def extract_link(self, body):
        # Buscar el enlace que contiene "update-primary-location" para extraer el link de aprobación
        start_idx = body.find("https://www.netflix.com/account/update-primary-location")
        if start_idx == -1:
            return None

        end_idx = body.find('"', start_idx)  # Buscar el cierre del enlace
        if end_idx == -1:
            end_idx = len(body)  # Si no encuentra comillas, tomar hasta el final del body

        return body[start_idx:end_idx]

    def close(self, mail):
        if mail:
            mail.logout()
