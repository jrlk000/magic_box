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