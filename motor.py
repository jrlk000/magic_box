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

class BTS7960Motor:

    # ---- Logik Pin Konfiguration ----

    """#Stromüberwachung mit Mapping von 1:8500 zwischen Motorstrom und gemessenen Strom
    R_IS = 32
    L_IS = 33

    #Ermögliche dsa ansteuern
    R_EN = 22
    L_EN = 23

    #Kontrolliere Richtung und Geschwindigkeit der Bewegung
    RPWM = 25
    LPWM = 26"""

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

    def __init__(self, r_adc_num: int, l_adc_num: int, r_pwm_num: int, l_pwm_num: int, r_en_num: int, l_en_num: int) -> None:
        """

        Args
        ----
        IS-Pins (Strommessung):
        Benötigen R-IS und L-IS: Motor dreht vorwärts, der Strom fließt durch den oberen Schalter der
        rechten Halbbrücke in den Motor hinein und links gegegn GND. Nur der rechte Chip kann den Strom messen.
        Motor dreht rückwärts, ist es genau umekehrt.
        Da der Strom durch den Treibe rsehr hoch passiert ein  Mapping von 8500:1 zwischen Motorstrom und gemessenen Strom.

        adc_r: Strommessung, wenn Fluss von rechts nach links (Vorwärts)
        adc_l: Strommessung, wenn Fluss von links nach rechts (Rückwärts)

        Steuern der Drehrichtung über die PWMs:
        Vorwärts: PWM signal mit def. duty cycle auf R_PWM und L_PWM wird auf LOW gehalten
        Effekt: Rechte Seite des Motors wird i mTakt des PWM-Signals mit Vcc verbunden, während die linke Seite fest mitGND verbunden bleibt.
        Stromfluss von rechts nach links.

        Rückwärts: PWM-Signal auf L_PWM und R_PWM auf permanent low.
        Effekt: Linke Seite wird im Takt des PWM Signals mit Vcc verbunden während die rechte Seite fest an GND liegt.
        Stromfluss von links nach rechts

        l_pwm: Steuert linke Hälfte der H-Brücke
        r_pwm_: Steuert rechte Hälfte der H-Brücke

        en: Aktivierung der Brücke durch das Setzen auf High.
        """

        self.spannungsschwelle = 100*3.3/2**16

        self.adcs = []
        self.pwms = []
        self.ens = []

        try:
            # ADCs
            self.adcs = [ADC(Pin(l_adc_num)), ADC(Pin(r_adc_num))]
            for adc in self.adcs:
                try:
                    adc.block().init(bits=12)  # map analog signal to {1, ..., 2**12}
                except AttributeError:
                    pass
                adc.init(atten=ADC.ATTN_11DB)  # allows an intervall from to [0, 3.3] [V]

            # PWMs
            self.pwms = [PWM(Pin(l_pwm_num)), PWM(Pin(r_pwm_num))]
            for pwm in self.pwms:
                pwm.freq(2000)
                pwm.duty(0)

            # Enables
            self.ens = [Pin(l_en_num, Pin.OUT, value=0, pull=Pin.PULL_DOWN),
                        Pin(r_en_num, Pin.OUT, value=0, pull=Pin.PULL_DOWN)]
            print("Aktuator erfolgreich initialisiert.")

        except ValueError as e:
            #self.error_mode(f"Hardwarefehler: {e}, versuche Neustart in 5 Sekunden...")
            self.stop_motor()
            print("Hardwarefehler, Hardware wurde gestopt...Mikrocontroller reset...")
            time.sleep(5)
            machine.reset()  # Führt einen Hard-Reset des Mikrocontrollers aus
        except Exception as e:
            print(f"Unbekannter Hardware-Fehler bei Initialisierung: {e}")
            self.stop_motor()
            print("Versuche Neustart in 5 Sekunden...")
            time.sleep(5)
            machine.reset()  # Führt einen Hard-Reset des Mikrocontrollers aus
        return None

    def wechsele_aktuellen_zustand(self):
        """
        Ermögliche die Ansteuerung des Motors ber den Treiber durch die ESP32.

        Return
        ------
        bool: Ansteuerung ermöglicht oder nicht.
        """
        for en in self.ens:
            en.value(not en.value())

        zustand = "ermöglicht" if self.ens[0].value() else "deaktiviert"
        print(f"Treiber Ansteuerung {zustand}!")
        return None

    def regle_geschwindigkeit(self,dc=2**10, frequency=2*1e3, vorwärts=True):
        """
        Regle die Geschwindigkeit des Aktuators über ein mapping durch PWM signale
        mit 10-bit resolution.

        Vorwärts:
        r_pwm: PWM-Signal
        l_pwm: Low

        Rückwärts:
        r_pwm: Low
        l_pwm: PWM-Signal

        Params
        ------
        duty_cycle : Setze HIGH-Anteil innerhalb Signal Periode [0, 2**10]
        frequency : PWm Frequenze - Wechsel zwischen High, Low pro Sekunde [1000, 4000] [Hz]
        """
        i = int(vorwärts)
        j = i - 1
        try:
            #Clamping, um ValueErrors zu verhindern.
            dc = int(max(0, min(1023, dc)))
            frequency = int(max(1, frequency))

            #High PWM side
            pwm = self.pwms[i]
            pwm.freq(frequency)
            pwm.duty(dc)

            #Low PWM side
            self.pwms[j].duty(0)

        except ValueError as e:
            print(f"[WARNUNG]: Ungültige PWM Parameter: {e}")
            #Sicherheits-Fallback: Motor stoppen!
            for pwm in self.pwms:
                pwm.duty(0)
        return None

    def motor_strom_monitoring(self, vorwärts=True):
        """
        Hier kann gut die Logik für Probleme in der Motor Bestromung gefunden werden
        und darauf hin das system lahmgelegt werden.
        :return:
        """
        idx = int(vorwärts)
        #spannungen = list()

        try:
            adc = self.adcs[idx]
            spannung = (adc.read_u16() / 2**16) * 3.3
            #spannungen.append(spannung) # [V]
            print(f"Motor Spannungsabfall: {spannung:.2f}")
            return spannung
        except Exception as e:
            print(f"Fehler beim Lesen des Stromsensors: {e}")
            return [0.0, 0.0]

    def warte_auf_endanschlag(self):
        """
        Blockiert das Programm, solange Strom fließt.
        Bricht ab, sobald die Endlage erreicht ist (Strom/Spannung sinkt).
         """
        print("Überwache Motorstrom...")
        # Kurze Austastzeit (Blanking Time), damit der Motor überhaupt erst anlaufen kann
        time.sleep_ms(500)

        while True:
            aktuelle_spannung = self.motor_strom_monitoring()

            if aktuelle_spannung < self.spannungsschwelle:
                print("-> Endlage detektiert.")
                break

            time.sleep_ms(50)  # CPU entlasten

        #print(f"Durch Motor Strom abgefangene Spannungen: {spannungen[0]}, {spannungen[-1]} [V]")Hauptschleife der Ansteuerung:

    def stop_motor(self):

        try:
            for adc in self.adcs:
                adc.deinit()
        except Exception as e:
            print(f"KRITISCHER FEHLER: {e}")

        try:
            for pwm in self.pwms:
                pwm.deinit()
        except (OSError, AttributeError) as e:
            print(f"KRITISCHER FEHLER: {e}")

        try:
            for en in self.ens:
                en.value(0)
        except(OSError, RuntimeError)as e:
            print(f"KRITISCHER FEHLER: {e}")


        """
                finally:
            # Deinitialisiere verwndete ADCs und PWMs, schalte die Ansteuerung aus. 
            print("Sicherheits-Abschaltung: Deinitialisiere PWMs...")
            
            #PWMs
            for pwm in self.pwms:
                try:
                    pwm.duty(0)  # hihg pegel des signals innerhalb Periode auf 0 setzen
                    pwm.deinit()  # Schaltet die Hardware-PWM-Generierung komplett ab
                except:
                    pass
            
            #Enables
            for en in self.ens:
                try:
                    en.value(0)
                except:
                    pass
            
            #ADCs
            for adc in self.adcs:
                try:
                    adc.deinit()
                except:
                    pass
        """





