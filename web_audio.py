import streamlit as st
import edge_tts
import asyncio
import os
import re
import io
import time
import base64
import zipfile
from gtts import gTTS

# ----------------- [강력한 텍스트 필터 기능] -----------------
def apply_custom_filters(text):
    filter_rules = r"""
[—ㅡ_]|[ㅠㅜ]|ㅂㅅ|-$|\[|\.?\]#->#
[♥♣♠◀▶★♩♪♫♬]#->#
;|……?\.?#->#,
([\.\* ?]){2,}#->#$1
- ?(\D)#->#$1
(?m)^#\d+화?.*#->#*
\(([一-鿕]|[㐀-䶵]|[豈-龎]).*?\)#->#
\([a-zA-Z].*?\)#->#
\([ぁ-ー].*?\)#->#
(가){3,}|(과){3,}|(구){3,}#->#$1$1$1$2$2$2$3$3$3
(기){3,}|(두){3,}|(드){3,}#->#$1$1$1$2$2$2$3$3$3
(라){3,}|(르){3,}|(버){3,}#->#$1$1$1$2$2$2$3$3$3
(아){3,}|(어){3,}|(에){3,}#->#$1$1$1$2$2$2$3$3$3
(오){3,}|(우){3,}|(으){3,}#->#$1$1$1$2$2$2$3$3$3
(이){3,}|(저){3,}|(지){3,}#->#$1$1$1$2$2$2$3$3$3
(콰){3,}|(타){3,}|(터){3,}#->#$1$1$1$2$2$2$3$3$3
(투){3,}|(하){3,}|(그){3,}#->#$1$1$1$2$2$2$3$3$3
(땡){3,}|(다){3,}|(탕){3,}#->#$1$1$1$2$2$2$3$3$3
No\.#->#넘버
LV\.#->#레벨.
(\d+)[kK][gG] ?([가-힣])#->#$1킬로그램$2
(\d+)[kK][mM] ?([가-힣])#->#$1킬로미터$2
(\d+)[mM] ?([가-힣])#->#$1미터$2
(\d+)[gG] ?([가-힣])#->#$1그램$2
 [kK][mM] ?([가-힣])#->#킬로미터$1
 [mM] ?([가-힣])#->#미터$1
([가-힣])([一-鿕]|[㐀-䶵]|[豈-龎])+#->#$1
ㄱㄱ+#->#,고고,
ㅇㅇ+#->#,응,
ㅈㄴ#->#졸라
ㅅㅂ#->#,스바,
ㄹㅇ#->#,리얼,
ㄴㄴ#->#,노노,
ㅇㅈ#->#,인정,
ㅅㄱ#->#,수고,
ㅋㅋ+#->#,크크,
ㅎㅎ+#->#,흐흐,
ㄷㄷ+#->#,덜덜,
ㅁㅊ#->#,미친,
ㅉㅉ#->#,쯔쯔,
ㄴㅈ#->#,노잼,
ㅎㄷ#->#후덜
ㅎㄷㄷ#->#,후덜덜,
(\d),(\d),?#->#$1$2
([1-4])/4 ?분기#->#$1사분기
([1-9])/([1-9][0-9]?[0-9]?)#->#$2분지$1
([0-9]):([0-9][0-9]?)#->#$1대$2
(\d)([가-힣])#->#$1~$2
(\d)~([개시월배명살달병대])#->#$1$2
(\d)~(마리|번째|공기|가지)#->#$1$2
(\d)(개국|개월|대대|대 )#->#$1~$2
1달[^라러]#->#한달
2달[^라러]#->#두달
3달[^라러]#->#세달
4달[^라러]#->#네달
 119 ?([가-힣])#-># 일일구$1 
 911 ?([가-힣])#-># 구일일$1
Ⅰ#->#원
Ⅱ#->#투
Ⅲ#->#쓰리
Ⅳ#->#포
Ⅴ#->#파이브
간략#->#갈략
6월#->#유월
10월#->#시월
것이리라#->#거시리라
없어#->#업서
없었#->#업섰
권력#->#궐력
붙인#->#부친
붙이#->#부치
붙여#->#부쳐
붙어#->#부터
뱉어#->#배터
뱉었#->#배텄
짙어#->#지터
없앨#->#업샐
없애#->#업새
곤란#->#,골란
헛웃음#->#허두슴
웃음#->#우슴
폭약#->#포갹
집터#->#집 터
뒷이야기#->#뒷 이야기
 못이([기겨긴겼길])#-># 못 이$1
([볼줄])게\.#->#$1께.
짓이([겨겼])#->#진니$1
아랫입술#->#아랫 입술
([라받])고[\.!\?,]”?#->#$1 고,
야지[\.!\?,]”?#->#야 지,
([모주상악]의) #->#$1
([가-힣])\1{2,}#->#$1$1
(알겠|없)어#->#$1써
(알겠|없)으#->#$1쓰
([붙뱉짙])어#->#$1터
([붙뱉짙])었#->#$1텄
 ([붙끝])이#-># $1치
 ([것곳뜻])이#-># $1시
 ([것곳뜻])일#-># $1실
['"\[\]](.*?)["'\[\]]([가-힣])#->#$1$2
(\d+)~(\d+)([가-힣])#->#$1,$2$3
    """
    for line in filter_rules.strip().split('\n'):
        line = line.strip()
        if '#->#' not in line: continue
        try:
            pattern, replacement = line.split('#->#')
            replacement = re.sub(r'\$(\d+)', r'\\\1', replacement)
            text = re.sub(pattern, replacement, text)
        except Exception:
            pass
    return text

