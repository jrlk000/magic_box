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
verbindung zwischen Treiber und der ESP zum Steuern des Aktuators

"""

import time
import machine
from machine import Pin, PWM, ADC

class LinearAktuator:

    # ---- Logik Pin Konfiguration ----

    """#Stromüberwachung mit Mapping von 1:8500 zwischen Motorstrom und gemessenen Strom
    R_IS = 21
    L_IS = 19

    #Ermögliche dsa ansteuern
    R_EN = 22
    L_EN = 23

    #Kontrolliere Richtung und Geschwindigkeit der Bewegung
    RPWM = 25
    LPWM = 26"""

    def error_mode(self, error_msg):
        print(f"KRITISCHER FEHLER: {error_msg}")

        # 1. Alles sicher abschalten (Safe State)
        # z.B. pwms auf 0 setzen
        for pwm in self.pwms:
            pwm.deinit()

        for en in self.ens:
            en.value(0)

        # 2. Fehler visuell anzeigen
        led = machine.Pin(2, machine.Pin.OUT)  # Interne blaue LED am ESP32
        while True:
            led.value(not led.value())
            time.sleep(0.1)

    def __init__(self, r_adc_num: int, l_adc_num: int, r_pwm_num: int, l_pwm_num: int, r_en_num: int, l_en_num: int) -> None:
        #Stromüberwachung/Strommesser (Strom von Battery duch Motor)
        #mit Mapping von 1:8500 zwischen Motorstrom und gemessenen Strom,
        # Messung erfolgt über Spannungsverlust über Widerstand
        try:
            self.adcs = [ADC(Pin(r_adc_num)), ADC(Pin(l_adc_num))]
            for adc in self.adcs:
                try:
                    adc.block().init(bits=12)  # map analog signal to {1, ..., 2**12}
                except AttributeError:
                    pass
                adc.init(atten=ADC.ATTN_11_DB)  # allows an intervall from to [0, 3.3] [V]

            # Ermöglicht das Ansteuern
            self.pwms = [PWM(Pin(r_pwm_num)), PWM(Pin(l_pwm_num))]
            for pwm in self.pwms:
                pwm.freq(2000)
                pwm.duty(0)

            # Kontrolliere Richtung und Geschwindigkeit der Bewegung
            self.ens = [Pin(r_en_num, Pin.OUT, value=0, pull=Pin.PULL_DOWN),
                        Pin(l_en_num, Pin.OUT, value=0, pull=Pin.PULL_DOWN)
                        ]
            print("Aktuator erfolgreich initialisiert.")

        except ValueError as e:
            self.error_mode(f"Hardwarefehler: {e}, versuche Neustart in 5 Sekunden...")
            print("Hardwarefehler, versuche Neustart in 5 Sekunden...")
            time.sleep(5)
            machine.reset()  # Führt einen Hard-Reset des Mikrocontrollers aus
        except Exception as e:
            self.error_mode(f"Unbekannter Hardware-Fehler bei Initialisierung: {e}")
            print("Versuche Neustart in 5 Sekunden...")
            time.sleep(5)
            machine.reset()  # Führt einen Hard-Reset des Mikrocontrollers aus

    """was muss gemacht werden, wann muss es gemaht werden und welche abfolgen gibt es."""

    """
    1) Treiber muss enablet werden, um steuerung per pwm zu machen 
    2) Motor kann mit verschieden geschwindigkeiten basierend auf dem Duty Cycle gesteuert, werden
    also Konfiguration des duty cycles, hochfahren, runterfahren
    
    Frage: 
    Wie mit try, except böcken etc auf hardware probleme reagieren?
    """

    def wechsele_aktuellen_zustand(self)-> None:
        """
        Ermögliche die Ansteuerung des Motors über den Treiber durch die ESP32.
        """
        for en in self.ens:
            en.value(not en.value())

        zustand = "ermöglicht" if self.ens[0].value() else "deaktiviert"
        print(f"Treiber Ansteuerung {zustand}!")
        return None

    def regle_geschwindigkeit(self,dc=2**10/4, frequency=2*1e3):
        """
        Regle die Geschwindigkeit des Aktuators über ein mapping durch PWM signale
        mit 10-bit resolution.

        Params
        ------
        duty_cycle : Setze HIGH-Anteil innerhalb Signal Periode [0, 2**10]
        frequenze : PWm Frequenze - Wechsel zwischen High, Low pro Sekunde [1000, 4000] [Hz]
        """
        try:
            #Clamping, um ValueErrors zu verhindern.
            dc = int(max(0, min(1023, dc)))
            frequency = max(1, frequency)

            for pwm in self.pwms:
                pwm.freq(frequency)
                pwm.duty(dc)

        except ValueError as e:
            print(f"[WARNUNG]: Ungültige PWM Parameter: {e}")
            #Sicherheits-Fallback: Motor stoppen!
            for pwm in self.pwms:
                pwm.duty(0)

    def motor_strom_monitoring(self):
        """
        Hier kann gut die Logik für Probleme in der Motor Bestromung gefunden werden
        und darauf hin das system lahmgelegt werden.
        :return:
        """
        spannungen = list()

        try:

            for adc in self.adcs:
                spannung = (adc.read_u16() / 2**16) * 3.3
                spannungen.append(spannung) # [V]
            print(f"Motor Spannungsabfall: {spannungen[0]:.2f} V, {spannungen[-1]:-2f} V")
            return spannungen
        except Exception as e:
            print(f"Fehler beim Lesen des Stromsensors: {e}")
            return [0.0, 0.0]

        print(f"Durch Motor Strom abgefangene Spannungen: {spannungen[0]}, {spannungen[-1]} [V]")



