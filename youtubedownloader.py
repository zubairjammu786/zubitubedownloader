import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QComboBox, \
    QCheckBox, QFileDialog, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QIcon, QPixmap
from pytube import YouTube

class DownloadThread(QThread):
    download_complete = pyqtSignal(str)
    download_failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super(DownloadThread, self).__init__(parent)
        self.video_stream = None
        self.output_path = None
        self.yt = None

    def set_parameters(self, video_stream, output_path, yt):
        self.video_stream = video_stream
        self.output_path = output_path
        self.yt = yt

    def run(self):
        try:
            self.video_stream.download(self.output_path)
            self.download_complete.emit("Download complete!")
        except Exception as e:
            self.download_failed.emit(f"Error: {e}")

class DownloaderApp(QMainWindow):
    def __init__(self):
        super(DownloaderApp, self).__init__()

        self.setWindowTitle("ZubiTube Downloader")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        # Title
        title_label = QLabel("<h1 style='color: #4CAF50;'>ZubiTube Downloader</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)

        self.url_label = QLabel("Enter YouTube Video URL(s):")
        self.layout.addWidget(self.url_label)

        self.url_entry = QLineEdit(placeholderText="https://www.youtube.com/watch?v=...")
        self.layout.addWidget(self.url_entry)

        self.fetch_button = QPushButton("Fetch Qualities", clicked=self.fetch_video_qualities)
        self.layout.addWidget(self.fetch_button)

        self.quality_label = QLabel("Select Video Quality:")
        self.layout.addWidget(self.quality_label)

        self.quality_menu = QComboBox()
        self.layout.addWidget(self.quality_menu)

        self.mp3_only_checkbox = QCheckBox("Download as MP3 Only")
        self.layout.addWidget(self.mp3_only_checkbox)

        self.download_location_button = QPushButton("Select Download Location", clicked=self.select_download_location)
        self.layout.addWidget(self.download_location_button)

        self.download_button = QPushButton("Download Video", clicked=self.download_video)
        self.layout.addWidget(self.download_button)

        self.status_label = QLabel()
        self.layout.addWidget(self.status_label)

        self.video_info_label = QLabel()
        self.layout.addWidget(self.video_info_label)

        # Buy Me a Coffee Link
        coffee_html = """
        <a href="https://www.buymeacoffee.com/zubairjammu" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-red.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;">
Donate to Project</a>
        """

        coffee_label = QLabel()
        coffee_label.setText(coffee_html)
        coffee_label.setOpenExternalLinks(True)
        coffee_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.layout.addWidget(coffee_label)

        # Footer Link
        footer_label = QLabel("<a href='https://www.facebook.com/zubairjammu786' style='color: #0000FF;'>Made by Zubair Jammu</a>")
        footer_label.setOpenExternalLinks(True)
        footer_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(footer_label)

        self.output_path = '.'  # Default download location
        self.download_in_progress = False

        self.download_thread = DownloadThread(self)

        self.download_thread.download_complete.connect(self.download_complete)
        self.download_thread.download_failed.connect(self.download_failed)

        self.central_widget.setLayout(self.layout)

        # Apply stylesheets for a modern look
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #A9A9A9;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton {
                padding: 8px;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                background-color: #4CAF50;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QComboBox, QCheckBox {
                padding: 8px;
                font-size: 12px;
            }
            QLabel a {
                text-decoration: none;
                color: #0000FF;
            }
        """)

    def fetch_video_qualities(self):
        video_url = self.url_entry.text()

        if not video_url:
            QMessageBox.warning(self, "Warning", "Please enter a YouTube video URL.")
            return

        try:
            yt = YouTube(video_url)
            qualities = [stream.resolution for stream in yt.streams.filter(file_extension="mp4")]
            self.quality_menu.addItems(qualities)

            # Display video information
            self.display_video_info(yt)

        except Exception as e:
            print(f"Error: {e}")
            QMessageBox.critical(self, "Error", f"Error: {e}")

    def download_video(self):
        if self.download_in_progress:
            QMessageBox.information(self, "Info", "Download in progress. Please wait.")
            return

        video_urls = [url.strip() for url in self.url_entry.text().split(',')]
        for video_url in video_urls:
            self.download_single_video(video_url)

    def download_single_video(self, video_url):
        selected_quality = self.quality_menu.currentText()

        if not video_url:
            QMessageBox.warning(self, "Warning", "Please enter a YouTube video URL.")
            return

        try:
            yt = YouTube(video_url)

            if self.mp3_only_checkbox.isChecked():
                video_stream = yt.streams.filter(only_audio=True).first()
            else:
                video_stream = yt.streams.filter(res=selected_quality, file_extension="mp4").first()

            if not video_stream:
                QMessageBox.warning(self, "Warning", f"No stream found for the selected quality: {selected_quality}")
                return

            # Disable download button during download
            self.download_button.setEnabled(False)
            self.download_in_progress = True

            self.status_label.setText(f"Downloading: {yt.title}")

            self.download_thread.set_parameters(video_stream, self.output_path, yt)
            self.download_thread.start()

        except Exception as e:
            print(f"Error: {e}")
            QMessageBox.critical(self, "Error", f"Error: {e}")
            self.download_button.setEnabled(True)
            self.download_in_progress = False

    def select_download_location(self):
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Download Location")
        if selected_folder:
            self.output_path = selected_folder
            QMessageBox.information(self, "Info", f"Download location set to: {self.output_path}")

    def display_video_info(self, yt):
        info_text = f"Title: {yt.title}\nDuration: {yt.length} seconds\nAuthor: {yt.author}\nUpload Date: {yt.publish_date}"
        self.video_info_label.setText(info_text)

    def download_complete(self, message):
        self.status_label.setText(message)
        # Re-enable download button after download completion
        self.download_button.setEnabled(True)
        self.download_in_progress = False

    def download_failed(self, message):
        self.status_label.setText(message)
        # Re-enable download button after download failure
        self.download_button.setEnabled(True)
        self.download_in_progress = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloaderApp()
    window.show()
    sys.exit(app.exec_())
