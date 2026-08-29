# Demo materials — tin-yu-mal

Three ready-to-run cases. Copy the prompt, set **Level** and **Language**, attach files if the case has them, then send.

Suggested live order: **Case 3** (fast, no files) → **Case 1** (thumbnails) → **Case 2** (Myanmar textbook grounding). After a chapter finishes, use the edit prompt.

---

## Case 1 — prompts + images

**Folder:** `demo/case-1-images/`

Attach all four photos (hold Ctrl/Cmd and select them):

| File | What it is |
|---|---|
| `mohinga-fish-noodle-soup.jpg` | မုန့်ဟင်းခါး |
| `laphet-thoke-tea-leaf-salad.jpg` | လက်ဖက်သုပ် |
| `shan-khauk-swe-noodles.jpg` | ရှမ်းခေါက်ဆွဲ |
| `yangon-tea-shop-morning.jpg` | လက်ဖက်ရည်ဆိုင် |

The app does not OCR images. The prompt has to name the dishes; the photos are there so judges see attachments and so the filenames reach the model.

### Settings

- **Level:** Beginner
- **Language:** English (switch to Burmese and use the second prompt if you want the course in မြန်မာ)

### Topic prompt (English)

```
Using these four photos, make a beginner course on everyday Myanmar food. Cover mohinga (the fish-noodle soup), laphet thoke (fermented tea-leaf salad), Shan khauk swe, and how a typical Yangon tea shop works — what you order, how you eat it, and a few cultural notes. Keep recipes doable at home. Include quizzes on ingredients and flashcards for Burmese dish names.
```

### Topic prompt (Burmese)

```
ဒီဓာတ်ပုံ လေးပုံကို အသုံးပြုပြီး မြန်မာ့နေ့စဉ် အစားအစာ beginner သင်တန်းတစ်ခု ဖန်တီးပါ။ မုန့်ဟင်းခါး၊ လက်ဖက်သုပ်၊ ရှမ်းခေါက်ဆွဲ၊ ပြီးတော့ ရန်ကုန် လက်ဖက်ရည်ဆိုင်မှာ ဘာမှာရလဲ / ဘယ်လိုစားလဲ ဆိုတာ ပါပါစေ။ အိမ်မှာ ချက်လို့ရအောင် ရိုးရိုးထားပါ။ ပါဝင်ပစ္စည်း quiz နဲ့ မြန်မာဟင်းအမည် flashcard တွေ ထည့်ပါ။
```

### After a chapter generates — try an edit

```
Add a vegetarian or vegan swap for each dish, and make the quiz about ingredients instead of cooking times.
```

or

```
ဒါကို ပိုရိုးအောင် ပြန်ရေးပါ။ ကလေးတွေ ဖတ်လို့ရအောင် စကားလုံးလည်း လွယ်အောင် လုပ်ပါ။
```

---

## Case 2 — prompts + PDFs only

**Folder:** `demo/case-2-pdfs/`

Attach the three sample lessons (original demo text, styled like Basic Education pages — not official textbook scans):

| File | Sample lesson |
|---|---|
| `grade5-science-water-cycle.pdf` | အဆင့် ၅ သိပ္ပံ · ရေသံသရာ |
| `grade6-science-photosynthesis.pdf` | အဆင့် ၆ သိပ္ပံ · အစာချက်လုပ်ခြင်း |
| `grade7-history-bagan.pdf` | အဆင့် ၇ သမိုင်း · ပုဂံခေတ် |

Text from the PDFs is what grounds generation. Keep all three attached so the model can see science + history.

### A — Burmese course from the books (main demo)

- **Level:** Beginner
- **Language:** Burmese

