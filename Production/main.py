#!/usr/bin/env python3
"""
Lume an E-Reader for Raspberry Pi Zero 2W with E-ink Display
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
import fitz  # PyMuPDF
from ebooklib import epub
from bs4 import BeautifulSoup

class BookReader:
    def display_page(self): pass
    def next_page(self): pass
    def prev_page(self): pass


class TextBookReader(BookReader):
    def __init__(self, file_path, display):
        self.file_path = file_path
        self.display = display
        self.current_page = 0
        self.pages = []
        self.chars_per_line = 80
        self.lines_per_page = 20
        self.load_book()

    def load_book(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.split('\n')
            current = []
            for line in lines:
                while len(line) > self.chars_per_line:
                    current.append(line[:self.chars_per_line])
                    line = line[self.chars_per_line:]
                current.append(line)
                if len(current) >= self.lines_per_page:
                    self.pages.append('\n'.join(current))
                    current = []
            if current:
                self.pages.append('\n'.join(current))
        except Exception as e:
            logging.error(f"Error loading TXT: {e}")
            self.pages = [f"Error loading book: {e}"]

    def display_page(self):
        if not self.pages: return
        self.display.buffer = Image.new('1', (self.display.WIDTH, self.display.HEIGHT), 1)
        y = 20
        for line in self.pages[self.current_page].split('\n'):
            self.display.draw_text(line, 10, y)
            y += 20
        self.display.draw_text(f"Page {self.current_page+1}/{len(self.pages)}", 10, self.display.HEIGHT - 25)
        self.display.display_image()

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.display_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()


class PDFBookReader(BookReader):
    def __init__(self, file_path, display):
        self.display = display
        self.doc = fitz.open(file_path)
        self.current_page = 0
        self.total_pages = len(self.doc)

    def display_page(self):
        page = self.doc.load_page(self.current_page)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        bw_image = image.convert("1").resize((self.display.WIDTH, self.display.HEIGHT))
        self.display.display_image(bw_image)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()


class EPUBBookReader(BookReader):
    def __init__(self, file_path, display):
        self.display = display
        self.book = epub.read_epub(file_path)
        self.pages = []
        self.current_page = 0
        self.parse_book()

    def parse_book(self):
        for item in self.book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                text = soup.get_text()
                self.pages.extend(self.paginate(text))

    def paginate(self, content):
        lines = content.split('\n')
        pages, current = [], []
        for line in lines:
            wrapped = [line[i:i+80] for i in range(0, len(line), 80)]
            for wline in wrapped:
                current.append(wline)
                if len(current) == 20:
                    pages.append('\n'.join(current))
                    current = []
        if current:
            pages.append('\n'.join(current))
        return pages

    def display_page(self):
        if not self.pages: return
        self.display.buffer = Image.new('1', (self.display.WIDTH, self.display.HEIGHT), 1)
        y = 20
        for line in self.pages[self.current_page].split('\n'):
            self.display.draw_text(line, 10, y)
            y += 20
        self.display.draw_text(f"Page {self.current_page+1}/{len(self.pages)}", 10, self.display.HEIGHT - 25)
        self.display.display_image()

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.display_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()



    def open_book(self):
        file_path = self.file_manager.get_file_path(self.selected_index)
        if file_path is None:
            return
        try:
            ext = file_path.suffix.lower()
            if ext == '.txt':
                self.current_book = TextBookReader(file_path, self.display)
            elif ext == '.pdf':
                self.current_book = PDFBookReader(file_path, self.display)
            elif ext == '.epub':
                self.current_book = EPUBBookReader(file_path, self.display)
            else:
                logging.warning(f"Unsupported format: {ext}")
                return

            if str(file_path) == self.settings.get('last_book'):
                self.current_book.current_page = self.settings.get('last_page', 0)

            self.current_book.display_page()
            self.current_menu = 'reading'

            logging.info(f"Opened book: {file_path.name}")
        except Exception as e:
            logging.error(f"Error opening book: {e}")
