# -*- coding: utf-8 -*-
"""
sektor_map.py — BIST hisse -> sektor haritasi (bagimsiz sabit).

arsiv/tarama_core.py'den KOPARILDI: telegram_alarm.py'nin sektor
yogunlasmasi icin ihtiyac duydugu KOD_SEKTOR sozlugu. Baska hicbir sey yok.
Tarama motoru / tahmin / AL-SAT mantigi ICERMEZ — sadece statik esleme.
"""

KOD_SEKTOR = {
    # 🏦 Bankacılık
    'AKBNK': '🏦 Bankacılık',
    'GARAN': '🏦 Bankacılık',
    'HALKB': '🏦 Bankacılık',
    'ISCTR': '🏦 Bankacılık',
    'VAKBN': '🏦 Bankacılık',
    'YKBNK': '🏦 Bankacılık',
    'TSKB': '🏦 Bankacılık',
    'ALBRK': '🏦 Bankacılık',
    'SKBNK': '🏦 Bankacılık',
    'KLNMA': '🏦 Bankacılık',

    # ⚡ Enerji
    'EUPWR': '⚡ Enerji',
    'ODAS': '⚡ Enerji',
    'ENJSA': '⚡ Enerji',
    'AKSEN': '⚡ Enerji',
    'ZOREN': '⚡ Enerji',
    'AYEN': '⚡ Enerji',
    'AYDEM': '⚡ Enerji',
    'KCAER': '⚡ Enerji',
    'CWENE': '⚡ Enerji',
    'NATEN': '⚡ Enerji',

    # 🏭 Sanayi
    'EREGL': '🏭 Sanayi',
    'KRDMD': '🏭 Sanayi',
    'ISDMR': '🏭 Sanayi',
    'CEMTS': '🏭 Sanayi',
    'CIMSA': '🏭 Sanayi',
    'AFYON': '🏭 Sanayi',
    'ARCLK': '🏭 Sanayi',
    'VESTL': '🏭 Sanayi',
    'BFREN': '🏭 Sanayi',
    'DOAS': '🏭 Sanayi',
    'OTKAR': '🏭 Sanayi',
    'FROTO': '🏭 Sanayi',
    'TOASO': '🏭 Sanayi',
    'TTRAK': '🏭 Sanayi',

    # 💊 Sağlık / Kimya
    'ECILC': '💊 Sağlık / Kimya',
    'SELEC': '💊 Sağlık / Kimya',
    'MPARK': '💊 Sağlık / Kimya',
    'DEVA': '💊 Sağlık / Kimya',
    'ECZYT': '💊 Sağlık / Kimya',
    'GUBRF': '💊 Sağlık / Kimya',
    'HEKTS': '💊 Sağlık / Kimya',
    'PETKM': '💊 Sağlık / Kimya',
    'SASA': '💊 Sağlık / Kimya',
    'TRCAS': '💊 Sağlık / Kimya',
    'PRKAB': '💊 Sağlık / Kimya',

    # 🛒 Perakende / Gıda
    'BIMAS': '🛒 Perakende / Gıda',
    'MGROS': '🛒 Perakende / Gıda',
    'SOKM': '🛒 Perakende / Gıda',
    'ULKER': '🛒 Perakende / Gıda',
    'CCOLA': '🛒 Perakende / Gıda',
    'AEFES': '🛒 Perakende / Gıda',
    'TATGD': '🛒 Perakende / Gıda',
    'PNSUT': '🛒 Perakende / Gıda',
    'BANVT': '🛒 Perakende / Gıda',
    'DARDL': '🛒 Perakende / Gıda',

    # 📡 Teknoloji / Telekom
    'TTKOM': '📡 Teknoloji / Telekom',
    'TCELL': '📡 Teknoloji / Telekom',
    'ASELS': '📡 Teknoloji / Telekom',
    'NETAS': '📡 Teknoloji / Telekom',
    'LOGO': '📡 Teknoloji / Telekom',
    'INDES': '📡 Teknoloji / Telekom',
    'ARENA': '📡 Teknoloji / Telekom',
    'DGATE': '📡 Teknoloji / Telekom',
    'KAREL': '📡 Teknoloji / Telekom',
    'SMART': '📡 Teknoloji / Telekom',
    'PAPIL': '📡 Teknoloji / Telekom',

    # ✈️ Ulaşım / Turizm
    'THYAO': '✈️ Ulaşım / Turizm',
    'PGSUS': '✈️ Ulaşım / Turizm',
    'TAVHL': '✈️ Ulaşım / Turizm',
    'CLEBI': '✈️ Ulaşım / Turizm',
    'MAALT': '✈️ Ulaşım / Turizm',
    'RYSAS': '✈️ Ulaşım / Turizm',

    # 🏗️ İnşaat / GYO
    'EKGYO': '🏗️ İnşaat / GYO',
    'ISGYO': '🏗️ İnşaat / GYO',
    'TRGYO': '🏗️ İnşaat / GYO',
    'KLGYO': '🏗️ İnşaat / GYO',
    'VKGYO': '🏗️ İnşaat / GYO',
    'SNGYO': '🏗️ İnşaat / GYO',
    'HLGYO': '🏗️ İnşaat / GYO',
    'ENKAI': '🏗️ İnşaat / GYO',
    'TKFEN': '🏗️ İnşaat / GYO',
    'GSDHO': '🏗️ İnşaat / GYO',

    # 💼 Holding
    'SAHOL': '💼 Holding',
    'KCHOL': '💼 Holding',
    'DOHOL': '💼 Holding',
    'ALARK': '💼 Holding',
    'BERA': '💼 Holding',
    'GOLTS': '💼 Holding',
    'ADEL': '💼 Holding',
    'GESAN': '💼 Holding',
    'MAVI': '💼 Holding',
    'BRISA': '💼 Holding',
    'KARSN': '💼 Holding',
    'GLYHO': '💼 Holding',
}
