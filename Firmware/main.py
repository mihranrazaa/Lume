#!/usr/bin/env python3
"""
Simple E-Reader for Raspberry Pi Zero 2W with E-ink Display
A basic but functional e-reader implementation focusing on core features.
"""

import RPi.GPIO as GPIO
import time
import os
import json
import logging
from PIL import Image, ImageDraw, ImageFont
import threading
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/ereader.log'),
        logging.StreamHandler()
    ]
)


class EInkDisplay:
    """Simple E-ink display handler for 7.5-inch display"""

    def __init__(self):
        # GPIO pins for E-ink display
        self.CS_PIN = 8
        self.DC_PIN = 25
        self.RST_PIN = 18
        self.BUSY_PIN = 17

        # Display dimensions (adjust for your specific display)
        self.WIDTH = 800
        self.HEIGHT = 480

        # Initialize SPI and GPIO
        self.setup_gpio()

        # Current display buffer
        self.buffer = Image.new('1', (self.WIDTH, self.HEIGHT), 1)  # 1 = white

        # Load default font
        try:
            self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
            self.font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        except:
            self.font = ImageFont.load_default()
            self.font_large = ImageFont.load_default()

    def setup_gpio(self):
        """Initialize GPIO pins for E-ink display"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.CS_PIN, GPIO.OUT)
        GPIO.setup(self.DC_PIN, GPIO.OUT)
        GPIO.setup(self.RST_PIN, GPIO.OUT)
        GPIO.setup(self.BUSY_PIN, GPIO.IN)

        # Initialize SPI
        import spidev
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # SPI0, CE0
        self.spi.max_speed_hz = 4000000
        self.spi.mode = 0

    def spi_write(self, data):
        """Write data via SPI"""
        GPIO.output(self.CS_PIN, GPIO.LOW)
        if isinstance(data, int):
            data = [data]
        self.spi.writebytes(data)
        GPIO.output(self.CS_PIN, GPIO.HIGH)

    def write_command(self, command):
        """Write command to display"""
        GPIO.output(self.DC_PIN, GPIO.LOW)
        self.spi_write(command)

    def write_data(self, data):
        """Write data to display"""
        GPIO.output(self.DC_PIN, GPIO.HIGH)
        self.spi_write(data)

    def reset(self):
        """Reset the display"""
        GPIO.output(self.RST_PIN, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(self.RST_PIN, GPIO.HIGH)
        time.sleep(0.2)

    def wait_until_idle(self):
        """Wait until display is not busy"""
        while GPIO.input(self.BUSY_PIN) == GPIO.HIGH:
            time.sleep(0.01)

    def init_display(self):
        """Initialize the e-ink display"""
        self.reset()
        self.wait_until_idle()

        # Basic initialization sequence (simplified)
        # Note: This is a generic sequence - you may need to adjust for your specific display
        self.write_command(0x01)  # Power setting
        self.write_data([0x37, 0x00])

        self.write_command(0x00)  # Panel setting
        self.write_data([0xCF, 0x08])

        self.write_command(0x06)  # Booster soft start
        self.write_data([0xc7, 0xcc, 0x28])

        self.write_command(0x04)  # Power on
        self.wait_until_idle()

        logging.info("E-ink display initialized")

    def display_image(self, image=None):
        """Display image on screen"""
        if image is None:
            image = self.buffer

        # Convert to 1-bit if needed
        if image.mode != '1':
            image = image.convert('1')

        # Resize to fit screen
        image = image.resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)

        # Convert to bytes
        buf = []
        for y in range(self.HEIGHT):
            for x in range(0, self.WIDTH, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < self.WIDTH:
                        pixel = image.getpixel((x + bit, y))
                        if pixel == 0:  # Black pixel
                            byte |= (0x80 >> bit)
                buf.append(byte)

        # Send to display
        self.write_command(0x13)  # Write image data
        self.write_data(buf)

        self.write_command(0x12)  # Display refresh
        self.wait_until_idle()

        logging.info("Display updated")

    def clear_screen(self):
        """Clear the screen"""
        self.buffer = Image.new('1', (self.WIDTH, self.HEIGHT), 1)
        self.display_image()

    def draw_text(self, text, x, y, font=None):
        """Draw text on buffer"""
        if font is None:
            font = self.font

        draw = ImageDraw.Draw(self.buffer)
        draw.text((x, y), text, font=font, fill=0)  # 0 = black

    def draw_menu(self, title, items, selected_index):
        """Draw a menu on screen"""
        self.buffer = Image.new('1', (self.WIDTH, self.HEIGHT), 1)
        draw = ImageDraw.Draw(self.buffer)

        # Title
        draw.text((10, 10), title, font=self.font_large, fill=0)
        draw.line((10, 40, self.WIDTH - 10, 40), fill=0)

        # Menu items
        y_start = 60
        for i, item in enumerate(items):
            y = y_start + i * 30
            if i == selected_index:
                # Highlight selected item
                draw.rectangle((5, y - 5, self.WIDTH - 5, y + 25), fill=0)
                draw.text((10, y), item, font=self.font, fill=1)  # White text
            else:
                draw.text((10, y), item, font=self.font, fill=0)  # Black text

        self.display_image()


class InputHandler:
    """Handle joystick and button inputs"""

    def __init__(self):
        # GPIO pins
        self.JOYSTICK_UP = 22
        self.JOYSTICK_DOWN = 23
        self.JOYSTICK_LEFT = 5
        self.JOYSTICK_RIGHT = 6
        self.JOYSTICK_CENTER = 12

        self.BUTTON_1 = 4  # Menu
        self.BUTTON_2 = 14  # Back
        self.BUTTON_3 = 15  # Bookmark
        self.BUTTON_4 = 27  # Settings

        # Setup GPIO
        self.setup_gpio()

        # Debouncing
        self.last_press_time = {}
        self.debounce_delay = 0.2

        # Event handlers
        self.event_handlers = {}

    def setup_gpio(self):
        """Setup GPIO pins for inputs"""
        pins = [
            self.JOYSTICK_UP, self.JOYSTICK_DOWN, self.JOYSTICK_LEFT,
            self.JOYSTICK_RIGHT, self.JOYSTICK_CENTER,
            self.BUTTON_1, self.BUTTON_2, self.BUTTON_3, self.BUTTON_4
        ]

        for pin in pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.handle_input, bouncetime=200)

    def handle_input(self, pin):
        """Handle GPIO input with debouncing"""
        current_time = time.time()

        if pin in self.last_press_time:
            if current_time - self.last_press_time[pin] < self.debounce_delay:
                return

        self.last_press_time[pin] = current_time

        # Map pin to event
        event_map = {
            self.JOYSTICK_UP: 'up',
            self.JOYSTICK_DOWN: 'down',
            self.JOYSTICK_LEFT: 'left',
            self.JOYSTICK_RIGHT: 'right',
            self.JOYSTICK_CENTER: 'select',
            self.BUTTON_1: 'menu',
            self.BUTTON_2: 'back',
            self.BUTTON_3: 'bookmark',
            self.BUTTON_4: 'settings'
        }

        event = event_map.get(pin)
        if event and event in self.event_handlers:
            self.event_handlers[event]()

    def set_handler(self, event, handler):
        """Set event handler"""
        self.event_handlers[event] = handler


class FileManager:
    """Manage e-book files"""

    def __init__(self, books_dir="/home/pi/books"):
        self.books_dir = Path(books_dir)
        self.books_dir.mkdir(exist_ok=True)

        self.supported_formats = ['.txt', '.pdf', '.epub']
        self.current_files = []
        self.refresh_files()

    def refresh_files(self):
        """Refresh the file list"""
        self.current_files = []

        for file_path in self.books_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                self.current_files.append(file_path)

        self.current_files.sort(key=lambda x: x.name.lower())
        logging.info(f"Found {len(self.current_files)} books")

    def get_file_list(self):
        """Get list of book files"""
        return [f.name for f in self.current_files]

    def get_file_path(self, index):
        """Get full path of file by index"""
        if 0 <= index < len(self.current_files):
            return self.current_files[index]
        return None


class BookReader:
    """Simple book reader for text files"""

    def __init__(self, file_path, display):
        self.file_path = file_path
        self.display = display
        self.current_page = 0
        self.pages = []
        self.chars_per_line = 80
        self.lines_per_page = 20

        self.load_book()

    def load_book(self):
        """Load and paginate book content"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple text pagination
            lines = content.split('\n')
            current_page_lines = []

            for line in lines:
                # Wrap long lines
                while len(line) > self.chars_per_line:
                    current_page_lines.append(line[:self.chars_per_line])
                    line = line[self.chars_per_line:]

                current_page_lines.append(line)

                # Check if page is full
                if len(current_page_lines) >= self.lines_per_page:
                    self.pages.append('\n'.join(current_page_lines))
                    current_page_lines = []

            # Add remaining lines as last page
            if current_page_lines:
                self.pages.append('\n'.join(current_page_lines))

            logging.info(f"Book loaded: {len(self.pages)} pages")

        except Exception as e:
            logging.error(f"Error loading book: {e}")
            self.pages = [f"Error loading book: {e}"]

    def display_page(self):
        """Display current page"""
        if not self.pages:
            return

        page_content = self.pages[self.current_page]

        # Clear screen and draw page
        self.display.buffer = Image.new('1', (self.display.WIDTH, self.display.HEIGHT), 1)

        # Draw page content
        lines = page_content.split('\n')
        y = 20

        for line in lines:
            if y > self.display.HEIGHT - 30:
                break
            self.display.draw_text(line, 10, y)
            y += 20

        # Draw page info
        page_info = f"Page {self.current_page + 1} of {len(self.pages)}"
        self.display.draw_text(page_info, 10, self.display.HEIGHT - 25)

        self.display.display_image()

    def next_page(self):
        """Go to next page"""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.display_page()
            return True
        return False

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()
            return True
        return False


