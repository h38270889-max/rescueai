"""
ResQAI Deterministic Emergency Classification & Safety Rule Engine.
Provides offline, instant, zero-latency emergency triage, priority ranking,
and safety guidance across 14 supported languages without relying on external APIs.
"""

# Multilingual keywords dictionary for emergency category identification
CATEGORY_KEYWORDS = {
    'medical': [
        'heart attack', 'chest pain', 'bleeding', 'unconscious', 'breathing', 'breath',
        'stroke', 'choking', 'fracture', 'cpr', 'ambulance', 'poison', 'overdose',
        'seizure', 'diabetic', 'cardiac', 'pulse', 'hospital', 'injured', 'injury',
        'दर्द', 'खून', 'बेहोश', 'सांस', 'दौरा', 'एम्बुलेंस', 'अस्पताल', 'घायल',  # hi
        'रक्तस्त्राव', 'श्वास', 'हृदयविकार', 'दवाखाना', 'जखमी',  # mr
        'রক্তপাত', 'অচেতন', 'শ্বাসকষ্ট', 'হার্ট অ্যাটাক', 'অ্যাম্বুলেন্স',  # bn
        'இரத்தப்போக்கு', 'மயக்கம்', 'சுவாசம்', 'மருத்துவமனை', 'காயம்',  # ta
        'రక్తస్రావం', 'స్పృహతప్పడం', 'శ్వాస', 'ఆసుపత్రి', 'గాయం',  # te
        'રક્તસ્ત્રાવ', 'બેભાન', 'શ્વાસ', 'ઇજા', 'દવાખાનું',  # gu
        'রক্তസ്രാവം', 'ശ്വാസം', 'ആശുപത്രി', 'പരിക്കേറ്റു',  # ml
        'ಖಾಯಿಲೆ', 'ರಕ್ತಸ್ರಾವ', 'ಉಸಿರಾಟ', 'ಆಸ್ಪತ್ರೆ', 'ಗಾಯ',  # kn
        'ਬੇਹੋਸ਼', 'ਖੂਨ', 'ਸਾਹ', 'ਹਸਪਤਾਲ', 'ਸੱਟ',  # pa
        'بے ہوش', 'خون', 'سانس', 'دل کا دورہ', 'ایمبولینس',  # ur
        'sangrado', 'inconsciente', 'respiración', 'infarto', 'ambulancia', 'herido',  # es
        'saignement', 'inconscient', 'respiration', 'infarctus', 'ambulance', 'blessé',  # fr
        'نزيف', 'إغماء', 'تنفس', 'نوبة قلبية', 'إسعاف', 'مستشفى', 'مصاب'  # ar
    ],
    'fire': [
        'fire', 'flames', 'smoke', 'burning', 'explosion', 'gas leak', 'cylinder blast',
        'electrical short circuit', 'firefighter', 'extinguisher', 'trapped in fire',
        'आग', 'धुआं', 'जल रहा', 'धमाका', 'गैस रिसाव', 'सिलेंडर',  # hi
        'आग लागली', 'धूर', 'स्फोट', 'गॅस गळती',  # mr
        'আগুন', 'ধোঁয়া', 'বিস্ফোরণ', 'গ্যাস লিক',  # bn
        'தீ', 'புகை', 'வெடிப்பு', 'எரிவாயு கசிவு',  # ta
        'మంటలు', 'పొగ', 'పేలుడు', 'గ్యాస్ లీక్',  # te
        'આગ', 'ધુમાડો', 'વિસ્ફોટ', 'ગેસ લિકેજ',  # gu
        'തീപിടുത്തം', 'പുക', 'സ്ഫോടനം', 'ഗ്യാസ് ചോർച്ച',  # ml
        'ಬೆಂಕಿ', 'ಹೊಗೆ', 'ಸ್ಫೋಟ', 'ಅನಿಲ ಸೋರಿಕೆ',  # kn
        'ਅੱਗ', 'ਧੂੰਆਂ', 'ਧਮਾਕਾ', 'ਗੈਸ ਲੀਕ',  # pa
        'آگ', 'دھواں', 'دھماکہ', 'گیس کا اخراج',  # ur
        'fuego', 'incendio', 'humo', 'explosión', 'fuga de gas',  # es
        'feu', 'incendie', 'fumée', 'explosion', 'fuite de gaz',  # fr
        'حريق', 'نار', 'دخان', 'انفجار', 'تسرب غاز'  # ar
    ],
    'flood': [
        'flood', 'rising water', 'water level', 'drowning', 'submerged', 'river overflowing',
        'flash flood', 'washed away', 'dam breach', 'storm surge', 'heavy rain',
        'बाढ़', 'पानी भर गया', 'डूब रहा', 'नदी उफान', 'जलभराव', 'तेज बारिश',  # hi
        'पूर', 'पाणी भरले', 'बुडत आहे', 'धरण फुटले', 'नदीचे पाणी', 'पाणी शिरले', 'पूर आला', 'छतावर',  # mr
        'বন্যা', 'পানিবন্দী', 'ডুবে যাচ্ছে', 'নদী উপচে পড়া',  # bn
        'வெள்ளம்', 'மூழ்குகிறது', 'நீர் மட்டம்',  # ta
        'వరదలు', 'మునిగిపోవడం', 'నీరు పెరిగింది',  # te
        'પૂર', 'પાણી ભરાયા', 'ડૂબી રહ્યું છે',  # gu
        'വെള്ളപ്പൊക്കം', 'മുങ്ങിത്താഴുന്നു',  # ml
        'ಪ್ರವಾಹ', 'ನೀರು ತುಂಬಿದೆ', 'ಮುಳುಗುತ್ತಿದೆ',  # kn
        'ਹੜ੍ਹ', 'ਪਾਣੀ ਚੜ੍ਹਿਆ', 'ਡੁੱਬ ਰਿਹਾ',  # pa
        'سیلاب', 'پانی بھر گیا', 'ڈوب رہا ہے',  # ur
        'inundación', 'ahogando', 'crecida', 'desbordamiento',  # es
        'inondation', 'noyade', 'crue', 'débordement',  # fr
        'فيضان', 'غرق', 'منسوب المياه', 'سيول'  # ar
    ],
    'earthquake': [
        'earthquake', 'tremor', 'shaking', 'building collapse', 'rubble', 'debris',
        'aftershock', 'cracks in wall', 'structural collapse',
        'भूकंप', 'इमारत गिरी', 'मलबे', 'झटके', 'दीवार में दरार',  # hi
        'धरणीकंप', 'इमारत कोसळली', 'ढिगारा', 'भूकंप',  # mr
        'ভূমিকম্প', 'ভবন ধস', 'ধ্বংসস্তূপ', 'কম্পন',  # bn
        'நிலநடுக்கம்', 'கட்டிடம் இடிந்தது', 'இடிபாடுகள்',  # ta
        'భూకంపం', 'భవనం కూలింది', 'శిథిలాలు',  # te
        'ધરતીકંપ', 'મકાન પડ્યું', 'કાટમાળ',  # gu
        'ഭൂകമ്പം', 'കെട്ടിടം തകർന്നു', 'അവശിഷ്ടങ്ങൾ',  # ml
        'ಭೂಕಂಪ', 'ಕಟ್ಟಡ ಕುಸಿತ', 'ಅವಶೇಷಗಳು',  # kn
        'ਭੂਚਾਲ', 'ਇਮਾਰਤ ਡਿੱਗੀ', 'ਮਲਬਾ',  # pa
        'زلزلہ', 'زلزلے', 'عمارت گر گئی', 'دیواریں گر', 'جھٹکے', 'ملبہ',  # ur
        'terremoto', 'sismo', 'temblor', 'derrumbe', 'escombros',  # es
        'séisme', 'tremblement de terre', 'effondrement', 'décombres',  # fr
        'زلزال', 'هزة أرضية', 'انهيار مبنى', 'أنقاض'  # ar
    ],
    'road_accident': [
        'accident', 'car crash', 'collision', 'vehicle rollover', 'pedestrian hit',
        'highway crash', 'bus collision', 'truck accident', 'run over',
        'दुर्घटना', 'गाड़ी टकरा गई', 'एक्सीडेंट', 'वाहन पलट', 'टक्कर',  # hi
        'अपघात', 'गाडी धडकली', 'वाहन उलटले',  # mr
        'দুর্ঘটনা', 'গাড়ি দুর্ঘটনা', 'সংঘর্ষ',  # bn
        'விபத்து', 'வாகன மோதல்',  # ta
        'ప్రమాదం', 'వాహన ఢీకొంది',  # te
        'અકસ્માત', 'વાહન અથડામણ',  # gu
        'അപകടം', 'വാഹന കൂട്ടിയിടി',  # ml
        'ಅಪಘಾತ', 'ವಾಹನ ಡಿಕ್ಕಿ',  # kn
        'ਹਾਦਸਾ', 'ਟੱਕਰ',  # pa
        'حادثہ', 'گاڑی کی ٹکر', 'تصادم',  # ur
        'accidente', 'choque', 'colisión', 'atropellado',  # es
        'accident', 'collision', 'carambolage',  # fr
        'حادث سير', 'اصطدام', 'انقلاب سيارة', 'دهس'  # ar
    ],
    'missing_person': [
        'missing', 'lost child', 'lost elderly', 'cannot find', 'disappeared',
        'untraceable', 'kidnapped', 'lost in flood', 'separated',
        'लापता', 'खो गया', 'बच्चा गायब', 'मिल नहीं रहा',  # hi
        'बेपत्ता', 'सापडत नाही', 'हरवला',  # mr
        'নিখোঁজ', 'খুঁজে পাওয়া যাচ্ছে না', 'হারিয়ে গেছে',  # bn
        'காணவில்லை', 'தொலைந்துவிட்டார்',  # ta
        'కనిపించడం లేదు', 'తప్పిపోయారు',  # te
        'લાપતા', 'ખોવાઈ ગયું',  # gu
        'കാണാതായി',  # ml
        'ನಾಪತ್ತೆ', 'ಕಾಣೆಯಾಗಿದ್ದಾರೆ',  # kn
        'ਲਾਪਤਾ', 'ਗੁੰਮ ਹੋ ਗਿਆ',  # pa
        'لاپتہ', 'گمشدہ', 'مل نہیں رہا',  # ur
        'desaparecido', 'perdido', 'extraviado',  # es
        'disparu', 'perdu', 'introuvable',  # fr
        'مفقود', 'تائه', 'اختفاء'  # ar
    ],
    'trapped_person': [
        'trapped', 'stuck', 'pinned down', 'cannot get out', 'elevator stuck',
        'door locked', 'collapsed room', 'stuck inside',
        'फंसे हुए', 'अटक गए', 'बाहर नहीं निकल पा रहे', 'लिफ्ट फंस गई',  # hi
        'अडकले आहेत', 'बाहेर पडता येत नाही',  # mr
        'আটকা পড়েছে', 'বের হতে পারছি না',  # bn
        'சிக்கிக்கொண்டனர்', 'வெளியே வர முடியவில்லை',  # ta
        'చిక్కుకున్నారు', 'బయటకు రాలేకపోతున్నారు',  # te
        'ફસાયેલા', 'બહાર નથી નીકળી શકાતું',  # gu
        'കുടുങ്ങിപ്പോയി',  # ml
        'ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ', 'ಹೊರಬರಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ',  # kn
        'ਫਸਿਆ ਹੋਇਆ',  # pa
        'پھنسے ہوئے', 'باہر نہیں نکل سکتے',  # ur
        'atrapado', 'encerrado', 'no puedo salir',  # es
        'piégé', 'coincé', 'bloqué',  # fr
        'عالق', 'محتجز', 'لا أستطيع الخروج'  # ar
    ],
    'rescue_request': [
        'rescue', 'evacuation', 'need boat', 'airlift', 'save us', 'stranded on roof',
        'sos', 'urgent help', 'send help', 'rescue team',
        'बचाओ', 'रेस्क्यू', 'नाव भेजो', 'मदद चाहिए', 'छत पर फंसे',  # hi
        'वाचवा', 'बचाव कार्य', 'मदत पाठवा',  # mr
        'বাঁচান', 'উদ্ধার', 'সাহায্য পাঠান',  # bn
        'காப்பாற்றுங்கள்', 'மீட்பு பணி',  # ta
        'కాపాడండి', 'రక్షించండి',  # te
        'બચાવો', 'મદદ મોકલો',  # gu
        'രക്ഷിക്കൂ',  # ml
        'ರಕ್ಷಿಸಿ', 'ಸಹಾಯ ಕಳುಹಿಸಿ',  # kn
        'ਬਚਾਓ', 'ਮਦਦ ਭੇਜੋ',  # pa
        'بچاؤ', 'مدد بھیجیں', 'ریسکیو',  # ur
        'rescate', 'evacuación', 'salvadnos', 'ayuda urgente',  # es
        'secours', 'évacuation', 'sauvez-nous', 'aide urgente',  # fr
        'إنقاذ', 'إخلاء', 'أنقذونا', 'نجدة'  # ar
    ],
    'shelter_request': [
        'shelter', 'no place to stay', 'homeless', 'food and water', 'relief camp',
        'blankets', 'clean drinking water', 'displaced',
        'आश्रय', 'रहने की जगह नहीं', 'राहत शिविर', 'खाना पानी',  # hi
        'निवारा', 'राहत छावणी', 'अन्न पाणी',  # mr
        'আশ্রয়', 'ত্রাণ শিবির', 'খাবার ও পানি',  # bn
        'தங்குமிடம்', 'நிவாரண முகாம்',  # ta
        'పునరావాసం', 'ఆశ్రయం', 'సహాయ శిబిరం',  # te
        'આશરો', 'રાહત કેમ્પ',  # gu
        'അഭയകേന്ദ്രം',  # ml
        'ಆಶ್ರಯ', 'ಪರಿಹಾರ ಶಿಬಿರ',  # kn
        'ਆਸਰਾ', 'ਰਾਹਤ ਕੈਂਪ',  # pa
        'پناہ گاہ', 'امدادی کیمپ', 'کھانا اور پانی',  # ur
        'refugio', 'albergue', 'sin hogar', 'comida y agua',  # es
        'refuge', 'abri', 'sans abri', 'nourriture et eau',  # fr
        'مأوى', 'مخيم إغاثة', 'طعام وماء', 'مشرد'  # ar
    ]
}

