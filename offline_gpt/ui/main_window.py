from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
import sys

def run_app():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Offline-GPT")
    window.setCentralWidget(QLabel("Offline-GPT Chat UI Coming Soon!"))
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec()) 