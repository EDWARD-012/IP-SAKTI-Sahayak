"""Append Hindi translations for chat chrome and compile django.mo via polib."""
from __future__ import annotations

from pathlib import Path

import polib

PO_PATH = Path("locale/hi/LC_MESSAGES/django.po")

NEW = {
    "Jurisdiction and language settings": "न्यायाधिकार क्षेत्र और भाषा सेटिंग्स",
    "Jurisdiction": "न्यायाधिकार क्षेत्र",
    "Select jurisdiction": "न्यायाधिकार क्षेत्र चुनें",
    "India jurisdiction": "भारत न्यायाधिकार क्षेत्र",
    "India": "भारत",
    "International jurisdiction": "अंतरराष्ट्रीय न्यायाधिकार क्षेत्र",
    "International": "अंतरराष्ट्रीय",
    "Both India and International jurisdiction": "भारत और अंतरराष्ट्रीय दोनों",
    "Both": "दोनों",
    "Current language": "वर्तमान भाषा",
    "Language: %(LANGUAGE_CODE)s": "भाषा: %(LANGUAGE_CODE)s",
    "Chat sidebar": "चैट साइडबार",
    "Corpus": "कॉर्पस",
    "Active version:": "सक्रिय संस्करण:",
    "Learn about the legal corpus": "कानूनी कॉर्पस के बारे में जानें",
    "About this corpus": "इस कॉर्पस के बारे में",
    "Session History": "सत्र इतिहास",
    "Recent questions in this session": "इस सत्र के हाल के प्रश्न",
    "No questions asked yet in this session.": "इस सत्र में अभी तक कोई प्रश्न नहीं पूछा गया।",
    "Clear all session data? This cannot be undone.": "सभी सत्र डेटा साफ़ करें? यह वापस नहीं लिया जा सकता।",
    "Clear chat session history": "चैट सत्र इतिहास साफ़ करें",
    "Clear Session": "सत्र साफ़ करें",
    "How to use IP-SAKTI": "IP-SAKTI कैसे उपयोग करें",
    "IP-SAKTI chat": "IP-SAKTI चैट",
    "Answer area": "उत्तर क्षेत्र",
    "Patents, GI, biodiversity, traditional knowledge — every answer cites a source.": "पेटेंट, जीआई, जैव विविधता, पारंपरिक ज्ञान — प्रत्येक उत्तर स्रोत उद्धृत करता है।",
    "Example questions": "उदाहरण प्रश्न",
    "Section 3(p) TK": "धारा 3(प) पारंपरिक ज्ञान",
    "GI registration": "जीआई पंजीकरण",
    "NBA / ABS": "एनबीए / एबीएस",
    "Ayurveda Aahara": "आयुर्वेद आहार",
    "Ask about patents, GI, biodiversity, TKDL…": "पेटेंट, जीआई, जैव विविधता, TKDL के बारे में पूछें…",
    "Cancel": "रद्द करें",
    "Help & Guide": "सहायता और मार्गदर्शिका",
    "Help": "सहायता",
    "How to Use the Ask IP-SAKTI Chat": "Ask IP-SAKTI चैट का उपयोग कैसे करें",
    "Understanding Evidence Labels": "साक्ष्य लेबल समझें",
    "How to Read Citations": "उद्धरण कैसे पढ़ें",
}

po = polib.pofile(str(PO_PATH)) if PO_PATH.exists() else polib.POFile()
if not PO_PATH.exists():
    po.metadata = {
        "Content-Type": "text/plain; charset=UTF-8",
        "Language": "hi",
    }

existing = {e.msgid for e in po}
added = 0
for msgid, msgstr in NEW.items():
    if msgid in existing:
        for e in po:
            if e.msgid == msgid and not e.msgstr:
                e.msgstr = msgstr
                added += 1
        continue
    entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
    po.append(entry)
    added += 1

po.save(str(PO_PATH))
po.save_as_mofile(str(PO_PATH.with_suffix(".mo")))
print(f"updated {PO_PATH}; touched/added ≈ {added}; total entries {len(po)}")
