import streamlit as st

from rag import NUSTAdmissionsRAG


st.set_page_config(
    page_title="NUST Admissions Assistant",
    page_icon="N",
    layout="centered",
)

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 15% 20%, #1b263b 0%, #0d1b2a 45%, #080f1c 100%);
        color: #e6edf7;
    }
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: 0.4px;
        margin-bottom: 0.3rem;
        color: #f8fafc;
    }
    .subtext {
        color: #b6c2d2;
        margin-bottom: 1.2rem;
    }
    .assistant-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.65rem;
        backdrop-filter: blur(8px);
    }
    .meta-line {
        font-size: 0.82rem;
        color: #9fb2c9;
        margin-top: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">NUST Admissions Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtext">Offline, retrieval-grounded answers from official FAQ data.</div>',
    unsafe_allow_html=True,
)


@st.cache_resource
def load_engine() -> NUSTAdmissionsRAG:
    return NUSTAdmissionsRAG()


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Ask any admissions-related question. I answer only from NUST FAQ context.",
                "confidence": None,
                "source": "FAQ",
            }
        ]


init_state()

try:
    rag_engine = load_engine()
except Exception as exc:
    st.error(
        "Failed to load knowledge base. Run setup.sh first, or run python ingest.py after setup."
    )
    st.exception(exc)
    st.stop()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(f'<div class="assistant-card">{message["content"]}</div>', unsafe_allow_html=True)
            if message.get("confidence") is not None:
                st.markdown(
                    f'<div class="meta-line">Source: {message.get("source", "FAQ")} | '
                    f'Confidence: {message["confidence"]:.1%}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(message["content"])


prompt = st.chat_input("Enter your admissions question")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving relevant FAQ context..."):
            result = rag_engine.answer(prompt)

        answer_text = result["answer"]
        confidence = float(result["confidence"])

        st.markdown(f'<div class="assistant-card">{answer_text}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="meta-line">Source: {result["source"]} | Confidence: {confidence:.1%}</div>',
            unsafe_allow_html=True,
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer_text,
            "confidence": confidence,
            "source": result["source"],
        }
    )
