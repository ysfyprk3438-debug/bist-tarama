# -*- coding: utf-8 -*-
"""
robot_calistir.py — ZAMANLANMIŞ GÖREV: NOVA otomatik al-sat turu.
Durumu yükler → tarar → al/sat kararı → kaydeder → Telegram bildirir.
GitHub Actions her çalıştığında robot_durum.json güncellenir ve commit edilir.
"""
import os
import sys

from tarama_core import tara
import robot_motor as rm
import telegram_alarm as ta


def main():
    durum = rm.yukle()
    sonuclar, _ = tara(os.environ.get("AVCI_VADE", "gunluk"))
    if not sonuclar:
        print("Veri yok — tur atlandı.")
        return 0
    durum, msgs = rm.tur(durum, sonuclar)
    rm.kaydet(durum)
    k = rm.karne(durum)
    print(f"Tur bitti · değer {k['deger']}₺ · açık {k['acik']} · başarı %{k['basari']} · skor {k['skor']}/10")
    if msgs:
        deg = f"{k['deger']:,}".replace(",", ".")
        ta.gonder("🤖 *NOVA* · sanal otomatik al-sat\n" + "\n".join(msgs) +
                  f"\n\n📊 Değer {deg}₺ · başarı %{k['basari']} · skor {k['skor']}/10")
    else:
        print("İşlem yok bu tur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
