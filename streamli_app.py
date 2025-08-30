import streamlit as st
import random
import json
from pathlib import Path
import base64

# Configuración de la página
st.set_page_config(
    page_title="DETION ARENA: LEAGUE OF DUNGEONEERS",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Funciones para manejar audio con HTML5
def autoplay_audio(file_path: str):
    """Reproduce audio automáticamente usando HTML5"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true" loop="true" style="display: none">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.components.v1.html(md, height=0)
    except Exception as e:
        st.error(f"Error reproduciendo audio: {e}")

def stop_audio():
    """Detiene todo el audio en la página"""
    js_code = """
    <script>
    var audioElements = document.getElementsByTagName('audio');
    for (var i = 0; i < audioElements.length; i++) {
        audioElements[i].pause();
        audioElements[i].currentTime = 0;
    }
    </script>
    """
    st.components.v1.html(js_code, height=0)

class ArenaApp:
    def __init__(self):
        self.cargar_configuraciones()
        self.inicializar_estados()
        
    def cargar_configuraciones(self):
        try:
            # En Streamlit, los archivos deben estar en el mismo directorio o en una estructura conocida
            self.BASE_DIR = Path(__file__).parent
            self.DATA_DIR = self.BASE_DIR / "assets" / "data"
            self.AUDIO_DIR = self.BASE_DIR / "assets" / "audio"

            # Cargar todos los archivos de configuración
            config_files = {
                "ui_config": "ui_config.json",
                "estados_config": "estados.json",
                "descansos": "descansos.json",
                "recompensas": "recompensas.json",
                "comportamiento": "comportamiento.json"
            }
            
            for attr, file_name in config_files.items():
                with open(self.DATA_DIR / file_name, "r", encoding="utf-8") as f:
                    setattr(self, attr, json.load(f))

        except Exception as e:
            st.error(f"No se pudieron cargar las configuraciones:\n{str(e)}")
            st.stop()
            
    def inicializar_estados(self):
        # Usar valores de configuración si están disponibles
        if not hasattr(self, 'estados_config'):
            self.cargar_configuraciones()
            
        limites = self.estados_config.get("limites", {})
        
        # Inicializar estado de la sesión de Streamlit
        if 'moral_grupo' not in st.session_state:
            st.session_state.moral_grupo = limites.get("moral_max", 10)
            st.session_state.cordura = limites.get("cordura_max", 10)
            st.session_state.heroes_nivel = None
            st.session_state.ronda_actual = 1
            st.session_state.encuentro_actual = None
            st.session_state.encuentros = {}
            st.session_state.acciones_heroicas = 0
            st.session_state.acciones_deshonrosas = 0
            st.session_state.bonif_critico = False
            st.session_state.apuesta_activa = False
            st.session_state.apuesta_monedas = 0
            st.session_state.musica_activada = False
            st.session_state.juego_iniciado = False
            st.session_state.nivel_valor = 1
            st.session_state.apuesta_valor = 0
            st.session_state.mensajes_log = []

    def reiniciar_arena(self):
        limites = self.estados_config.get("limites", {})
        st.session_state.moral_grupo = limites.get("moral_max", 10)
        st.session_state.cordura = limites.get("cordura_max", 10)
        st.session_state.heroes_nivel = None
        st.session_state.ronda_actual = 1
        st.session_state.encuentro_actual = None
        st.session_state.encuentros = {}
        st.session_state.acciones_heroicas = 0
        st.session_state.acciones_deshonrosas = 0
        st.session_state.bonif_critico = False
        st.session_state.apuesta_activa = False
        st.session_state.apuesta_monedas = 0
        st.session_state.juego_iniciado = False
        st.session_state.mensajes_log = []
        
        if st.session_state.musica_activada:
            stop_audio()
            st.session_state.musica_activada = False

    def toggle_musica(self):
        if st.session_state.musica_activada:
            stop_audio()
            st.session_state.musica_activada = False
            st.success("Música desactivada")
        else:
            try:
                musica_path = self.AUDIO_DIR / "musica_fondo.mp3"
                autoplay_audio(str(musica_path))
                st.session_state.musica_activada = True
                st.success("Música activada")
            except Exception as e:
                st.error(f"No se pudo reproducir la música: {e}")
        st.rerun()

    def iniciar_arena(self):
        nivel = st.session_state.nivel_valor
        apuesta = st.session_state.apuesta_valor
        
        try:
            if apuesta < 0 or apuesta > 500:
                raise ValueError("La apuesta debe estar entre 0 y 500")

            # Determinar archivo según nivel y clave para recompensas
            nivel_config = {
                (1, 2): {"archivo": "nivel_1_2.json", "clave_recompensa": "nivel_1_2"},
                (3, 4): {"archivo": "nivel_3_4.json", "clave_recompensa": "nivel_3_4"},
                (5, 6): {"archivo": "nivel_5_6.json", "clave_recompensa": "nivel_5_6"},
                (7, 10): {"archivo": "nivel_7_8.json", "clave_recompensa": "nivel_7_8"}
            }
            
            config_seleccionada = None
            for rango, config in nivel_config.items():
                if rango[0] <= nivel <= rango[1]:
                    st.session_state.heroes_nivel = f"{rango[0]}_{rango[1]}"
                    config_seleccionada = config
                    break
            
            if not config_seleccionada:
                raise ValueError("Nivel debe estar entre 1 y 10")

            # Cargar encuentros
            encuentros_dir = self.DATA_DIR / "encuentros"
            if not encuentros_dir.exists():
                raise ValueError(f"Directorio de encuentros no encontrado: {encuentros_dir}")
                
            encuentros_path = encuentros_dir / config_seleccionada["archivo"]
            if not encuentros_path.exists():
                raise ValueError(f"Archivo de encuentros no encontrado: {encuentros_path}")
                
            with open(encuentros_path, "r", encoding="utf-8") as f:
                st.session_state.encuentros = json.load(f)

            st.session_state.apuesta_monedas = apuesta
            st.session_state.apuesta_activa = apuesta > 0
            st.session_state.juego_iniciado = True

            # Obtener el multiplicador de recompensas usando la clave correcta
            recompensa = self.recompensas.get(config_seleccionada["clave_recompensa"], {})
            multiplicador = recompensa.get("multiplicador_monedas", 1.0)
            
            # Mensajes de inicio
            st.session_state.mensajes_log = []
            self.agregar_mensaje_log("\n=== BIENVENIDO A LA ARENA DE LORAINIA ===", "titulo")
            self.agregar_mensaje_log("¡Atención, ciudadanos de Lorainia! Aventureros de las Tierras Antiguas,\n"
                                    "estáis bajo la atenta mirada de los dioses y del gran rey Logan III. Aquí hallaréis muerte o gloria.", "publico")
            self.agregar_mensaje_log("Reglamento escrito por José Manuel Arena v1.3 y aplicacion por Omar Nieto (DETION)","enemigo")
            
            self.agregar_mensaje_log("\n«¡Atención, nobles espectadores!»", "speaker")
            
            if st.session_state.apuesta_activa:
                ganancia_potencial = int(st.session_state.apuesta_monedas * multiplicador)
                self.agregar_mensaje_log(f"«¡Nuestros valientes héroes han apostado {st.session_state.apuesta_monedas} monedas!»", "speaker")
                self.agregar_mensaje_log(f"«Si logran la victoria, obtendrán {ganancia_potencial} monedas adicionales!»", "speaker")
            else:
                self.agregar_mensaje_log("«¡Jajaja nuestros héroes no han apostado o eso quiere decir que solo les queda la vida!»", "speaker")
                self.agregar_mensaje_log("«¡Una muestra de valentía o tal vez de locura!»", "speaker")
            
            self.agregar_mensaje_log("«¡Que comience el espectáculo!»", "speaker")

            self.agregar_mensaje_log(f"\n=== HÉROES DE NIVEL {st.session_state.heroes_nivel.replace('_', '-')} ===", "titulo")
            if st.session_state.apuesta_activa:
                self.agregar_mensaje_log(f"¡Has apostado {st.session_state.apuesta_monedas} monedas!", "apuesta")
            else:
                self.agregar_mensaje_log("¡No has realizado ninguna apuesta!", "apuesta")
                
            self.ejecutar_ronda(1)
            st.rerun()

        except Exception as e:
            st.error(f"No se pudo iniciar la arena:\n{str(e)}")

    def ejecutar_ronda(self, ronda):
        st.session_state.ronda_actual = ronda
        tipo_ronda = "Calentamiento" if ronda == 1 else "Desafío" if ronda == 2 else "Jefe Final"

        encuentros_ronda = st.session_state.encuentros[f"ronda_{ronda}"]
        tirada = random.randint(1, 100)

        for encuentro in encuentros_ronda:
            rango_min, rango_max = map(int, encuentro["rango"].split("-"))
            if rango_min <= tirada <= rango_max:
                st.session_state.encuentro_actual = encuentro["enemigos"]
                break
        else:
            # Si no se encuentra encuentro, usar el último por defecto
            st.session_state.encuentro_actual = encuentros_ronda[-1]["enemigos"]

        self.agregar_mensaje_log(f"\n=== RONDA {ronda}: {tipo_ronda.upper()} ===", "ronda")
        self.agregar_mensaje_log(f"Tirada: {tirada}", "enemigo")
        self.mostrar_enemigos()
        st.session_state.bonif_critico = False

    def mostrar_enemigos(self):
        enemigos = st.session_state.encuentro_actual.split(" y ")
        self.agregar_mensaje_log("\nENEMIGOS EN LA ARENA:", "enemigo")
        
        # Diccionario de iconos para tipos de enemigos
        iconos_enemigos = {
            "Hechicero": "🧙",
            "Escudo": "🛡️", 
            "Espada": "⚔️",
            "Hacha": "⚔️"
        }
        
        for enemigo in enemigos:
            icono = "🐺"  # Por defecto
            for tipo, emoji in iconos_enemigos.items():
                if tipo in enemigo:
                    icono = emoji
                    break
                    
            self.agregar_mensaje_log(f"{icono} {enemigo.strip()}", "enemigo")

    def evaluar_accion(self, tipo_accion):
        if tipo_accion == "heroica":
            st.session_state.acciones_heroicas += 1
            tag = "heroico"
            tipo_reaccion = "apoyo"
            self.actualizar_estados("heroica")
        else:
            st.session_state.acciones_deshonrosas += 1
            tag = "deshonroso"
            tipo_reaccion = "desprecio"
            self.actualizar_estados("deshonrosa")

        reacciones = self.comportamiento["reacciones_publico"][tipo_reaccion]
        reaccion = random.choice(reacciones)

        self.agregar_mensaje_log(f"\nLos héroes realizan una acción {tipo_accion}:", tag)
        self.agregar_mensaje_log(f"» {reaccion['efecto']}", "critical" if reaccion['id'] > 15 else "efecto")

        self.aplicar_efecto_publico(reaccion['id'], tipo_accion == "heroica")
        st.rerun()

    def aplicar_efecto_publico(self, id_efecto, es_apoyo):
        if es_apoyo:
            if id_efecto == 4:
                st.session_state.bonif_critico = True
                self.agregar_mensaje_log("¡BONIFICACIÓN CRÍTICA ACTIVADA!", "critical")
            elif id_efecto == 19:
                st.session_state.moral_grupo = min(self.estados_config["limites"]["moral_max"], st.session_state.moral_grupo + 1)
                self.agregar_mensaje_log("+1 a la Moral del Grupo", "heroico")
        else:
            if id_efecto == 4:
                st.session_state.moral_grupo = max(0, st.session_state.moral_grupo - 1)
                self.agregar_mensaje_log("-1 a la Moral del Grupo", "deshonroso")
            elif id_efecto == 5:
                st.session_state.cordura = max(0, st.session_state.cordura - 1)
                self.agregar_mensaje_log("-1 a la Cordura", "deshonroso")
        self.actualizar_estados()

    def actualizar_estados(self, accion=None):
        if accion == "heroica":
            st.session_state.moral_grupo = min(
                self.estados_config["limites"]["moral_max"],
                st.session_state.moral_grupo + self.estados_config["efectos"]["heroico"]["moral"]
            )
        elif accion == "deshonrosa":
            st.session_state.cordura = max(
                0,
                st.session_state.cordura + self.estados_config["efectos"]["deshonroso"]["cordura"]
            )

        self.agregar_mensaje_log(
            f"\nMoral del Grupo: {st.session_state.moral_grupo}/{self.estados_config['limites']['moral_max']} "
            f"| Cordura: {st.session_state.cordura}/{self.estados_config['limites']['cordura_max']}",
            "efecto"
        )

    def mostrar_descanso(self):
        tipo = "corto"
        descanso = self.descansos[tipo]

        self.agregar_mensaje_log(f"\n=== {descanso['descripcion']} ===", "titulo")
        for beneficio in descanso["beneficios"]:
            self.agregar_mensaje_log(beneficio, "lista")

        st.session_state.moral_grupo = min(
            self.estados_config["limites"]["moral_max"],
            st.session_state.moral_grupo + descanso["efectos"]["moral"]
        )
        
        # Parsear y aplicar efecto de cordura
        cordura_efecto = descanso["efectos"]["cordura"]
        if "d" in cordura_efecto:
            dado_cordura = int(cordura_efecto.split("d")[1])
            cordura_sumada = random.randint(1, dado_cordura)
        else:
            cordura_sumada = int(cordura_efecto)
            
        st.session_state.cordura = min(
            self.estados_config["limites"]["cordura_max"],
            st.session_state.cordura + cordura_sumada
        )
        self.actualizar_estados()

    def siguiente_ronda(self):
        if st.session_state.ronda_actual < 3:
            # Mostrar descanso después de la ronda actual
            if st.session_state.ronda_actual > 0:
                self.mostrar_descanso()
            
            st.session_state.ronda_actual += 1
            self.ejecutar_ronda(st.session_state.ronda_actual)
            st.rerun()
        else:
            self.mostrar_recompensas()
            st.rerun()

    def mostrar_recompensas(self):
        # Mapear el nivel a la clave correcta del JSON
        nivel_config = {
            "1_2": "nivel_1_2",
            "3_4": "nivel_3_4", 
            "5_6": "nivel_5_6",
            "7_10": "nivel_7_8"
        }
        
        clave_recompensa = nivel_config.get(st.session_state.heroes_nivel, "nivel_1_2")
        recompensa = self.recompensas.get(clave_recompensa, {})
        multiplicador = recompensa.get("multiplicador_monedas", 1.0)
        monedas_base = recompensa.get("monedas", 0)
        
        # Calcular monedas ganadas
        monedas_ganadas = monedas_base
        
        # Aplicar multiplicador si el usuario apostó algo
        if st.session_state.apuesta_activa and st.session_state.apuesta_monedas > 0:
            ganancia_apuesta = int(st.session_state.apuesta_monedas * multiplicador)
            monedas_ganadas += ganancia_apuesta

        experiencia_ganada = recompensa.get("experiencia", 0)
        tesoros_ganados = recompensa.get("tesoros", [])

        # Mostrar recompensas
        st.session_state.recompensas = {
            "monedas": monedas_ganadas,
            "monedas_base": monedas_base,
            "ganancia_apuesta": ganancia_apuesta if st.session_state.apuesta_activa else 0,
            "experiencia": experiencia_ganada,
            "tesoros": tesoros_ganados
        }
        
        self.agregar_mensaje_log("\n=== ¡VICTORIA! ===", "titulo")
        self.agregar_mensaje_log(f"Monedas ganadas: {monedas_ganadas}", "heroico")
        if st.session_state.apuesta_activa:
            self.agregar_mensaje_log(f" - Base: {monedas_base} monedas", "efecto")
            self.agregar_mensaje_log(f" - Ganancia por apuesta: +{ganancia_apuesta} monedas", "efecto")
        self.agregar_mensaje_log(f"Experiencia: {experiencia_ganada} puntos", "heroico")
        
        if tesoros_ganados:
            self.agregar_mensaje_log("Tesoros obtenidos:", "titulo")
            for tesoro in tesoros_ganados:
                self.agregar_mensaje_log(f"» {tesoro}", "lista")

    def agregar_mensaje_log(self, mensaje, tag=None):
        if 'mensajes_log' not in st.session_state:
            st.session_state.mensajes_log = []
        
        st.session_state.mensajes_log.append({"mensaje": mensaje, "tag": tag})

    def renderizar_interfaz(self):
        # CSS personalizado para la aplicación
        st.markdown("""
        <style>
        .main {
            background-color: #2D2D2D;
            color: white;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        .log-container {
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            height: 400px;
            overflow-y: auto;
            color: black !important;
        }
        .titulo { 
            color: #000000; 
            font-weight: bold; 
            font-size: 18px; 
            text-align: center;
        }
        .enemigo { 
            color: #8B0000; 
            font-weight: bold; 
            font-size: 16px; 
            text-align: center;
        }
        .heroico { 
            color: #006400; 
            font-weight: bold; 
            text-align: center;
        }
        .deshonroso { 
            color: #8B0000; 
            font-weight: bold; 
            text-align: center;
        }
        .critical { 
            color: #8B0000; 
            font-weight: bold; 
            animation: blink 1s infinite; 
            text-align: center;
        }
        @keyframes blink { 
            50% { opacity: 0.5; } 
        }
        .speaker { 
            color: #8B4513; 
            font-weight: bold; 
            font-style: italic; 
            text-align: center;
        }
        .efecto {
            color: #000000;
            text-align: center;
        }
        .apuesta {
            color: #006400;
            font-weight: bold;
            text-align: center;
        }
        .lista {
            color: #000000;
            text-align: center;
        }
        .ronda {
            color: #000000;
            font-weight: bold;
            font-size: 16px;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Título de la aplicación
        st.title("⚔️ DETION ARENA: LEAGUE OF DUNGEONEERS")
        
        # Controles superiores
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.subheader("Nivel de Héroes")
            st.session_state.nivel_valor = st.slider("Nivel", 1, 10, st.session_state.nivel_valor, 1, label_visibility="collapsed", key="nivel_slider")
            
        with col2:
            st.subheader("Apuesta")
            st.session_state.apuesta_valor = st.slider("Monedas", 0, 500, st.session_state.apuesta_valor, 10, label_visibility="collapsed", key="apuesta_slider")
            
        with col3:
            st.subheader("Controles")
            if not st.session_state.get('juego_iniciado', False):
                if st.button("🎮 Iniciar Arena", use_container_width=True, key="iniciar_btn"):
                    self.iniciar_arena()
            else:
                if st.session_state.ronda_actual < 3:
                    if st.button("➡️ Siguiente Ronda", use_container_width=True, key="siguiente_btn"):
                        self.siguiente_ronda()
                
            if st.button("🔁 Reiniciar", use_container_width=True, key="reiniciar_btn"):
                self.reiniciar_arena()
                
            if st.button("🔊 Música: " + ("ON" if st.session_state.get('musica_activada', False) else "OFF"), 
                        use_container_width=True, key="musica_btn"):
                self.toggle_musica()
        
        # Área de log de eventos
        st.subheader("Eventos de la Arena")
        
        # Crear contenedor para el log
        log_html = '<div class="log-container">'
        for msg in st.session_state.get('mensajes_log', []):
            clase = msg.get('tag', 'efecto')
            mensaje = msg['mensaje'].replace('\n', '<br>')
            log_html += f'<p class="{clase}">{mensaje}</p>'
        log_html += '</div>'
        
        st.markdown(log_html, unsafe_allow_html=True)
        
        # Botones de acción durante el juego
        if st.session_state.get('juego_iniciado', False) and st.session_state.get('ronda_actual', 1) <= 3:
            col4, col5 = st.columns(2)
            with col4:
                if st.button("🛡️ Acción Heroica", use_container_width=True, key="heroica_btn"):
                    self.evaluar_accion("heroica")
            with col5:
                if st.button("💀 Acción Deshonrosa", use_container_width=True, key="deshonrosa_btn"):
                    self.evaluar_accion("deshonrosa")
        
        # Mostrar recompensas al final
        if hasattr(st.session_state, 'recompensas'):
            st.subheader("🎉 ¡Victoria!")
            st.write(f"**Monedas ganadas:** {st.session_state.recompensas['monedas']}")
            if st.session_state.apuesta_activa:
                st.write(f"** - Base:** {st.session_state.recompensas['monedas_base']}")
                st.write(f"** - Ganancia por apuesta:** {st.session_state.recompensas['ganancia_apuesta']}")
            st.write(f"**Experiencia:** {st.session_state.recompensas['experiencia']} puntos")
            if st.session_state.recompensas['tesoros']:
                st.write("**Tesoros:**")
                for tesoro in st.session_state.recompensas['tesoros']:
                    st.write(f" - {tesoro}")

# Crear y ejecutar la aplicación
if __name__ == "__main__":
    if 'app' not in st.session_state:
        st.session_state.app = ArenaApp()
    
    st.session_state.app.renderizar_interfaz()