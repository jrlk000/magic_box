import network
import ubinascii
import espnow
import json
import time

class Empfänger:

    def __init__(self):
        # ---- WLAN einschalten ----
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        #mögliche Verbindungen trennen
        self.wlan.disconnect()

        # ---- ESP-NOW aktivieren ----
        self.esp_now = espnow.ESPNOW()
        self.esp_now.active(True)
        print("Empfänger bereit. Warte auf ESP-NOW Pakete...")

        # ---- Cooldown-Variablen ----
        self.cooldown_zeit = 2*1e3 #Sperrzeit für neue Signale [ms]
        self.letzter_befehl_zeitpunkt = 0
        self.motor_leuft = False

    def sende_MAC(self):
        # MAC-Adresse auslesen und lesbar formatieren
        mac_bytes = self.wlan.config('mac')
        mac_string = ubinascii.hexlify(mac_bytes, ':').decode()

        print("Die MAC-Adresse DIESES Boards lautet:", mac_string)
        return mac_string

    def lauschen(self):
        while True:
            mac, msg = self.esp_now.recv(timeout_ms=500)

            if msg:
                momentaner_zeitpunkt = time.tick_ms()

                #Nehme neue Inhalte erst nach Sperrzeit wieder war.
                if time.ticks_diff(momentaner_zeitpunkt, self.letzter_befehl_zeitpunkt) > self.cooldown_zeit:

                    #Prüfe ob Signal, ein Starter ist.
                    try:
                        text = msg.decode('utf-8')
                        daten = json.loads(text)

                    except Exception as err:
                        print("Fehler beim lesen der Nachricht:", err)

                    print(f"Befehl erhalten: {daten}")

                    #Prüfe ob der Motor schon läuft
                    if not self.motor_lauft:
                        print(">>> Erstes Signal Akzeptiert! Motor startet.")
                        # motor_starten()
                        motor_lauft = True

                        self.letzter_befehl_zeitpunkt = momentaner_zeitpunkt
                    else:
                        print("Motor läuft bereits. Signal ignoriert.")

                else:
                    print("Ignoriere redundantes Signal.")

