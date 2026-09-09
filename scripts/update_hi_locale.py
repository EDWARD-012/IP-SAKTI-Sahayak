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
    # Corpus about page
    "About the Legal Corpus": "कानूनी कॉर्पस के बारे में",
    "Corpus Information": "कॉर्पस जानकारी",
    "Active Corpus Version": "सक्रिय कॉर्पस संस्करण",
    "Version": "संस्करण",
    "Source Documents": "स्रोत दस्तावेज़",
    "Indexed Chunks": "इंडेक्स किए गए खंड",
    "Metadata only (vectors on live laptop profile)": "केवल मेटाडेटा (वेक्टर लाइव लैपटॉप प्रोफ़ाइल पर)",
    "Last Updated": "अंतिम अद्यतन",
    "Collection": "संग्रह",
    "Cloud demo lists curated statutes below. Live RAG retrieval uses the laptop-indexed Chroma corpus.": "क्लाउड डेमो नीचे चयनित अधिनियम दिखाता है। लाइव RAG लैपटॉप पर अनुक्रमित Chroma कॉर्पस उपयोग करता है।",
    "Source Priority Tiers": "स्रोत प्राथमिकता स्तर",
    "Sources are ranked by authority. P0 sources (primary legislation) are always preferred over P1 (secondary legislation, guidelines).": "स्रोतों को प्राधिकार के अनुसार क्रमबद्ध किया गया है। P0 (प्राथमिक कानून) को हमेशा P1 (द्वितीयक कानून, नियम) से ऊपर रखा जाता है।",
    "Tier": "स्तर",
    "Source": "स्रोत",
    "Authority": "प्राधिकार",
    "IP Types": "आईपी प्रकार",
    "Status": "स्थिति",
    "P0 — Primary Legislation (Highest Authority)": "P0 — प्राथमिक कानून (सर्वोच्च प्राधिकार)",
    "P1 — Secondary Legislation, Rules & International Treaties": "P1 — द्वितीयक कानून, नियम और अंतरराष्ट्रीय संधियाँ",
    "✓ Active": "✓ सक्रिय",
    "Pending": "लंबित",
    "Official English statute names appear on hover. Citation quotes stay in English.": "आधिकारिक अंग्रेज़ी अधिनियम नाम होवर पर दिखते हैं। उद्धरण अंग्रेज़ी में रहते हैं।",
    "View Full Source List →": "पूर्ण स्रोत सूची देखें →",
    "Corpus Coverage & Limitations": "कॉर्पस कवरेज और सीमाएँ",
    "Important limitations to note:": "ध्यान देने योग्य महत्वपूर्ण सीमाएँ:",
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
