import machine
import esp32
import time
from L289N import L289NMotor
from empfanger import Empfanger

"""
Main des ESP32  WROVER für die Kisten Ansteuerung. 
"""

# ---- Konfiguration ----

# ---- Zeiten ----
INTERAKTIONS_ZEIT = 30000  # [ms]
AUSFAHR_ZEIT = 4000  # [ms]
EINFAHR_ZEIT = 4000  # [ms]

EMPFANGS_ZEITRAUM = 150  # [ms]
EMPFANGS_PAUSE = 1800  # [ms]

# Aktiv-Fenster Definition
START_STUNDE = 9
END_STUNDE = 16

# ---- PWM ----
DUTY_CYCLE = 2 ** 16 - 1
FREQ = 4000  # [1/s]

# ---- Motor Treiber L298N----
IN_1_PIN = 23
IN_2_PIN = 22
PWM_PIN = 26


def motor_interaktion(motor: L289NMotor) -> None:
    """
    Steuert gesamte Motor interaktion: Hochfahren und Runterfahren.

    Args
    ----
    motor L289NMotor : Treiber, der die Motor Spannungsversorgung regelt.

    Returns
    -------
    None
    """
    print("Motor interaktion statartet...")
    motor.setup()

    # ----Konfiguration für Vorwärts einstellen----
    motor.treiber_vorwärts()

    # ----GESCHWINDIGKEIT REGULIEREN----
    motor.regle_geschwindigkeit(dc=DUTY_CYCLE, frequency=FREQ)

    time.sleep_ms(AUSFAHR_ZEIT)

    motor.spannungsversorgung_sperren()

    # ----INTERAKTIONS-LOOP----
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < INTERAKTIONS_ZEIT:
        # motor.motor_strom_monitoring()
        time.sleep_ms(500)

    # ---- Motor runterfahren ----
    motor.treiber_rückwärts()
    time.sleep_ms(EINFAHR_ZEIT)

    motor.spannungsversorgung_sperren()

    motor.deinit_motor()
    print("Motorinteraktion beendet...")


def main() -> None:
    print("ESP32 Wake-Up Routine gestartet ---")

    empfänger = None
    motor = None

    def handle_signal(mac, msg):
        """Callback-Funktion: Wird automatisch aufgerufen, sobald ein Signal eingeht."""
        print(f"Signal empfangen von {mac}: {msg}")

        #Hier können beliebige auszuführende Ansteuerungen platziert werden.
        motor_interaktion(motor)

        if empfänger:
            empfänger.puffer_leeren()
        print("Ansteuerung erfolgreich!")

    try:
        # Initialisierung registriert direkt den Hardware-Callback
        empfänger = Empfanger(on_receive_callback=handle_signal)
        empfänger.mac_anzeigen()

        motor = L289NMotor(23, 22, 26)

    except OSError as e:
        print(f"Fehler bei der Initialisierung des Empfängers oder Motors: {e}")
        print("Gehe in 5 Minuten Sicherheits-Schlaf...")
        machine.deepsleep(300000)  # 5 Minuten interner Schlaf als Notfall-Lösung

    while True:
        machine.idle()

if __name__ == "__main__":
    main()
