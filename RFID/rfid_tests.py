

"""
!Notizen zur Verkabelung vom RC522 Modul

RC522 Pin -> ESP32 Pin
----------------------
SDA (SS) -> Pin 5 (SPI Chip Select, Ansprech-Leitung)
SCK Pin18 (SPI Clock) (Takt Kalibrierung für Kommunikation)
MOSI Pin23 (SPI Master Out Slave In) (Hinweg der Kommunikation)
MISO Pin19 (SPI Master In Slave Out) (Rückweg der Kommunikation)
IRQ / (Interruption Request)
GND GND Erde
RST Pin 22
3.3V 3.3V


weiterführende Informationen zu den Anschlüssen basierrend auf dem SPI-Protokoll (Serial Peripheral Interface):

SPI (Synchroner(festen taktgeber) Serieller(Datennbits wandern nacheinander über Leitung) Datenbus)
Master -> ESP32 (Kommunikationsleiter)
Slave -> RC522-Modul (nur anzworten, wenn gefragt)

SCK - Serial Clock (Serieller Takt)
Esp erzeugt hier ein kontinuierliches Rechtecksignal

MOSI - MAster Out, Slave In (Hauptgerät raus, Nebengerät rein, Hinweg)
Esp sendet hier befehle an RFID-Modul. Passend zum SCK Takt wird 3.3V oder 0V angelegt. RC522-Modul liest diese Spannung an seinem Eingang

MISO (Master in, Slave out - Rückweg)
Esp fordert daten vom RD522 Modul schaltet diesen Pin auf ausgang. Er legt nun im Rythmus des SCK-Takts Spannungen an, die der ESP32 an seinem Eingang misst.

SDA/SS - Slave Select / Chip Select (Ansprech-Leitung, Slave Auswahl)
Über SPI kann ein Master theoretisch mit vielen Slaves gleichzeitig verbunden sein. Sie alle teilen sich Leitungen SCK, MOSI, MISO.
Damit nicht alle durcheinanderquatschen, hat jedes Gerät eine eigene SDA/SS Leitung.

WEnn der ESP 32 mit dem RC522 sprechen will, zieht er diese Leitung elektronischvon 3.3V runter auf 0V. Das signalisiert dem Modul (Höre zu!)

SPI-Parameter
Clock Polarity znd Clock Phase definieren zusammen das exacte Timing-Protokoll auf den SPI-Bus
baud_rate: number of signal symbols or state chenges transmitted per second in a communication system
Polarität: def. Ruhezustand der Taktleitung
(hier: 0 also Ruhezustand low, erste Bewegung des Taktsignals ist steigende Flanke)
Phase: bei welcher Taktflanke die Daten auf der MOSI/MISO-Leitung abgetastet, bei welcher die verändert werden
(hier: 0, Daten bei ersten Taktflanke eingelesen, auf der darauf folgenden Flanke ändert der Master die Spannung für nächstes Bit)

Bibliothek
----------
"mfrc522"

Good to know:
- sleep totales einfrieren aller Vorgänge
-ticks_ms zählen der Zeit ab einem Zeitpunkt im Code
-time.ticks_add(time.ticks_ms(), 10000)
-time.ticks_diff(lernmodus_ende, time.ticks_ms()) > 0
"""

"""
ESP32 RFID (RC522) Controller

Dieses Modul liest RFID-Tags über ein RC522-Modul an einem ESP32 aus 
und löst basierrend auf der erkannten Karten-ID spezifische Aktionen aus.
"""

from machine import Pin, SPI
from time import sleep
from mfrc522 import MFRC522 #RFID Bibliothek
from ucollections import namedtuple #Enum equivalent

# ---- Konstanten ----

#SPI Pin-Konfiguration (VSPI)
PIN_SDA = 5
PIN_SCK = 18
PIN_MOSI = 23
PIN_MISO = 19
PIN_RST = 22

# SPI-Kommunikationsparameter
SPI_ID = 2
SPI_BAUDRATE = 2_500_000
SPI_POLARITY = 0
SPI_PHASE = 0

#Zeitliche Parameter (in Sekunden)
DELAY_BETWEEN_READS = 1.5
DELAY_CPU_REST = 0.1

#Bekannte Karten -IDs und die dazugehörigen Vorgänge
VorgaengeType = namedtuple("Vorgänge", ["LERNEN"])