# Critical indicators requiring instant highest triage priority
CRITICAL_INDICATORS = [
    'cardiac', 'heart attack', 'unconscious', 'severe bleeding', 'not breathing', 'drowning',
    'burning alive', 'cylinder blast', 'massive fire', 'building collapse', 'trapped under rubble',
    'choking baby', 'electrocution', 'severe head injury', 'bleeding heavily',
    'बेहोश', 'सांस नहीं', 'ज्यादा खून', 'इमारत गिरी', 'मलबे में दबा',
    'অচেতন', 'শ্বাস বন্ধ', 'ভবন ধস', 'ধ্বংসস্তূপে আটকা',
    'inconsciente', 'no respira', 'hemorragia', 'edificio colapsado',
    'inconscient', 'ne respire pas', 'hémorragie grave',
    'فقدان الوعي', 'توقف التنفس', 'نزيف حاد', 'انهيار كامل'
]

HIGH_INDICATORS = [
    'fracture', 'broken leg', 'rising water', 'stuck in lift', 'fire spreading',
    'injured', 'accident', 'cut', 'flames', 'heavy flooding', 'debris',
    'टूट गई', 'फंसा', 'आग फैल रही', 'तेज बहाव',
    'herido', 'atrapado', 'fractura', 'agua subiendo',
    'blessé', 'bloqué', 'eau monte', 'flammes',
    'مصاب', 'محاصر', 'كسر', 'مياه ترتفع'
]

