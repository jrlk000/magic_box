"""
Treiber ist die Verknüpfung zwischen der ESP32 als Logik Element
und dem Aktuator als Arbeiter.


Übersicht Verbindungen:
VCC, GND
R_IS, L_IS
R_EN, L_EN (Rückwärts, Vorwärts)
RPWM, LPWM (Enable)

Verkanelung:
Batterie an Treiber + und VCC, -, in plus muss auf jeden fall eine Sicherung reina

Treiber mit Motor an M- und M+

Logikinterface:
VCC, GND
R_EN, L_EN (dauerhaftes scharf stellen)

RPWM, LPWM

Exkurs sleep modus einer Esp32:

Hauptsytem -> Hauptfresser:
Hier sitzen schnelle Hauptprozessoren, das WLAN-Modul, das Bluetooth und die
"normalen" digitalen Pins.
Wenn dieses System aktiv ist, verbraucht der ESP32 relativ viel
Strom ca. 40 bis 240 mA.

RTC-Domäne (Wächter)
Extrem stromsparender. winziger seperater Bereich auf dem Chip
der völlig unabhängig vom Hauptsystem läuft.

Deep-Sleep:
Hauptsystem vom Strom getrennt nur die RTC-Domäne bleibt wach.

RTC-Pins:
RTC-Pins sind harwareseitig physikalisch mit dieser zweiten, stromsparenden RTC-Domäne verdrahtet.
Wenn das Hauptsystem schläft wird die Kontrolle an den kleien RTC-Wächter übergeben. Liegt
an dem RTC-Pin nun ein Spannungsimpulse merkt der Wächter, dass das Hauptsystem durch
einen Reset wieder aufgeweckt werden soll.

Pins die mit der RTC-Domäne verbunden sind: 0, 2, 4, 12, 13, 14, 15, 25, 26, 27, 32, 33, 34, 36, 39

Unproblematisch sind 32, 33 beste Wahl, da hier keine Boot probleme, wie bei "Strapping Pins"
"""

# ---- Imports ----
import esp32
from machine import Pin

class BewegungsSensor:
    def __init__(self, trigger_pin: int)->None:
        #!!! Da der eingestellte Pin zum aufwecken der ESP
        # verwendet wird, muss dieser ein RTC Pin sein.
        #self.trigger_pin = Pin(trigger_pin, Pin.PULL_DOWN)
        self.trigger_pin = Pin(trigger_pin)
        print(f"Bewegungs Sensor initialisiert an RTC-Pin {trigger_pin}.")

    def wurde_bewegung_erkannt(self)->int:
        """
        Gibt einen High Signal weiter, sobald der Bewegungssensor anschlägt.

        Returns
        -------
        int : 0 keine Bewegung, 1 Bewegung wahrgenommen.
        """
        return self.trigger_pin.value()

    def ermögliche_aufwachen(self):
        """
        ESP konfigurieren, dass er aufwacht, sobald der RTC-Pin auf High gesetzt wird.

        !!! Das funktioniert auf der ESP nur mit RTC-Pins
        """
        esp32.wake_on_ext1(pin=(self.trigger_pin), level=esp32.WAKEUP_ANY_HIGH)
        print("Wake-Up durch Bewegungssensor (ext1) aktiviert.")

"""
Exkurs zu internen Vorgängen in wake_on_ext0:
MicroPython schreibt hier in internen Konfigurationsregister der RTC-Domäne.
Der übergebene Pin wird vom Wächter von nun an beobachtet. 
WAKEUP_ANY_HIGH sorgt dafür, dass intern ein Komperator (electronischer Spannungsvergleicher)
aktiviert wird. Der reagieren soll, sobald die Spannung an dem Pin über eine Schwellspannung
für ein digitales HIGH-Signal steigt. 
"""