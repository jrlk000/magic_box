import machine
import time
from motor import BTS7960Motor

"""from ESP_NOW.Empfänger import Empfänger
#Momentane Packetstruktur muss für spätere Struktur
#im DateienRegister der ESP32 verändert werden.
#from Zeit_Modul.motion import Zeit_Modul
from LinearAktuator.motor import BTS7960Motor
from machine import esp32"""

#from Zeit_Modul.ds3231 import DS3231

# ---- Konfiguration ----
INTERAKTIONSZEITRAUM = 5000 #[ms]
AUSFAHRZEIT = 0 # [ms]
EINFAHRZEIT = 0 # [ms]

# ---- Motor Treiber ----
#Stromüberwachung
R_IS = 32
L_IS = 33

# Ermögliche das Ansteuern
R_EN = 22
L_EN = 23

# Kontrolliere Richtung und Geschwindigkeit der Bewegung
R_PWM = 25
L_PWM = 27

# ---- DS3231 Uhr Modul ----
# I2C Pins (SDA: Datenleitung, SCL: Taktleitung)
PIN_SDA = 26
PIN_SCL = 27

# Hardware-Interrupt Pin (verbunden mit SQW am DS3231)
PIN_WAKE = 33

# Aktiv-Fenster Definition
START_STUNDE = 12
END_STUNDE = 16


def enter_deep_sleep(rtc, wake_pin):
    """Programmiert den RTC-Wecker und schickt den ESP schlafen."""
    print(f"Setze Wecker auf {START_STUNDE:02d}:00:00 Uhr...")

    try:
        # Alarm für den nächsten Tag/Startzeitpunkt stellen
        rtc.set_alarm(START_STUNDE, 0, 0)
        # WICHTIG: Flag löschen, sonst weckt der SQW Pin den ESP sofort wieder auf!
        rtc.clear_alarm()
    except OSError as e:
        print(f"Kritischer I2C Fehler beim Wecker stellen: {e}")
        # Fallback: Wenn RTC ausfällt, schlafe pauschal für 1 Stunde (interner Timer)
        machine.deepsleep(3600000)

    print(f"Aktiviere Wake-Up an Pin {PIN_WAKE} (LOW-Signal erwartet).")
    esp32.wake_on_ext0(pin=wake_pin, level=esp32.WAKEUP_ALL_LOW)

    print("Gehe in Deep Sleep. Gute Nacht!")
    time.sleep(0.1)  # Kurze Pause, damit die Print-Ausgabe über Serial fertig laden kann
    machine.deepsleep()


def run_active_tasks(rtc, empfänger, motor):
    """
    Läuft im Aktivzeitraum. Wartet dank optimiertem Timeout
    nahezu lückenlos auf ESP-NOW Signale.
    """
    print(">>> ESP im Aktivmodus. Warte auf Signale...")

    while True:
        # 1. Uhrzeit prüfen
        try:
            _, _, _, stunde, _, _ = rtc.get_time()
        except OSError:
            print("Fehler beim Lesen der RTC in der Schleife. Versuche es später erneut.")
            time.sleep(5)
            continue

        # 2. Prüfen, ob wir das Fenster verlassen haben
        if not (START_STUNDE <= stunde < END_STUNDE):
            print(">>> Aktivfenster beendet. Verlasse die Schleife.")
            break

        # 3. Lauschen
        daten = empfänger.lauschen()

        # 4. Signal prüfen, Motor Interaktion starten
        if daten:
            print("Gültiges Signal erhalten. Starte Motor...")
            motor_interaktion(motor)
            break




def motor_interaktion(motor: BTS7960Motor):
    """
    Steuert gesamte Motor interaktion: Hochfahren und Runterfahren.
    Args
    ----
    bool: True wenn Vorwärts bewegung, False andernfalls.

    Returns
    -------
    bool: Zustand unfd Geschwindigkeit wurde erfolgreich eingestellt.
    """
    print("Motor interaktion statartet...")
    #Ermöliche die Motor Ansteuerung
    motor.wechsele_aktuellen_zustand()

    #Motor HOCHFAHREN.
    motor.regle_geschwindigkeit(vorwärts=True)

    #Warte Endzustand des Motors ab.
    motor.warte_auf_endanschlag()

    #Zeitrahmen für User-Interaktion abwarten (Best Practice MicroPython)
    print(f"Warte {INTERAKTIONSZEITRAUM / 1000} Sek. auf User-Interaktion...")
    start_zeit = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_zeit) < INTERAKTIONSZEITRAUM:
        print(f"Verbleibende Zeit: {INTERAKTIONSZEITRAUM-time.ticks_diff(time.ticks_ms(), start_zeit)}")
        time.sleep_ms(50)

    motor.regle_geschwindigkeit(vorwärts=False)

    motor.warte_auf_endanschlag()

    motor.stop_motor()

    print("---- Motorinteraktion abgeschlossen. ----")




