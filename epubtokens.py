import os
import shutil
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, List, Set
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QFileDialog, QMessageBox, QProgressBar, QCheckBox, QRadioButton
)
from ebooklib import epub
import tiktoken
from settings_manager import SettingsManager

# Configure logging
logging.basicConfig(
    filename='epubtokens.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TokenCounterApp(QWidget):
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit for files
    CHUNK_SIZE = 8192  # Read files in 8KB chunks
    
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.processed_files: Set[str] = set()
        self.init_ui()
        self.load_settings()

    def init_ui(self) -> None:
        """Initialize the user interface components."""
        self.setWindowTitle("EPUB Token Counter")
        self.setGeometry(100, 100, 400, 200)
        self._create_layout()

    def _create_layout(self) -> None:
        """Create and setup the UI layout."""
        self.layout = QVBoxLayout()
        
        # Source folder selection
        self._add_folder_selection()
        
        # Token count input
        self._add_token_input()
        
        # Destination folder selection
        self._add_destination_selection()
        
        # Progress tracking
        self._add_progress_tracking()
        
        self.setLayout(self.layout)

    def _add_folder_selection(self) -> None:
        """Add source folder selection widgets."""
        self.folder_label = QLabel("Select folder containing EPUB files:")
        self.folder_input = QLineEdit()
        self.folder_button = QPushButton("Browse")
        self.folder_button.clicked.connect(self.select_source_folder)
        
        self.layout.addWidget(self.folder_label)
        self.layout.addWidget(self.folder_input)
        self.layout.addWidget(self.folder_button)

    def _add_token_input(self) -> None:
        """Add token count input widgets."""
        self.token_label = QLabel("Enter maximum token count:")
        self.token_input = QLineEdit()
        
        self.layout.addWidget(self.token_label)
        self.layout.addWidget(self.token_input)

    def _add_destination_selection(self) -> None:
        """Add destination folder selection widgets."""
        # Add operation mode selection
        self.operation_group = QHBoxLayout()
        self.count_only_radio = QRadioButton("Count Only")
        self.copy_radio = QRadioButton("Copy Files")
        self.move_radio = QRadioButton("Move Files")
        self.count_only_radio.setChecked(True)  # Default to count only
        
        self.operation_group.addWidget(self.count_only_radio)
        self.operation_group.addWidget(self.copy_radio)
        self.operation_group.addWidget(self.move_radio)
        
        self.layout.addLayout(self.operation_group)
        
        # Existing destination folder widgets
        self.dest_label = QLabel("Select destination folder for processed files:")
        self.dest_input = QLineEdit()
        self.dest_button = QPushButton("Browse")
        self.dest_button.clicked.connect(self.select_dest_folder)
        
        self.layout.addWidget(self.dest_label)
        self.layout.addWidget(self.dest_input)
        self.layout.addWidget(self.dest_button)
        
        # Connect radio buttons to enable/disable destination widgets
        self.count_only_radio.toggled.connect(self._update_destination_widgets)
        self._update_destination_widgets()

    def _update_destination_widgets(self) -> None:
        """Enable/disable destination widgets based on selected mode."""
        dest_widgets_enabled = not self.count_only_radio.isChecked()
        self.dest_label.setEnabled(dest_widgets_enabled)
        self.dest_input.setEnabled(dest_widgets_enabled)
        self.dest_button.setEnabled(dest_widgets_enabled)

    def _add_progress_tracking(self) -> None:
        """Add progress tracking widgets."""
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_processing)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        
        self.progress_bar = QProgressBar()
        
        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.progress_bar)

    def calculate_tokens(self, text: str) -> Optional[int]:
        """Calculate token count for given text."""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logging.error(f"Token calculation error: {str(e)}")
            return None

    def process_epub(self, file_path: str) -> Tuple[Optional[str], Optional[int]]:
        """Process single EPUB file and return title and token count."""
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None, None

        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                logging.warning(f"File too large: {file_path}")
                return None, None

            book = epub.read_epub(file_path)
            title = self._get_epub_title(book, file_path)
            token_count = self._process_epub_content(book)
            
            return title, token_count

        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
            return None, None

    def _get_epub_title(self, book: epub.EpubBook, file_path: str) -> str:
        """Extract title from EPUB metadata."""
        title_metadata = book.get_metadata("DC", "title")
        return title_metadata[0][0] if title_metadata else Path(file_path).name

    def _process_epub_content(self, book: epub.EpubBook) -> Optional[int]:
        """Process EPUB content and return token count."""
        full_text = ""
        for item in book.get_items():
            if item.media_type == "application/xhtml+xml":
                try:
                    content = item.get_content().decode("utf-8", errors="ignore")
                    if content:
                        full_text += content
                except Exception as e:
                    logging.error(f"Error processing EPUB item: {str(e)}")

        return self.calculate_tokens(full_text) if full_text else None

    def get_epub_files(self, folder: str) -> List[str]:
        """Get list of EPUB files in folder and all subfolders."""
        epub_files = []
        try:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.epub'):
                        full_path = os.path.join(root, file)
                        epub_files.append(full_path)
            logging.info(f"Found {len(epub_files)} EPUB files in {folder} and its subfolders")
        except Exception as e:
            logging.error(f"Error scanning directory: {str(e)}")
        return epub_files

    def validate_inputs(self) -> Tuple[bool, str]:
        """Validate user inputs before processing."""
        try:
            max_tokens = int(self.token_input.text().replace(",", ""))
            if max_tokens <= 0:
                return False, "Token count must be positive"
        except ValueError:
            return False, "Invalid token count"

        if not os.path.exists(self.folder_input.text()):
            return False, "Source folder does not exist"
        
        # Only validate destination folder if not in count-only mode
        if not self.count_only_radio.isChecked():
            if not os.path.exists(self.dest_input.text()):
                return False, "Destination folder does not exist"

        return True, ""

    def select_source_folder(self) -> None:
        """Handle source folder selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.folder_input.setText(folder)

    def select_dest_folder(self) -> None:
        """Handle destination folder selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_input.setText(folder)

    def load_settings(self) -> None:
        """Load saved settings and update UI."""
        settings = self.settings_manager.load_settings()
        self.folder_input.setText(settings['input_folder'])
        self.dest_input.setText(settings['output_folder'])
        self.token_input.setText(settings['token_count'])

    def save_current_settings(self) -> None:
        """Save current settings."""
        settings = {
            'input_folder': self.folder_input.text(),
            'output_folder': self.dest_input.text(),
            'token_count': self.token_input.text()
        }
        self.settings_manager.save_settings(settings)

    def cancel_processing(self) -> None:
        """Cancel the processing of files."""
        self.processing_cancelled = True
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def start_processing(self) -> None:
        """Start processing EPUB files."""
        self.processing_cancelled = False
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        # Save current settings
        self.save_current_settings()

        # Validate inputs
        is_valid, error_message = self.validate_inputs()
        if not is_valid:
            QMessageBox.critical(self, "Error", error_message)
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            return

        source_folder = self.folder_input.text()
        max_tokens = int(self.token_input.text().replace(",", ""))
        
        # Determine operation mode
        is_count_only = self.count_only_radio.isChecked()
        is_move = self.move_radio.isChecked()
        
        # Get output folder based on mode
        output_folder = self.dest_input.text() if not is_count_only else source_folder

        # Get list of files to process
        epub_files = self.get_epub_files(source_folder)
        if not epub_files:
            QMessageBox.warning(self, "Warning", "No EPUB files found!")
            self.start_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            return

        # Show warning if move operation is selected
        if is_move:
            response = QMessageBox.warning(
                self,
                "Warning - Files Will Be Moved",
                "You have selected to MOVE files. This will REMOVE files from the source folder.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if response == QMessageBox.No:
                self.start_button.setEnabled(True)
                self.cancel_button.setEnabled(False)
                return

        # Setup progress tracking
        self.progress_bar.setMaximum(len(epub_files))
        self.progress_bar.setValue(0)
        
        # Setup CSV file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = os.path.join(output_folder, f"epub_token_counts_{timestamp}.csv")
        
        operation_type = "Moved" if is_move else "Copied" if not is_count_only else "Counted"
        processed_count = 0
        operated_count = 0
        
        with open(csv_file, mode="w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Title", "Token Count", "File Path", "Status"])

            for file_path in epub_files:
                if self.processing_cancelled:
                    break
                
                if file_path in self.processed_files:
                    continue
                    
                title, token_count = self.process_epub(file_path)
                if title and token_count:
                    # In count-only mode, write all files to CSV
                    # In copy/move mode, only write files that meet token criteria
                    should_write_to_csv = (
                        is_count_only or 
                        (not is_count_only and token_count <= max_tokens)
                    )
                    
                    if should_write_to_csv:
                        status = (
                            "Within Limit" if token_count <= max_tokens 
                            else "Exceeds Limit"
                        )
                        csv_writer.writerow([title, token_count, file_path, status])
                    
                    # Handle file operations for copy/move modes
                    if not is_count_only and token_count <= max_tokens:
                        try:
                            dest_path = os.path.join(output_folder, os.path.basename(file_path))
                            if is_move:
                                shutil.move(file_path, dest_path)
                                logging.info(f"Moved {file_path} (Tokens: {token_count}) to {dest_path}")
                            else:
                                shutil.copy2(file_path, dest_path)
                                logging.info(f"Copied {file_path} (Tokens: {token_count}) to {dest_path}")
                            operated_count += 1
                        except Exception as e:
                            logging.error(f"Error {operation_type.lower()}ing file {file_path}: {str(e)}")
                
                self.processed_files.add(file_path)
                processed_count += 1
                self.progress_bar.setValue(processed_count)
                QApplication.processEvents()

        completion_message = "Processing completed!" if not self.processing_cancelled else "Processing cancelled!"
        
        if is_count_only:
            QMessageBox.information(
                self, 
                "Done", 
                f"{completion_message}\n"
                f"Processed: {processed_count} files\n"
                f"CSV saved to {csv_file}"
            )
        else:
            QMessageBox.information(
                self, 
                "Done", 
                f"{completion_message}\n"
                f"Processed: {processed_count} files\n"
                f"{operation_type}: {operated_count} files\n"
                f"CSV saved to {csv_file}"
            )
        
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

if __name__ == "__main__":
    app = QApplication([])
    window = TokenCounterApp()
    window.show()
    app.exec_()