def create_file_chunks_with_overlap(text, max_length):
    paragraphs = text.split('\n')
    chunks = []
    current_chunk_paragraphs = []
    current_length = 0
    for p in paragraphs:
        if current_length + len(p) > max_length and current_chunk_paragraphs:
            chunks.append('\n'.join(current_chunk_paragraphs))
            overlap_p = ""
            for prev_p in reversed(current_chunk_paragraphs):
                if prev_p.strip(): 
                    overlap_p = prev_p
                    break
            current_chunk_paragraphs = [overlap_p, p] if overlap_p else [p]
            current_length = sum(len(x) for x in current_chunk_paragraphs) + len(current_chunk_paragraphs)
        else:
            current_chunk_paragraphs.append(p)
            current_length += len(p) + 1
    if current_chunk_paragraphs:
        chunks.append('\n'.join(current_chunk_paragraphs))
    return chunks

def chunk_text(text, max_length=1000):
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_length:
            current_chunk += p + " "
        else:
            if current_chunk: chunks.append(current_chunk.strip())
            if len(p) >= max_length:
                for i in range(0, len(p), max_length):
                    chunks.append(p[i:i+max_length])
                current_chunk = ""
            else:
                current_chunk = p + " "
    if current_chunk: chunks.append(current_chunk.strip())
    return chunks

def create_download_link(audio_bytes, filename, btn_text):
    """실시간 개별 다운로드 HTML 버튼"""
    b64 = base64.b64encode(audio_bytes).decode()
    href = f'''
        <div style="margin-bottom: 10px;">
            <a href="data:audio/mp3;base64,{b64}" download="{filename}" 
               style="display: inline-block; padding: 10px 20px; color: #fff; 
                      background-color: #007BFF; text-decoration: none; 
                      border-radius: 5px; font-weight: bold; border: 1px solid #0056b3;
                      box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
               📥 {btn_text}
            </a>
        </div>
    '''
    return href

