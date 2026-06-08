"""
Main loop für die sender devices.
"""

import machine
import time
from sender import Sender
aufwach_pin_num = 3
led_pin_num = 4

try:
    print("Initialisiere Sender...")
    sender = Sender()

    start = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start) < 45*1e3:
        sender.kontaktiere_empfänger_debug()
        time.sleep_ms(50)

    sender.deinit_sender()


    #led = machine.Pin(led_pin_num, machine.Pin.OUT, value=1)
    #trigger = machine.Pin(aufwach_pin_num, machine.Pin.IN, machine.Pin.PULL_UP, hold=True)
    #print("Wache auf Schlaf Phase zu ende...")

    #aufwachmodus = machine.reset_cause()
    #ursache = machine.wake_reason()
    #print(f'Aufwach grund {ursache}')

    """aufwach_modi = {
        "machine.PWRON_RESET":"Strom wurde gerade angeschlossen...",
        "machine.HARD_RESET":"Reset-Knopf wurde gedrückt...",
        "4":f"Erwachen aus deep sleep, ursache: {ursache}..."
    }"""

    #Schlaf status herausfinden
    """if aufwachmodus in aufwach_modi:
        print(aufwach_modi[aufwachmodus])
    else:
        print('Undefinierter Zustand, aus dem das Board kommt.')"""

    """while True:
        message  = input("Bitte gebe einen Befehl ein:").strip().upper()

        if message in ("AUS", "STOPP", "0", "SLEEP"):
            print("System wird in Schlaf versetzt für höchstens 20 sek...")
            print("Frühzeitiges aufwachen über GPIO3 ermöglicht...")
            break

        print("Befehl hat keine Wirkung...")"""

    # 1. Board schlafen legen für definierte Zeit
    #machine.deepsleep([5e3])  # Zeit in ms

    print("Konfiguriere WakeUp-Pin...")
    # 2. Board schlafen legen und trigger initialisieren
    #trigger.irq(trigger=machine.Pin.IRQ_FALLING, wake=machine.DEEPSLEEP)

    #time.sleep(10)
    #led.value(0)
    #machine.deepsleep(int(5e3))



except KeyboardInterrupt:
    # Sauberes Aufräumen beim Beenden
    print("Programm beendet. Räume auf...")
    #blink_timer.deinit()
    #trigger.deinit()
    #led.value(0)
except Exception as e:
    # Fange unerwartete Hardware-Fehler ab
    print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    #led.value(0)