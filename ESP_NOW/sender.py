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

    #def __init__(self, start_pin)->None:
    def __init__(self) -> None:
        #self.start_pin = Pin(start_pin, Pin.IN, Pin.PULL_DOWN)
        #pin würd zum aufwachen aus deep-sleep verwendet also beachte RTC
        #priorisiert sind GPIO 32, 33
        self.ziel_mac =  b'\x08\xb6\x1fo.\xe4'

        # ---- Antene / ESPNOW ----
        # 1. AP-Modus sicherheitshalber ausschalten (verhindert Konflikte)
        wlan_ap = network.WLAN(network.AP_IF)
        wlan_ap.active(False)

        # 2. Station-Modus aktivieren (Pflicht für normales ESP-NOW)
        wlan_sta = network.WLAN(network.STA_IF)
        wlan_sta.active(True)
        wlan_sta.disconnect()  # Trennen von evtl. alten Router-Verbindungen

        # 3. ESP-NOW starten
        self.esp_now = espnow.ESPNow()
        self.esp_now.active(True)
        """self.wlan = network.WLAN(network.STA_IF)

        self.esp_now = espnow.ESPNow()
        self.esp_now.active(True)"""
        print("Sender wurde konfiguriert.")

    """def wurde_pin_gedrückt(self):
        return self.start_pin.value()

    def switch_pin_zustand(self):
        self.start_pin.value(not self.start_pin.value)

    def _ermögliche_aufwachen(self)->None:
        esp32.wake_on_ext0(pin=self.start_pin, level=esp32.WAKEUP_ANY_HIGH)
        print(f"Wake-Up Triger durch RCT-Pin initialisiert.")

    def _gehe_schlafen(self)->None:
        #Starte Überwachung des RTC Pins
        self._ermögliche_schlafen()
        time.sleep(500)

        print("ESP deep sleep eingeleitet!")
        time.sleep(500)

        #herunterfahren des Hauptsystems, Code drunter wird nicht mehr ausgeführt
        machine.deepsleep()"""

    def _aktiviere_antenne(self):
        self.wlan.active(True)
        self.wlan.disconnect()

    def _aktiviere_esp_now(self):
        self.esp_now.active(True)
        #self.esp_now.add_peer(self.ziel_mac)

    def _verpacke_nachricht(self, aktion: str):
        daten = {"aktion" : aktion} # Befehl muss 'motor_starten' sein.
        msg_bytes = json.dumps(daten).encode('utf-8')
        return msg_bytes


    """def kontaktiere_empfänger(self):
        grund = machine.reset_cause()

        if grund == machine.DEEPSLEEP_RESET:
            self._aktiviere_antenne()
            self._aktiviere_esp_now()
            msg_bytes = self._verpacke_nachricht()

            #SEnde Nachricht
            erfolg = self.esp_now.send(self.ziel_mac, msg_bytes)

            if erfolg:
                print("Erfolgreich auftrag an Empfänger übermittelt.")
            else:
                print("Senden fehlgecshlagen (Empfänger nicht erreichbar).")

            time.sleep_ms(100)

            #RTC-Pin konfiguration als Weckruf enthalten.
            self._gehe_schlafen()
        else:
            print("ACHTUNG: Kaltstart oder falscher Code! Gehe in 2 Sekunden wieder schlafen.")
            time.sleep(2)
            self.gehe_schalfen()"""

    """def kontaktiere_empfänger_debug(self):
        self._aktiviere_antenne()
        self._aktiviere_esp_now()
        msg_bytes = self._verpacke_nachricht("Starte Interaktion")

        #SEnde Nachricht
        erfolg =  self.esp_now.send(self.ziel_mac, msg_bytes)

        if erfolg:
            print("Auftrga an Empfänger übermittelt.")

        else:
            print("Auftrag konnte an Empfänger nicht übermittelt werden.")
        return erfolg
"""
    def kontaktiere_empfänger_debug(self):
        """
        Sendet Daten. Falls der Peer fehlt, wird er automatisch hinzugefügt.
        Fängt Längen- und Existenz-Fehler hardwarenah ab.
        """
        # 1. Vorab-Check der Paketgröße (vom ersten Fehler gelernt)
        """if len(data) > espnow.MAX_DATA_LEN:
            print(f"Fehler: Daten zu groß ({len(data)} Bytes).")
            return False"""

        try:
            # 2. Wir versuchen einfach zu senden
            msg_bytes = self._verpacke_nachricht("Starte Interaktion")
            self.esp_now.send(self.ziel_mac, msg_bytes, True)
            print("Erfolg: Nachricht wurde gesendet und per ACK bestätigt!")
            return True

        except OSError as err:
            # err.args ist ein Tuple: (Fehlercode, Fehlermeldung)
            if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                print("Warnung: Peer war nicht registriert. Füge ihn jetzt hinzu...")

                try:
                    # Peer nachregistrieren
                    self.esp_now.add_peer(self.ziel_mac)

                    # Zweiter Sendeversuch
                    self.esp_now.send(self.ziel_mac, msg_bytes, True)
                    print("Erfolg: Nachricht im zweiten Anlauf gesendet!")
                    return True

                except OSError as add_err:
                    print(f"Kritischer Fehler beim Nachregistrieren: {add_err}")
                    return False
            else:
                # Ein ganz anderer Hardware-Fehler (z.B. WLAN aus)
                print(f"Allgemeiner Sende-Fehler: {err}")
                return False

    def deinit_sender(self):
        try:
            self.wlan.active(False)
            self.esp_now.active(False)
            print("Sender heruntergefahren...")
        except Exception as e:
            print(e)