class EReader:
    """Main E-Reader application"""

    def __init__(self):
        self.display = EInkDisplay()
        self.input_handler = InputHandler()
        self.file_manager = FileManager()

        # Application state
        self.current_menu = 'main'
        self.selected_index = 0
        self.current_book = None
        self.running = True

        # Settings
        self.settings = self.load_settings()

        # Setup input handlers
        self.setup_input_handlers()

        logging.info("E-Reader initialized")

    def load_settings(self):
        """Load settings from file"""
        settings_file = '/home/pi/ereader_settings.json'
        default_settings = {
            'last_book': None,
            'last_page': 0,
            'font_size': 16
        }

        try:
            with open(settings_file, 'r') as f:
                return json.load(f)
        except:
            return default_settings

    def save_settings(self):
        """Save settings to file"""
        settings_file = '/home/pi/ereader_settings.json'
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")

    def setup_input_handlers(self):
        """Setup input event handlers"""
        self.input_handler.set_handler('up', self.handle_up)
        self.input_handler.set_handler('down', self.handle_down)
        self.input_handler.set_handler('left', self.handle_left)
        self.input_handler.set_handler('right', self.handle_right)
        self.input_handler.set_handler('select', self.handle_select)
        self.input_handler.set_handler('menu', self.handle_menu)
        self.input_handler.set_handler('back', self.handle_back)
        self.input_handler.set_handler('bookmark', self.handle_bookmark)
        self.input_handler.set_handler('settings', self.handle_settings)

    def handle_up(self):
        """Handle up joystick"""
        if self.current_menu == 'main':
            if self.selected_index > 0:
                self.selected_index -= 1
                self.show_main_menu()
        elif self.current_menu == 'reading':
            if self.current_book:
                self.current_book.prev_page()

    def handle_down(self):
        """Handle down joystick"""
        if self.current_menu == 'main':
            files = self.file_manager.get_file_list()
            if self.selected_index < len(files) - 1:
                self.selected_index += 1
                self.show_main_menu()
        elif self.current_menu == 'reading':
            if self.current_book:
                self.current_book.next_page()

    def handle_left(self):
        """Handle left joystick"""
        if self.current_menu == 'reading' and self.current_book:
            self.current_book.prev_page()

    def handle_right(self):
        """Handle right joystick"""
        if self.current_menu == 'reading' and self.current_book:
            self.current_book.next_page()

    def handle_select(self):
        """Handle center joystick (select)"""
        if self.current_menu == 'main':
            self.open_book()

    def handle_menu(self):
        """Handle menu button"""
        if self.current_menu == 'reading':
            self.current_menu = 'main'
            self.show_main_menu()

    def handle_back(self):
        """Handle back button"""
        if self.current_menu == 'reading':
            self.current_menu = 'main'
            self.show_main_menu()

    def handle_bookmark(self):
        """Handle bookmark button"""
        if self.current_menu == 'reading' and self.current_book:
            # Save current position
            self.settings['last_book'] = str(self.current_book.file_path)
            self.settings['last_page'] = self.current_book.current_page
            self.save_settings()
            logging.info(f"Bookmarked page {self.current_book.current_page}")

    def handle_settings(self):
        """Handle settings button"""
        # Simple settings toggle (can be expanded)
        pass

    def show_main_menu(self):
        """Show main menu"""
        self.file_manager.refresh_files()
        files = self.file_manager.get_file_list()

        if not files:
            files = ["No books found"]

        self.display.draw_menu("E-Reader", files, self.selected_index)
        self.current_menu = 'main'

    def open_book(self):
        """Open selected book"""
        file_path = self.file_manager.get_file_path(self.selected_index)

        if file_path is None:
            return

        try:
            # Only handle .txt files for now (can be extended)
            if file_path.suffix.lower() == '.txt':
                self.current_book = BookReader(file_path, self.display)

                # Resume from bookmark if available
                if str(file_path) == self.settings.get('last_book'):
                    self.current_book.current_page = self.settings.get('last_page', 0)

                self.current_book.display_page()
                self.current_menu = 'reading'

                logging.info(f"Opened book: {file_path.name}")
            else:
                logging.warning(f"Unsupported format: {file_path.suffix}")

        except Exception as e:
            logging.error(f"Error opening book: {e}")

    def run(self):
        """Main application loop"""
        try:
            # Initialize display
            self.display.init_display()

            # Show main menu
            self.show_main_menu()

            # Main loop
            while self.running:
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage

        except KeyboardInterrupt:
            logging.info("Shutting down...")
        except Exception as e:
            logging.error(f"Application error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.save_settings()
        GPIO.cleanup()
        logging.info("Cleanup completed")


def main():
    """Main entry point"""
    logging.info("Starting E-Reader...")

    # Create and run the e-reader
    ereader = EReader()
    ereader.run()


if __name__ == "__main__":
    main()