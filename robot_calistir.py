# -*- coding: utf-8 -*-
"""
robot_calistir.py — ZAMANLANMIS GOREV: NOVA otomatik al-sat turu.
Durumu yukler -> tarar -> al/sat karari -> kaydeder -> Telegram bildirir.
Her turda (islem olsa da olmasa da) kisa bir ozet Telegram'a gonderilir.
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
        print("Veri yok - tur atlandi.")
        ta.gonder("🤖 *NOVA* · tur calisti\n"
                  "📭 Su an piyasa verisi yok (borsa kapali olabilir).\n"
                  "Islem yapilmadi, bir sonraki turda tekrar bakacagim.")
        return 0

    durum, msgs = rm.tur(durum, sonuclar)
    rm.kaydet(durum)
    k = rm.karne(durum)
    deg = f"{k['deger']:,}".replace(",", ".")
    print(f"Tur bitti - deger {k['deger']} - acik {k['acik']} - basari {k['basari']} - skor {k['skor']}")

    if msgs:
        ta.gonder("🤖 *NOVA* · sanal otomatik al-sat\n" + "\n".join(msgs) +
                  f"\n\n📊 Deger {deg}₺ · basari %{k['basari']} · skor {k['skor']}/10")
    else:
        print("Islem yok bu tur.")
        ta.gonder("🤖 *NOVA* · tur calisti\n"
                  f"✅ Tarama yapildi, bu turda yeni al-sat sinyali yok.\n"
                  f"📊 Deger {deg}₺ · acik pozisyon {k['acik']} · basari %{k['basari']} · skor {k['skor']}/10")
    return 0


if __name__ == "__main__":
    sys.exit(main())
