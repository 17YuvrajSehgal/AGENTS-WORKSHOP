import os
os.environ["PYTHAINLP_DATA_DIR"] = "/tmp/kt_1237/pythainlp-data"
import hashlib, random
from pythainlp.soundex import prayut_and_somchaip
from pythainlp.util import expand_maiyamok
from pythainlp.util import date as _date
from pythainlp.tokenize.thaisumcut import ThaiSentenceSegmentor, middle_cut
from pythainlp.ulmfit import preprocess as pp

random.seed(1237)
h = hashlib.sha256()
def upd(x): h.update(repr(x).encode())

words = ["บูรณะ", "บูรณการ", "มัก", "มัค", "รถ", "รด", "ลัก", "รัก", "ก็", "จัก", "กษัตริย์", "สมชาย", "ประยุทธ์", "น้ำ", "ปลา", "คอมพิวเตอร์"]
upd(_date.dates_list)
thai = "ก ข ค ง จ ฉ ช ซ ด ต ถ ท น บ ป ผ พ ฟ ม ย ร ล ว ส ห อ".split()
seg = ThaiSentenceSegmentor()
text = ("วันนี้อากาศดีมาก เราไปเที่ยวทะเลกัน! คุณจะไปด้วยไหม? ฉันไม่แน่ใจ "
        "แต่คิดว่าน่าจะไปได้ 3 วัน หลังจากนั้นเราจะกลับบ้านพร้อมกันทุกคนเพราะว่างานรออยู่มากมายหลายอย่างที่ต้องทำให้เสร็จ!  ! ")
for r in range(3):
    upd(seg.split_into_sentences(text * (r + 1)))
    upd(seg.split_into_sentences(text * (r + 1), isMiddleCut=True))
upd(middle_cut([text * 2, "", "สวัสดี"]))

for it in range(2500):
    for w in words:
        upd(prayut_and_somchaip(w, length=4))
    w = "".join(random.choice(thai) for _ in range(random.randint(3, 12)))
    upd(prayut_and_somchaip(w))
    sent = ["คนๆ", "นั้น", "ไปๆมาๆ", "เด็กๆ", "ดี", "ๆๆ"]
    upd(expand_maiyamok(sent))
    upd(expand_maiyamok("ด้วยกันๆ"))
    toks = [random.choice(["กา", "น้ำ", "Hello", "ABC", "ปลา"]) for _ in range(60)]
    upd(pp.replace_wrep_post(toks))
    upd(pp.replace_wrep_post_nonum(toks))
    upd(pp.lowercase_all(toks))
for i in range(5):
    upd(seg.split_into_sentences(text * 20))
print(h.hexdigest())