# Actionable Safety Instructions for Fallback Responses
SAFETY_GUIDELINES = {
    'medical': {
        'en': "1. Call Emergency 112 / 102 (Ambulance) immediately.\n2. Do NOT move an injured person unless there is immediate danger (e.g., fire).\n3. Apply direct, firm pressure with a clean cloth to stop severe bleeding.\n4. If unconscious but breathing, place in the recovery side position.\n5. Keep the patient warm and calm. Do not administer oral liquids to unconscious persons.",
        'hi': "1. तुरंत आपातकालीन नंबर 112 / 102 (एम्बुलेंस) पर कॉल करें।\n2. जब तक तत्काल खतरा न हो, घायल व्यक्ति को न हिलाएं।\n3. भारी रक्तस्राव रोकने के लिए साफ कपड़े से सीधा दबाव बनाएं।\n4. यदि व्यक्ति बेहोश है लेकिन सांस ले रहा है, तो उसे करवट से लिटाएं।\n5. मरीज को शांत रखें और बेहोश व्यक्ति को कुछ भी न पिलाएं।",
        'mr': "1. ताबडतोब 112 किंवा 102 (रुग्णवाहिका) वर संपर्क साधा.\n2. तात्काळ धोका नसल्यास जखमी व्यक्तीला हलवू नका.\n3. रक्तस्त्राव थांबवण्यासाठी स्वच्छ कापडाने दाब द्या.\n4. रुग्ण शुद्धीवर नसल्यास करवंटीवर झोपवा आणि धीर द्या.",
        'es': "1. Llame a emergencias (112 / 911) inmediatamente.\n2. No mueva al herido a menos que haya peligro inminente.\n3. Aplique presión directa con un paño limpio para detener hemorragias.\n4. Si está inconsciente pero respira, colóquelo de lado en posición de recuperación.",
        'fr': "1. Appelez les urgences (112 / 15) immédiatement.\n2. Ne déplacez pas la victime sauf danger immédiat.\n3. Comprimez la plaie avec un linge propre pour arrêter le saignement.\n4. Si la personne est inconsciente et respira, placez-la en Position Latérale de Sécurité (PLS).",
        'ur': "1. فوری طور پر ایمرجنسی 112 / 1122 پر کال کریں۔\n2. جب تک شدید خطرہ نہ ہو، زخمی شخص کو مت ہلائیں۔\n3. خون بہنا روکنے کے لیے صاف کپڑے سے دباؤ ڈالیں۔\n4. بے ہوش شخص کو کروٹ کے بل لٹائیں اور کچھ کھانے پینے کو نہ دیں۔",
        'ar': "1. اتصل برقم الطوارئ فوراً.\n2. لا تحرك المصاب إلا في حالات الخطر المباشر.\n3. اضغط بقوة بقطعة قماش نظيفة لوقف النزيف.\n4. إذا كان فاقداً للوعي ويتنفس، ضعه في وضع الإفاقة على جانبه."
    },
    'fire': {
        'en': "1. Call Fire Services at 101 or 112 immediately.\n2. Evacuate immediately — DO NOT use elevators; use stairwells.\n3. Stay low to the ground to avoid inhaling toxic smoke.\n4. Feel door handles before opening; if hot, do NOT open.\n5. If trapped, seal gaps around doors with wet cloth and signal from a window.",
        'hi': "1. तुरंत 101 या 112 (अग्निशामक दल) को कॉल करें।\n2. तुरंत बाहर निकलें — लिफ्ट का उपयोग न करें, सीढ़ियों का प्रयोग करें।\n3. धुएं से बचने के लिए जमीन के करीब झुककर चलें।\n4. दरवाज़ा खोलने से पहले हैंडल छूकर देखें, अगर गर्म है तो न खोलें।\n5. यदि आप फंसे हैं, तो खिड़की से संकेत दें और दरवाज़े के नीचे गीला कपड़ा लगाएं।",
        'mr': "1. ताबडतोब 101 किंवा 112 (अग्निशामक) वर फोन करा.\n2. तत्काळ बाहेर पडा — लिफ्ट वापरू नका, जिन्याचा वापर करा.\n3. धुरापासून वाचण्यासाठी जमिनीलगत खाली वाकून चाला.\n4. अडकल्यास खिडकीतून मदत मागा आणि दरवाजाखाली ओला कपडा लावा.",
        'es': "1. Llame a los bomberos al 101 / 112 de inmediato.\n2. Evacúe de inmediato por las escaleras; no use elevadores.\n3. Camine agachado para evitar inhalar humo tóxico.\n4. Si está atrapado, tape las rendijas de la puerta con toallas húmedas y pida auxilio por la ventana.",
        'fr': "1. Appelez les pompiers (18 / 112) immédiatement.\n2. Évacuez par les escaliers; n'utilisez jamais les ascenseurs.\n3. Baissez-vous sous les fumées pour respirer de l'air frais.\n4. Si vous êtes coincé, calfeutrez les portes avec du linge mouillé et manifestez-vous à la fenêtre.",
        'ur': "1. فوری طور پر فائر بریگیڈ 101 یا 112 پر اطلاع دیں۔\n2. فورا عمارت خالی کریں اور لفٹ کی بجائے سیڑھیوں کا استعمال کریں۔\n3. دھوئیں سے بچنے کے لیے جھک کر یا رینگ کر چلیں۔\n4. اگر پھنس جائیں تو دروازے کے نیچے گیلا کپڑا رکھیں اور کھڑکی سے اشارہ کریں۔",
        'ar': "1. اتصل بفرق الإطفاء فوراً.\n2. قم بالإخلاء السريع عبر الدرج وتجنب المصاعد تماماً.\n3. انحنِ أرضاً لتجنب استنشاق الدخان السام.\n4. في حال الحصار، اغلق أسفل الأبواب بأقمشة مبللة واطلب النجدة عبر النافذة."
    },
    'flood': {
        'en': "1. Move immediately to higher ground or upper floors.\n2. NEVER attempt to walk, swim, or drive through flowing water (even 6 inches can sweep you off feet).\n3. Turn off main electricity switches and gas valves if safe to do so.\n4. Stay away from downed electrical wires.\n5. Call 112 or NDRF (1078) for rescue assistance.",
        'hi': "1. तुरंत किसी ऊंचे स्थान या ऊपरी मंजिल पर जाएं।\n2. बहते पानी में चलने, तैरने या गाड़ी चलाने की कोशिश कभी न करें।\n3. यदि सुरक्षित हो तो मुख्य बिजली और गैस कनेक्शन बंद कर दें।\n4. टूटे हुए बिजली के तारों से दूर रहें।\n5. बचाव सहायता के लिए 112 या NDRF (1078) पर कॉल करें।",
        'mr': "1. तातडीने उंच ठिकाणी किंवा इमारतीच्या वरच्या मजल्यावर जा.\n2. वाहत्या पाण्यातून चालण्याचा किंवा गाडी चालवण्याचा प्रयत्न करू नका.\n3. शक्य असल्यास वीज आणि गॅसचा मुख्य पुरवठा बंद करा.\n4. मदतीसाठी 112 किंवा NDRF 1078 वर संपर्क साधा.",
        'es': "1. Diríjase de inmediato a terrenos altos o plantas superiores.\n2. NUNCA intente cruzar a pie o en vehículo corrientes de agua.\n3. Desconecte la electricidad y el gas si es seguro hacerlo.\n4. Contacte al 112 para rescate de emergencia.",
        'fr': "1. Rejoignez immédiatement un point haut ou un étage supérieur.\n2. Ne vous engagez jamais à pied ou en voiture sur une voie inondée.\n3. Coupez l'électricité et le gaz si possible.\n4. Contactez le 112 pour les secours.",
        'ur': "1. فوری طور پر کسی اونچی جگہ یا بالائی منزل پر جائیں۔\n2. بہتے ہوئے پانی میں چلنے یا گاڑی چلانے کی ہرگز کوشش نہ کریں۔\n3. اگر ممکن ہو تو بجلی کا مین سوئچ اور گیس بند کر دیں۔\n4. ریسکیو کے لیے 112 پر رابطہ کریں۔",
        'ar': "1. انتقل فوراً إلى أماكن مرتفعة أو الطوابق العليا.\n2. لا تحاول السير أو القيادة في المياه الجارية إطلاقاً.\n3. افصل التيار الكهربائي والغاز إن كان ذلك آمناً.\n4. اتصل بأرقام الطوارئ للإنقاذ فوراً."
    },
    'earthquake': {
        'en': "1. DROP, COVER, and HOLD ON. Drop to your hands and knees, cover your head and neck under sturdy furniture.\n2. If indoors, stay indoors. Stay away from windows, glass, and exterior walls.\n3. If outdoors, move to an open area away from buildings, streetlights, and power lines.\n4. Expect aftershocks. Check yourself and others for injuries.\n5. Call 112 once the shaking stops if anyone is trapped or injured.",
        'hi': "1. झुकें, ढकें और पकड़ें (Drop, Cover, Hold on)। मजबूत मेज के नीचे सिर और गर्दन की रक्षा करें।\n2. यदि घर के अंदर हैं, तो अंदर ही रहें; खिड़कियों और कांच से दूर रहें।\n3. यदि बाहर हैं, तो इमारतों, खंभों और बिजली के तारों से दूर खुले स्थान पर जाएं।\n4. झटके रुकने के बाद चोटों की जांच करें और फंसे होने पर 112 पर कॉल करें।",
        'mr': "1. खाली बसा, डोके झाका आणि घट्ट पकडा (Drop, Cover, Hold).\n2. घरात असल्यास खिडक्या आणि काचेपासून लांब राहा.\n3. बाहेर असल्यास इमारती आणि विजेच्या खांबांपासून दूर मोकळ्या जागेत जा.\n4. धक्के थांबल्यावर जखमींची पाहणी करा आणि मदतीसाठी 112 वर कॉल करा.",
        'es': "1. ¡AGÁCHESE, CÚBRASE Y AGÁRRESE! Protéjase bajo una mesa resistente.\n2. Si está adentro, quédese adentro lejos de ventanas y vidrios.\n3. Si está afuera, aléjese de edificios, postes y cables eléctricos.\n4. Esté preparado para réplicas y llame al 112 si hay víctimas.",
        'fr': "1. BAISSEZ-VOUS, ABRIEZ-VOUS ET AGIPPÉ-VOUS sous un meuble solide.\n2. Éloignez-vous des fenêtres et des objets pouvant tomber.\n3. À l'extérieur, éloignez-vous des bâtiments et des lignes électriques.\n4. Préparez-vous aux répliques et contactez le 112 si besoin.",
        'ur': "1. جھکیں، سر کو مضبوط میز کے نیچے ڈھانپیں اور مضبوطی سے پکڑیں۔\n2. کھڑکیوں اور شیشوں سے دور رہیں۔\n3. اگر باہر ہیں تو عمارتوں اور بجلی کی تاروں سے دور کھلی جگہ پر جائیں۔\n4. زلزلے کے بعد زخمیوں کی مدد کریں اور 112 پر کال کریں۔",
        'ar': "1. انخفض، احتمِ تحت طاولة قوية، وتمسك بها جيداً.\n2. ابقَ في الداخل وابتعد عن النوافذ والجدران الخارجية.\n3. إذا كنت في الخارج، ابتعد عن المباني وأعمدة الكهرباء إلى مكان مفتوح.\n4. استعد للهزات الارتدادية واطلب الطوارئ عند الحاجة."
    },
    'other': {
        'en': "1. Stay calm and assess the immediate hazard around you.\n2. For immediate life-saving support, contact Pan-India Emergency Helpline: 112.\n3. If safe, submit an Emergency Report on ResQAI with your exact location.\n4. Keep your phone battery conserved and notify family or trusted contacts.",
        'hi': "1. शांत रहें और आसपास के खतरे का आकलन करें।\n2. आपातकालीन सहायता के लिए 112 पर तुरंत कॉल करें।\n3. यदि सुरक्षित हों, तो ResQAI पर अपनी सही लोकेशन के साथ रिपोर्ट दर्ज करें।\n4. मोबाइल की बैटरी बचाकर रखें।",
        'mr': "1. शांत राहा आणि सभोवतालच्या परिस्थितीचा आढावा घ्या.\n2. आपत्कालीन मदतीसाठी 112 वर कॉल करा.\n3. सुरक्षित असल्यास ResQAI वर लोकेशनसह रिपोर्ट नोंदवा.",
        'es': "1. Mantenga la calma y evalúe la situación.\n2. Para asistencia inmediata comuníquese al 112.\n3. Si es seguro, envíe su reporte de emergencia en ResQAI con su ubicación.",
        'fr': "1. Restez calme et évaluez les risques environnants.\n2. Pour toute urgence vitale, contactez le 112.\n3. Si vous êtes en sécurité, soumettez un rapport sur ResQAI avec votre position.",
        'ur': "1. پرسکون رہیں اور خطرے کا اندازہ لگائیں۔\n2. فوری مدد کے لیے 112 پر رابطہ کریں۔\n3. اگر محفوظ ہیں تو اپنی لوکیشن کے ساتھ ایمرجنسی رپورٹ درج کریں۔",
        'ar': "1. حافظ على هدوئك وتأكد من سلامة محيطك.\n2. لطلب المساعدة الفورية اتصل برقم الطوارئ 112.\n3. قم بتقديم بلاغ في المنصة مع موقعك الدقيق متى كان ذلك آمناً."
    }
}

