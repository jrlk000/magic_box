import numpy as np
import math


def leistung_nach_bug_converter(leistung_verbraucher: float, wirkungsgerad=0.85, ruhe_verlust_wandler=0.02)->float:
    return leistung_verbraucher / wirkungsgerad + ruhe_verlust_wandler

def gesamt_strom_aus_akkumulator(akku_voltage: float, watts_devices: np.array) -> float|None:
    if akku_voltage == 0:
        print(f"Gegebene Batteriespannung {akku_voltage}V ist unzulässig.")
        return
    return np.sum(watts_devices/akku_voltage)


def cap_battery(I_verbraucher, I_ruhe, t_aktiv, t_standby, t_autonomie=7) -> tuple[float]:
    C_aktiv = I_verbraucher * t_aktiv
    C_standby = I_ruhe * t_standby
    C_tag = C_aktiv+C_standby

    return C_tag * t_autonomie / 0.8, C_tag


def solar_watts_needed(C_tag, U_akku, t_sonne_effektiv =3.5) -> float:
    return C_tag * U_akku / t_sonne_effektiv


def Batterielaufzeit(C_akku: float, C_tag: float, I_ges:float)->tuple[float]:
    t_autonomie = C_akku * 0.8 / C_tag
    t_dauer_betrieb = C_akku * 0.8 / I_ges
    return t_autonomie, t_dauer_betrieb

# ---- Komponneten Daten ----
AKKU_V = 12

W_ESP_A = 0.1
W_ESP_S = 0.033 * 1e-3

W_RFID_A = 0.066 # [W]
W_RFID_S = 0.033*1e-3 #[W]


W_ESP_RFID_A = leistung_nach_bug_converter(W_ESP_A + W_RFID_A)
W_ESP_RFID_S = leistung_nach_bug_converter(W_ESP_S + W_RFID_S)

BEWEGUNGSSENSOR_A = 2*1e-3 * 12
BEWEGUNGSSENSOR_S = 0.065*1e-3 * 12

W_SOLAR_LADE_MODUL= 0.18 #[W] ca 15mA bei 12V

W_LINEARAKTUATOR_A = 30 #[W]

W_DEVICES_A = np.array([
    W_LINEARAKTUATOR_A,
                       W_SOLAR_LADE_MODUL,
                       BEWEGUNGSSENSOR_A,
                       W_ESP_RFID_A
                       ], dtype=float)

W_DEVICES_S = np.array([
                       BEWEGUNGSSENSOR_S,
                       W_ESP_RFID_S,
                       W_SOLAR_LADE_MODUL],
                       dtype=float)

# ---- Berechnungen ----
I_aktiv = gesamt_strom_aus_akkumulator(AKKU_V, W_DEVICES_A)
I_ruhe = gesamt_strom_aus_akkumulator(AKKU_V, W_DEVICES_S)


t_aktiv, t_standby = 15/60, 23 + 45/60 #[min]

c_batt, c_tag = cap_battery(I_aktiv, I_ruhe, t_aktiv, t_standby)
solar_watts = solar_watts_needed(c_tag, AKKU_V, t_sonne_effektiv =3.5)
t_autonomie, t_dauer_betrieb = Batterielaufzeit(c_batt, c_tag, I_aktiv)


# ---- Output ----
print(f"--- SOLAR- & AKKU-ANALYSE ---")
print(f"Stromaufnahme Aktiv:   {I_aktiv:.3f} A")
print(f"Stromaufnahme Standby: {I_ruhe:.3f} A")
print(f"Tagesbedarf:           {c_tag:.3f} Ah\n")

print(f"Empfohlene Batterie:   {c_batt:.2f} Ah (für 7 Tage Autonomie)")
print(f"Empfohlenes Solarpanel:{solar_watts:.2f} Wp")
print(f"Theoretische Autonomie:{t_autonomie:.1f} Tage (bis 50% Entladung)")
print(f"Maximale Dauerlaufzeit:{t_dauer_betrieb:.2f} Stunden (bei Dauer-Aktivität)")


"""
Ableitungen für die Realität: 

20-30 W Solarpannel vollkommen ausreichend

wechsel von Blei zu LiFePO4 mit Battery Managment System, 
da nicht aufgeladen werden soll unter 0°C

6 Ah oder 10 Ah LiFePO4-Batterie oder 10 Ah bis 14 Ah Batterie
"""