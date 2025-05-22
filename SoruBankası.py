import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QListWidget, QTextEdit, QComboBox, QMessageBox,
    QStackedWidget
)

db_file = "soru_bankasi.db"

conn = sqlite3.connect(db_file)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS sorular (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ders TEXT NOT NULL,
    soru TEXT NOT NULL,
    sik_a TEXT,
    sik_b TEXT,
    sik_c TEXT,
    sik_d TEXT,
    dogru_sik TEXT,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()


def show_message(text):
    msg = QMessageBox()
    msg.setWindowTitle("Bilgi")
    msg.setText(text)
    msg.exec_()


class GirisEkrani(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        self.label = QLabel("Soru Bankası Uygulamasına Hoş Geldiniz")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-posta")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Şifre")
        self.login_button = QPushButton("Giriş Yap")
        self.register_button = QPushButton("Üye Ol")

        self.login_button.clicked.connect(self.giris_yap)
        self.register_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)
        self.setLayout(layout)

    def giris_yap(self):
        email = self.email_input.text()
        password = self.password_input.text()
        try:
            c.execute("SELECT id, name FROM users WHERE email=? AND password=?", (email, password))
            user = c.fetchone()
            if user:
                ders_secim_ekrani = self.stacked_widget.widget(2)
                ders_secim_ekrani.user_id = user[0]
                ders_secim_ekrani.user_name = user[1]
                ders_secim_ekrani.guncelle_mesaj()
                self.stacked_widget.setCurrentIndex(2)
            else:
                show_message("E-posta veya şifre yanlış!")
        except Exception as e:
            show_message(f"Hata oluştu: {e}")


class UyeOlEkrani(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.init_ui()

    def init_ui(self):
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("İsim Soyisim")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-posta")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Şifre")
        self.register_button = QPushButton("Kaydol")
        self.register_button.clicked.connect(self.kayit_ol)

        layout = QVBoxLayout()
        layout.addWidget(self.name_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.register_button)
        self.setLayout(layout)

    def kayit_ol(self):
        name = self.name_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        if not (name and email and password):
            show_message("Lütfen tüm alanları doldurun.")
            return
        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            show_message("Kayıt başarılı! Giriş yapabilirsiniz.")
            self.stacked_widget.setCurrentIndex(0)
        except sqlite3.IntegrityError:
            show_message("Bu e-posta zaten kayıtlı!")
        except Exception as e:
            show_message(f"Hata oluştu: {e}")


class DersSecimEkrani(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.user_id = None
        self.user_name = ""
        self.ders_ekranlari = {}
        self.init_ui()

    def init_ui(self):
        self.label = QLabel("Hoş geldiniz! Lütfen bir ders seçiniz.")
        self.list_widget = QListWidget()
        dersler = ["Matematik", "Türkçe", "Fen Bilimleri", "Hayat Bilgisi", "İngilizce"]
        self.list_widget.addItems(dersler)
        self.list_widget.itemDoubleClicked.connect(self.ders_secildi)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def guncelle_mesaj(self):
        self.label.setText(f"Hoş geldiniz, {self.user_name}! Lütfen bir ders seçiniz.")

    def ders_secildi(self, item):
        ders_adi = item.text()
        if ders_adi not in self.ders_ekranlari:
            ekran = DersEkrani(self.stacked_widget, ders_adi, self.user_id)
            self.ders_ekranlari[ders_adi] = ekran
            self.stacked_widget.addWidget(ekran)
        self.stacked_widget.setCurrentWidget(self.ders_ekranlari[ders_adi])


class DersEkrani(QWidget):
    def __init__(self, stacked_widget, ders_adi, user_id):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.ders_adi = ders_adi
        self.user_id = user_id
        self.init_ui()
        self.sorulari_yukle()

    def init_ui(self):
        self.label = QLabel(f"{self.ders_adi} Soruları")
        self.soru_listesi = QListWidget()
        self.soru_ekle_buton = QPushButton("Soru Ekle")
        self.cevaplari_gor_buton = QPushButton("Cevapları Gör")

        self.soru_ekle_buton.clicked.connect(self.soru_ekle)
        self.cevaplari_gor_buton.clicked.connect(self.cevaplari_goster)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.soru_listesi)
        layout.addWidget(self.soru_ekle_buton)
        layout.addWidget(self.cevaplari_gor_buton)
        self.setLayout(layout)

    def sorulari_yukle(self):
        self.soru_listesi.clear()
        try:
            c.execute("""
                SELECT soru, sik_a, sik_b, sik_c, sik_d FROM sorular
                WHERE ders=? AND user_id=?
            """, (self.ders_adi, self.user_id))
            sorular = c.fetchall()
            for i, (soru, a, b, c_, d) in enumerate(sorular, 1):
                metin = (
                    f"{i}. Soru: {soru}\n"
                    f"   A) {a}\n"
                    f"   B) {b}\n"
                    f"   C) {c_}\n"
                    f"   D) {d}"
                )
                self.soru_listesi.addItem(metin)
        except Exception as e:
            show_message(f"Soru yükleme hatası: {e}")

    def soru_ekle(self):
        self.soru_ekle_ekrani = SoruEkleEkrani(self.ders_adi, self.user_id, self)
        self.soru_ekle_ekrani.show()

    def cevaplari_goster(self):
        try:
            c.execute("SELECT soru, dogru_sik FROM sorular WHERE ders=? AND user_id=?", (self.ders_adi, self.user_id))
            cevaplar = c.fetchall()
            if not cevaplar:
                show_message("Henüz soru yok.")
                return
            mesaj = "\n".join([f"{i + 1}. Soru: Doğru Şık: {dogru}" for i, (soru, dogru) in enumerate(cevaplar)])
            show_message(mesaj)
        except Exception as e:
            show_message(f"Cevap gösterme hatası: {e}")


