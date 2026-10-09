// UI text in Hindi (default) and English. Content titles come from NCERT as they are.
import { settings, saveSettings } from "./store.js";

const STR = {
  hi: {
    app: "ज्ञान पथ", tagline: "NCERT की सामग्री – सीधे शिक्षार्थी तक",
    home: "होम", learn: "सीखें", teach: "शिक्षक व अभिभावक", office: "कार्यालय", shelf: "मेरी शेल्फ़", whatsnew: "नया क्या है",
    search: "खोजें", searchPh: "किताब, विषय, वीडियो, सूचना… खोजें", about: "जानकारी व सेटिंग",
    pickClass: "अपनी कक्षा चुनें", classN: "कक्षा", allClasses: "सभी कक्षाएँ", quick: "सीधे पहुँचें",
    newForLearners: "NCERT से नया", recentlyUpdated: "हाल में अपडेट हुई फ़ाइलें", recent: "हाल में खोले गए",
    open: "खोलें", openPage: "पेज खोलें", save: "सेव", saved: "सेव किया", remove: "हटाएँ", more: "और दिखाएँ",
    from: "स्रोत", updated: "अपडेट", online: "इंटरनेट चाहिए", offlineNow: "आप ऑफ़लाइन हैं – सूची और खोज चलेंगी, फ़ाइलें खोलने के लिए इंटरनेट चाहिए।",
    items: "सामग्री", none: "कुछ नहीं मिला।", filter: "छाँटें", lang: "भाषा", anyLang: "कोई भी भाषा", kind: "प्रकार",
    anyKind: "सभी प्रकार", product: "लाभ", anyProduct: "सभी लाभ", sort: "क्रम", sortRel: "उपयोगी पहले",
    sortNew: "नया पहले", sortAZ: "अ–ज्ञ / A–Z", filterIn: "इस सूची में खोजें",
    textbooks: "पाठ्यपुस्तकें", chapters: "अध्याय", chapter: "अध्याय", prelims: "प्रारंभिक पृष्ठ", wholeBook: "पूरी किताब (ZIP)",
    answers: "उत्तर", appendix: "परिशिष्ट", olderEditions: "पुराने संस्करण", subjects: "विषय", books: "किताबें",
    videos: "वीडियो", channels: "चैनल", collections: "संग्रह", playAll: "सब चलाएँ", play: "चलाएँ", close: "बंद करें",
    videoNote: "वीडियो YouTube (privacy-enhanced) से चलते हैं – दबाने से पहले YouTube को कुछ नहीं भेजा जाता।",
    newBadge: "नया", updBadge: "अपडेट", remBadge: "हटाया गया", forLearners: "शिक्षार्थियों के लिए", forOffice: "कार्यालय",
    noChanges: "अभी कोई बदलाव दर्ज नहीं। ऐप हर 6 घंटे में NCERT जाँचता है।",
    myOffline: "मेरी ऑफ़लाइन PDF", addPdf: "डिवाइस से PDF जोड़ें", offlineHelp: "NCERT से डाउनलोड की गई PDF यहाँ जोड़ें – बिना इंटरनेट इसी ऐप में खुलेगी। फ़ाइल आपके फ़ोन में ही रहती है।",
    savedItems: "सेव की गई सामग्री", emptyShelf: "अभी कुछ सेव नहीं किया। किसी भी कार्ड पर ☆ दबाएँ।",
    synced: "NCERT से आख़िरी जाँच", theme: "थीम", themeAuto: "अपने-आप", themeLight: "हल्की", themeDark: "गहरी",
    officeIntro: "यह NCERT का प्रशासनिक हिस्सा है – नीतियाँ, शोध, सूचनाएँ, भर्ती, निविदाएँ। पढ़ाई की सामग्री 'सीखें' में है।",
    teachIntro: "शिक्षकों, अभिभावकों और स्वयंसेवकों के लिए – जो बच्चों तक ज्ञान पहुँचाते हैं।",
    learnIntro: "सीधे शिक्षार्थी के काम की सामग्री – पढ़ें, देखें, अभ्यास करें।",
    updateReady: "NCERT की नई सामग्री लोड हो गई।", copyright: "अनौपचारिक सूची। सारी सामग्री © NCERT; लिंक ncert.nic.in पर खुलते हैं।",
    allIn: "सब देखें", results: "परिणाम", languages: "भाषाएँ", size: "आकार",
  },
  en: {
    app: "Gyan Path", tagline: "NCERT resources – straight to the learner",
    home: "Home", learn: "Learn", teach: "Teachers & parents", office: "Office", shelf: "My shelf", whatsnew: "What's new",
    search: "Search", searchPh: "Search books, topics, videos, notices…", about: "About & settings",
    pickClass: "Pick your class", classN: "Class", allClasses: "All classes", quick: "Go straight to",
    newForLearners: "New from NCERT", recentlyUpdated: "Recently updated files", recent: "Recently opened",
    open: "Open", openPage: "Open page", save: "Save", saved: "Saved", remove: "Remove", more: "Show more",
    from: "From", updated: "Updated", online: "Needs internet", offlineNow: "You are offline – lists and search work; opening files needs internet.",
    items: "items", none: "Nothing found.", filter: "Filter", lang: "Language", anyLang: "Any language", kind: "Type",
    anyKind: "All types", product: "Benefit", anyProduct: "All benefits", sort: "Order", sortRel: "Most useful",
    sortNew: "Newest", sortAZ: "A–Z", filterIn: "Search in this list",
    textbooks: "Textbooks", chapters: "Chapters", chapter: "Chapter", prelims: "Prelims", wholeBook: "Whole book (ZIP)",
    answers: "Answers", appendix: "Appendix", olderEditions: "Older editions", subjects: "Subjects", books: "Books",
    videos: "Videos", channels: "Channels", collections: "Collections", playAll: "Play all", play: "Play", close: "Close",
    videoNote: "Videos play from YouTube (privacy-enhanced). Nothing is sent to YouTube until you press play.",
    newBadge: "New", updBadge: "Updated", remBadge: "Removed", forLearners: "For learners", forOffice: "Office",
    noChanges: "No changes recorded yet. The app checks NCERT every 6 hours.",
    myOffline: "My offline PDFs", addPdf: "Add a PDF from this device", offlineHelp: "Add PDFs you downloaded from NCERT – they open inside this app without internet. The file stays on your device.",
    savedItems: "Saved items", emptyShelf: "Nothing saved yet. Tap ☆ on any card.",
    synced: "Last checked NCERT", theme: "Theme", themeAuto: "Automatic", themeLight: "Light", themeDark: "Dark",
    officeIntro: "NCERT's administrative side – policies, research, notices, jobs, tenders. Learning material is under 'Learn'.",
    teachIntro: "For teachers, parents and volunteers – the people who bring learning to children.",
    learnIntro: "Material the learner uses directly – read, watch, practise.",
    updateReady: "New NCERT material loaded.", copyright: "Unofficial index. All content © NCERT; links open ncert.nic.in.",
    allIn: "See all", results: "results", languages: "Languages", size: "Size",
  },
};

