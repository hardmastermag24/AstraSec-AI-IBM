"""Restrained enterprise console inspired by Carbon neutral and blue tokens."""
import streamlit as st

def apply_design():
    st.markdown('''<style>
    :root{color-scheme:light;--text-color:#161616;--background-color:#f4f4f4;--secondary-background-color:#ffffff;--primary-color:#0f62fe}
    .stApp{background:#f4f4f4;color:#161616;font-family:"IBM Plex Sans","Segoe UI",Arial,sans-serif}
    [data-testid=stHeader]{background:#161616;border-bottom:1px solid #393939}
    [data-testid=stHeader] button{color:#ffffff!important}
    [data-testid=stSidebar]{background:#ffffff;border-right:1px solid #e0e0e0}
    [data-testid=stSidebarNav]{display:none}
    /* Sidebar navigation controls: flat console styling and compact brand area. */
    [data-testid="stSidebarHeader"]{height:0!important;min-height:0!important;margin-bottom:0!important;position:relative;z-index:2}
    [data-testid="stSidebarCollapseButton"]{position:absolute;top:8px;right:0;visibility:visible!important;opacity:1!important;margin:0!important}
    [data-testid="stSidebarUserContent"]{padding-top:12px!important}
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stExpandSidebarButton"]{
        display:inline-flex!important;align-items:center;justify-content:center;
        width:40px!important;height:40px!important;min-width:40px!important;
        border:0!important;border-radius:0!important;box-shadow:none!important;
        opacity:1!important;visibility:visible!important;transition:background-color .15s ease;
    }
    [data-testid="stSidebarCollapseButton"] button{color:#161616!important;background:#ffffff!important}
    [data-testid="stSidebarCollapseButton"] button *{color:#161616!important;opacity:1!important}
    [data-testid="stSidebarCollapseButton"] button:hover{background:#e8e8e8!important}
    [data-testid="stExpandSidebarButton"]{color:#ffffff!important;background:#161616!important;border-right:1px solid #393939!important}
    [data-testid="stExpandSidebarButton"] *{color:#ffffff!important;opacity:1!important}
    [data-testid="stExpandSidebarButton"]:hover{background:#393939!important}
    [data-testid="stSidebarCollapseButton"] button:focus-visible,
    [data-testid="stExpandSidebarButton"]:focus-visible{outline:2px solid #0f62fe!important;outline-offset:-2px!important}
    @media(prefers-reduced-motion:reduce){
        [data-testid="stSidebarCollapseButton"] button,[data-testid="stExpandSidebarButton"]{transition:none!important}
    }

    .block-container{padding-top:4rem;padding-bottom:3rem;max-width:1600px}
    h1,h2,h3{color:#161616!important;letter-spacing:0!important;font-weight:400!important}
    h1{font-size:2rem!important;line-height:1.25!important}
    h2{font-size:1.5rem!important}h3{font-size:1.2rem!important}
    [data-testid=stMarkdownContainer],label,[data-testid=stText]{color:#161616}
    [data-testid=stCaptionContainer],[data-testid=stCaptionContainer] p{color:#525252!important}
    [data-testid=stMetric]{background:#ffffff;border:0;border-top:2px solid #0f62fe;border-radius:0;padding:20px;min-height:120px}
    [data-testid=stMetricLabel]{color:#525252!important;font-size:.875rem;text-transform:none;letter-spacing:0}
    [data-testid=stMetricValue]{color:#161616!important;font-size:2.5rem;font-weight:300}
    [data-testid=stVerticalBlockBorderWrapper]>div{background:#ffffff;border-color:#e0e0e0!important;border-radius:0!important}
    .stButton>button,.stDownloadButton>button{background:#ffffff;color:#0f62fe;border:1px solid #0f62fe;border-radius:0;min-height:44px;font-weight:400;box-shadow:none}
    .stButton>button[kind=primary]{background:#0f62fe;color:#ffffff;border-color:#0f62fe}
    .stButton>button:hover,.stDownloadButton>button:hover{background:#edf5ff;color:#0043ce;border-color:#0043ce}
    .stButton>button[kind=primary]:hover{background:#0043ce;color:#ffffff}
    .stTextInput input,.stTextArea textarea{background:#f4f4f4;color:#161616;border-radius:0;border-bottom:1px solid #8d8d8d}
    [data-baseweb=select]>div{background:#f4f4f4;color:#161616;border-radius:0}
    [data-testid=stExpander]{border-radius:0;border-color:#e0e0e0;background:#ffffff}
    [data-testid=stDataFrame]{border:1px solid #e0e0e0;border-radius:0}
    [data-testid=stAlert]{border-radius:0}
    [data-testid=stCode]{background:#f4f4f4;color:#161616;border:1px solid #e0e0e0;border-radius:0}
    [data-testid=stText], [data-testid=stText] *{color:#161616!important;background:transparent!important}
    [data-testid=stExpander] summary, [data-testid=stExpander] summary p{color:#161616!important;background:#f4f4f4!important}
    [data-testid=stCode] pre, [data-testid=stCode] code{color:#161616!important;background:#f4f4f4!important}
    .console-eyebrow{font-size:12px;font-weight:400;letter-spacing:0;color:#525252;margin-bottom:12px}
    .console-brand{font-size:22px;font-weight:600;letter-spacing:0;color:#161616}
    .console-brand span{color:inherit}
    .console-status{display:inline-block;padding:5px 10px;border:0;background:#e0e0e0;color:#393939;border-radius:0;font-size:12px;white-space:nowrap}
    .console-rule{height:1px;background:#c6c6c6;margin:24px 0}
    [data-testid=stSidebar] .stRadio label{padding:7px 0}
    @media(max-width:1150px){[data-testid=stHorizontalBlock]{flex-wrap:wrap!important}[data-testid=stColumn]{min-width:min(100%,240px)!important;flex:1 1 240px!important}.block-container{padding-left:1.5rem;padding-right:1.5rem}[data-testid=stMetricLabel]{white-space:normal!important}}
    [data-testid=stCaptionContainer] *{color:#525252!important} [data-testid=stSidebar] [data-testid=stRadio] p{font-size:14px} </style>''',unsafe_allow_html=True)

def brand():
    from pathlib import Path
    logo = Path(__file__).resolve().parents[1] / 'assets/astrasec-logo.svg'
    if logo.is_file():
        st.image(str(logo), width="stretch", alt="AstraSec AI · Evidencia, análisis y decisión")
    else:
        st.markdown('<div class="console-brand">AstraSec AI</div>', unsafe_allow_html=True)
    st.caption('Gestión de evidencias criptográficas')