def run():
    print("\n--- ESP32 Wake-Up Routine gestartet ---")

    # I2C Bus initiieren
    i2c = machine.I2C(0, scl=machine.Pin(PIN_SCL), sda=machine.Pin(PIN_SDA))

    #Empfänger erstellen
    empfänger = Empfänger()
    empfänger.sende_MAC() #einmaliges Senden der MAC-Addresse


    # Aufwach-Pin initiieren (Pull-Up ist wichtig, da der SQW Pin auf LOW zieht)
    wake_pin = machine.Pin(PIN_WAKE, mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)

    try:
        # RTC Objekt erstellen
        rtc = DS3231(i2c)

        #Erstelle ein BTS7960 Motor Treiber instanz
        motor = BTS7960Motor(R_IS,
                             L_IS,
                             R_PWM,
                             L_PWM,
                             R_EN,
                             L_EN)

        # Zwingend das Alarm-Flag des letzten Aufwachens bereinigen
        rtc.clear_alarm()

        # Aktuelle Zeit ausgeben
        jahr, monat, tag, stunde, minute, sekunde = rtc.get_time()
        print(f"Systemzeit: {tag:02d}.{monat:02d}.{jahr} - {stunde:02d}:{minute:02d}:{sekunde:02d}")

    except OSError as e:
        print(f"Fehler bei der RTC-Initialisierung: {e}")
        print("Gehe in 5 Minuten Sicherheits-Schlaf...")
        machine.deepsleep(300000)  # 5 Minuten interner Schlaf als Notfall-Lösung

    # Prüfen, ob wir uns gerade innerhalb des Fensters befinden
    if START_STUNDE <= stunde < END_STUNDE:
        run_active_tasks(rtc, empfänger, motor)

    # Wenn die Aufgabe erledigt ist oder wir außerhalb des Fensters wach wurden:
    enter_deep_sleep(rtc, wake_pin)

def run_motor_debug():
    print("\n--- ESP32 Motor Debug gestartet ---")

    # I2C Bus initiieren
    #i2c = machine.I2C(0, scl=machine.Pin(PIN_SCL), sda=machine.Pin(PIN_SDA))

    # Empfänger erstellen
    #empfänger = Empfänger()
    #empfänger.sende_MAC()  # einmaliges Senden der MAC-Addresse

    # Aufwach-Pin initiieren (Pull-Up ist wichtig, da der SQW Pin auf LOW zieht)
    #wake_pin = machine.Pin(PIN_WAKE, mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)

    try:
        # RTC Objekt erstellen
        #rtc = DS3231(i2c)

        # Erstelle ein BTS7960 Motor Treiber instanz
        motor = BTS7960Motor(32,
                             33,
                             25,
                             26,
                             22,
                             23)

        message = input("Starte motor interaktion y/n:").strip().lower()

        if message == "y":
            motor_interaktion(motor)


        print("Interaktion beendet!")

        # Zwingend das Alarm-Flag des letzten Aufwachens bereinigen
        #rtc.clear_alarm()

        # Aktuelle Zeit ausgeben
        #jahr, monat, tag, stunde, minute, sekunde = rtc.get_time()
        #print(f"Systemzeit: {tag:02d}.{monat:02d}.{jahr} - {stunde:02d}:{minute:02d}:{sekunde:02d}")

    except OSError as e:
        print(f"Fehler bei der RTC-Initialisierung: {e}")
        print("Gehe in 5 Minuten Sicherheits-Schlaf...")
        machine.deepsleep(300000)  # 5 Minuten interner Schlaf als Notfall-Lösung

    # Prüfen, ob wir uns gerade innerhalb des Fensters befinden
    #if START_STUNDE <= stunde < END_STUNDE:


    # Wenn die Aufgabe erledigt ist oder wir außerhalb des Fensters wach wurden:
    #enter_deep_sleep(rtc, wake_pin)









