"""
Innen Leben des Motortreibers:

besteht intern aus einer H-Brücke (vier dicke elektronische Schalter)

PWM: diktiert wie schnell der Motor laufen soll, R/L steuert die Richtung.
Enable: Hauptschalter für die H-Brücke -> beide EN_pins müssen auf HIHG sein,
 damit Motor angesteuert werden kann.

 Aufteilung: Motortreiber Chip, kleiner Logik-Chip
 Mikrochip besitzt an jedem einzelnen Daten-Pin interne ESD-Schutzdioden.
"""

"""
motor Treiber als verbindung zwischen der ESP und dem Aktuator.
"""

import time
import machine
from machine import Pin, PWM, ADC


class L289NMotor:
    # ---- Logik Pin Konfiguration ----

    """#Stromüberwachung mit Mapping von 1:8500 zwischen Motorstrom und gemessenen Strom
    R_IS = 32
    L_IS = 33

    #Ermögliche dsa ansteuern
    IN1 = 22
    IN2 = 23

    #Kontrolliere Geschwindigkeit der Bewegung
    ENA(PWM) = 26 (duty cycle, frequency)
    """

    """def error_mode(self, error_msg):
        print(f"KRITISCHER FEHLER: {error_msg}")

        # 1. Alles sicher abschalten (Safe State)
        # z.B. pwms auf 0 setzen
        for pwm in self.pwms:
            pwm.deinit()

        for adc in self.adcs:
            adc.init(mode=machine.Pin.IN, pull=None)

        for en in self.ens:
            en.value(0)

        # 2. Fehler visuell anzeigen
        led = machine.Pin(2, machine.Pin.OUT)  # Interne blaue LED am ESP32
        while True:
            led.value(not led.value())
            time.sleep(0.1)"""

    def __init__(self, in_1_pin: int, in_2_pin: int, pwm_pin: int) -> None:
        """

        Args
        ----

        ---- in_1 und in_2 steuern die Motoraktivität ----

        in_1 HIGH, in_2 LOW : Vorwärts
        in_1 LOW, in_2_HIGH: Rückwärts

        ---- pwm ----
        pwm steuert die Geschwindigkeit über duty cycle und freqency


        """

        # self.spannungsschwelle = 100*3.3/2**16
        #self.spannungsschwelle = 0.125885009765625
        self.blanking_time = 500
        self.ins = []

        try:
            # ADCs
            """self.adcs = [ADC(Pin(l_adc_num)), ADC(Pin(r_adc_num))]
            for adc in self.adcs:
                try:
                    adc.block().init(bits=12)  # map analog signal to {1, ..., 2**12}
                except AttributeError:
                    pass
                adc.init(atten=ADC.ATTN_11DB)  # allows an intervall from to [0, 3.3] [V]"""

            # PWMs
            self.pwm = PWM(Pin(pwm_pin, Pin.OUT, value=0, pull=Pin.PULL_DOWN))

            # Enables
            self.ins = [Pin(in_1_pin, Pin.OUT, value=0, pull=Pin.PULL_DOWN),
                        Pin(in_2_pin, Pin.OUT, value=0, pull=Pin.PULL_DOWN)]
            print("Aktuator erfolgreich initialisiert.")

        except ValueError as e:
            # self.error_mode(f"Hardwarefehler: {e}, versuche Neustart in 5 Sekunden...")
            self.deinit_motor()
            print("Hardwarefehler, Hardware wurde gestopt...Mikrocontroller reset...")
            time.sleep(5)
            machine.reset()  # Führt einen Hard-Reset des Mikrocontrollers aus
        except Exception as e:
            print(f"Unbekannter Hardware-Fehler bei Initialisierung: {e}")
            self.deinit_motor()
            print("Versuche Neustart in 5 Sekunden...")
            time.sleep(5)
            machine.reset()  # Führt einen Hard-Reset des Mikrocontrollers aus
        return None

    """def wechsele_aktuellen_zustand(self):

        Ermögliche die Ansteuerung des Motors ber den Treiber durch die ESP32.

        Return
        ------
        bool: Ansteuerung ermöglicht oder nicht.

        for en in self.ens:
            en.value(not en.value())

        zustand = "ermöglicht" if self.ens[0].value() else "deaktiviert"
        print(f"Treiber Ansteuerung {zustand}!")
        return None"""

    def treiber_vorwärts(self)->None:
        """

        """
        self.ins[0].value(1)
        self.ins[1].value(0)
        time.sleep_ms(self.blanking_time)
        print("Treiber stellt vorwärts ein...!")

    def treiber_rückwärts(self)->None:
        """

        """
        self.ins[0].value(0)
        self.ins[1].value(1)
        print("Treiber stellt rückwärts ein!")

    def regle_geschwindigkeit(self, dc=(2 ** 16)/4, frequency=2 * 1e3):
        """
        Regle die Geschwindigkeit des Aktuators über ein mapping durch PWM signale
        mit 16-bit resolution.



        Params
        ------
        duty_cycle : Setze HIGH-Anteil innerhalb Signal Periode [0, 2**10]
        frequency : PWm Frequenze - Wechsel zwischen High, Low pro Sekunde [1000, 4000] [Hz]
        """
        try:
            # Clamping, um ValueErrors zu verhindern.
            dc = int(max(0, min(2 ** 16 - 1, dc)))
            frequency = int(max(1, frequency))

            # High PWM side
            self.pwm.freq(frequency)
            self.pwm.duty_u16(dc)

            print('Geschwindigkeitsreglung eingestellt.')

        except ValueError as e:
            print(f"[WARNUNG]: Ungültige PWM Parameter: {e}")
            # Sicherheits-Fallback: Motor stoppen!
            self.pwm.duty_u16(0)
            self.pwm.deinit()
        return None

    """def motor_strom_monitoring(self, vorwärts=True):
        
        Hier kann gut die Logik für Probleme in der Motor Bestromung gefunden werden
        und darauf hin das system lahmgelegt werden.
        :return:
        
        idx = int(vorwärts)
        # spannungen = list()

        try:
            adc = self.adcs[idx]
            spannung = (adc.read_u16() / 2 ** 16) * 3.3
            # spannungen.append(spannung) # [V]
            print(f"Motor Spannungsabfall: {spannung:.2f}")
            return spannung
        except Exception as e:
            print(f"Fehler beim Lesen des Stromsensors: {e}")
            return [0.0, 0.0]"""

    """def warte_auf_endanschlag(self):
        
        Blockiert das Programm, solange Strom fließt.
        Bricht ab, sobald die Endlage erreicht ist (Strom/Spannung sinkt).
         
        print("Überwache Motorstrom...")
        # Kurze Austastzeit (Blanking Time), damit der Motor überhaupt erst anlaufen kann
        time.sleep_ms(self.blanking_time)

        while True:
            aktuelle_spannung = self.motor_strom_monitoring()

            if aktuelle_spannung < self.spannungsschwelle:
                print("-> Endlage detektiert.")
                break

            time.sleep_ms(50)"""  # CPU entlasten

        # print(f"Durch Motor Strom abgefangene Spannungen: {spannungen[0]}, {spannungen[-1]} [V]")Hauptschleife der Ansteuerung:

    def deinit_motor(self):
        """

        """
        try:
            self.pwm.duty_u16(0)
            self.pwm.deinit()
        except (OSError, AttributeError) as e:
            print(f"KRITISCHER FEHLER: {e}")

        try:
            for enable in self.ins:
                enable.value(0)
        except(OSError, RuntimeError) as e:
            print(f"KRITISCHER FEHLER: {e}")