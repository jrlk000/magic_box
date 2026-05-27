# ---- Imports ----
from machine import Pin
import espnow
import json
import esp32
import machine
import time
import network
import esp32



class Sender:

    def __init__(self, start_pin)->None:
        self.start_pin = Pin(start_pin, Pin.IN, Pin.PULL_DOWN)
        #pin würd zum aufwachen aus deep-sleep verwendet also beachte RTC
        #priorisiert sind GPIO 32, 33
        self.ziel_mac = "" #b'\x24\x0A\xC4\x11\x22\x33'

        # ---- Antene / ESPNOW ----
        self.wlan = network.WLAN(network.STA_IF)

        self.esp_now = espnow.ESPNow()

        print("Sender wurde konfiguriert.")

    def wurde_pin_gedrückt(self):
        return self.start_pin.value()

    def switsch_pin_zustand(self):
        self.start_pin.value(not self.start_pin.value)

    def _ermögliche_aufwachen(self)->None:
        esp32.wake_on_ext0(pin=self.start_pin, level=esp32.WAKEUP_ANY_HIGH)
        print(f"Wake-Up Triger durch RCT-Pin initialisiert.")

    def gehe_schlafen(self)->None:
        #Starte Überwachung des RTC Pins
        self._ermögliche_schlafen()
        time.sleep(500)

        print("ESP deep sleep eingeleitet!")
        time.sleep(500)

        #herunterfahren des Hauptsystems, Code drunter wird nicht mehr ausgeführt
        machine.deepsleep()

    def aktiviere_antenne(self):
        self.wlan.active(True)
        self.wlan.disconnect()

    def aktiviere_esp_now(self):
        self.esp_now.active(True)
        self.esp_now.add_peer(self.ziel_mac)

    def verpacke_nachricht(self, aktion: str):
        daten = {"aktion" : aktion} # Befehl muss 'motor_starten' sein.
        msg_bytes = json.dumps(daten).encode('utf-8')
        return msg_bytes


    def kontaktiere_empfänger(self):
        grund = machine.reset_cause()

        if grund == machine.DEEPSLEEP_RESET:
            self.aktiviere_antenne()
            self.aktiviere_esp_now()
            msg_bytes = self.verpacke_nachricht()

            #SEnde Nachricht
            erfolg = self.esp_now.send(self.ziel_mac, msg_bytes)

            if erfolg:
                print("Erfolgreich auftrag an Empfänger übermittelt.")
            else:
                print("Senden fehlgecshlagen (Empfänger nicht erreichbar).")

            time.sleep_ms(100)

            #RTC-Pin konfiguration als Weckruf enthalten.
            self.gehe_schlafen()
        else:
            print("ACHTUNG: Kaltstart oder falscher Code! Gehe in 2 Sekunden wieder schlafen.")
            time.sleep(2)
            self.gehe_schalfen()

