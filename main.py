import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QDateEdit, QTextBrowser, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox
from PySide6.QtUiTools import QUiLoader
import pandas as pd
from requests import get
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from PySide6.QtCore import QDate, Qt
from matplotlib.ticker import AutoLocator


currencies_list = ['thb', 'usd', 'aud', 'hkd', 'cad', 'nzd', 'sgd', 'eur', 'huf', "chf", "gbp", "uah", "jpy", "czk", "dkk",
                   "isk", "nok", "sek", "ron", "bgn", "try", "ils", "clp", "php", "mxn", "zar", "brl"]


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        loader = QUiLoader()
        self.window = loader.load("exchange_rate_calculator.ui", self)
        self.window.findChild(QPushButton, "start").clicked.connect(self.press_button)
        self.window.findChild(QPushButton, "wykres").clicked.connect(self.plot_chart)
        self.window.findChild(QLineEdit, "kod_waluty").returnPressed.connect(self.press_button)

        # Ustawienie orientacji QBoxLayout na poziomą
        layout = QVBoxLayout()
        sub_layout = QHBoxLayout()
        layout.addLayout(sub_layout)
        layout.addWidget(self.window)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Ograniczenie zakresu dat w dateEdit i dateEdit_2 do maksymalnie 1,5 roku
        dateEdit = self.window.findChild(QDateEdit, "dateEdit")
        dateEdit_2 = self.window.findChild(QDateEdit, "dateEdit_2")

        current_date = datetime.now().date()
        max_date = current_date + timedelta(days=547)  # Dodanie 547 dni (1,5 roku) do aktualnej daty
        dateEdit.setMaximumDate(max_date)
        dateEdit_2.setMaximumDate(max_date)

        dateEdit.setMaximumDate(QDate.currentDate())  # Dodaj tę linię

        self.showMaximized()
        self.show()

    def press_button(self):
        kod_waluty = self.window.findChild(QLineEdit, "kod_waluty").text().lower()
        start_date = self.window.findChild(QDateEdit, "dateEdit").date().toString("yyyy-MM-dd")
        end_date = self.window.findChild(QDateEdit, "dateEdit_2").date().toString("yyyy-MM-dd")
        print("Wprowadzony kod waluty:", kod_waluty)
        print("Data początkowa:", start_date)
        print("Data końcowa:", end_date)

        label_komunikat = self.window.findChild(QTextBrowser, "komunikat")
        label_komunikat.setStyleSheet("font-weight: bold; font-size: 20px; color: yellow; text-align: center;")

        if kod_waluty not in currencies_list:
            # Wyświetlanie komunikatu na UI
            label_komunikat.setText("Podaj poprawny kod waluty")
        else:
            # Sprawdzenie przedziału czasowego
            date1 = datetime.strptime(start_date, "%Y-%m-%d").date()
            date2 = datetime.strptime(end_date, "%Y-%m-%d").date()
            max_date = date1 + timedelta(days=547)  # Maksymalny przedział czasowy - 1,5 roku

            if date2 > max_date:
                # Wyświetlanie komunikatu na UI
                label_komunikat.setText("Maksymalny zakres czasowy to 1,5 roku")
            elif date1 > date2:
                label_komunikat.setText("Błąd: Data początkowa nie może być późniejsza niż data końcowa.")
            else:
                # Komunikat znika, gdy podano poprawny przedział czasowy
                label_komunikat.setText("")

                answer = get(
                    f"http://api.nbp.pl/api/exchangerates/rates/a/{kod_waluty}/{start_date}/{end_date}/?format=json")
                dane = answer.json()
                print(dane)
                kurs = dane['rates']
                print(kurs)
                df = pd.DataFrame(kurs)
                print(df)
                df.drop('no', axis=1, inplace=True)
                print(df)

                df.rename(columns=({'effectiveDate': 'Data', 'mid': 'Kurs'}), inplace=True)

                # Obliczanie średniej wartości kursu
                srednia_kursu = df['Kurs'].mean()
                print("Średnia kursu:", srednia_kursu)

                # Wyświetlanie średniej kursu w UI
                label_srednia = self.window.findChild(QTextBrowser, "srednia")
                label_srednia.setText(f" {srednia_kursu:.4f}")

                # Zapisanie danych do atrybutów obiektu klasy
                self.kurs_data = df
                self.kod_waluty = kod_waluty
                self.start_date = start_date
                self.end_date = end_date

    def plot_chart(self):
        df = self.kurs_data
        kod_waluty = self.kod_waluty
        start_date = self.start_date
        end_date = self.end_date

        x = df['Data']
        y = df['Kurs']
        df['MA_5'] = df['Kurs'].rolling(5).mean()

        plt.figure(figsize=(12, 6))  # Zmniejszenie rozmiaru wykresu (szerokość, wysokość)
        plt.plot(x, y, label='Kurs')
        plt.plot(x, df['MA_5'], label='MA_5')

        plt.axhline(y=df['Kurs'].mean(), color='r', linestyle='--', label='Średnia kursu')
        plt.grid(True)

        # Oznaczenie maksymalnej wartości
        max_value = df['Kurs'].max()
        max_index = df['Kurs'].idxmax()
        plt.annotate(f'Max: {max_value:.4f}', xy=(x[max_index], max_value),
                     xytext=(5, -15), textcoords='offset points',
                     arrowprops=dict(arrowstyle="->", color='red')) # Dodanie strzałki wskazujące na wartości maksymalne

        # Oznaczenie minimalnej wartości
        min_value = df['Kurs'].min()
        min_index = df['Kurs'].idxmin()
        plt.annotate(f'Min: {min_value:.4f}', xy=(x[min_index], min_value),
                     xytext=(5, 5), textcoords='offset points',
                     arrowprops=dict(arrowstyle="->", color='green'))  # Dodanie strzałki wskazujące na wartości minimalne

        plt.xlabel('Data')
        plt.ylabel('Kurs')
        plt.title(f'Wykres kursu {kod_waluty.upper()} w przedziale {start_date} - {end_date}')
        plt.legend()
        plt.xticks(rotation=45)  # Obrócenie oznaczeń na osi x o 45 stopni
        ax = plt.gca()
        ax.xaxis.set_major_locator(AutoLocator())
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