// Groups inside each section: [key, icon, hindi, english, hindi description, english description]
export const GROUPS = {
  learn: [
    ["books", "📚", "पाठ्यपुस्तकें", "Textbooks", "कक्षा → विषय → किताब → अध्याय", "Class → subject → book → chapter"],
    ["media", "🎬", "वीडियो व ऑडियो", "Videos & audio", "NCERT के चैनल और वीडियो संग्रह", "NCERT channels and video collections"],
    ["practice", "✍️", "अभ्यास", "Practice", "उदाहरणात्मक प्रश्न, प्रश्न पत्र, नमूना प्रश्न", "Exemplar problems, question papers, samples"],
    ["read", "📖", "पढ़ें", "Read", "कहानियाँ, प्रवेशिकाएँ, पत्रिकाएँ, विशेष मॉड्यूल", "Story books, primers, magazines, modules"],
    ["interactive", "🧩", "इंटरैक्टिव", "Interactive", "डिजिटल किताबें, फ़्लिपबुक, जादुई पिटारा, तमन्ना", "Digital readers, flipbooks, Jaadui Pitara, TAMANNA"],
    ["skills", "🛠️", "कौशल", "Skills", "प्रयोगशाला पुस्तिकाएँ, किट, कला", "Lab manuals, kits, arts"],
    ["wellbeing", "💚", "स्वास्थ्य व करियर", "Wellbeing & career", "मनोदर्पण, स्वास्थ्य, करियर मार्गदर्शन", "Manodarpan, health, career guidance"],
    ["opportunity", "🏆", "अवसर", "Opportunities", "NTSE, बाल विज्ञान प्रदर्शनी, कला उत्सव, प्रयास", "NTSE, science exhibition, Kala Utsav, PRAYAAS"],
    ["adult", "🪔", "प्रौढ़ साक्षरता (उल्लास)", "Adult literacy (ULLAS)", "15+ आयु के शिक्षार्थियों के लिए", "For learners aged 15+"],
    ["portals", "🌐", "ऐप व पोर्टल", "Apps & portals", "दीक्षा, ई-पाठशाला, स्वयं…", "DIKSHA, ePathshala, SWAYAM…"],
  ],
  teach: [
    ["guides", "📘", "पुस्तिकाएँ व संसाधन", "Handbooks & resources", "", ""],
    ["training", "🎓", "प्रशिक्षण व कोर्स", "Training & courses", "", ""],
    ["assessment", "📊", "मूल्यांकन व सीखने के प्रतिफल", "Assessment & outcomes", "", ""],
    ["journals", "📰", "शिक्षकों की पत्रिकाएँ", "Teachers' journals", "", ""],
    ["events", "🗓️", "संगोष्ठी व वेबिनार", "Seminars & webinars", "", ""],
  ],
  office: [
    ["system", "🧭", "नीति, पाठ्यचर्या व शोध", "Policy, curriculum & research", "", ""],
    ["notices", "📢", "सूचनाएँ", "Notices", "", ""],
    ["jobs", "💼", "भर्ती", "Jobs", "", ""],
    ["tenders", "📑", "निविदाएँ", "Tenders", "", ""],
    ["accounts", "🧾", "लेखा व पेंशन", "Accounts & pension", "", ""],
    ["about", "🏛️", "NCERT के बारे में", "About NCERT", "", ""],
    ["news", "🗞️", "समाचार व गैलरी", "News & gallery", "", ""],
    ["links", "🔗", "अन्य सरकारी लिंक", "Other government links", "", ""],
  ],
};

