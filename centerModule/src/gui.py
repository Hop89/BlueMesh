from PyQt6.QtWidgets import QApplication, QPushButton

app = QApplication([])

window = QPushButton("Push Me")
window.show()

app.exec()