"""class Main():

    def __init__(self):
        

    
        self.motor = LinearAktuator(R_IS, L_IS, R_PWM, L_PWM, R_EN, L_EN)

    




    def main(self):
        # --- WICHTIGE NEUERUNG ---
        # Wir halten das Skript für 3 Sekunden an!
        # Das gibt deinem PC die Zeit, den COM-Port zu erkennen
        # und den Seriellen Monitor zu öffnen, BEVOR der ESP wieder schlafen geht.
        time.sleep(3)

        cause = machine.reset_cause()

        print("-----------------------------------")
        print("SYSTEM GESTARTET!")
        print(f"Gemeldeter Reset-Grund (Code): {cause}")
        print(f"Erwarteter Code für Deep Sleep: {machine.DEEPSLEEP_RESET}")
        print("-----------------------------------")

        if cause == machine.DEEPSLEEP_RESET:
            print("AUFGEWACHT: Trigger wurde erfolgreich ausgelöst!")
        else:
            print("ACHTUNG: Kaltstart oder falscher Code! Gehe in 2 Sekunden wieder schlafen.")
            time.sleep(2)
            self.go_to_deep_sleep()

        start_time = time.ticks_ms()

        #Aktuator fährt aus.
        self.motor_interaktion(vorwärts=True)
        time.sleep_ms(AUSFAHRZEIT)

        while True:
            if pir_sensor.is_motion_detected():
                start_time = time.ticks_ms()
                print("Knopf gedrückt / Bewegung da, verlängere Wach-Zeit...")

            # Zeitüberwachung
            elapsed_time = time.ticks_diff(time.ticks_ms(), start_time)

            #Aktuator fährt ein.
            if elapsed_time > INTERAKTIONSZEITRAUM:
                self.motor_interaktion(vorwätrs=False)

                print("Interaktionszeitraum ist zu Ende.")
                time.sleep(EINFAHRZEIT)

                print("Timeout abgelaufen. Gehe wieder schlafen.")
                self.go_to_deep_sleep()

            time.sleep_ms(200)"""






"""def main():
    # ---- Aufwachen zuordnen ---
    if machine.reset_cause() == machine.DEEPSLEEP_RESET:
        print("Aufgewacht: Bewegung erkannt!")
        print(f"Aktuelles signal an Trigger-Pin {pir_sensor.trigger_pin.value()}")
        #rfid karten leser starten
    else:
        print("Aufwachgrund war keine registrierete Bewegung",
              "Deep Sleep eingeleitet.")
        go_to_deep_sleep()

    # ----Zeitmessung starten ----
    start_zeit = time.tick_ms()

    while True:
        # ---- smarter Timeout ----
        if pir_sensor.wurde_bewegung_erkannt():
            start_time = time.ticks_ms()
            print("Bewegung erkannt, verlängere Wach-Zeit...")

        # ---- Interaktionsinterval prüfen ----
        vergangene_zeit = time.ticks.diff(time.tick_ms(), start_zeit)

        if vergangene_zeit > INTERAKTIONSZEITRAUM:
            print("Zeitfenster zum einlesen  der Karten ist geschlossen!")
            go_to_deep_sleep()

        print(f"Fenster zum Kartenlesen ist noch {INTERAKTIONSZEITRAUM - vergangene_zeit} [sek] geöffnet.")
        time.sleep_ms(200)"""

"""
Exkurs Startvorgänge des ESP Chips: 

ESP startet die main nach jedem aufwach wieder von neu, sodass 
nach jedem deep sleep der Trigger zum aufwachen neu gesetzt
werden muss. 


ESP hat interne HardwareÜberwachung die genau 
Buch darüber führt, warum der Chip neu gestartet wurde.

System war vom Strom getrennt : Kaltstart
Reset Taste des Boards : Hardware-Reset
Sicherheits Reset bei aufgehängtem Code : Watchdog-TimerReset
urch Programmierumgebung : Software-Reset
Aufwecken durch Trigger : DEEP_SLEEP_RESET
"""

if __name__ == "__main__":
    run_motor_debug()
