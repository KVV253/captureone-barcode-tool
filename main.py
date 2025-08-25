import socket
import logging
import time

import barcode
from barcode.writer import ImageWriter
import datetime
from datetime import datetime
import os
import sys
from PIL import Image
from io import BytesIO

SOCKET_PATH = '/tmp/barcode_daemon_socket'

# Setting up the logger
logger = logging.getLogger('barcode_app')
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

handler = logging.FileHandler('/tmp/barcode_daemon.log')
formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info('Logger configured.')


class BarcodeGenerator:
    def __init__(self):
        self.target_directory = 'None'
        self.barcode_data = 'None'

        self.barcode_image = None
        self.final_image_path = 'None'
        self.formatted_time = None

        self.font_path = None

        try:
            if hasattr(sys, '_MEIPASS'):
                self.font_path = os.path.join(sys._MEIPASS, 'DejaVuSans-Bold.ttf')
            else:
                self.font_path = 'DejaVuSans-Bold.ttf'
            if not os.path.exists(self.font_path):
                logger.warning(f'Font file not found: {self.font_path}')
        except Exception as ex:
            logger.exception(f'Failed to load font: {ex}')

        self.background_color = (255, 255, 255)

        logger.info('BarcodeGenerator initialized.')

    def set_params_and_go(self, target_directory: str, barcode_data: str, next_img_name: str = 'noname_0.jpg'):
        """Accepts the operating parameters and starts the execution chain"""
        self.barcode_data = barcode_data
        self.target_directory = target_directory
        self.final_image_path = os.path.join(target_directory, f'{next_img_name}.jpg')
        self.formatted_time = datetime.now().strftime('%Y:%m:%d %H:%M:%S')
        self.run_process()

    def run_process(self):
        """Initiates a sequential call of functions"""
        self.create_barcode_img_in_memory()
        self.create_barcode_img_in_folder()

    def create_barcode_img_in_memory(self):
        """Creates a barcode in memory"""
        try:
            barcode_class = barcode.get_barcode_class('code128')
            barcode_obj = barcode_class(self.barcode_data, writer=ImageWriter())
            barcode_obj.writer.font_path = self.font_path
            barcode_image_io = BytesIO()
            barcode_obj.write(barcode_image_io)
        except Exception as e:
            logger.exception(f'Failed to render barcode to memory: {e}')
            return

        try:
            barcode_image_io.seek(0)
            self.barcode_image = Image.open(barcode_image_io)
        except Exception as e:
            logger.exception(f'Failed to open barcode image from buffer: {e}')

    def create_barcode_img_in_folder(self):
        """Creates a barcode image in the working folder"""
        try:
            # Creating a canvas
            canvas = Image.new('RGB', (474, 260), self.background_color)
            canvas.paste(self.barcode_image, (10, 10))

            # Saving the final image
            canvas.save(self.final_image_path, 'JPEG', quality=90)
            logger.info(f'Saved barcode image to {os.path.normpath(self.final_image_path)}')

        except FileNotFoundError as ex:
            logger.error(f'File not found: {ex.filename}')
        except OSError as ex:
            logger.error(f'OS error while saving barcode image: {ex}')
        except AttributeError as ex:
            logger.error(f'Attribute error while building barcode image: {ex}')
        except TypeError as ex:
            logger.error(f'Type error while building barcode image: {ex}')
        except Exception as ex:
            logger.exception(f'Unexpected error while saving barcode image: {ex}')


class BarcodeDaemon:
    def __init__(self):
        try:
            logger.info('Initializing BarcodeGenerator')
            self.barcode_generator = BarcodeGenerator()
        except Exception as e:
            logger.exception(f'Failed to initialize BarcodeGenerator: {e}')

        self.server = None  # Initialize server as None

    def run(self):
        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
                logger.info(f'Removed stale socket: {SOCKET_PATH}')
            except Exception as e:
                logger.error(f'Failed to delete stale socket {SOCKET_PATH}: {e}')

        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            self.server.bind(SOCKET_PATH)
            self.server.listen(1)
            logger.info(f'Listening on {SOCKET_PATH}')

            while True:
                conn, addr = self.server.accept()
                data = conn.recv(1024).decode('utf-8').strip()

                if data:
                    if data == 'kill process':
                        self.shutdown()
                    folder_path, barcode_data, next_img_name = data.split(",", 2)
                    logger.info(f'Request: folder="{folder_path}", barcode="{barcode_data}", name="{next_img_name}"')
                    try:
                        self.barcode_generator.set_params_and_go(
                            target_directory=folder_path,
                            barcode_data=barcode_data,
                            next_img_name=next_img_name
                        )
                    except Exception as e:
                        logger.exception(f'Failed to generate barcode image: {e}')
                conn.close()
                time.sleep(0.1)
        except Exception as e:
            logger.exception(f'Daemon error: {e}')
        finally:
            if self.server:
                self.server.close()
                logger.info(f'Closed socket: {SOCKET_PATH}')
            if os.path.exists(SOCKET_PATH):
                try:
                    os.remove(SOCKET_PATH)
                    logger.info(f'Removed socket file: {SOCKET_PATH}')
                except Exception as e:
                    logger.error(f'Failed to delete socket file {SOCKET_PATH}: {e}')

    def shutdown(self):
        logger.info('Shutdown requested ("kill process").')
        if self.server:
            self.server.close()
            logger.info(f'Closed socket: {SOCKET_PATH}')
        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
                logger.info(f'Removed socket file: {SOCKET_PATH}')
            except Exception as e:
                logger.error(f'Failed to delete socket file {SOCKET_PATH}: {e}')
        sys.exit(0)


if __name__ == '__main__':
    try:
        logger.info("Starting BarcodeDaemon")
        daemon = BarcodeDaemon()
        daemon.run()
    except Exception as e:
        logger.exception(f'Daemon startup error: {e}')