# ----------------- [변환 + 실시간 링크 생성 + ZIP 압축 로직] -----------------
async def generate_and_display_audio(text, original_filename, engine_type, voice, rate, pitch, split_size, range_mode, target_num, speed_limit, progress_bar, status_text, links_container):
    big_chunks = create_file_chunks_with_overlap(text, max_length=split_size)
    total_files = len(big_chunks)
    
    rate_str = f"{rate:+d}%" if rate != 0 else "+0%"
    pitch_str = f"{pitch:+d}Hz" if pitch != 0 else "+0Hz"
    
    sem = asyncio.Semaphore(speed_limit)
    start_time = time.time()
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_idx, big_chunk in enumerate(big_chunks, 1):
            
            if range_mode == "특정 번호부터 만들기" and file_idx < target_num:
                continue
            if range_mode == "특정 번호만 만들기" and file_idx != target_num:
                continue
            
            elapsed = int(time.time() - start_time)
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            status_text.info(f"⏳ [{file_idx}/{total_files}] 번째 파일 변환 중... (누적 시간: {h:02d}:{m:02d}:{s:02d})")
            
            small_chunks = [c for c in chunk_text(big_chunk, max_length=1000) if c.strip()]
            results = [None] * len(small_chunks)
            
            async def fetch_audio(i, chunk_text_part):
                for attempt in range(5):
                    try:
                        async with sem:
                            if "Edge" in engine_type:
                                communicate = edge_tts.Communicate(chunk_text_part, voice, rate=rate_str, pitch=pitch_str)
                                audio_data = b""
                                async for chunk_data in communicate.stream():
                                    if chunk_data["type"] == "audio":
                                        audio_data += chunk_data["data"]
                                results[i] = audio_data
                            elif "Google" in engine_type:
                                def get_gtts():
                                    t = gTTS(chunk_text_part, lang='ko')
                                    fp = io.BytesIO()
                                    t.write_to_fp(fp)
                                    return fp.getvalue()
                                results[i] = await asyncio.to_thread(get_gtts)
                            return
                    except Exception:
                        await asyncio.sleep(1.5)

            tasks = [fetch_audio(i, chunk) for i, chunk in enumerate(small_chunks)]
            await asyncio.gather(*tasks)
            final_audio = b"".join(filter(None, results))
            
            # 1. 파일 이름 설정
            filename = f"{original_filename}_{file_idx}.mp3"
            
            # 2. ZIP 파일 공간에 조각난 오디오 추가
            zip_file.writestr(filename, final_audio)
            
            # 3. 화면에 실시간 개별 다운로드 버튼 표시
            btn_text = f"{file_idx}번 완료: {filename} 개별 다운로드"
            html_link = create_download_link(final_audio, filename, btn_text)
            links_container.markdown(html_link, unsafe_allow_html=True)
            
            progress_bar.progress(file_idx / total_files)
            
    return zip_buffer.getvalue()

# ----------------- [웹 UI 구성] -----------------
st.set_page_config(page_title="오디오북 메이커", page_icon="🎧", layout="centered")

st.title("🎧오디오북 메이커")
st.markdown("TTS엔진을 이용한 txt파일 mp3 변환")

uploaded_file = st.file_uploader("변환할 텍스트(TXT) 파일을 올려주세요", type=["txt"])

st.markdown("### ⚙️ 상세 설정")
engine_option = st.selectbox("0. TTS 엔진 선택", ["Edge TTS (최고음질)", "Google TTS (기본)"])

col1, col2, col3 = st.columns(3)
with col1:
    if "Edge" in engine_option:
        voice_option = st.selectbox("목소리", ["여성 (선희)", "남성 (인준)"])
        voice_code = "ko-KR-SunHiNeural" if voice_option == "여성 (선희)" else "ko-KR-InJoonNeural"
    else:
        voice_option = st.selectbox("목소리", ["한국어 (기본)"])
        voice_code = "한국어 (기본)"

with col2:
    is_google = "Google" in engine_option
    rate = st.slider("말하기 속도", -100, 100, 0, disabled=is_google)

with col3:
    is_google = "Google" in engine_option
    pitch = st.slider("목소리 높낮이", -50, 50, 0, disabled=is_google)

