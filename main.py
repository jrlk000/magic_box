import machine
import time
from motion import BewegungsSensor
#Momentane Packetstruktur muss für spätere Struktur
#im DateienRegister der ESP32 verändert werden.
#from BewegungsSensor.motion import BewegungsSensor
#from rfid_reader import RFIDReader
#from motor import MotorController

# ---- Konfiguration ----
PIR_PIN = 25 # Muss ein RTC-fähiger Pin sein.
INTERAKTIONSZEITRAUM = 5000

pir_sensor = BewegungsSensor(PIR_PIN)

def go_to_deep_sleep()->None:
    """
    Beobachtung des PIR-Pins konfigurieren und
    das Herunterfahren des Hauptsystems einleiten.
    """
    print("Bereite Deep Sleep vor...")

    #Strate die  Beobachtung des übergebenen RTC-Pins aus der RTC-Domäne.
    pir_sensor.ermögliche_aufwachen()
    time.sleep(500)

    print("ESP Deep Sleep eingeleitet.")
    time.sleep(500)

    #Fahre das Hauptsystem des ESP herunter.
    #Code darunter wird nicht mehr ausgeführt.
    machine.deepsleep()


def main():
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
        go_to_deep_sleep()

    start_time = time.ticks_ms()

    while True:
        if pir_sensor.is_motion_detected():
            start_time = time.ticks_ms()
            print("Knopf gedrückt / Bewegung da, verlängere Wach-Zeit...")

        elapsed_time = time.ticks_diff(time.ticks_ms(), start_time)

        if elapsed_time > INTERAKTIONSZEITRAUM:
            print("Timeout abgelaufen. Gehe wieder schlafen.")
            go_to_deep_sleep()

        time.sleep_ms(200)

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
    main()