```
ဒီပြဋ္ဌာန်းစာအုပ်နမူနာ သုံးဖိုင်ကို အခြေခံပြီး beginner သင်တန်းတစ်ခု လုပ်ပါ။ ရေသံသရာ၊ အပင်များ အစာချက်လုပ်ခြင်း၊ ပုဂံခေတ် ဆိုတဲ့ သုံးပိုင်းကို ဆက်စပ်အောင် သင်ပါ။ စာအုပ်ထဲက အဓိက စကားလုံးနဲ့ လေ့ကျင့်ခန်းတွေကို သုံးပြီး quiz / flashcard ထည့်ပါ။ စာအုပ်ကို စာလုံးတိုင်း မကူးပါနဲ့ — ရှင်းပြချက်အသစ် ရေးပါ။
```

### B — English course from Myanmar PDFs (good for mixed-language judges)

- **Level:** Intermediate
- **Language:** English

```
Turn these three Myanmar sample textbook chapters into an intermediate course in English. Ground every chapter in the uploaded lessons: the water cycle, photosynthesis, and the Bagan period (Anawrahta, Kyansittha, Alaungsithu, 1287). Use the practice questions as quiz seeds. Do not paste the PDFs verbatim — teach from them.
```

### After a chapter generates — try an edit

```
Add one Myanmar-specific example (monsoon rice farming for water cycle, or Bagan temples as heritage) and a flashcard set for the key terms in both Burmese and English.
```

or, on the Bagan chapter:

```
ပုဂံအခန်းကို ပိုတိုအောင် ဖြတ်ပါ။ ဘုရားနာမည်တွေ လျှော့ပြီး နိုင်ငံတော် ဘယ်လို စုစည်းခဲ့လဲ ဆိုတာကို ပိုအလေးပေးပါ။
```

---

## Case 3 — prompts only (no files)

Paste one topic. No attachments.

### 3a — fast English beginner (open with this)

- **Level:** Beginner
- **Language:** English

```
How neural networks work — for someone who has never written code. Use one everyday analogy (a team of people passing notes) and keep math out until the last chapter.
```

**Edit after a chapter:**

```
Make this simpler, and add a multiple-choice quiz about layers vs weights.
```

### 3b — Burmese, no uploads

- **Level:** Intermediate
- **Language:** Burmese

```
ပုဂံခေတ် နိုင်ငံတော် ဘယ်လို တည်ထောင်ခဲ့လဲ။ အနော်ရထာ၊ ကျန်စစ်သား၊ အလောင်းစည်သူ၊ ပြီးတော့ ၁၂၈၇ မွန်ဂိုကျူးကျော်မှုအထိ။ သမိုင်းကို ဇာတ်လမ်းလို ပြောပါ၊ ခုနှစ်တွေ အလွန်မများအောင်။
```

**Edit after a chapter:**

```
ဥပမာကို ကား / ခရီးသွား လူတွေနဲ့ ဆက်စပ်အောင် ထည့်ပါ။ ဒုတိယ ပုံကို ဖယ်ပါ။
```

### 3c — denser English (if there is time)

- **Level:** Advanced
- **Language:** English

```
How a compiler turns source code into a running program: lexing, parsing, type checking, IR, and codegen. Assume the reader knows what a function is. Prefer free-response checks over multiple choice.
```

**Edit after a chapter:**

```
Add a worked example that compiles the tiny program `print(1+2)` through each stage.
```

### Extra prompts if you need a spare

```
Photosynthesis, simply — as if explaining it to a Grade 6 student in Yangon, including why monsoon clouds still matter for plants.
```

```
How the internet routes a packet from a phone in Mandalay to a server in Singapore.
```

```
ကားအင်ဂျင် (four-stroke) ဘယ်လို အလုပ်လုပ်လဲ။ စက်ပြင်ဆိုင်မှာ ကြားရတဲ့ စကားလုံးတွေနဲ့ ရှင်းပြပါ။
```

---

## Live-demo checklist

1. Sign in, land on “What do you want to learn?”
2. Case 3a first — chapter list appears, click a chapter, wait for stream, try the quiz, then the edit box.
3. New course → Case 1 — attach the four images so the thumbnail strip is visible, then send.
4. New course → Case 2 — attach the three PDFs, Burmese beginner (or English intermediate if the room is mixed).
5. If anything is slow, talk over the chapter list; don’t regenerate unless you must.
