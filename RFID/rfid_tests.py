

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

import time
from machine import Pin, SPI
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
LERN_ZEIT = 30000

#Bekannte Karten -IDs und die dazugehörigen Vorgänge
VorgaengeType = namedtuple("Vorgänge", ["LERNEN", "DEFAULT"])

Vorgaenge = VorgaengeType(LERNEN="vorgang_lernen", DEFAULT="vorgang_default")

#Vorgaenge.LERNEN
BEKANNTE_KARTEN = {
    "0x88045F42" : Vorgaenge.LERNEN
}

# ---- Funktionen ----

def to_deci_hex(raw)->int:
    """
    Konvertiere in eine hex zahl mit zwei stellen für jede Hex Zahl.
    Param
    -----
    raw : rohes aufgenommenes Karten signal

    Returns
    -------
    int : Hex identifier
    """
    return "0x" + "".join([f"{x:02X}" for x in raw[:4]])

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
    reader = MFRC522(spi=spi_bus, sda_pin=PIN_SDA, rst_pin=PIN_RST)
    print("RFID-Reader erfolgreich gestartet!")
    return reader

def fuehre_vorgang_aus(vorgangs_name: str, reader:MFRC522) -> None:
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
    print(f"-> Starte Vorgang: {vorgangs_name}")

    if vorgangs_name == Vorgaenge.LERNEN:
        lernen(reader)
    elif vorgangs_name == Vorgaenge.Default:
        print("[AKTION] Zukünftig beliebig erweiterbar.")
    else:
        print("[ERROR] Vorgang ist nicht implementiert.")
    return None

def lernen(reader)->None:
    """
    Lernmodus des RFID-Kartenlesers.
    Während definierter Zeitspanne könne neue Karten eingelesen werden.

    !!!Momnetan nur default vorgänge vorgesehen.
    Param
    -----
    reader : MFRC522
        RFID Kartenleser instanz.

    Returns
    -------
    None
    """
    print("--- LERNMODUS AKTIV ---")
    print(f"Zeitfenster: {LERN_ZEIT/1e3} [sek]. Bitte Karte zum hinzufügen vorhalten.")

    # ---- Zeitmessung Start----
    start_zeit = time.ticks_ms()
    end_zeit = time.ticks_add(start_zeit, LERN_ZEIT)

    while time.ticks_diff(end_zeit, time.ticks_ms()) > 0:

        (status, tag_type) = reader.request(reader.REQIDL)

        if status != reader.OK:
            time.sleep(DELAY_CPU_REST)
            continue

        # Karte is im Feld!
        (status, raw_uid) = reader.anticoll()

        if status == reader.OK:
            card_id = to_deci_hex(raw_uid)
            print(f"\nKarte erkannt! ID: {card_id}")

            # Prüfe ob Karte in der Datenbank registriert ist
            if card_id in BEKANNTE_KARTEN:
                print("-> Larte ist dem System bereits bekannt. Wird ignoriert.")
            else:
                # Momentan keine anderen Vorgänge als der Lern Modus vorgesehen somit default Zuweisung.
                BEKANNTE_KARTEN[card_id] = Vorgaenge.DEFAULT
                print("-> ERFOLG: Neue Karte gespeichert!")

            time.sleep(DELAY_BETWEEN_READS)
            print(f"Bereit für nächste Karte... "
                  f"(Verbleibende Lernzeit: {time.ticks_diff(end_zeit, time.ticks_ms()) // 1e3:.3f}s)")

    print("\n--- LERNMODUS BEENDET ---")
    print("Kehre zum normalen Betriebsmodus zurück...\n")
    return None

def run() -> None:
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

    print("\nSystem bereit. Warte auf Karte...")

    try:
        while True:
            # Weckruf
            (status, tag_type) = reader.request(reader.REQIDL)

            if status != reader.OK:
                time.sleep(DELAY_CPU_REST)
                continue

            (status, raw_uid) = reader.anticoll()

            if status == reader.OK:
                card_id = to_deci_hex(raw_uid)
                print(f"\nKarte erkannt! ID: {card_id}")

                # Prüfe ob Karte in der Datenbank registriert ist
                if card_id in BEKANNTE_KARTEN:
                    vorgang = BEKANNTE_KARTEN[card_id]
                    fuehre_vorgang_aus(vorgang, reader)
                else:
                    print("[INFO] Unbekannte Karte. Keine Aktion hinterlegt.")

                # Pause, damit selber Scan nicht mehrfach getriggert wird.
                time.sleep(DELAY_BETWEEN_READS)
                print("Bereit für nächste Karte...")

    #OS - Operating System - Betriebssystem
    except OSError:
        print("[FEHLER] Kabel zum RFID-Reader abgerissen! Versuche Neustart...")
        time.sleep(2)
        init_rfid_reader()  # Versucht die Hardware neu zu starten, Skript läuft weiter!

    except ValueError as e:
        print(f"[FEHLER] Datenmüll auf der Karte gelesen: {e}")
        # Skript ignoriert die kaputte Karte und läuft weiter!

    return None

# ---- PROGRAMMSTART----
if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[System] Programm durch Benutzer beendet.")

"""
KeyboardInterrup absolute ausnahme bezüglich der Platzierung 
- eigentlich möglichst selektiv und so nah am Uhrsprung des Fehlers wie möglich-
hier muss aber das Programm von jedem Ausgangspunkt gekillt werden können durch den User. 
"""
