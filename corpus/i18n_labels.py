"""
corpus/i18n_labels.py — Display labels for corpus source rows (Hindi UI).
Official English statute titles remain available as secondary text.
"""
from __future__ import annotations

from django.utils.translation import gettext as _
from django.utils.translation import get_language

# source_id → Hindi short title for UI lists
SOURCE_TITLE_HI: dict[str, str] = {
    "patents-act-1970": "पेटेंट अधिनियम, 1970",
    "gi-act-1999": "भौगोलिक संकेत अधिनियम, 1999",
    "biological-diversity-act-2002": "जैव विविधता अधिनियम, 2002",
    "drugs-cosmetics-act-1940": "औषधि एवं प्रसाधन सामग्री अधिनियम, 1940",
    "ayurveda-aahara-regs-2022": "आयुर्वेद आहार विनियम, 2022",
    "nagoya-protocol": "नागोया प्रोटोकॉल",
    "trips-agreement": "ट्रिप्स समझौता",
    "tkdl": "पारंपरिक ज्ञान डिजिटल लाइब्रेरी (TKDL)",
}

AUTHORITY_HI: dict[str, str] = {
    "Legislative Department / India Code": "विधायी विभाग / इंडिया कोड",
    "Legislative Department / India Code; Ministry of Ayush": "विधायी विभाग / इंडिया कोड; आयुष मंत्रालय",
    "Ministry of Ayush": "आयुष मंत्रालय",
    "Food Safety and Standards Authority of India (FSSAI)": "भारतीय खाद्य सुरक्षा और मानक प्राधिकरण (FSSAI)",
    "FSSAI": "एफएसएसएआई (FSSAI)",
    "NBA / MoEFCC": "एनबीए / पर्यावरण मंत्रालय",
    "Convention on Biological Diversity (CBD) Secretariat, United Nations": "जैव विविधता सम्मेलन (CBD) सचिवालय, संयुक्त राष्ट्र",
    "World Trade Organization (WTO)": "विश्व व्यापार संगठन (WTO)",
    "WIPO / WTO": "डब्ल्यूआईपीओ / डब्ल्यूटीओ",
    "CSIR & Ministry of Ayush, Government of India": "सीएसआईआर एवं आयुष मंत्रालय, भारत सरकार",
    "CSIR / TKDL": "सीएसआईआर / TKDL",
}

IP_TYPE_HI: dict[str, str] = {
    "patents": "पेटेंट",
    "gi": "जीआई",
    "biodiversity": "जैव विविधता",
    "traditional-knowledge": "पारंपरिक ज्ञान",
    "trademarks": "ट्रेडमार्क",
    "regulatory": "विनियामक",
    "tkdl": "TKDL",
    "international": "अंतरराष्ट्रीय",
    "trade": "व्यापार",
    "abs": "एबीएस",
}


def _lang() -> str:
    return (get_language() or "en").split("-")[0].lower()


def localize_title(source_id: str, english_title: str) -> str:
    if _lang() != "hi":
        return english_title
    return SOURCE_TITLE_HI.get(source_id, english_title)


def localize_authority(authority: str) -> str:
    if _lang() != "hi" or not authority:
        return authority or "—"
    return AUTHORITY_HI.get(authority, authority)


def localize_ip_types(ip_types: list | str | None) -> str:
    if isinstance(ip_types, list):
        items = [str(x) for x in ip_types]
    elif ip_types:
        items = [p.strip() for p in str(ip_types).split(",") if p.strip()]
    else:
        return "—"

    if _lang() != "hi":
        return ", ".join(items)

    return ", ".join(IP_TYPE_HI.get(x, x) for x in items)


def bilingual_subtitle(source_id: str, english_title: str) -> str:
    """English official name under Hindi title (hi UI only)."""
    if _lang() != "hi":
        return ""
    hi = SOURCE_TITLE_HI.get(source_id)
    if hi and english_title and hi != english_title:
        return english_title
    return ""