Vorgaenge = VorgaengeType("vorgang_lernen")

BEKANNTE_KARTEN = {
}

# ---- Funktionen ----

def fuehre_vorgang_aus(vorgangs_name: str) -> None:
    """
    Führt eine definierte Aktion basierrend auf dem Vorgangsnamen aus.

    Diese Funktion dient als Router für die verschiedenen Aktionen,
    die durch die RFID-Karten getriggert werden sollen.

    Parameters
    ----------
    vorgangs_name : str
        Ser interne Name des Vorgangs (Schlüsselwort), der ausgeführt werden soll.

    Returns
    -------
    None
    """
    """print(f"-> Starte Vorgang: {vorgangs_name}")

    if vorgangs_name == Vorgaenge.LERNEN:
        
    else:
        print("[ERROR] Vorgang ist nicht implementiert.")"""


def init_rfid_reader() -> MFRC522:
    """
    Initialisiert den Hardware-SPI-Bus und das RC522-Modul.

    Richtet die Pins für den ESP32 anhand der globalen Konstanten ein
    und übergibt diese an die MFRC522-Bibliothek.

    Parameters
    ----------
    None

    Returns
    -------
    MFRC522
        Eine instanziierte und einsatzbereite MFRC522 Reader-Klasse.
    """
    print("Initialisiere Hardware-SPI...")
    # 1. Das SPI-Netzwerk aufbauen (Hardware SPI Block 1 beim ESP32)
    spi_bus = SPI(1, baudrate=1000000, polarity=0, phase=0,
                  sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))

    # 2. Das fertige SPI-Werkzeug an den Reader übergeben (Dependency Injection)
    reader = MFRC522(spi=spi_bus, cs_pin=PIN_CS, rst_pin=PIN_RST)
    print("RFID-Reader erfolgreich gestartet!")

    return reader
    #return MFRC522(spi, PIN_SDA, PIN_RST)

def main() -> None:
    """
    Hauptschleife des RFID-Readers.

    Sucht kontinuierlich nach RFID-Tags, liest deren UID aus, formatiert
    diese in einen Hex-String und gleicht sie mit dem Dictionary ab.
    Bei Erfolg wird der entsprechende Vorgang ausgelöst.

    Master-Karten Logik implementiert:
    Eine der Karten ist als fester Master gesetzt und switcht in den "Lern-Modus"

    Parameters
    ----------
    None

    Returns
    -------
    None

    Raises
    ------
    KeyboardInterrupt
        Wird ausgelöst, wenn das Programm durch den Benutzer abgebrochen wird.
    """
    reader = init_rfid_reader()

    print("Warte auf Karte. ",
          "\nBitte Karte vorhalten...")

    try:
        while True:
            # Nach einer Karte suchen (Weckruf)
            #Nur nicht initialisierrte Karten werden geweckt für permanentes anspringen auf signal REQALL
            (status, tag_type) = reader.request(reader.REQIDL)

            if status == reader.OK:
                # ID der Karte auslesen
                # (2) ID-Abfrage Antikollision
                # (3) Select, Auswahl welche Karte ihre UID schicken darf,
                # sendet Signal um HALT und SENDE zustand im Chip auszulösen
                # (sobald weg vom sender ist chip aber wieder in Werkseinstellungen).
                (status, raw_uid) = reader.anticoll()

                if status == reader.OK:
                    # Die ID in einen lesbaren Hex-String umwandeln
                    card_id = "0x" + "".join([f"{x:02X}" for x in raw_uid[:4]]) #Breite von zwei Zeiche um Injectivität zu wahren
                    print(f"\nKarte erkannt! ID: {card_id}")

                    #Prüfe ob Karte in der Datenbank registriert ist
                    if card_id in BEKANNTE_KARTEN:
                        vorgang = BEKANNTE_KARTEN[card_id]
                        fuehre_vorgang_aus(vorgang)
                    else:
                        print("[INFO] Unbekannte Karte. Keine Aktion hinterlegt.")

                    #Pause, damit selber Scan nicht mehrfach getriggert wird.
                    sleep(DELAY_BETWEEN_READS)
                    print("Bereit für nächste Karte...")

            sleep(DELAY_CPU_REST)

    except KeyboardInterrupt:
        print("\nProgramm regulär beendet.")

# ---- PROGRAMMSTART----

if __name__ == "__main__":
    main()
