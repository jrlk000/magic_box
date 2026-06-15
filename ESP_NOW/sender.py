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

        try:
            # 1. AP-Modus sicherheitshalber ausschalten
            wlan_ap = network.WLAN(network.AP_IF)
            wlan_ap.active(False)

            # 2. Station-Modus aktivieren
            wlan_sta = network.WLAN(network.STA_IF)
            wlan_sta.active(True)
            wlan_sta.disconnect()  # Trennen von evtl. alten Router-Verbindungen

            # 3. ESP-NOW starten
            self.esp_now = espnow.ESPNow()
            self.esp_now.active(True)

        except OSError as e:
            print(f"Fehler bei Initialisiereung des Senders {e}.")
            self.deinit_sender()

    def deinit_sender(self):
        try:
            #Deaktivierung

            # ----Wlan----
            wlan_sta = network.WLAN(network.STA_IF)
            wlan_sta.active(False)

            wlan_ap = network.WLAN(network.AP_IF)
            wlan_ap.active(False)

            # ----Esp-now----
            self.esp_now.active(False)

            print("Sender heruntergefahren...")

        except Exception as e:
            print(f"Fehler beim Deinitialisieren des Senders: {e}")



    def _verpacke_nachricht(self, nachricht: str)->str|None:
        """
        Verschlüssele Nachricht in byte-code.
        """
        daten = {"nachricht" : nachricht}
        msg_bytes = json.dumps(daten).encode('utf-8')

        if len(msg_bytes) > espnow.MAX_DATA_LEN:
            print(f"Fehler: Daten zu groß ({len(msg_bytes)} Bytes).")
            return None

        return msg_bytes

    def kontaktiere_empfänger_debug(self, msg: str):
        """
        Sendet Daten. Falls der Peer fehlt, wird er automatisch hinzugefügt.
        Fängt Längen- und Existenz-Fehler hardwarenah ab.
        """
        msg_bytes = self._verpacke_nachricht(msg)

        try:
            # 1. Sendeversuch
            self.esp_now.send(self.ziel_mac, msg_bytes, True)
            print("Erfolg: Nachricht wurde gesendet!")
            return True

        except OSError as err:
            # err.args ist ein Tuple: (Fehlercode, Fehlermeldung)
            if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                print("Warnung: Peer war nicht registriert. Füge ihn jetzt hinzu...")

                try:
                    # Peer nachregistrieren
                    self.esp_now.add_peer(self.ziel_mac)

                    # 2. Sendeversuch
                    self.esp_now.send(self.ziel_mac, msg_bytes, True)
                    print("Erfolg: Nachricht im zweiten Anlauf gesendet!")
                    return True

                except OSError as add_err:
                    print(f"Kritischer Fehler beim Nachregistrieren: {add_err}")
                    #self.deinit_sender() #DEinitialisieren 2 sek. Dauerfeuer Fehlermeldungen harmlos, lediglich nicht reagieren  des empfängers.
                    return False
            else:
                # Ein ganz anderer Hardware-Fehler (z.B. WLAN aus)
                print(f"Allgemeiner Sende-Fehler: {err}")
                #self.deinit_sender()
                return False

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
