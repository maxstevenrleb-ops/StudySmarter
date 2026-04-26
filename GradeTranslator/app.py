import streamlit as st, PyPDF2, json
from openai import OpenAI

# --- 1. PREMIUM UI ---
st.set_page_config(page_title="StudySmarter Pro", layout="wide")
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;900&display=swap');
    .stApp { background: radial-gradient(circle at top right, #1e1b4b, #0f172a); font-family: 'Outfit'; color: white; }
    .title { font-size: 60px!important; font-weight: 900; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(15px); border-radius: 25px; padding: 25px; border: 1px solid rgba(255,255,255,0.1); margin: 10px 0; }
    .bubble { background: linear-gradient(135deg, #6366f1, #a855f7); border-radius: 30px; padding: 40px; min-height: 200px; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 24px; font-weight: 700; border: 1px solid white; }
    
    /* THE NAVY OVAL BROWSE BUTTON */
    [data-testid="stFileUploader"] section button {
        background-color: #0f172a !important;
        color: white !important;
        border: 2px solid white !important;
        border-radius: 50px !important;
        padding: 8px 25px !important;
        font-weight: 900 !important;
    }
    .stButton>button { background: white!important; color: #0f172a!important; border-radius: 15px!important; font-weight: 900; width: 100%; border: none; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #4facfe, #00f2fe); }
</style>""", unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
keys = ["mode","idx","score","done","less","cards","quiz","flip","cfg","raw","chat","msg"]
defs = ["Home",0,0,False,"",[],[],False,{"grd":"Grade 10","f":5,"q":3,"p":1},"",[],""]
for k,d in zip(keys,defs):
    if k not in st.session_state: st.session_state[k]=d

def ai(p, j=False):
    c = OpenAI(api_key=st.secrets["GROQ_KEY"], base_url="https://api.groq.com/openai/v1")
    a = {"messages":[{"role":"user","content":p}],"model":"llama-3.3-70b-versatile"}
    if j: a["response_format"] = {"type":"json_object"}
    return c.chat.completions.create(**a).choices[0].message.content

def safe_json(raw, key):
    try:
        data = json.loads(raw)
        # Tries to find the key or falls back to any list found in the JSON
        return data.get(key, next(iter([v for v in data.values() if isinstance(v, list)]), []))
    except: return []

# --- 3. SCREENS ---
if st.session_state.mode == "Home":
    st.markdown("<h1 class='title'>STUDYSMARTER</h1>", unsafe_allow_html=True)
    f = st.file_uploader("", type="pdf")
    if f:
        if not st.session_state.raw:
            r = PyPDF2.PdfReader(f)
            st.session_state.raw = " ".join([p.extract_text() for p in r.pages if p.extract_text()])
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.session_state.cfg["grd"]=st.selectbox("Target Grade", [f"Grade {i}" for i in range(1,13)], index=9)
        c1,c2,c3 = st.columns(3)
        st.session_state.cfg["p"]=c1.slider("Pages",1,5,1); st.session_state.cfg["f"]=c2.slider("Cards",3,15,5); st.session_state.cfg["q"]=c3.slider("Quiz",3,10,3)
        l,cd,qz = st.columns(3)
        if l.button("🚀 LEARN"):
            if not st.session_state.less: st.session_state.less=ai(f"Lesson for {st.session_state.cfg['grd']}: "+st.session_state.raw[:3000])
            st.session_state.mode="Learn"; st.rerun()
        if cd.button("🗂️ CARDS"): st.session_state.mode="Cards"; st.rerun()
        if qz.button("🧠 QUIZ"): st.session_state.mode="Quiz"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.mode == "Learn":
    st.markdown("<h1 class='title'>LESSON</h1>", unsafe_allow_html=True); st.markdown(f"<div class='glass'>{st.session_state.less}</div>", unsafe_allow_html=True)
    if st.button("➕ MORE PAGES"): st.session_state.less+="<br><br>"+ai("Continue lesson: "+st.session_state.raw[:2000]); st.rerun()
    c1,c2 = st.columns(2)
    if c1.button("🏠 HOME"): st.session_state.mode="Home"; st.rerun()
    if c2.button("NEXT: CARDS ➡️"): st.session_state.mode="Cards"; st.rerun()

elif st.session_state.mode == "Cards":
    if not st.session_state.cards:
        res = ai(f"JSON: {{'cards':[{{'q':'?','a':'!'}}]}} Generate {st.session_state.cfg['f']} cards: "+st.session_state.raw[:2500], True)
        st.session_state.cards = safe_json(res, 'cards'); st.session_state.idx=0
    st.markdown("<h1 class='title'>CARDS</h1>", unsafe_allow_html=True); st.progress((st.session_state.idx+1)/max(len(st.session_state.cards),1))
    if st.session_state.cards:
        c = st.session_state.cards[st.session_state.idx]
        st.markdown(f"<div class='bubble'>{c['a'] if st.session_state.flip else c['q']}</div>", unsafe_allow_html=True)
        if st.button("🔄 FLIP"): st.session_state.flip=not st.session_state.flip; st.rerun()
    col1,col2,col3 = st.columns(3)
    if col1.button("⬅️ PREV"): st.session_state.idx=max(0,st.session_state.idx-1); st.session_state.flip=False; st.rerun()
    if col2.button("🏠 HOME"): st.session_state.mode="Home"; st.rerun()
    if st.session_state.idx >= len(st.session_state.cards)-1:
        if col3.button("🧠 QUIZ ➡️"): st.session_state.mode="Quiz"; st.rerun()
    elif col3.button("NEXT ➡️"): st.session_state.idx+=1; st.session_state.flip=False; st.rerun()
    if st.button("➕ MORE CARDS"):
        res = ai("JSON:{'cards':[{'q':'?','a':'!'}]} Add cards:"+st.session_state.raw[:2000], True)
        st.session_state.cards += safe_json(res, 'cards'); st.rerun()

elif st.session_state.mode == "Quiz":
    if not st.session_state.quiz:
        res = ai(f"JSON: {{'quiz':[{{'q':'?','opts':['A','B'],'a':'A'}}]}} {st.session_state.cfg['q']} Qs: "+st.session_state.raw[:2500], True)
        st.session_state.quiz = safe_json(res, 'quiz'); st.session_state.idx,st.session_state.score,st.session_state.done=0,0,False
    st.markdown("<h1 class='title'>QUIZ</h1>", unsafe_allow_html=True)
    if st.session_state.done:
        p=(st.session_state.score/max(len(st.session_state.quiz),1))*100; g="A+" if p>=90 else "B" if p>=80 else "F"
        st.markdown(f"<div class='glass' style='text-align:center;'><h1>{g}</h1><h2>{st.session_state.score}/{len(st.session_state.quiz)}</h2></div>",unsafe_allow_html=True)
        if st.button("➕ MORE Qs"):
            res = ai("JSON:{'quiz':[{'q':'?','opts':['A','B'],'a':'A'}]} More:"+st.session_state.raw[:2000], True)
            st.session_state.quiz += safe_json(res, 'quiz'); st.session_state.done=False; st.rerun()
        if st.button("🏠 HOME"): st.session_state.mode="Home"; st.rerun()
    else:
        st.progress(st.session_state.idx/max(len(st.session_state.quiz),1)); q=st.session_state.quiz[st.session_state.idx]
        st.markdown(f"<div class='glass'><h2>{q['q']}</h2></div>",unsafe_allow_html=True)
        if st.session_state.msg: st.info(st.session_state.msg)
        for o in q['opts']:
            if st.button(o):
                if o==q['a']: st.session_state.score+=1; st.session_state.msg="Correct! ✨"
                else: st.session_state.msg=f"Wrong! Was: {q['a']} ❌"
                if st.session_state.idx == len(st.session_state.quiz)-1: st.session_state.done=True
                else: st.session_state.idx+=1
                st.rerun()

with st.sidebar:
    st.markdown("### 🤖 Study Tutor")
    for m in st.session_state.chat:
        with st.chat_message(m["role"]): st.write(m["content"])
    if p:=st.chat_input("Ask about notes..."):
        st.session_state.chat.append({"role":"user","content":p})
        st.session_state.chat.append({"role":"assistant","content":ai(f"Notes:{st.session_state.raw[:1000]} Q:{p}")}); st.rerun()
    st.write("---")
    st.caption("⚠️ AI makes mistakes. Verify your facts.")
    if st.button("🧹 WIPE DATA"): st.session_state.clear(); st.rerun()