class SoruEkleEkrani(QWidget):
    def __init__(self, ders_adi, user_id, ders_ekrani):
        super().__init__()
        self.ders_adi = ders_adi
        self.user_id = user_id
        self.ders_ekrani = ders_ekrani
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"{self.ders_adi} - Soru Ekle")
        self.soru_input = QTextEdit()
        self.soru_input.setPlaceholderText("Soruyu buraya yazınız...")
        self.sik_a = QLineEdit()
        self.sik_b = QLineEdit()
        self.sik_c = QLineEdit()
        self.sik_d = QLineEdit()
        self.sik_a.setPlaceholderText("A şıkkı")
        self.sik_b.setPlaceholderText("B şıkkı")
        self.sik_c.setPlaceholderText("C şıkkı")
        self.sik_d.setPlaceholderText("D şıkkı")
        self.dogru_sik_combo = QComboBox()
        self.dogru_sik_combo.addItems(["A", "B", "C", "D"])
        self.kaydet_button = QPushButton("Kaydet")
        self.kaydet_button.clicked.connect(self.kaydet)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Soru:"))
        layout.addWidget(self.soru_input)
        layout.addWidget(QLabel("Şıklar:"))
        layout.addWidget(self.sik_a)
        layout.addWidget(self.sik_b)
        layout.addWidget(self.sik_c)
        layout.addWidget(self.sik_d)
        layout.addWidget(QLabel("Doğru Şık:"))
        layout.addWidget(self.dogru_sik_combo)
        layout.addWidget(self.kaydet_button)
        self.setLayout(layout)

    def kaydet(self):
        soru = self.soru_input.toPlainText().strip()
        a = self.sik_a.text().strip()
        b = self.sik_b.text().strip()
        c_ = self.sik_c.text().strip()
        d = self.sik_d.text().strip()
        dogru = self.dogru_sik_combo.currentText()

        if not soru or not a or not b or not c_ or not d:
            show_message("Lütfen tüm alanları doldurun.")
            return

        try:
            c.execute("""
                INSERT INTO sorular (ders, soru, sik_a, sik_b, sik_c, sik_d, dogru_sik, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.ders_adi, soru, a, b, c_, d, dogru, self.user_id))
            conn.commit()
            show_message("Soru başarıyla eklendi.")
            self.ders_ekrani.sorulari_yukle()
            self.close()
        except Exception as e:
            show_message(f"Hata oluştu: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    stacked_widget = QStackedWidget()

    giris = GirisEkrani(stacked_widget)
    uye_ol = UyeOlEkrani(stacked_widget)
    ders_secim = DersSecimEkrani(stacked_widget)

    stacked_widget.addWidget(giris)       # index 0
    stacked_widget.addWidget(uye_ol)      # index 1
    stacked_widget.addWidget(ders_secim)  # index 2

    stacked_widget.setFixedSize(400, 600)
    stacked_widget.show()

    sys.exit(app.exec_())
