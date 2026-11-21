"""
Klasse zum Bauteil MC33926 (Detailiertere Informationen unter: https://www.pololu.com/product/1212).

Klasse dient als Fundament für die Steuerung eines Linear Aktuators über das Treibermodul.
Sie stellt alle Funktionalitäten zur Verfügung die benötigt werden, um den Treiber über einen Mikrocontroller (hier: XiaoC3 (https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/))
zu steuern.
"""

from machine import Pin, PWM, ADC

class MC33926:
    """
    Angesteuerte Pins des Treibers:
    EN: Aktivierung der Ansteuerung (High) sonst sleep mode
    IN1: OUT1 Steuerung
    IN2: OUT2 Steuerung
    (INV: Invertiert die aktuelle Logik an IN1 und IN2)
    D2: PWM Steuerung der Ausgänge (Ausgnag folgt Signal)
    D1: dauerhaft low (nicht verwendet)
    (SF: dauer High bis auf bei Kurzschlüssen, Ausgangsprobleme basierend auf PWM Signal)
    (FB: Strommessungsaussgang mit einer zuordnung von 525mV pro 1A)
    """

    # Konstanten
    HIGH = 1
    LOW = 0
    MAX_U = 3.3 #[V]
    ADC_AUFLÖSUNG = 2**12



    def __init__(self, in_1: int, in_2: int, pwm, adc: int, en:int, d2:int, d1:int) -> None:
        """


        """
        #ADC
        self.adc = ADC(Pin(adc))
        try:
            adc.block().init(bits=12)  # map analog signal to {1, ..., 2**12}
        except AttributeError:
            pass
        adc.init(atten=ADC.ATTN_11DB)  # allows an intervall from to [0, 3.3] [V]


        # PWMs
        self.pwm = PWM(Pin(pwm, Pin.OUT, value=0, pull=Pin.PULL_DOWN))

        # Enables
        self.ins = [Pin(in_1, Pin.OUT, value=0, pull=Pin.PULL_DOWN),
                    Pin(in_2, Pin.OUT, value=0, pull=Pin.PULL_DOWN)]

        self.en = Pin(en, Pin.OUT, value=1, pull=Pin.PULL_UP)

        self.d2 = Pin(d2, Pin.OUT, value=0, pull=Pin.DOWN)
        self.d2.duty_u16(0)
        self.d2.freq()
        # 500Hz bis 10kHz Werte ausprobieren, klassische DC-Motoransteuerung (5-10kHz)

        self.d1 = Pin(d1, Pin.OUT, value=0, pull=Pin.DOWN)