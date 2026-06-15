"""
Main loop für die sender devices.
"""

import machine
import time
import esp32
from machine import Pin, ADC
from sender import Sender

MSG = "Motor"
WAKE_PIN = Pin(3, Pin.IN, Pin.PULL_DOWN)
POTENTIOMETER = esp32.WAKEUP_ANY_HIGH
BUTTON = esp32.WAKEUP_ALL_LOW

#Sende Zeit von 2200 ms um garantiert ein Packet im Rythmus des Empfängers zu verschicken.
#Beachte: Sende Zeit diktiert implizit den delay der Interaktion.
#Empfänger: Rythmus von 200 ms mit wach: 150 ms, 1800 ms
SENDE_ZEIT = 2.2*1e3


# ---- Messungen ----
"""adc =  ADC(WAKE_PIN)
adc.atten(adc.ATTN_11DB)

OBERESPANNUNGSGRENZE = 2.7-3.3 # [V]
UNTERESPANNUNGSGRENZE = 0-0.1 # [V]"""


try:

    #time.sleep_ms(2000)
    """print("Aufgewacht...")
    grund = machine.reset_cause()

    if grund == machine.DEEPSLEEP_RESET:
        print("Board ist nach ablauf der deep sleep zeit erwacht.")

    elif grund == machine.PIN_WAKE:
        print("Board ist durch RTC trigger aus dem schlaf geholt worden.")

    else:
        print("Unrelevanter Aufwachgrund.")"""

    # ---- Sender Initialisierung ----
    print("Initialisiere Sender...")
    sender = Sender()

    #Messungen
    """while True:
        u_sum = 0
        v_sum = 0
        for _ in range(100):
            u_sum += adc.read_u16()
            v_sum += adc.read_uv()

        print(f"Anliegende Spannung ...u_16:{u_sum/100 *3.3/2**16} [V]")
        print(f"Spannung ...uv: {v_sum/100 * 1e-6 :.3f} [V]")

        time.sleep_ms(2000)"""


    #----Senden ----
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < SENDE_ZEIT:
        sender.kontaktiere_empfänger_debug(MSG)
        print(f"Verbleibende Zeit {(SENDE_ZEIT - time.ticks_diff(time.ticks_ms(), start))/1000:.2f}")
        time.sleep_ms(50)

    sender.deinit_sender()

    print("Initialisiere Trigger-Pin")

    #[BEACHTE]: Button möchte any low haben / Potentiometer braucht any high
    esp32.wake_on_gpio([WAKE_PIN], BUTTON)
    #WAKE_PIN.irq(trigger=machine.Pin.IRQ_RISING)

    time.sleep_ms(2000)

    #start = time.ticks_ms()
    #machine.lightsleep()
    machine.deepsleep()

    # [Hinweis]: nach dem aufwachen aus dem Deep Sleep wird neu gebootet, somit wird auch diese file von Vorne abgespielt.







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

    #print("Konfiguriere WakeUp-Pin...")
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