from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCalendarWidget, \
    QFormLayout, QDialog, QListWidget, QListWidgetItem, QCheckBox, QLineEdit, QDialogButtonBox, QComboBox
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, QSize
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import requests
import pickle
import datetime
from matplotlib.dates import DateFormatter

class CryptoSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_currency = "USD"
        self.setWindowTitle("Выбор криптовалют")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.crypto_list = self.load_crypto_list()

        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText("Поиск криптовалюты...")
        self.search_line_edit.textChanged.connect(self.filter_crypto_list)
        layout.addWidget(self.search_line_edit)

        self.crypto_list_widget = QListWidget()
        self.crypto_list_widget.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.crypto_list_widget)

        selected_crypto = self.load_selected_crypto()
        for crypto in self.crypto_list:
            item = QListWidgetItem(crypto)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if item.text() in selected_crypto else Qt.Unchecked)
            self.crypto_list_widget.addItem(item)

        self.selected_currency = "USDT"

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.load_selected_crypto()

    def get_selected_crypto(self):
        selected_crypto = []
        for row in range(self.crypto_list_widget.count()):
            item = self.crypto_list_widget.item(row)
            if item.checkState() == Qt.Checked:
                selected_crypto.append(item.text())
        return selected_crypto

    def save_selected_crypto(self):
        selected_crypto = self.get_selected_crypto()
        with open("selected_crypto.pickle", "wb") as f:
            pickle.dump(selected_crypto, f)

    def load_crypto_list(self):
        url = "https://api.binance.com/api/v3/ticker/price"
        response = requests.get(url)
        data = response.json()
        crypto_list = []
        for item in data:
            symbol = item['symbol']
            if symbol.endswith('BTC'):
                crypto = symbol[:-3].replace('-', ' - ')
                crypto_list.append(crypto)
        return crypto_list

    def load_selected_crypto(self):
        try:
            with open("selected_crypto.pickle", "rb") as f:
                selected_crypto = pickle.load(f)
                for row in range(self.crypto_list_widget.count()):
                    item = self.crypto_list_widget.item(row)
                    if item.text() in selected_crypto:
                        item.setCheckState(Qt.Checked)
                return selected_crypto
        except (FileNotFoundError, EOFError):
            pass

    def filter_crypto_list(self, search_text):
        for row in range(self.crypto_list_widget.count()):
            item = self.crypto_list_widget.item(row)
            if search_text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Отслеживание курса валют")
        self.setMinimumSize(QSize(1024, 768))

        widget = QWidget()
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.select_crypto_button = QPushButton("Выбрать криптовалюты")
        layout.addWidget(self.select_crypto_button)

        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        timeframe_label = QLabel("Выберите временной диапазон:")
        layout.addWidget(timeframe_label)
        timeframe_layout = QHBoxLayout()
        layout.addLayout(timeframe_layout)

        self.data_combobox = QComboBox()
        self.data_combobox.addItems(["Цена открытия", "Цена закрытия"])
        layout.addWidget(self.data_combobox)

        from_date = datetime.datetime.now() - datetime.timedelta(days=7)
        to_date = datetime.datetime.now()

        self.from_calendar = QCalendarWidget()
        self.from_calendar.setSelectedDate(from_date)
        timeframe_layout.addWidget(self.from_calendar)

        self.to_calendar = QCalendarWidget()
        self.to_calendar.setSelectedDate(to_date)
        timeframe_layout.addWidget(self.to_calendar)

        self.update_button = QPushButton("Обновить график")
        layout.addWidget(self.update_button)

        self.select_crypto_button.clicked.connect(self.select_crypto)
        self.update_button.clicked.connect(self.update_chart)

        self.selected_crypto = None
        self.selected_currency = None
        self.ax = self.figure.add_subplot(111)

    def update_axis_labels(self):
        self.ax.set_ylabel('Цена (USDT)')
        self.canvas.draw()

    def select_crypto(self):
        dialog = CryptoSelectionDialog(self)
        dialog.selected_currency = self.selected_currency
        if dialog.exec_() == QDialog.Accepted:
            self.selected_crypto = dialog.get_selected_crypto()
            self.selected_currency = dialog.selected_currency
            if self.selected_crypto:
                dialog.save_selected_crypto()
            else:
                print("Не выбрана ни одна криптовалюта")

    def update_chart(self):
        from_date = self.from_calendar.selectedDate().toPyDate()
        to_date = self.to_calendar.selectedDate().toPyDate() + datetime.timedelta(days=1)

        start_timestamp = int(datetime.datetime(from_date.year, from_date.month, from_date.day).timestamp()) * 1000
        end_timestamp = int(datetime.datetime(to_date.year, to_date.month, to_date.day).timestamp()) * 1000

        if not self.selected_crypto:
            print("Не выбрана ни одна криптовалюта")
            return

        self.ax.clear()
        selected_data = self.data_combobox.currentText()

        for crypto in self.selected_crypto:
            symbol = f"{crypto}USDT"
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&startTime={start_timestamp}&endTime={end_timestamp}"
            response = requests.get(url)

            if response.status_code != 200:
                print(f"Ошибка при получении данных: {response.status_code}")
                continue

            data = response.json()

            x = []
            y = []
            for item in data:
                try:
                    if not isinstance(item[0], int):
                        continue
                    timestamp = item[0] / 1000
                    if selected_data == "Цена открытия":
                        value = item[1]
                    elif selected_data == "Цена закрытия":
                        value = item[4]
                    x.append(datetime.datetime.fromtimestamp(float(timestamp)))
                    y.append(float(value))
                except (ValueError, IndexError, AttributeError):
                    continue

            self.ax.plot(x, y, label=crypto)
            self.ax.autoscale_view()

        self.ax.set_xlabel('Дата')
        self.ax.set_ylabel(f'Цена закрытия ({self.selected_currency})')
        self.ax.set_title('График цены криптовалют')
        self.ax.legend()
        self.update_axis_labels()
        self.ax.grid(color='lightgray', linestyle='--')

        date_format = DateFormatter('%d.%m.%y')
        self.ax.xaxis.set_major_formatter(date_format)
        plt.xticks(rotation=90)

        self.ax.set_xlim(from_date, to_date + datetime.timedelta(days=1))
        self.canvas.draw()

    def showEvent(self, event):
        super().showEvent(event)
        self.select_crypto()
        self.update_chart()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()