import streamlit as st
import hashlib
from functools import wraps
import time

def check_auth():
    """Verifica se usuário está autenticado"""
    return st.session_state.get('authenticated', False)

def login_page():
    """Página de login"""
    st.set_page_config(page_title="Login - economiza.ai", page_icon="🔐", layout="centered")
    
    # CSS customizado para login
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    .login-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Logo e título
        st.markdown("# 🤖 economiza.ai")
        st.markdown("### Sistema de Gestão Financeira")
        st.markdown("---")
        
        # Formulário de login
        with st.form("login_form", clear_on_submit=False):
            st.markdown("#### 🔐 Área Restrita")
            
            username = st.text_input(
                "Usuário",
                placeholder="Digite seu usuário",
                key="login_user"
            )
            
            password = st.text_input(
                "Senha",
                type="password",
                placeholder="Digite sua senha",
                key="login_pass"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submit = st.form_submit_button(
                    "🔓 Entrar",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_btn2:
                demo = st.form_submit_button(
                    "👁️ Demo",
                    use_container_width=True,
                    help="Use: demo/demo"
                )
            
            if submit or demo:
                # Validar credenciais
                try:
                    # Credenciais do secrets
                    stored_user = st.secrets["auth"]["username"]
                    stored_pass = st.secrets["auth"]["password"]
                    
                    # Credenciais demo
                    demo_user = st.secrets.get("auth", {}).get("demo_username", "demo")
                    demo_pass = st.secrets.get("auth", {}).get("demo_password", "demo")
                    
                    # Verificar login
                    if (username == stored_user and password == stored_pass) or \
                       (username == demo_user and password == demo_pass) or \
                       (demo and username == "demo" and password == "demo"):
                        
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = username
                        st.session_state['login_time'] = time.time()
                        
                        st.success("✅ Login realizado com sucesso!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Credenciais inválidas!")
                        st.caption("Dica: Use demo/demo para testar")
                        
                except Exception as e:
                    # Fallback para desenvolvimento local
                    if username == "admin" and password == "admin123":
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = username
                        st.session_state['login_time'] = time.time()
                        st.success("✅ Login local realizado!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erro na autenticação. Use admin/admin123 localmente.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Informações adicionais
        st.markdown("---")
        st.caption("🔒 Sistema protegido | 💡 Desenvolvido com Streamlit")

def require_auth(func):
    """Decorator para páginas que precisam de autenticação"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not check_auth():
            login_page()
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def logout():
    """Realiza logout do usuário"""
    for key in ['authenticated', 'username', 'login_time']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def get_user_info():
    """Retorna informações do usuário logado"""
    if check_auth():
        return {
            'username': st.session_state.get('username', 'Usuário'),
            'login_time': st.session_state.get('login_time', time.time()),
            'session_duration': time.time() - st.session_state.get('login_time', time.time())
        }
    return None