def classify_message_rule_based(text):
    """
    Deterministic zero-latency keyword and pattern classifier.
    Returns:
        dict: {
            'category': str,
            'urgency': 'Critical' | 'High' | 'Medium' | 'Low',
            'confidence': float,
            'explanation': str,
            'is_high_risk': bool
        }
    """
    if not text or not text.strip():
        return {
            'category': 'other',
            'urgency': 'Low',
            'confidence': 0.5,
            'explanation': 'Empty or generic input.',
            'is_high_risk': False
        }

    lower_text = text.lower()
    
    # 1. Check Critical urgency
    is_critical = any(ind in lower_text for ind in CRITICAL_INDICATORS)
    is_high = any(ind in lower_text for ind in HIGH_INDICATORS)
    
    # 2. Score Categories
    category_scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in lower_text)
        if score > 0:
            category_scores[cat] = score

    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        confidence = min(0.95, 0.65 + (category_scores[best_category] * 0.1))
    else:
        best_category = 'other'
        confidence = 0.50

    if is_critical:
        urgency = 'Critical'
        is_high_risk = True
        explanation = f"Flagged as Critical: Life-threatening indicators detected for {best_category} emergency."
    elif is_high or best_category in ('medical', 'fire', 'trapped_person'):
        urgency = 'High'
        is_high_risk = True
        explanation = f"Flagged as High: Urgent rescue or medical hazard detected in {best_category} category."
    elif best_category in ('flood', 'earthquake', 'road_accident', 'rescue_request'):
        urgency = 'Medium'
        is_high_risk = False
        explanation = f"Flagged as Medium: Incident categorized under {best_category} requiring responder coordination."
    else:
        urgency = 'Low'
        is_high_risk = False
        explanation = "Flagged as Low: General query or non-immediate hazard."

    return {
        'category': best_category,
        'urgency': urgency,
        'confidence': round(confidence, 2),
        'explanation': explanation,
        'is_high_risk': is_high_risk
    }

def get_safety_instructions(category, language='en'):
    """Return verified safety guidance for the given category in preferred language."""
    cat_guides = SAFETY_GUIDELINES.get(category, SAFETY_GUIDELINES['other'])
    # Return requested language if available, else English
    return cat_guides.get(language, cat_guides.get('en', SAFETY_GUIDELINES['other']['en']))
