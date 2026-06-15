import time
from empfanger import Empfanger

try:
    print("Initialisiere Empfanger und Sender...")
    emfänger = Empfanger()

    start = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(),start) < 45*1e3:

        emfänger.lauschen()

except KeyboardInterrupt:
    print("Empfangen abgebrochen...")
except Exception as e:
    print(f"Fehler bei dem Senden von daten: {e}")