col4, col5 = st.columns(2)
with col4:
    split_option = st.selectbox("파일 분할 기준", ["5만자 (약 1.5시간)", "10만자 (약 3시간)", "20만자 (약 6시간)"])
    if "5만자" in split_option: split_size = 50000
    elif "10만자" in split_option: split_size = 100000
    else: split_size = 200000

with col5:
    speed_option = st.selectbox("온라인 엔진 속도", ["안전 모드 (동시 5개)", "고속 모드 (동시 10개)"])
    speed_limit = 10 if "10개" in speed_option else 5

col6, col7 = st.columns([2, 1])
with col6:
    range_mode = st.selectbox("작업 범위", ["전체 만들기", "특정 번호부터 만들기", "특정 번호만 만들기"])
with col7:
    target_num = st.number_input("대상 번호", min_value=1, value=1, step=1, disabled=(range_mode == "전체 만들기"))

text_input = None
original_filename = "오디오북"
filtered_text = ""

if uploaded_file is not None:
    original_filename = os.path.splitext(uploaded_file.name)[0]
    raw_bytes = uploaded_file.read()
    
    for enc in ['utf-8', 'cp949', 'euc-kr', 'utf-16']:
        try:
            text_input = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
            
    if text_input:
        filtered_text = apply_custom_filters(text_input)
        chunks = create_file_chunks_with_overlap(filtered_text, max_length=split_size)
        st.info(f"💡 현재 텍스트는 총 **{len(chunks)}개**의 MP3 파일로 분할되어 순차적으로 생성됩니다.")

st.markdown("---")

if st.button("▶ 현재 설정으로 미리듣기"):
    sample_text = "안녕하세요. 지금 설정하신 목소리입니다. 마음에 드시나요?"
    with st.spinner("미리듣기 생성 중..."):
        if "Edge" in engine_option:
            async def get_edge_preview():
                r_str = f"{rate:+d}%" if rate != 0 else "+0%"
                p_str = f"{pitch:+d}Hz" if pitch != 0 else "+0Hz"
                c = edge_tts.Communicate(sample_text, voice_code, rate=r_str, pitch=p_str)
                buf = io.BytesIO()
                async for chunk_data in c.stream():
                    if chunk_data["type"] == "audio":
                        buf.write(chunk_data["data"])
                return buf.getvalue()
            audio_bytes = asyncio.run(get_edge_preview())
            st.audio(audio_bytes, format="audio/mp3")
            
        elif "Google" in engine_option:
            t = gTTS(sample_text, lang='ko')
            buf = io.BytesIO()
            t.write_to_fp(buf)
            st.audio(buf.getvalue(), format="audio/mp3")

# 4. 전체 변환 시작
if st.button("🚀 MP3 변환 시작", use_container_width=True):
    if not uploaded_file or not text_input:
        st.warning("⚠️ 먼저 TXT 파일을 올려주세요!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.markdown("### 📥 다운로드 목록")
        # 개별 다운로드 버튼
        links_container = st.container()
        
        with st.spinner("엔진 가동 중... 완성될 때마다 개별 다운로드 버튼이 생겨납니다!"):
            zip_data = asyncio.run(generate_and_display_audio(
                filtered_text, original_filename, engine_option, voice_code, rate, pitch, split_size, range_mode, target_num, speed_limit, progress_bar, status_text, links_container
            ))
            
            status_text.success("🎉 모든 변환이 성공적으로 완료되었습니다!")
            
            st.markdown("---")
            st.markdown("### 📦 전체 파일 한 번에 다운로드")
            st.success("모든 작업이 끝났습니다! 전체 파일을 하나로 받으실 수 있습니다.")
            
            st.download_button(
                label=f"💾 [{original_filename}] 전체 파일 모음 (ZIP) 다운로드",
                data=zip_data,
                file_name=f"{original_filename}_전체오디오북.zip",
                mime="application/zip",
                use_container_width=True
            )
