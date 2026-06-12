import network
import ubinascii
import espnow
import json
import errno

class Empfanger:

    def __init__(self):
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
            self.deinit_empfänger()

        # ---- Cooldown-Variablen ----
        self.cooldown_zeit = 2*1e3 #Sperrzeit für neue Signale [ms]
        self.letzter_befehl_zeitpunkt = 0
        self.motor_leuft = False
        self.mac = "08:b6:1f:6f:2e:e4"

    def deinit_empfänger(self):
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

    def sende_MAC(self):
        # MAC-Adresse auslesen und lesbar formatieren
        mac_bytes = self.wlan.config('mac')
        mac_string = ubinascii.hexlify(mac_bytes, ':').decode()

        print("Die MAC-Adresse DIESES Boards lautet:", mac_string, mac_bytes)
        return mac_string

    def lauschen(self)->str|None:
        print("Warte auf ankommende Signale...")

        try:
            mac, msg = self.esp_now.recv(timeout_ms=1000)

        except OSError as ex:
            err_code = ex.arg[0]

            if err_code == errno.ETIMEDOUT:
                #Keine Daten im Puffer
                print("Keine Pakete in der Nähe...")
                pass

            elif err_code == errno.ECONNRESET:
                print("[WARNUNG]: ESP-NOW Empfangspuffer voll (Datenverlust)!")

            else:
                print(f"Kritischer Fehler beim Empangen von daten: {ex}")
                self.deinit_empfänger()

        if not msg:
            return None

        try:
            text = msg.decode('utf-8')
            print("Erhaltene Nachricht", text)
            return json.loads(text)

        except (ValueError, TypeError) as ex:
            print('Fehler bei decodieren des Signals.'
                  f'Fehlermeldung: {ex}')
            return None



    """def lauschen(self):
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
                    print("Ignoriere redundantes Signal.")"""