export const PRODUCTS = {
  K: ["📚", "ज्ञान", "Knowledge"], S: ["🛠️", "कौशल", "Skill"], T: ["💡", "सोच व रचनात्मकता", "Thinking & creativity"],
  C: ["🎯", "करियर व अवसर", "Career & opportunity"], W: ["💚", "स्वास्थ्य व सुरक्षा", "Wellbeing & safety"], M: ["🗂️", "कई तरह", "Mixed"],
};
export const KINDS = {
  pdf: ["📄", "PDF", "PDF"], doc: ["📝", "दस्तावेज़", "Document"], zip: ["🗜️", "ZIP", "ZIP"], epub: ["📘", "ई-बुक", "e-Book"],
  img: ["🖼️", "चित्र", "Image"], video: ["🎬", "वीडियो", "Video"], audio: ["🎧", "ऑडियो", "Audio"], flip: ["📖", "फ़्लिपबुक", "Flipbook"],
  link: ["🔗", "वेबसाइट", "Website"], page: ["🌐", "पेज", "Page"],
};
export const LANG_NAMES = { en: ["अंग्रेज़ी", "English"], hi: ["हिंदी", "Hindi"], ur: ["उर्दू", "Urdu"] };

export const lang = () => (settings.lang === "en" ? "en" : "hi");
export const t = (k) => STR[lang()][k] ?? STR.en[k] ?? k;
export const pick = (hi, en) => (lang() === "en" ? en : hi);
export function setLang(l) {
  settings.lang = l;
  saveSettings();
  document.documentElement.lang = l;
}
export const groupInfo = (sec, key) => (GROUPS[sec] || []).find((g) => g[0] === key);
