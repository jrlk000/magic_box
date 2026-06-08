"""
Treiber ist die Verknüpfung zwischen der ESP32 als Logik Element
und dem Aktuator als Arbeiter.


Übersicht Verbindungen:
VCC, GND
R_IS, L_IS
R_EN, L_EN (Rückwärts, Vorwärts)
RPWM, LPWM (Enable)

Verkanelung:
Batterie an Treiber + und VCC, -, in plus muss auf jeden fall eine Sicherung reina

Treiber mit Motor an M- und M+

Logikinterface:
VCC, GND
R_EN, L_EN (dauerhaftes scharf stellen)

RPWM, LPWM

Exkurs sleep modus einer Esp32:

Hauptsytem -> Hauptfresser:
Hier sitzen schnelle Hauptprozessoren, das WLAN-Modul, das Bluetooth und die
"normalen" digitalen Pins.
Wenn dieses System aktiv ist, verbraucht der ESP32 relativ viel
Strom ca. 40 bis 240 mA.

RTC-Domäne (Wächter)
Extrem stromsparender. winziger seperater Bereich auf dem Chip
der völlig unabhängig vom Hauptsystem läuft.

Deep-Sleep:
Hauptsystem vom Strom getrennt nur die RTC-Domäne bleibt wach.

RTC-Pins:
RTC-Pins sind harwareseitig physikalisch mit dieser zweiten, stromsparenden RTC-Domäne verdrahtet.
Wenn das Hauptsystem schläft wird die Kontrolle an den kleien RTC-Wächter übergeben. Liegt
an dem RTC-Pin nun ein Spannungsimpulse merkt der Wächter, dass das Hauptsystem durch
einen Reset wieder aufgeweckt werden soll.

Pins die mit der RTC-Domäne verbunden sind: 0, 2, 4, 12, 13, 14, 15, 25, 26, 27, 32, 33, 34, 36, 39

Unproblematisch sind 32, 33 beste Wahl, da hier keine Boot probleme, wie bei "Strapping Pins"
"""

# ---- Imports ----
from machine import I2C

class DS3231:
    """
    Treiber-Klasse zur Steuerung eines DS3231 RTC-Moduls über I2C.
    Unterstützt das Auslesen/Setzen der Zeit sowie Alarm 1 für Hardware-Interrupts.
    """

    # --- KONSTANTEN (Register-Adressen des DS3231) ---
    ADDR = 0x68  # I2C Standard-Adresse des Moduls
    REG_TIME = 0x00  # Start-Register für die Uhrzeit
    REG_ALARM1 = 0x07  # Start-Register für Alarm 1
    REG_CONTROL = 0x0E  # Kontroll-Register (für Alarme/SQW)
    REG_STATUS = 0x0F  # Status-Register (für Alarm-Flags)

    def __init__(self, i2c):
        """Initialisiert das Modul und prüft die Verbindung."""
        self.i2c = i2c
        if self.ADDR not in self.i2c.scan():
            raise OSError(f"DS3231 Modul unter I2C-Adresse {hex(self.ADDR)} nicht gefunden! Verkabelung prüfen.")

    # --- INTERNE HILFSFUNKTIONEN ---

    @staticmethod
    def _dec_to_bcd(val):
        """Wandelt eine normale Dezimalzahl in Binary-Coded Decimal (BCD) um."""
        return (val // 10 << 4) | (val % 10)

    @staticmethod
    def _bcd_to_dec(val):
        """Wandelt Binary-Coded Decimal (BCD) zurück in eine Dezimalzahl."""
        return ((val >> 4) * 10) + (val & 0x0F)

    # --- HAUPTFUNKTIONEN ---

    def set_time(self, year, month, day, hour, minute, second):
        """Speichert eine neue Uhrzeit auf dem RTC-Modul."""
        yy = year % 100
        data = bytearray([
            self._dec_to_bcd(second),
            self._dec_to_bcd(minute),
            self._dec_to_bcd(hour),
            0x01,  # Wochentag (1-7), für dieses Projekt meist irrelevant
            self._dec_to_bcd(day),
            self._dec_to_bcd(month),
            self._dec_to_bcd(yy)
        ])
        self.i2c.writeto_mem(self.ADDR, self.REG_TIME, data)

    def get_time(self):
        """Liest die Uhrzeit aus und gibt ein Tuple zurück: (Jahr, Monat, Tag, Stunde, Minute, Sekunde)"""
        data = self.i2c.readfrom_mem(self.ADDR, self.REG_TIME, 7)

        second = self._bcd_to_dec(data[0])
        minute = self._bcd_to_dec(data[1])
        hour = self._bcd_to_dec(data[2] & 0x3F)  # Bit 6 filtern für 24h-Modus
        day = self._bcd_to_dec(data[4])
        month = self._bcd_to_dec(data[5] & 0x1F)
        year = self._bcd_to_dec(data[6]) + 2000

        return (year, month, day, hour, minute, second)

    # --- ALARM & INTERRUPT FUNKTIONEN ---

    def clear_alarm(self):
        """
        Löscht das Alarm-1-Flag.
        MUSS aufgerufen werden, damit der SQW-Pin nach einem Alarm wieder von LOW auf HIGH wechselt.
        """
        status = self.i2c.readfrom_mem(self.ADDR, self.REG_STATUS, 1)[0]
        # Bit 0 (A1F) auf 0 setzen, alle anderen Bits unverändert lassen
        status = status & 0xFE
        self.i2c.writeto_mem(self.ADDR, self.REG_STATUS, bytearray([status]))

    def set_alarm(self, hour, minute, second):
        """
        Programmiert Alarm 1 für eine tägliche Auslösung (Tag ist irrelevant).
        Zieht den SQW-Pin zur Zielzeit auf LOW.
        """
        data = bytearray([
            self._dec_to_bcd(second) & 0x7F,
            self._dec_to_bcd(minute) & 0x7F,
            self._dec_to_bcd(hour) & 0x7F,
            0x80  # Setzt A1M4 auf 1 (Löst jeden Tag aus)
        ])
        self.i2c.writeto_mem(self.ADDR, self.REG_ALARM1, data)

        # Alarm aktivieren: INTCN und A1IE im Kontroll-Register setzen
        ctrl = self.i2c.readfrom_mem(self.ADDR, self.REG_CONTROL, 1)[0]
        ctrl = ctrl | 0x05
        self.i2c.writeto_mem(self.ADDR, self.REG_CONTROL, bytearray([ctrl]))

        # Flag vorsichtshalber direkt löschen
        self.clear_alarm()