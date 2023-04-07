import sys
import os
import json
import datetime
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QTableWidget, QTableView, QTableWidgetItem, QVBoxLayout, QPushButton, QLineEdit, QLabel, QWidget, QHeaderView, QTextEdit
from PyQt5.QtCore import QFileSystemWatcher, Qt
import logging
from PyQt5.QtCore import QTimer


logging.basicConfig(filename='debug.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def split_and_join_with_newlines(text, block_length):
    words = text.split()
    blocks = []
    current_block = ""
    for i, word in enumerate(words):
        if len(current_block) + len(word) > block_length:
            blocks.append(current_block.strip())
            current_block = ""
        current_block += " " + word
        if i == len(words) - 1:
            blocks.append(current_block.strip())
    for i in range(1, len(blocks)):
        blocks[i] = "    " + blocks[i]
    return "\n".join(blocks)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load stylesheet from external file
        with open(resource_path("style.css"), "r") as file:
            self.setStyleSheet(file.read())

        self.setWindowTitle("Moon+ Reader Page Position Viewer")
        self.resize(1100, 600)  # Set the default size of the app

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.search_files)

        self.layout.addWidget(self.search_label)
        self.layout.addWidget(self.search_input)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["Filename", "Extension", "Page", "Progress", "Created Date"])
        self.table_widget.setSortingEnabled(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.setWordWrap(True)  # Enable word-wrap for table cells
        self.table_widget.setEditTriggers(QTableView.NoEditTriggers)

        self.layout.addWidget(self.table_widget)

        self.path_label = QLabel("Selected Folder:")
        self.path_text = QLabel()

        self.layout.addWidget(self.path_label)
        self.layout.addWidget(self.path_text)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)

        self.layout.addWidget(self.browse_button)

        # File system watcher to monitor file changes
        self.file_system_watcher = QFileSystemWatcher()
        # self.file_system_watcher.directoryChanged.connect(self.load_files)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(2000)  # delay of 1 second
        self.file_system_watcher.directoryChanged.connect(self.on_directory_changed)

        self.load_config()

    def on_directory_changed(self, directory):
        self.timer.start()
        self.timer.timeout.connect(lambda: self.load_files(directory))

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.file_system_watcher.addPath(folder_path)  # Add the path to the file system watcher
            self.load_files(folder_path)
            self.save_config(folder_path)



    def load_files(self, folder_path):
        self.table_widget.setRowCount(0)
        self.path_text.setText(folder_path)
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    first_line = f.readline().strip()

                row = self.table_widget.rowCount()
                self.table_widget.insertRow(row)

                parts = file.split(".")
                parts.pop()
                file_extension = parts.pop()
                file = ".".join(parts)
                
                self.table_widget.setItem(row, 0, QTableWidgetItem(split_and_join_with_newlines(file, 60)))
                self.table_widget.setItem(row, 1, QTableWidgetItem(file_extension))

                content_parts = first_line.split("*")             
                unix_timestamp = 1680888953918 / 1000  # convert to seconds
                timestamp = datetime.datetime.fromtimestamp(unix_timestamp)
                timestamp = timestamp.strftime("%B %d, %Y at %I:%M %p")
                content_parts_2 = content_parts[1].split(":")
                page = content_parts_2[0] if content_parts_2[0] != "0@0#0" else "NA"
                progress = content_parts_2[1]

                self.table_widget.setItem(row, 2, QTableWidgetItem(page))
                self.table_widget.setItem(row, 3, QTableWidgetItem(progress))
                self.table_widget.setItem(row, 4, QTableWidgetItem(timestamp))


    def search_files(self, text):
        for i in range(self.table_widget.rowCount()):
            match = False
            for j in range(self.table_widget.columnCount()):
                item = self.table_widget.item(i, j)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table_widget.setRowHidden(i, not match)

    def load_config(self):
        try:
            with open("moon_position.json", "r") as file:
                config = json.load(file)
                folder_path = config.get("folder_path", "")
                if folder_path:
                    self.file_system_watcher.addPath(folder_path)  # Add the path to the file system watcher
                    self.load_files(folder_path)
        except FileNotFoundError:
            pass

    def save_config(self, folder_path):
        config = {"folder_path": folder_path}
        with open("moon_position.json", "w") as file:
            json.dump(config, file)

try:
    app = QApplication(sys.argv)
    app.setApplicationName("Moon+ Reader Page Position Viewer")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
except Exception as e:
    logging.exception(e)

