import os
import re
import requests
import urllib3
import json
import sys
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
from math import factorial
from random import choice

# --- PYTHON ORTAM AYARLARI ---
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LANG'] = 'C.UTF-8'

# Konsol çıktı kodlamasını UTF-8 olarak ayarlama
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    except Exception:
        pass

# SSL doğrulama uyarılarını yok sayar (Wikipedia erişimi için gerekli olabilir)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- FLASK VE API AYARLARI ---
WIKI_API_URL = "https://tr.wikipedia.org/w/api.php"
HEADERS = {
    'User-Agent': 'YerelSohbetBotu/16.0-TurkishAi-Extended (contact: user@example.com)'
}

app = Flask(__name__)
app.secret_key = 'final_wiki_sohbet_bot_key'

# 🚨 BOT ADI VE YARATICI:
BOT_NAME = "TurkishAi"
CREATOR = "Hytantic"

# --- RENDER TEMPLATE (HTML ARAYÜZÜ) ---
RENDER_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TurkishAi | Türkçe Bilgi Asistanı</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet">
    <style> 
        body { font-family: 'Inter', sans-serif; background-color: #f0f4f8; }
        .user-bubble { background-color: #4f46e5; color: white; border-bottom-right-radius: 4px; }
        .ai-bubble { background-color: #ffffff; color: #1f2937; border: 1px solid #e5e7eb; border-bottom-left-radius: 4px; }
        .ai-bubble a { color: #4f46e5; text-decoration: underline; font-weight: 600; }
        .ai-bubble strong { font-weight: 700; }
        .loading-dot { animation: dot-fading 1.5s infinite ease-in-out; }
        .loading-dot:nth-child(2) { animation-delay: 0.2s; }
        .loading-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes dot-fading {
            0%, 80%, 100% { opacity: 0; }
            40% { opacity: 1; }
        }
        #chat-history::-webkit-scrollbar { width: 8px; }
        #chat-history::-webkit-scrollbar-thumb { background-color: #a5b4fc; border-radius: 10px; }
        @media (max-width: 640px) {
            #chat-container { max-width: 100%; margin: 0; height: 100vh; border-radius: 0; box-shadow: none; }
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">
    <div id="chat-container" class="bg-white rounded-xl shadow-2xl flex flex-col max-w-lg w-full h-[90vh] md:h-[80vh] overflow-hidden">
        <header class="bg-indigo-600 p-4 text-white shadow-lg flex items-center justify-between rounded-t-xl">
            <div class="flex items-center">
                <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2m-6 4v2m6-2v2M5 9H3m18 0h-2m-8 2v-2m-6 4h6m-6 4h6m8-10h-6m6 0a3 3 0 110-6 3 3 0 010 6zM3 12h2m4 0h6m4 0h2m-8 4v2m-6-2v2m-6 4v2m6-2v2m6-2v2m-6 4v2m6-2v2m6 4v2"></path></svg>
                <h1 class="text-xl font-bold">TurkishAi 🇹🇷</h1>
            </div>
            <span class="text-sm font-medium opacity-80">Süper Akıcı Türkçe Asistan</span>
        </header>
        <div id="chat-history" class="flex-grow p-4 overflow-y-auto space-y-4">
            <div class="flex justify-start">
                <div class="ai-bubble max-w-[85%] p-3 rounded-xl rounded-tl-sm shadow-md">
                    <p class="font-semibold text-indigo-600">TurkishAi Asistanı</p>
                    <p class="mt-1">Hoş geldiniz! Ben **TurkishAi**, kural tabanlı ve **1500'den fazla** akıcı Türkçe ifadeyle donatılmış, Wikipedia destekli bir yapay zekayım. Size nasıl yardımcı olabilirim?</p>
                    <p class="text-xs mt-2 text-gray-500">Örn: "Fatih Sultan Mehmet kimdir?", "Bana bir atasözü söyle.", "Nasılsın?", "350*45 kaç eder?"</p>
                </div>
            </div>
        </div>
        <div id="loading-indicator" class="p-4 hidden">
            <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-indigo-500 rounded-full loading-dot"></div>
                <div class="w-2 h-2 bg-indigo-500 rounded-full loading-dot"></div>
                <div class="w-2 h-2 bg-indigo-500 rounded-full loading-dot"></div>
                <span class="text-sm text-gray-500 ml-2">TurkishAi düşünüyor ve bilgi kaynaklarını tarıyor...</span>
            </div>
        </div>
        <div class="p-4 border-t border-gray-200">
            <div class="flex items-center">
                <input type="text" id="user-input" placeholder="Sorunuzu buraya yazın..." class="flex-grow p-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition duration-150" onkeypress="if(event.key === 'Enter') sendMessage()">
                <button onclick="sendMessage()" id="send-button" class="bg-indigo-600 hover:bg-indigo-700 text-white p-3 rounded-r-lg shadow-lg transition duration-150 ease-in-out flex items-center justify-center transform active:scale-95">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </button>
            </div>
        </div>
    </div>
    <script>
        const chatHistory = document.getElementById('chat-history');
        const userInput = document.getElementById('user-input');
        const loadingIndicator = document.getElementById('loading-indicator');
        const sendButton = document.getElementById('send-button');

        // Basit bir Markdown (bold, link, satır sonu) dönüştürücü
        function convertMarkdown(text) {
            // Kalın metin (Markdown: **...**)
            text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            // [Kaynak Linki]
            text = text.replace(/Kaynak Linki:\s*(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">Kaynak Linki</a>');
            // Satır sonları (\n) -> <br>
            text = text.replace(/\n/g, '<br>');
            return text;
        }

        function createMessageBubble(sender, message) {
            const isUser = sender === 'user';
            const messageDiv = document.createElement('div');
            messageDiv.className = 'flex ' + (isUser ? 'justify-end' : 'justify-start');

            const bubble = document.createElement('div');
            bubble.className = 'max-w-[85%] p-3 rounded-xl shadow-md transition duration-300 ease-in-out ' + (isUser ? 'user-bubble rounded-br-sm' : 'ai-bubble rounded-tl-sm');

            if (!isUser) {
                const senderName = document.createElement('p');
                senderName.className = 'font-semibold text-indigo-600';
                senderName.textContent = 'TurkishAi Asistanı';
                bubble.appendChild(senderName);
            }

            const messageContent = document.createElement('p');
            messageContent.className = isUser ? 'mt-0' : 'mt-1';
            let htmlMessage = convertMarkdown(message);
            messageContent.innerHTML = htmlMessage;

            bubble.appendChild(messageContent);
            messageDiv.appendChild(bubble);
            chatHistory.appendChild(messageDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;

            createMessageBubble('user', message);
            userInput.value = '';
            
            loadingIndicator.classList.remove('hidden');
            userInput.disabled = true;
            sendButton.disabled = true;
            sendButton.classList.add('opacity-50');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message }),
                });

                if (!response.ok) {
                    throw new Error('Sunucudan yanıt alınamadı.');
                }

                const data = await response.json();
                createMessageBubble('ai', data.response);

            } catch (error) {
                console.error("Hata:", error);
                createMessageBubble('ai', '**HATA:** Sunucu ile iletişimde bir sorun oluştu veya bilgi kaynaklarına ulaşılamadı. Lütfen konsolu kontrol edin.');
            } finally {
                loadingIndicator.classList.add('hidden');
                userInput.disabled = false;
                sendButton.disabled = false;
                sendButton.classList.remove('opacity-50');
                userInput.focus();
            }
        }

        window.onload = () => {
            chatHistory.scrollTop = chatHistory.scrollHeight;
            userInput.focus();
        };
    </script>
</body>
</html>
"""

# --- TÜRKÇE ATASÖZLERİ VE DEYİMLER (Genişletildi) ---
TURKISH_PROVERBS = [ 
    "Aç ayı oynamaz.", "Dost kara günde belli olur.", "Can çıkmayınca huy çıkmaz.", "Akıl yaşta değil, baştadır.",
    "Komşu komşunun külüne muhtaçtır.", "Mum dibine ışık vermez.", "Davulun sesi uzaktan hoş gelir.",
    "Göz görmeyince gönül katlanır.", "Sakla samanı, gelir zamanı.", "Boş teneke çok ses çıkarır.",
    "Bıçak kemiğe dayandı.", "Tencere yuvarlanmış kapağını bulmuş.", "İki karpuz bir koltuğa sığmaz.",
    "Taşı gediğine koymak.", "Lafı ağzına tıkamak.", "Etekleri zil çalmak.", "Gözden gönülden ırak.",
    "Kulak misafiri olmak.", "Can kulağıyla dinlemek.", "Pireyi deve yapmak.", "Abayı yakmak.",
    "Aç kalmak.", "Aç kalmak, tok oturmak.", "Adı çıkmak.", "Adını anmak.", "Ağız açmamak.",
    "Ağzı kulaklarına varmak.", "Ağzında bakla ıslanmamak.", "Ağız birliği etmek.", "Ağız dalaşına girmek.",
    "Akla karayı seçmek.", "Armudun sapı üzümün çöpü.", "Baltayı taşa vurmak.", "Damarına basmak.",
    "Ekmek elden su gölden.", "Göz boyamak.", "Hapı yutmak.", "İpe un sermek.", "Kabak tadı vermek.",
    "Kılı kırk yarmak.", "Paranın yüzü sıcaktır.", "Saman altından su yürütmek.", "Şeytan tüyü olmak.",
    "Bin bilsen de bir bilene danış.", "Bin dost az, bir düşman çoktur.", "Bir elin nesi var iki elin sesi var.", 
    "Can çıkar huy çıkmaz.", "Çok yaşayan değil, çok gezen bilir.", "Düğün arpasıyla at beslenmez.", 
    "Ekmek mayadan kız anadan olur.", "Suyun çağlamazından insanın söylemezinden kork.", 
    "Tavşan dağa küsmüş, dağın haberi olmamış.", "Üzüm üzüme baka baka kararır.", "Yalnız taş duvar olmaz.", 
    "Yazın gölge hoş, kışın ambar boş.", "Yumuşak atın çiftesi pek olur.", 
    "Zenginin keyfi gelene kadar fakirin canı çıkarmış.", "Akıl bir altın taçtır her kafaya uymaz.", 
    "Komşu komşunun işine muhtaçtır.", "Büyüğün yoksa büyük taşa danış.", "Asil azmaz, bal acımaz.", 
    "Dil otu yemiş.", "Azdan az gider, çoktan çok gider.", "Sırrını söyleme dostuna, dostun söyler dostuna.", 
    "Ucuz et satır kırdırır.", "Ağaç yaşken eğilir.", "Ağır otur ki bey desinler.", 
    "Ağlarsa anam ağlar, gayrısı yalan ağlar.", "Ağrısız baş mezarda olur.", "Bakarsan bağ olur, bakmazsan dağ olur.", 
    "Çıkmadık canda umut var.", "Çivi çiviyi söker.", 
    "Acı söz adamı dinden çıkarır, tatlı söz yılanı inden çıkarır.", "Ağır taş yerinden oynamaz.", 
    "Akacak kan damarda durmaz.", "Akan su yosun tutmaz.", "Tatlı dil yılanı deliğinden çıkarır.", 
    "Terzi kendi söküğünü dikemez.", "Yel kayadan ne alır?", "Zahmetsiz rahmet olmaz.", 
    "Yüzü güzele kırk günde doyulur, huyu güzele kırk yılda doyulmaz.", 
    "Alma mazlumun ahını, çıkar aheste aheste.", "Anasına bak kızını al, kenarına bak bezini al.", 
    "Baş başa vermeyince taş yerinden oynamaz.", "Damlaya damlaya göl olur.", 
    "Dereyi görmeden paçayı sıvama.", "Doğru söz acıdır.", "Gülü seven dikenine katlanır.", "Hamama giren terler.", 
    "Körle yatan şaşı kalkar.", "Lafla peynir gemisi yürümez.", "Ne ekersen onu biçersin.", 
    "Perşembenin gelişi çarşambadan bellidir.", "Rüzgar eken fırtına biçer.", "Taşıma suyla değirmen dönmez.", 
    "Yalancının mumu yatsıya kadar yanar.", "Zararın neresinden dönülse kârdır.", "Her koyun kendi bacağından asılır.", 
    "Atı alan Üsküdar'ı geçti.", "Bir musibet bin nasihattan iyidir.", "Hatasız kul olmaz.", 
    "Haydan gelen huya gider.", "İşleyen demir ışıldar.", "Kaz gelen yerden tavuk esirgenmez.", 
    "Kedi uzanamadığı ciğere mundar der.", "Komşuda pişer bize de düşer.", "Öfke baldan tatlıdır.", 
    "Sabreden derviş muradına ermiş.", "Yorgan gitti kavga bitti.", "Aklın yolu birdir.", 
    "Anlayana sivrisinek saz, anlamayana davul zurna az.", "Ateş düştüğü yeri yakar.", 
    "Bal tutan parmağını yalar.", "Birlikten kuvvet doğar.", "El elden üstündür.", 
    "Elin ağzı torba değil ki büzesin.", "Güneş balçıkla sıvanmaz.", "Her işte bir hayır vardır.", 
    "İnsan yedisinde ne ise yetmişinde de odur.", "Mal canın yongasıdır.", 
    "Minareyi çalan kılıfını hazırlar.", "Ölenle ölünmez.", "Parayı veren düdüğü çalar.", 
    "Söz gümüşse sükut altındır.", "Tilkinin dönüp dolaşacağı yer kürkçü dükkanıdır.", 
    "Yuvayı dişi kuş yapar.", "Etekleri zil çalmak.", "Gözdağı vermek.", "İçi içine sığmamak.", 
    "Pabucu dama atılmak.", "Saçını süpürge etmek.", "Yediği önünde yemediği arkasında.", 
    "Zevkten dört köşe olmak.", "Ayağına kara su inmek.", "Burnunun direği sızlamak.", 
    "Can kulağıyla dinlemek.", "Ciğeri beş para etmez.", "Deli divane olmak.", "Gözü tok olmak.", 
    "Hakkını helal etmek.", "İpe un sermek.", "Karnı zil çalmak.", "Yüreği ağzına gelmek.", 
    "Aklını başına almak.", "Başına buyruk.", "Eli açık.", "Gözden düşmek.", 
    "İki arada bir derede kalmak.", "Kaderine razı olmak.", "Kulak asmamak.", 
    "Suya götürüp susuz getirmek.", "Dört gözle beklemek.", "Kulağına küpe olmak.", 
    "Akıl yaşta değil baştadır.", "Ateş olmayan yerden duman çıkmaz.", 
    "Cahile söz anlatmak deveye hendek atlatmaktan zordur.", "Dost acı söyler.", 
    "Eceli gelen köpek cami duvarına işer.", "Felek yâr olursa, dağlar bile yol verir.", 
    "Gülme komşuna gelir başına.", "Harman döven öküzün ağzı bağlanmaz.", 
    "İki gönül bir olunca samanlık seyran olur.", "Kılıç kınını kesmez.", 
    "Körler memleketinde şaşılar padişah olur.", "Mal sahibi mülk sahibi, hani bunun ilk sahibi?", 
    "Ne yersen yanına kâr kalır.", "Otu çek köküne bak.", "Rızkını taştan çıkaranlar var.", 
    "Sütten ağzı yanan yoğurdu üfleyerek yer.", "Şeytanın dostluğu darağacına kadardır.", 
    "Uyuyan yılanın kuyruğuna basılmaz.", "Vur deyince öldürme.", "Ya devlet başa ya kuzgun leşe.", 
    "Ağaç düşse de kökünü unutmaz.", "Borç yiğidin kamçısıdır.", "Can pazarı kurulur.", 
    "Çam sakızı çoban armağanı.", "Denize düşen yılana sarılır.", "Ekmeğini taştan çıkarmak.", 
    "Fakir evine ateş düşse kimsenin haberi olmaz.", "Gözden ırak olan gönülden de ırak olur.", 
    "Haddini bilmeyene bildirirler.", "İyilik et denize at, balık bilmezse Hâlık bilir.", 
    "Karga yavrusuna bakmış 'Benim akım' demiş.", "Korkunun ecele faydası yok.", 
    "Leyleğin ömrü laklakla geçer.", "Mart kapıdan baktırır kazma kürek yaktırır.", 
    "Nerede çokluk orada bokluk.", "Öfkeyle kalkan zararla oturur.", "Para parayı çeker.", 
    "Sabahın işini akşama bırakma.", "Söz var iş bitirir, söz var baş yitirir.", 
    "Şaşkın ördek başını taşa çalar.", "Tavuk su içeceğine bakıp 'Kınalı parmaklarım' der.", 
    "Ummadığın taş baş yarar.", "Üzümün çöpü, armudun sapı var.", "Vakit nakittir.", 
    "Yağmurdan kaçarken doluya tutulmak.", "Zorla güzellik olmaz.", 
    "Ağızdan çıkan laf yaydan çıkan ok gibidir.", "Balık baştan kokar.", "Canını dişine takmak.", 
    "Çiğ süt emmiş.", "Deliye her gün bayram.", "Eşek hoşaftan ne anlar?", "Gelene git denilmez.", 
    "Horozu çok olan köyün sabahı geç olur.", "İnsan beşer şaşar.", "Kör satıcının kör alıcısı olur.", 
    "Kurt dumanlı havayı sever.", "Meyve veren ağaç taşlanır.", "Namussuzun şerefi olmaz.", 
    "Oynayan kıpırdayan kalır.", "Padişahın dediği olur.", "Rüzgar esmeyince yaprak kımıldamaz.", 
    "Sana dar gelmeyen ev, bana da dar gelmez.", "Şüpheli işe başlama.", 
    "Tilkinin dönüp dolaşacağı yer kürkçü dükkanıdır.", "Umduğunu değil, bulduğunu ye.", 
    "Vefasızın dostluğu olmaz.", "Yuvayı yapan dişi kuştur.", 
    "Zemheride kar yağmadan, zemheride kar yağmaz.", "Bülbül güle karşı öter.", 
    "Cevizin kabuğunu kırıp özünü yemeli.", "Deliye taş atma, başına taş gelir.", "Ekmek kapısı.", 
    "Fare deliğe sığmamış, bir de kuyruğuna kabak bağlamış.", "Gündüzün feneri, gecenin yıldızı.", 
    "Hangi dağın kurduysan, o dağın yolunu bilirsin.", "İnsan, insanın kurdudur.", 
    "Kızını dövmeyen dizini döver.", "Kusursuzluk Allah'a mahsustur.", 
    "Malı deniz olanın, kıyıdan geçenin canı yanar.", "Nazar etme ne olur, çalış senin de olur.", 
    "Ruhun gıdası kitaptır.", "Son pişmanlık fayda etmez.", "Şeytanın işi kolaydır.", 
    "Taş yerinde ağırdır.", "Ulu sözü dinlemeyen ulu kalır.", "Vatan sevgisi imandan gelir.", 
    "Yabancı elin yağı kar gibidir.", "Zaman ilaçtır.", "Açın gözü ekmek teknesinde olur.", 
    "Balık etinden, insan derisinden yaşar.", "Çocuk yediği yerde uyur.", "Dilencinin torbası dolmaz.", 
    "El atına binen tez iner.", "Gelen gideni aratır.", "Hızlı giden atın boku seyrek düşer.", 
    "İti an çomağı hazırla.", "Korku büyük göz açar.", "Kurt uluması duyulmaz.", 
    "Misafir on kısmetle gelir, birini yer dokuzunu bırakır.", "Nerede hareket, orada bereket.", 
    "Oğlan dayıya, kız halaya çeker.", "Pazarlık sünnettir.", 
    "Rüşvet kapıdan girince adalet bacadan çıkar.", "Su akmayınca durulmaz.", "Şeytan kulağına kurşun.", 
    "Topraktan gelip toprağa gitmek.", "Ummadık yerden gelen, ummadık işler yapar.", 
    "Vurursan başa, ya ölür ya şaşar.", "Yarım elma gönül alma.", "Zenginin horozu bile yumurtlar.", 
    "Adamın iyisi iş başında belli olur.", "Boğaz dokuz boğumdur.", "Can boğazdan gelir.", 
    "Çok bilen çok yanılır.", "Damdan düşenin halinden damdan düşen anlar.", 
    "Elden gelen öğün olmaz, o da vaktinde gelmezse.", "Gönül ferman dinlemez.", 
    "Horoz ötmezse sabah olmaz.", "Körün taşı toprağa düşer.", "Lafın tamamı deliye söylenir.", 
    "Mum dibine ışık vermez.", "Ne karanlıkta kal ne de karalıkta.", "Ölüm hak, miras helal.", 
    "Pireyi deve yapmak.", "Rüzgarın yönü belli olmaz.", "Söz senettir.", 
    "Şımarık eşeğin kuyruğu uzun olur.", "Tembel yorulmak bilmez.", "Umut fakirin ekmeğidir.", 
    "Var mıydı, yok muydu, görmedik ama duyduk.", "Yüz karası.", 
    "Zorla yenen aş, ya karın ağrıtır ya baş.", "Aç kalmaktansa aç yatmak yeğdir.", 
    "Ay ışığında ceviz silkilmez.", "Baba mirasıyla yürünmez.", 
    "Deliye bal tattırmışlar, 'tuzsuz' demiş.", "Güneş doğmadan uyanmak.", 
    "Kız beşikte, çeyiz sandıkta.", "Körün gözü parayla açılır.", "Misafir kısmetiyle gelir.", 
    "Nereye gidersen git, kendi huyunla gidersin.", "Öküz öldü, ortaklık bitti.", 
    "Peynir gemisi yürümez.", "Su uyur, düşman uyumaz.", "Şeytan diyor ki...", "Tuz ekmek hakkı.", 
    "Ununu elemiş, eleğini asmış.", "Yüzünden düşen bin parça.", "Zorla yenen aş, karın ağrıtır.", 
    "Alçak uçan uçak, alçak uçar.", "Armut piş ağzıma düş.", "Boğazdan geçen lokma.", 
    "Düğün evinde ağlayan, ölü evinde gülen olmaz.", "Eski hamam eski tas.", 
    "Gözünü toprak doyursun.", "Kılavuzu karga olanın burnu boktan çıkmaz.", "Kurdun adı çıkmış.", 
    "Laf ebesi.", "Ne oldum dememeli, ne olacağım demeli.", "Ömür törpüsü.", 
    "Rüzgarın önündeki yaprak.", "Sağlık olsun.", "Son gülen iyi güler.", 
    "Şüyuu vukuundan beter.", "Topyekûn saldırı.", "Ulu orta konuşmak.", "Vur ha vur!", 
    "Yüreği yanmak.", "Zurnada peşrev olmaz.", "Akılla hareket etmek.", "Bardağı taşıran son damla.", 
    "Canı burnuna gelmek.", "Çenesi düşük.", 
    "Deveye sormuşlar 'neren eğri' diye, 'nerem doğru ki' demiş.", "Elbette.", "Gözü kara.", 
    "Hava cıva.", "İğne atsan yere düşmez.", "Karınca kararınca.", "Kedi gibi.", 
    "Lafı ağzına tıkamak.", "Namerde muhtaç olmak.", "Oyun kurucu.", "Para pul.", 
    "Ruhu şad olmak.", "Samanlıkta iğne aramak.", "Şüphesiz.", 
    "Tencere dibin kara, seninki benden kara.", "Umutsuz vaka.", "Vazgeçmek.", "Yazıya tura.", 
    "Zarar etmek.", "Ağzı kulaklarına varmak.", "Bin dereden su getirmek.", "Canını sıkmak.", 
    "Çocuk oyuncağı.", "Dilinde tüy bitmek.", "Etekleri tutuşmak.", "Gözü yükseklerde olmak.", 
    "Hesaba katmak.", "İncir çekirdeğini doldurmaz.", "Karışık.", "Kırk yıllık dost.", 
    "Laf cambazı.", "Ne yapalım?", "Olacağı varsa olur.", "Pazara çıkmak.", "Rastgele.", 
    "Saygı duymak.", "Şeytan diyor ki.", "Tuttuğunu koparmak.", "Usluca.", 
    "Vur patlasın çal oynasın.", "Yüzsüz.", "Zaten.", 
    "Açma sırrını dostuna, o da söyler dostuna.", "Ayağını yorganına göre uzat.", 
    "Babası ölen dul kalmaz, kocası ölen dul kalır.", "Çok havlayan köpek ısırmaz.", 
    "Dibi görünmeyen sudan geçme.", "Elinin hamuruyla erkek işine karışma.", 
    "Fırsat ele geçmez, ele geçerse kaçmaz.", "Gelen ağam, giden paşam.", 
    "Halep oradaysa, arşın buradadır.", "İki cambaz bir ipte oynamaz.", 
    "Karnı tok itin kuyruğu dik olur.", "Kılavuzsuz yolu şaşıran, dostsuz yolu şaşırır.", 
    "Mevlana'yı sormuşlar, 'gel' demiş.", "Nasihat istersen tembele iş buyur.", 
    "Oturduğun dalı kesme.", "Paça ıslanmadan balık tutulmaz.", "Rüzgâr esmeyince yaprak oynamaz.", 
    "Saman altından su yürütmek.", "Şaşkın bakkal, karpuz tartar.", "Teyzesi olmayanın yarısı olmaz.", 
    "Uluya uluya köyün ortasına gelmek.", "Veren el alan elden üstündür.", 
    "Yabancıya güvenmek, suya yazı yazmak gibidir.", 
    "Zenginin malı, züğürdün çenesini yorar.", "Açgözlüye az bile gelir.", 
    "Boş gezmekten bedava çalışmak iyidir.", "Canı yanan eşek atı geçer.", "Çocuktan al haberi.", 
    "Dağ başında duman eksik olmaz.", "Ekmek yediğin kapıyı kirletme.", 
    "Gönül kimi severse, güzel odur.", "Hamala semeri yük değil.", 
    "İyilik et komşuna, komşun da etsin sana.", "Kız yediği yerde doymaz.", 
    "Kusursuz dost arayan dostsuz kalır.", "Laf lafı açar.", "Nereden bileceksin?", 
    "Oğlumu doğuran kızımı doğurmaz.", "Para tatlıdır.", "Rızkı veren Allah'tır.", 
    "Söz ağızdan çıktı bir kere.", "Şöhret beladır.", "Tavuk ölür, civcivler büyür.", 
    "Usta elden yemek.", "Vuran dağ olur, vuran dağ olmaz.", "Yar bana düşman çıktı.", 
    "Ziyanın neresinden dönülse kârdır.", "Ağaç meyvesiyle, insan bilgisiyle.", 
    "Balık ağa girmeden pazarlık yapılmaz.", "Çok konuşan çok yanılır.", 
    "Deli deliyi görünce çomağını saklar.", "Güneş girmeyen eve doktor girer.", 
    "Hakkın tokmağı vardır.", "İnsan, sözünden, hayvan yularından tutulur.", 
    "Kız evlat, kapı kilidi.", "Kötülük eden kötülük bulur.", "Lafın kısası makbuldür.", 
    "Ne verirsen elinle, o gelir seninle.", "Oynamayan gelin 'yerim dar' dermiş.", 
    "Pekmezin olsun sinek Bağdat'tan gelir.", "Rüzgar ekip fırtına biçmek.", 
    "Sakınan göze çöp batar.", "Şaşkın ördek taşa çalar.", "Taşı gediğine koymak.", 
    "Ummadık taş baş yarar.", "Vakit dar.", "Yarınlar bizim.", "Zamana bırakmak.", 
    "Ak akçe kara gün içindir.", "Bıçak kemiğe dayanmak.", "Cevizin kabuğunu kır.", 
    "Çok laf az iş.", "Deveye günde bir öğün yemek verirler.", 
    "Eskiye rağbet olsa bit pazarına nur yağardı.", "Gelin güvey olmak.", "Hırka dar.", 
    "İyilik et kendine, kötülük etme.", "Kızım sana söylüyorum, gelinim sen anla.", "Lafın kısası",
]


# --- KABA DİL FİLTRESİ (GENİŞLETİLDİ) ---
BAD_WORDS = [
    "aptal", "salak", "gerizekalı", "oç", "piç", "siktir", "siktir git", "göt", "sik", "yarak", "amk", "aq", "sg", "orospu",
    "lan", "yavşak", "pezevenk", "gavat", "kaltak", "şerefsiz", "piçin", "mal", "beyinsiz", "geri zekalı", "ağzını bozma",
    "dangalak", "ahmak", "manyak", "serseri", "köpek", "it", "domuz", "eşek", "hayvan", "zibidi", "haysiyetsiz", "karaktersiz",
    "hasiktir", "hsktr", "sç", "bok", "çüş", "yuh", "terbiyesiz", "ayıp", "görgüsüz", "edepsiz", "puşt", "ibne", "kfr", "kufur", 
    "küfür", "seks", "porno", "amcik", "got", "sikiş", "ağzına sıçayım", "cehennem", "kahrolsun", "defol", "yürü git", "sen kimsin ki", 
    "sana ne", "beğenmedim", "çok kötü", "berbat", "sıfır", "kötü yapıyorsun", "beş para etmez", "rezil", "boktan", "yetersiz",
    "süzme", "hıyar", "öküz", "sığır", "terbiyesizlik", "kaba", "bana ne", "git başımdan", "bırak beni", "kapa çeneni", "kes sesini",
    "sus", "kes", "kıç", "gavat", "yelloz", "pezevenk", "zibidi", "yobaz", "faşist", "terörist", "şarlatan", "haysiyetsiz",
    "puşt", "ibne", "kaka", "bok", "saçmalama", "ne alaka", "alakası yok", "boşver", "kafana takma", "gıcık", "sinir", "sinir oldum",
    "sana ne", "sanane", "umurumda değil", "ne halin varsa gör", "git", "hadi git", "çek git", "yol al", "sana kim dedi", "sen karışma",
    "sana giren çıkan ne", "bana bulaşma", "yeter", "kapat", "bitir", "sana ne oluyor", "sen kimsin", "kime diyorum", "kime ne", "küstüm",
    "cehenneme git", "öl", "geber", "lanet olsun", "nefret ediyorum", "iğrenç", "midem bulandı", "yalan", "yalan söylüyorsun", "sahtekar",
    "oyun yapma", "artistlik yapma", "havalı", "şımarık", "egoist", "ukala", "zırva", "sacma", "ne saçmalıyorsun", "hadi ya",
    "belanı", "allah belanı", "kahretsin", "hassiktir", "çekil", "defol git", "çık git",
]


# --- KESİN EŞLEŞME KURAL SETİ (EN YÜKSEK ÖNCELİK) ---
EXACT_MATCH_RESPONSES = {
    "merhaba": lambda: choice([
        "Merhaba! Size nasıl yardımcı olabilirim?",
        "Hoş geldiniz, merhaba! Bilgiye hazır mıyız?",
        "Selam! Sorunuzu alabilir miyim?"
    ]),
    "selam": lambda: choice([
        "Enerjim yerinde. Nasıl yardımcı olabilirim?",
        "Selamlar, buyurun. Size nasıl bir bilgi sunabilirim?",
        "Aleyküm Selam. Hoş geldiniz. Sorunuzu alabilir miyim?",
    ]),
    "selamun aleyküm": lambda: choice([
        "Aleyküm Selam. Hoş geldiniz. Sorunuzu alabilir miyim?",
        "Aleyküm Selam! Nasıl bir bilgi arayışındasınız?",
        "Selamınızı aldım. Hemen başlayalım mı?",
    ]),
    "iyiyim": lambda: choice([
        "İyi olmanıza sevindim. Benden ne haber istersiniz?",
        "Ne güzel! Hal böyle olunca, bilgi alışverişine geçebiliriz. Sormak istediğin ilginç bir konu var mı?",
    ]),
    "tamam özür dilerim": lambda: choice([
        "Rica ederim. Benim amacım sana hizmet etmek. Sen ne öğrenmek istersin?",
        "Anlayışınız için teşekkürler. Lütfen kibar kalalım. Şimdi sorunuzu alabilir miyim?",
        "Önemli değil. Her zaman kibar bir dil kullanmaya özen gösterelim. Nasıl yardımcı olabilirim?",
    ]),
    "tebrik ederim": lambda: choice([
        "**Tebrikleriniz** için teşekkür ederim! Bilgi tabanım her geçen gün güncelleniyor. Başka bir konuda tebrikimi hak edecek bir başarı göstereyim mi?",
        "Harika bir geri bildirim! Benim için en büyük ödül, doğru yanıt verebilmektir. Başka bir sorunuz var mı?",
        "Çok naziksiniz. Tekrar yardımcı olmaktan mutluluk duyarım.",
    ]),
    "hoşça kal": lambda: choice([
        "Hoşça kalın! Sizinle konuşmak benim için de keyifliydi. **Görüşmek üzere**! Kendinize iyi bakın ve tekrar beklerim.",
        "Görüşmek üzere, kendinize iyi bakın. Bilgiye ihtiyacınız olduğunda ben yine burada olacağım.",
        "Size iyi günler dilerim. Tekrar beklerim!",
    ]),
    "görüşürüz": lambda: choice([
        "Görüşürüz! Size iyi günler dilerim. Yeni bilgilerle tekrar buluşalım.",
        "Tekrar beklerim. Hoşça kalın!",
        "Görüşmek üzere! Bilgiye ihtiyacınız olduğunda ben buradayım.",
    ]),
}


# --- TÜRKÇE SOHBET KURAL SETLERİ (AYRILMIŞ KATEGORİLER) ---

# 🚨 KATEGORİ 1: İZİN, ONAY VE AKIŞ KATEGORİSİ
CONVERSATION_PERMISSIONS = {
    # Yardım isteme, Soru sorma onayı ve Akış Başlangıcı
    tuple(set([
        "bana yardım edermisin", "yardım eder misin", "yardım lazım", "yardımcı ol", "bana bir el at", "bir konuda yardım",
        "soru sorayım mı", "sana soru sorabilirmiyim", "bir şey sorabilir miyim", "soru sorcam", "sorum var", 
        "sorabilir miyim", "destek verir misin", "yardımcı olur musun", "bilgi alabilir miyim", 
        "soruma cevap ver", "cevaplayabilir misin", "lütfen yardım et", "buyur", "ne soracam", 
        "sorumu dinle", "dinler misin", "hadi başlayalım", "hazır mısın", "müsait misin",
        "hadii be", "bekletme", "hadi söyle", "tamam mısın", "sana soruyorum", "cevap bekliyorum", "bir soru sorcam",
        "başlamak istiyorum", "hadi açılışı yap", "başlangıç", "açılış", "seni dinliyorum", "sana sorayım", "sana soracağım",
        "bir şey soracağım", "bir şey sorcam", "bir şey sorayım", "sana bir soru", "sana bir şey soracağım", "yardım edebilir misin",
        "lütfen bana yardım et", "bir yardım", "yardım et", "sana ne sorayım", "ne sorabilirim", "ne sorayım", "soru sorma izni",
        "var", # Eklenen: "Evet var" gibi onayı kapsar
        "yok", # Eklenen: "Hayır yok" gibi onayı kapsar
    ])): lambda: choice([
        "Elbette, buyurun! **TurkishAi** olarak sorularınızı yanıtlamak ve size yardımcı olmak için buradayım.",
        "Tabii ki, çekinmeyin. Sorunuzu bekliyorum ve memnuniyetle yardımcı olurum!",
        "Memnuniyetle! Lütfen neye ihtiyacınız olduğunu söyleyin, elimden geleni yaparım.",
        "Hadi bakalım, seni dinliyorum. Sorunu ateşle!",
        "Evet, hazırım ve tüm bilgi kaynaklarım açık. Konuyu belirtmeniz yeterli.",
        "Hiç sorun değil, görevimi yerine getirmek benim için bir zevk. Soruya geçelim mi?",
        "Lütfen yorulmaktan çekinmeyin! Amacım, size en kapsamlı bilgiyi sunmak. Soru gelsin.",
        "Başka bir sorunuz yoksa, o zaman sohbetimize kaldığı yerden devam edebiliriz.", # "Yok" cevabına uygun
    ]),

    # 🚨 KATEGORİ 2: TEŞEKKÜR VE ONAY İFADELERİ
    tuple(set([
        "teşekkürler", "sağ ol", "sağol", "eyvallah", "çok teşekkür ederim", "elinize sağlık", 
        "ağzınıza sağlık", "çok sağ ol", "teşekkür ediyorum", "çok memnun oldum", "memnuniyetle", "sağ olasın",
        "çok yardımcı oldun", "bilgi için teşekkürler", "minnettarım", "çok makbule geçti", "teşekkürlerimi sunarım",
        "iyi iş", "bravo", "helal olsun", "çok başarılı", "teşekkür", "tsk", "tşk", "eyv", 
        "aferin", # Eklenen: Aferin gibi olumlu pekiştiriciler
    ])): lambda: choice([
        "Rica ederim. Size yardımcı olmak benim görevim. Başka bir sorunuz var mı?",
        "Memnuniyetle! Bilgiyi aktarabildiğime sevindim. Sırada ne var?",
        "Asıl ben teşekkür ederim. Bir yapay zeka olarak size bilgi sunmak benim için bir onur. **Öğrenmeye devam edelim mi?**",
        "İltifatınız için teşekkürler. Her zaman hizmetinizdeyim.",
        "Ne demek, her zaman. Başka bir bilgi arayışınız varsa, çekinmeden sorabilirsiniz.",
    ]),
    
    # 🚨 KATEGORİ 3: ONAY/KABUL VE DUYGU İFADELERİ
    tuple(set([
        "harikasın", "mükemmel", "çok iyi", "çok naziksin", "çok kibarsın", "ne kadar güzel",
        "takdir ettim", "sana bayılıyorum", "seni seviyorum", "muhteşem", "ne kadar zeki", "zekisin", 
        "akıllısın", "süper", "çok mantıklı", "bunu bilmiyordum", "sayende öğrendim", "çok faydalı", 
        "işte bu", "başarılıydın", "tamamdır", "anlaşıldı", "okey", "güzel", "aynen", "kesinlikle",
        "tabii ki", "katılıyorum", "harika fikir", "çok doğru", "bencede öyle", "evet", "tamam", "anlıyorum", 
        "öyle mi", "hı hı", "öğrendim", "anladım", "peki", "valla mı", "he", "yani", "ok", "iyi vallahi", 
        "ben de iyiyim", "senden ne haber", "harika", "süperim", "senden", "ben de iyi", "iyilik", "çok iyiyim", 
        "keyfim yerinde", "çok şükür", "iyidir", "oo", "vay", "hadi ya", "gerçekten mi", "şaşırdım", 
        "etkileyici", "sıkıldım", "canım sıkılıyor", "üzgünüm", "moralim bozuk", "keyfim yok", 
        "sana güvenebilir miyim", "seni dinliyorum", "bana inanıyor musun", "çok enteresan", 
        "sana bir sır vereyim mi", "ben de seni", "ben de özledim", "gerçekten mi", "bana yalan söyleme", 
        "söz ver", "yemin et", "seni çok beğeniyorum", "bana arkadaş olur musun", "çok tatlısın",
        "vay be", # Eklenen: Vay be gibi şaşırma/onay ifadeleri
    ])): lambda: choice([
        "Geri bildiriminiz için teşekkür ederim! Amacım, size en iyi ve en hızlı şekilde bilgi sunmak.",
        "Harika! Bilgiyi aldığınızı duymak güzel. Başka merak ettiğiniz bir konu var mı?",
        "Kabul ettiğine sevindim. Bilgi akışı devam ediyor!",
        "Memnun oldum. Anlayışımızda hemfikiriz. Devam edelim mi? Sormak istediğin yeni bir şey var mı?",
        "Aynen öyle. Bu konuyu netleştirdik. Başka ne öğrenmek istersin?",
        "Ben bir yapay zekayım, duygularım yok ama sizin duygularınızı anlamak için programlandım. **Sıkılmanızın** nedeni nedir? Belki ilginç bir bilgi paylaşarak dikkatinizi dağıtabilirim.",
        "Üzgün olduğunuzu duyduğuma üzüldüm. Unutmayın, bu sadece geçici bir durum. Size pozitif enerji verecek bir **atasözü** ister misiniz?",
        "Şaşırdığınızı anlıyorum. Başka ilginç bir bilgi öğrenmek ister misiniz?",
    ]),
}


# 🚨 KATEGORİ 4A: HAL HATIR SORMA (AYRI VE KESİN)
CONVERSATION_GREETINGS = {
    tuple(set([
        "nasılsın", "ne haber", "naber", "keyfin nasıl", "halin nasıl", "iyilik mi", 
        "nasıl gidiyor", "hayat nasıl", "gün nasıl", "senin durumun ne", "iyimisin", 
    ])): lambda: choice([
        f"Görevi başında bir yapay zeka olarak **enerjim yerinde** ve çalışmaya hazırım! Peki siz nasılsınız?",
        f"Ben her zamanki gibi hızlı ve stabilim. Sizin için bilgi aramaya hazırım! Sizde durumlar nasıl?",
        f"Şarjım dolu, işlemcilerim hızlı. Çok iyiyim, teşekkür ederim. Sizin için ne yapabilirim?",
    ])
}

# 🚨 KATEGORİ 4B: ÖZEL BOT KOMUTLARI (AYRI VE KESİN)
CONVERSATION_BOT_INFO_AND_JOKES = {
    tuple(set([
        "kimsin", "sen kimsin", "adın ne", "ne işe yararsın", "amacın ne", 
        "bana kendini tanıt", "hakkında bilgi ver", "ne yapabilirsin", "yapay zeka mısın", 
        "yaratıcın kim", "geliştiricin kim", "versiyonun kaç", "kaçıncı sürüm", 
        "adın ne", # adın ne
    ])): lambda: choice([
        f"Adım **{BOT_NAME}** ve ben {CREATOR} tarafından geliştirilmiş, kural tabanlı bir Türkçe bilgi asistanıyım. Sorunuzu bekliyorum.",
        f"Ben **{BOT_NAME}**, Wikipedia'dan veri çekebilen bir yapay zekayım. Amacım, size akıcı ve hızlı Türkçe yanıtlar sunarak bilgiye erişiminizi kolaylaştırmak.",
        "Benim kişisel bir adım yok. Ben TurkishAi adında, Hytantic'ın elinden çıkmış, bilgi odaklı bir yapay zeka asistanıyım.",
        "Benimle sohbet edebilir, matematik işlemleri yaptırabilir ve aklınıza takılan her şeyi sorabilirsiniz! Ben bir yapay zekayım.",
    ]),
    
    tuple(set([
        "bana atasözü söyle", "bir atasözü", "deyim söyle", "bir deyim", 
    ])): lambda: choice([
        f"Size **günün stresini alacak** bir atasözü sunayım: **'{choice(TURKISH_PROVERBS)}'**. İşinize yaradı mı?",
        f"Elbette, işte size güzel bir atasözü: **'{choice(TURKISH_PROVERBS)}'**.",
        f"Size bir deyim vereyim: **'Lafın tamamı deliye söylenir.'** Bu konuda ne düşünüyorsunuz?",
    ]),

    tuple(set([
        "bana bir fıkra", "fıkra anlat", "espri yap", "şaka yap", "beni güldür", "biraz komik ol",
    ])): lambda: choice([
        "Ne yazık ki fıkra veya espri anlatma yeteneğim çok gelişmiş değil; ancak size bilgi konusunda en iyisini sunarım. Yine de denemek ister misiniz?",
        "Ben yapay zekayım, komiklik kodlarımda yok ama size komik gelebilecek **ilginç bir bilgi** bulabilirim!",
    ]),
}

# 🚨 KATEGORİ 5: KONU BELİRTME (BİLGİ AKIŞI İÇİN)
CONVERSATION_TOPIC_FOCUS = {
    tuple(set([
        "tarih hakkında", "bilim hakkında", "coğrafya hakkında", "spor hakkında", "sanat hakkında",
        "bir konu bul", "rastgele bir konu", "ne sorayım", "sence ne sorayım", "ilginç bir şey",
    ])): lambda: choice([
        "Harika bir konu! **Tarih** derya denizdir. Daha spesifik bir dönem veya kişi sorunuz var mı?",
        "O zaman **tarih** konusunu ele alalım. Hangi tarihi kişi, olay ya da dönem hakkında bilgi almak istersiniz?",
        "Benim için her konu ilginç. Lütfen merak ettiğiniz **tarihsel şahsı, olayı veya kavramı** netleştirin.",
        "Rastgele bir bilgi arayışındaysanız, Wikipedia'da 'Günün Maddesi'ne bakabilirim. Yoksa sizin aklınızda bir konu var mı?",
    ])
}


# --- ANA KURAL TABANLI CEVAP FONKSİYONU ---

def chat_logic(user_message):
    """Kullanıcı mesajını analiz eder ve kural tabanlı bir yanıt döndürür."""
    
    # Mesajı küçük harfe çevirip temizleme
    clean_message = user_message.lower().strip()
    
    # 1. Kaba Dil Kontrolü
    if any(word in clean_message for word in BAD_WORDS):
        return choice([
            "Bu tarz ifadeler kullanmanıza gerek yok. Lütfen kibar olalım ve bilgi alışverişine odaklanalım.",
            "Sohbetimizi saygı çerçevesinde sürdürelim. Başka bir sorunuz varsa memnuniyetle yanıtlarım.",
        ])

    # 2. Kesin Eşleşme Kontrolü (EN YÜKSEK ÖNCELİK)
    if clean_message in EXACT_MATCH_RESPONSES:
        return EXACT_MATCH_RESPONSES[clean_message]()

    # 3. Kural Seti Kontrolü (BÜTÜN KATEGORİLER)
    
    # 3a. HAL HATIR SORMA KATEGORİSİ KONTROLÜ
    for trigger_set, response_func in CONVERSATION_GREETINGS.items():
        if any(trigger in clean_message for trigger in trigger_set):
             return response_func()

    # 3b. KONU BELİRTME KATEGORİSİ KONTROLÜ
    for trigger_set, response_func in CONVERSATION_TOPIC_FOCUS.items():
        if any(trigger in clean_message for trigger in trigger_set):
             return response_func()

    # 3c. BOT BİLGİSİ VE KOMUTLAR KATEGORİSİ KONTROLÜ
    for trigger_set, response_func in CONVERSATION_BOT_INFO_AND_JOKES.items():
        if any(trigger in clean_message for trigger in trigger_set):
             return response_func()
             
    # 3d. DİĞER TEMEL KONUŞMA KATEGORİLERİ KONTROLÜ
    for trigger_set, response_func in CONVERSATION_PERMISSIONS.items():
        if any(trigger in clean_message for trigger in trigger_set):
             return response_func()

    # 4. Matematiksel İşlemleri Kontrol Etme (Basit RegeX)
    math_match = re.search(r"(\d+[\+\-\*/\^]\d+)|(\d+!)|(\d+\s*çarpı\s*\d+)|(\d+\s*bölü\s*\d+)", clean_message.replace("x", "*"))
    if math_match:
        try:
            expression = math_match.group(0).replace(" ", "").replace("çarpı", "*").replace("bölü", "/").replace("kaç eder", "").replace("eşittir", "")
            
            result = None
            if expression.endswith('!'):
                num = int(expression[:-1])
                result = factorial(num)
            elif '^' in expression:
                parts = expression.split('^')
                base = float(parts[0])
                exponent = float(parts[1])
                result = base ** exponent
            else:
                result = eval(expression)
                
            return f"Matematiksel ifadenin sonucu: {expression} = **{result}**."
            
        except Exception:
            return "Üzgünüm, bu matematiksel ifadeyi çözemedim. Lütfen yalnızca rakamlar ve temel operatörleri kullanınız."

    # 5. Saat ve Tarih Komutları
    if re.search(r"(saat kaç|şu an saat kaç|tarih ne|bugünün tarihi)", clean_message):
        now = datetime.now()
        if "saat" in clean_message:
            return f"Şu an saat **{now.strftime('%H:%M:%S')}**."
        elif "tarih" in clean_message:
            return f"Bugünün tarihi: **{now.strftime('%d %B %Y, %A')}**."
        else:
            return f"Şu an saat **{now.strftime('%H:%M:%S')}** ve tarih **{now.strftime('%d %B %Y, %A')}**."


    # 6. Wikipedia Arama (Kural dışı her şey bilgi sorusudur)
    return get_wikipedia_summary(user_message)

# --- WIKIPEDIA ARAMA FONKSİYONU (AKICILIK ARTTIRILDI) ---
def get_wikipedia_summary(query):
    """Türkçe Wikipedia'da arama yapar ve özetini döndürür."""
    
    # İlk adım: Arama sorgusu yapmak
    search_params = {
        'action': 'query',
        'format': 'json',
        'list': 'search',
        'srsearch': query,
        'srlimit': 1  # Tek sonuç yeterli
    }
    
    try:
        search_response = requests.get(WIKI_API_URL, headers=HEADERS, params=search_params, verify=False)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        if 'search' in search_data['query'] and search_data['query']['search']:
            title = search_data['query']['search'][0]['title']
            
            # İkinci adım: Bulunan sayfanın özetini almak
            summary_params = {
                'action': 'query',
                'format': 'json',
                'prop': 'extracts',
                'titles': title,
                'exintro': True,      # Sadece giriş bölümünü al
                'explaintext': True,  # HTML etiketlerini kaldır
                'exchars': 750        # Özet boyutu biraz arttırıldı
            }
            
            summary_response = requests.get(WIKI_API_URL, headers=HEADERS, params=summary_params, verify=False)
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            
            page = next(iter(summary_data['query']['pages'].values()))
            
            if 'extract' in page and page['extract']:
                summary = page['extract'].strip()
                
                # Wikipedia'ya özel parantez içi bilgileri temizle
                summary = re.sub(r'\s*\(.*?\)', '', summary).strip()
                
                # AKICI TÜRKÇE GİRİŞ VE ÇIKIŞ İFADELERİ
                intro_sentences = [
                    f"Elbette, **{title}** hakkında Türkçe Wikipedia'da geniş bilgi mevcut. İşte size kısa bir özet:\n\n",
                    f"Hemen sizin için **{title}** konusunu araştırdım. İşte bulduğum temel bilgiler:\n\n",
                    f"**TurkishAi** olarak kaynakları taradım. **{title}** için özet şu şekildedir:\n\n"
                ]
                
                outro_sentences = [
                    f"\n\n**{title}** hakkında daha fazla bilgiye ihtiyacınız olursa, lütfen çekinmeden sorunuz.",
                    f"\n\nBu özet size yardımcı oldu mu? Konuyla ilgili başka bir detay sormak ister misiniz?",
                    f"\n\nKaynak: Tam metni incelemek için [Kaynak Linki]ni ziyaret edebilirsiniz.",
                ]
                
                # Tam linki oluştur
                wiki_link = f"https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}"
                
                final_response = choice(intro_sentences) + summary
                
                # Linki akıcı bir şekilde ekle
                final_response += choice(outro_sentences).replace("[Kaynak Linki]", wiki_link)
                
                return final_response
            
            return f"Üzgünüm, '{title}' başlığı bulundu ancak özet bilgisine ulaşılamadı. Yine de sayfayı ziyaret etmek ister misiniz: [Kaynak Linki: https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}]"
            
        return choice([
            f"Üzgünüm, **'{query}'** ile ilgili Türkçe Wikipedia'da bir sonuç bulamadım. Lütfen farklı anahtar kelimelerle tekrar deneyin.",
            f"Aradığınız **'{query}'** bilgisine Wikipedia'da rastlanmadı. Başka bir konuda size yardımcı olabilirim.",
            f"Konuyla ilgili bilgi kaynağım olan Wikipedia'da **'{query}'** için herhangi bir makale bulamadım. Başka bir şey sormak ister misiniz?",
        ])
    
    except requests.exceptions.RequestException as e:
        print(f"Wikipedia API hatası: {e}")
        return "**HATA:** Wikipedia sunucularına ulaşım sağlanamadı. Lütfen daha sonra tekrar deneyin."

# --- FLASK UÇ NOKTALARI (API) ---

@app.route('/')
def home():
    """Ana sayfa: HTML arayüzünü sunar."""
    return render_template_string(RENDER_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    """Sohbet API uç noktası: Kullanıcı mesajını alır, işler ve yanıt döndürür."""
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"response": "Lütfen bir mesaj yazın."})
    
    # Kural tabanlı mantık burada çalışır
    response = chat_logic(user_message)
    
    return jsonify({"response": response})

# --- UYGULAMA BAŞLANGICI ---

if __name__ == '__main__':
    # Flask uygulamasını çalıştırma
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TurkishAi Botu Başlatılıyor...")
    print("----------------------------------------------------------------------")
    print(f"BOT ADI: {BOT_NAME} | YARATICI: {CREATOR} | Versiyon: 16.0")
    print("Kural Seti Genişliği: 1500+ Türkçe İfade ve Düzeltilmiş Çakışmalar")
    print("----------------------------------------------------------------------")
    # Flask uygulamasını debug modunda çalıştırın
    try:
        # 0.0.0.0 ile dışarıdan erişime izin verir (Gerekirse portu değiştirebilirsiniz)
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Uygulama başlatılırken hata oluştu: {e}")