import random
import os
import sys
import subprocess
import json
import pygame
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
                             QTextEdit, QMessageBox, QScrollArea, QFrame, QVBoxLayout)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QFont, QColor, QTextCursor, QTextCharFormat, QIcon
from PyQt6.QtCore import QSize


class ArenaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Predefinir atributos para mejor organización
        self._setup_attributes()
        self.cargar_configuraciones()
        self.inicializar_ui()
        self.inicializar_estados()
        self.mostrar_mensaje_bienvenida()
        self.iniciar_efecto_parpadeo()
        self.inicializar_musica()

    def _setup_attributes(self):
        """Predefinir atributos para mejor organización y legibilidad"""
        # Configuración
        self.BASE_DIR = None
        self.DATA_DIR = None
        self.IMAGES_DIR = None
        self.AUDIO_DIR = None
        self.ui_config = None
        self.estados_config = None
        self.descansos = None
        self.recompensas = None
        self.comportamiento = None
        
        # Estado del juego
        self.heroes_nivel = None
        self.ronda_actual = 1
        self.encuentro_actual = None
        self.encuentros = {}
        self.acciones_heroicas = 0
        self.acciones_deshonrosas = 0
        self.moral_grupo = 0
        self.cordura = 0
        self.bonif_critico = False
        self.apuesta_activa = False
        self.apuesta_monedas = 0
        self.reward_log_visible = False
        
        # Control de música
        self.musica_activada = True
        self.btn_musica_on = None
        self.btn_musica_off = None
        
        # UI elements
        self.background_label = None
        self.btn_nivel_down = None
        self.nivel_label = None
        self.btn_nivel_up = None
        self.btn_apuesta_down = None
        self.apuesta_label = None
        self.btn_apuesta_up = None
        self.event_log = None
        self.reward_log = None
        self.botones = []
        self.text_formats = {}
        
        # Valores de configuración
        self.nivel_valor = 1
        self.apuesta_valor = 0
        
        # Efectos
        self.blink_state = False
        self.blink_timer = None

        # Factores de escala para responsive design
        self.width_scale = 1.0
        self.height_scale = 1.0
        self.scale_factor = 1.0

    def cargar_configuraciones(self):
        try:
            self.BASE_DIR = Path(__file__).parent
            self.DATA_DIR = self.BASE_DIR / "assets" / "data"
            self.IMAGES_DIR = self.BASE_DIR / "assets" / "imagenes"
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
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las configuraciones:\n{str(e)}")
            sys.exit(1)
            
    def cargar_imagen(self, nombre_archivo, tamaño=None):
        try:
            ruta = self.IMAGES_DIR / nombre_archivo
            if not ruta.exists():
                print(f"Archivo no encontrado: {ruta}")
                return None
                
            pixmap = QPixmap(str(ruta))
            if pixmap.isNull():
                print(f"Error: No se pudo cargar la imagen {nombre_archivo}")
                return None
                
            if tamaño:
                pixmap = pixmap.scaled(tamaño[0], tamaño[1], Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            return pixmap
        except Exception as e:
            print(f"Error cargando imagen {nombre_archivo}: {e}")
            return None
        
    def escalar_imagen(self, nombre_archivo, tamaño_base):
        """Cargar y escalar una imagen según el factor de escala"""
        try:
            # Calcular nuevo tamaño basado en escala
            nuevo_ancho = int(tamaño_base[0] * self.scale_factor)
            nuevo_alto = int(tamaño_base[1] * self.scale_factor)
            
            ruta = self.IMAGES_DIR / nombre_archivo
            if not ruta.exists():
                print(f"Archivo no encontrado: {ruta}")
                return None
                
            pixmap = QPixmap(str(ruta))
            if pixmap.isNull():
                print(f"Error: No se pudo cargar la imagen {nombre_archivo}")
                return None
                
            pixmap = pixmap.scaled(nuevo_ancho, nuevo_alto, 
                                Qt.AspectRatioMode.KeepAspectRatio, 
                                Qt.TransformationMode.SmoothTransformation)
            return pixmap
        except Exception as e:
            print(f"Error escalando imagen {nombre_archivo}: {e}")
            return None

    def inicializar_musica(self):
        """Inicializar música con pygame al iniciar la aplicación"""
        try:
            pygame.mixer.init()
            musica_path = self.AUDIO_DIR / "musica_fondo.mp3"
            
            if musica_path.exists():
                pygame.mixer.music.load(str(musica_path))
                pygame.mixer.music.set_volume(0.7)
                
                # Siempre reproducir al iniciar (por defecto está activada)
                pygame.mixer.music.play(-1)  # -1 para loop infinito
                print("Música iniciada con pygame")
            else:
                print("Archivo de música no encontrado")
                
        except Exception as e:
            print(f"Error inicializando música con pygame: {e}")

    def activar_musica(self):
        """Activar música - llamado por btn_sin_musica"""
        self.musica_activada = True
        self.btn_musica_off.hide()  # Oculta el botón de música OFF
        self.btn_musica_on.show()   # Muestra el botón de música ON
        
        if hasattr(pygame, 'mixer') and pygame.mixer.get_init():
            pygame.mixer.music.unpause()
            print("Música activada")
        else:
            self.inicializar_musica()

    def desactivar_musica(self):
        """Desactivar música - llamado por btn_con_musica"""
        self.musica_activada = False
        self.btn_musica_on.hide()   # Oculta el botón de música ON
        self.btn_musica_off.show()  # Muestra el botón de música OFF
        
        if hasattr(pygame, 'mixer') and pygame.mixer.get_init():
            pygame.mixer.music.pause()
            print("Música pausada")
    
    def actualizar_fondo(self):
        """Actualiza el fondo cuando la ventana cambia de tamaño"""
        if hasattr(self, 'background_label') and self.background_label is not None:
            fondo_pixmap = self.cargar_imagen("fondo.png", (self.width(), self.height()))
            if fondo_pixmap:
                self.background_label.setPixmap(fondo_pixmap)
                self.background_label.setScaledContents(True)
                self.background_label.setGeometry(0, 0, self.width(), self.height())
            else:
                # Respaldo: establecer un fondo de color sólido si falla la carga de la imagen
                self.background_label.setStyleSheet("background-color: #2D2D2D;")

    def inicializar_ui(self):
        self.setWindowTitle("DETION ARENA: LEAGUE OF DUNGEONEERS")
        self.setMinimumSize(1024, 768)  # Establecer un tamaño mínimo
        self.showMaximized()

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Crear un QLabel para el fondo
        self.background_label = QLabel(central_widget)
        self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Cargar y establecer el fondo
        self.actualizar_fondo()
        
        # Asegurar que el fondo esté detrás de todos los elementos
        self.background_label.lower()

        # Configurar elementos UI
        self._configurar_ui_elementos(central_widget)

    def _configurar_ui_elementos(self, parent):
        """Configurar todos los elementos UI en un método organizado"""
        # Primero configurar todos los elementos
        self.configurar_paneles_configuracion(parent)
        self.configurar_log(parent)
        self.configurar_log_recompensas(parent)
        self.configurar_controles(parent)
        
        # Calcular factores de escala iniciales
        self.calcular_factores_escala()
        
        # Aplicar escalado inicial
        self.aplicar_escalado_completo()

    def calcular_factores_escala(self):
        """Calcular factores de escala basados en la resolución actual"""
        base_width = 1920
        base_height = 1080
        
        # Calcular factores independientes para ancho y alto
        self.width_scale = self.width() / base_width
        self.height_scale = self.height() / base_height
        
        # Usar el factor más pequeño para mantener las proporciones
        self.scale_factor = min(self.width_scale, self.height_scale)
        
        # Para elementos que necesitan escalado uniforme
        self.uniform_scale = min(self.width_scale, self.height_scale) * 0.9  # Pequeño margen

    def resizeEvent(self, event):
        # Actualizar el fondo al redimensionar
        super().resizeEvent(event)
        self.actualizar_fondo()
        
        # Recalcular factores de escala
        self.calcular_factores_escala()
        
        # Aplicar nuevo escalado
        self.aplicar_escalado_completo()

    def aplicar_escalado_completo(self):
        """Aplicar escalado a todos los elementos de la UI"""
        # Recalcular factores de escala
        self.calcular_factores_escala()
        
        # Actualizar formatos de texto
        self.actualizar_formatos_texto(self.scale_factor)
        
        # Actualizar TODOS los botones (reemplaza los dos métodos anteriores)
        self.actualizar_imagenes_botones()
        
        # Actualizar etiquetas
        self.actualizar_etiquetas()
        
        # Actualizar logs
        self.actualizar_logs()
        
        # Reposicionar elementos
        self.reposicionar_elementos()
        
        # Actualizar el fondo
        self.actualizar_fondo()

    def actualizar_imagenes_botones(self):
        """Actualizar imágenes y tamaños de todos los botones según el factor de escala"""
        btn_size = int(80 * self.scale_factor)
        
        # Actualizar botones principales
        for btn in self.botones:
            if btn is not None:
                btn.setFixedSize(btn_size, btn_size)
                if hasattr(btn, 'image_name'):
                    pixmap = self.escalar_imagen(btn.image_name, (80, 80))
                    if pixmap:
                        btn.setIcon(QIcon(pixmap))
                        btn.setIconSize(QSize(btn_size, btn_size))
        
        # Actualizar botones de configuración
        config_buttons = [
            (self.btn_nivel_down, "btn_nivel_down.png"),
            (self.btn_nivel_up, "btn_nivel_up.png"),
            (self.btn_apuesta_down, "btn_apuesta_down.png"),
            (self.btn_apuesta_up, "btn_apuesta_up.png")
        ]
        
        for btn, image_name in config_buttons:
            if btn is not None:
                btn.setFixedSize(btn_size, btn_size)
                pixmap = self.escalar_imagen(image_name, (80, 80))
                if pixmap:
                    btn.setIcon(QIcon(pixmap))
                    btn.setIconSize(QSize(btn_size, btn_size))
        
        # Actualizar botones de música
        music_buttons = [
            (self.btn_musica_on, "btn_con_musica.png"),
            (self.btn_musica_off, "btn_sin_musica.png")
        ]
        
        for btn, image_name in music_buttons:
            if btn is not None:
                btn.setFixedSize(btn_size, btn_size)
                pixmap = self.escalar_imagen(image_name, (80, 80))
                if pixmap:
                    btn.setIcon(QIcon(pixmap))
                    btn.setIconSize(QSize(btn_size, btn_size))
                

    def actualizar_etiquetas(self):
        """Actualizar etiquetas de configuración según el factor de escala"""
    
            
    def actualizar_logs(self):
        """Actualizar logs de eventos y recompensas"""
        log_width = int(1000 * self.width_scale)
        log_height = int(300 * self.height_scale)
        
        if hasattr(self, 'event_log') and self.event_log is not None:
            self.event_log.setFixedSize(log_width, log_height)
            # Actualizar fuentes del log
            font = self.event_log.font()
            font.setPointSize(int(14 * self.scale_factor))
            self.event_log.setFont(font)
        
        if hasattr(self, 'reward_log') and self.reward_log is not None:
            reward_width = int(450 * self.width_scale)
            reward_height = int(250 * self.height_scale)
            self.reward_log.setFixedSize(reward_width, reward_height)
            # Actualizar fuentes del log de recompensas
            font = self.reward_log.font()
            font.setPointSize(int(10 * self.scale_factor))
            self.reward_log.setFont(font)

    def reposicionar_elementos(self):
        """Reposicionar todos los elementos basado en factores de escala"""
        # Definir posiciones relativas (proporciones de 0 a 1) para 1920x1080
        positions = {
            'btn_nivel_down': (0.106, 0.495),
            'nivel_label': (0.13, 0.43),
            'btn_nivel_up': (0.155, 0.495),
            'btn_apuesta_down': (0.846, 0.495),
            'apuesta_label': (0.87, 0.43),
            'btn_apuesta_up': (0.893, 0.495)
        }
        
        # Mover elementos de configuración
        for element, (rel_x, rel_y) in positions.items():
            widget = getattr(self, element, None)
            if widget is not None:
                x = int(self.width() * rel_x - widget.width()/2)
                y = int(self.height() * rel_y - widget.height()/2)
                widget.move(x, y)
        
        # Posicionar event_log (centrado horizontalmente, posición vertical específica)
        if hasattr(self, 'event_log') and self.event_log is not None:
            self.event_log.move(
                int(self.width() * 0.5 - self.event_log.width()/2), 
                int(self.height() * 0.41 - self.event_log.height()/2)
            )
        
        # Posicionar reward_log (basado en el código original)
        if hasattr(self, 'reward_log') and self.reward_log is not None:
            self.reward_log.move(
                int(self.width() * 0.5 - self.reward_log.width()/2), 
                int(self.height() * 0.53 + self.event_log.height()/2 + (20 * self.scale_factor))
            )
        
        # Actualizar posiciones de botones principales
        btn_positions = [
            (0.15, 0.94), (0.27, 0.94), (0.39, 0.94),
            (0.51, 0.94), (0.63, 0.94), (0.75, 0.94), (0.87, 0.94)
        ]
            
        if hasattr(self, 'botones') and self.botones:
            for i, btn in enumerate(self.botones):
                if btn is not None:
                    x = int(self.width() * btn_positions[i][0] - btn.width()/2)
                    y = int(self.height() * btn_positions[i][1] - btn.height()/2)
                    btn.move(x, y)
        
        # Actualizar posición del botón de música alternativo
        if hasattr(self, 'btn_musica_off') and self.btn_musica_off is not None and hasattr(self, 'btn_musica_on'):
            self.btn_musica_off.move(self.btn_musica_on.pos())

    def configurar_paneles_configuracion(self, parent):
            btn_size = (int(80 * self.scale_factor), int(80 * self.scale_factor))
        
        # Cargar imágenes con verificación de errores
            btn_images = {
                "nivel_up": "btn_nivel_up.png",
                "nivel_down": "btn_nivel_down.png", 
                "apuesta_up": "btn_apuesta_up.png",
                "apuesta_down": "btn_apuesta_down.png"
            }
            
            for key, image in btn_images.items():
                pixmap = self.cargar_imagen(image, btn_size)
                if pixmap:
                    setattr(self, f"pixmap_{key}", pixmap)
                else:
                    print(f"Error: No se pudo cargar la imagen {image}")
                    setattr(self, f"pixmap_{key}", None)
            
            # Estilo común para botones
            button_style = """
                QPushButton {
                    background-color: #2D2D2D;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #3D3D3D;
                }
            """
            
            # Configurar botones de NIVEL con verificación
            self.btn_nivel_down = self._crear_boton_configuracion(
                parent, getattr(self, "pixmap_nivel_down", None), self.decrementar_nivel, button_style
            )
            
            self.nivel_label = QLabel("1", parent)
            if self.nivel_label:
                self.nivel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.nivel_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: transparent;
                        color: black;
                        border: none;
                        font: bold {int(50 * self.scale_factor)}px Arial;
                        min-width: {int(80 * self.scale_factor)}px;  /* ANCHO MÍNIMO PARA 2-3 DÍGITOS */
                    }}
                """)
                self.nivel_label.adjustSize()  # Ajustar tamaño automáticamente
            else:
                print("Error: No se pudo crear nivel_label")
            
            self.btn_nivel_up = self._crear_boton_configuracion(
                parent, getattr(self, "pixmap_nivel_up", None), self.incrementar_nivel, button_style
            )
            
            # Configurar botones de APUESTA con verificación
            self.btn_apuesta_down = self._crear_boton_configuracion(
                parent, getattr(self, "pixmap_apuesta_down", None), self.decrementar_apuesta, button_style
            )

            self.apuesta_label = QLabel("0", parent)
            if self.apuesta_label:
                self.apuesta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.apuesta_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: transparent;
                        color: black;
                        border: none;
                        font: bold {int(50 * self.scale_factor)}px Arial;
                        min-width: {int(100 * self.scale_factor)}px;  /* ANCHO MÍNIMO MAYOR PARA APUESTAS (hasta 500) */
                    }}
                """)
                self.apuesta_label.adjustSize()  # Ajustar tamaño automáticamente
            else:
                print("Error: No se pudo crear apuesta_label")

            self.btn_apuesta_up = self._crear_boton_configuracion(
                parent, getattr(self, "pixmap_apuesta_up", None), self.incrementar_apuesta, button_style
            )

    def _crear_boton_configuracion(self, parent, pixmap, callback, style):
        """Método helper para crear botones de configuración"""
        try:
            btn = QPushButton(parent)
            if pixmap:
                btn.setIcon(QIcon(pixmap))
                btn.setIconSize(QSize(int(80 * self.scale_factor), int(80 * self.scale_factor)))
            btn.setFixedSize(int(80 * self.scale_factor), int(80 * self.scale_factor))
            btn.setStyleSheet(style)
            btn.clicked.connect(callback)
            return btn
        except Exception as e:
            print(f"Error creando botón: {e}")
            return None

    def configurar_log(self, parent):
        self.event_log = QTextEdit(parent)
        self.event_log.setReadOnly(True)
        
        # Calcular tamaño basado en escala
        log_width = int(1000 * self.scale_factor)
        log_height = int(300 * self.scale_factor)
        font_size = int(14 * self.scale_factor)
        
        self.event_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: black;
                border: none;
                font: {font_size}px Arial;
            }}
            /* Ocultar completamente la barra desplazadora */
            QScrollBar:vertical {{
                width: 0px;
            }}
            QScrollBar:horizontal {{
                height: 0px;
            }}
        """)
        self.event_log.setFixedSize(log_width, log_height)
        self.event_log.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Configurar formatos de texto
        self._configurar_formatos_texto()
    
    def _configurar_formatos_texto(self):
        """Configurar todos los formatos de texto en un método organizado"""
        formatos = {
            "titulo": ("#000000", int(16 * self.scale_factor), True, False),
            "recompensa": ("#006400", int(13 * self.scale_factor), False, False),
            "enemigo": ("#8B0000", int(16 * self.scale_factor), True, False),
            "lista": ("#000000", int(12 * self.scale_factor), False, False),
            "ronda": ("#000000", int(14 * self.scale_factor), True, False),
            "heroico": ("#006400", int(13 * self.scale_factor), True, False),
            "deshonroso": ("#8B0000", int(13 * self.scale_factor), True, False),
            "publico": ("#000000", int(13 * self.scale_factor), False, True),
            "efecto": ("#000000", int(13 * self.scale_factor), False, False),
            "critical": ("#8B0000", int(13 * self.scale_factor), True, False),
            "blink": ("#000000", int(13 * self.scale_factor), False, False),
            "apuesta": ("#006400", int(13 * self.scale_factor), True, False),
            "center": ("#000000", int(14 * self.scale_factor), False, False),
            "speaker": ("#8B4513", int(14 * self.scale_factor), True, True)
        }
        
        for nombre, (color, size, bold, italic) in formatos.items():
            self.text_formats[nombre] = self.crear_formato_texto(color, size, bold, italic)
    
    def configurar_log_recompensas(self, parent):
        self.reward_log = QTextEdit(parent)
        self.reward_log.setReadOnly(True)
        self.reward_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: black;
                border: none;
                font: {int(10 * self.scale_factor)}px Arial;
            }}
        """)
        self.reward_log.setFixedSize(int(450 * self.width_scale), int(250 * self.height_scale))
        self.reward_log.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reward_log.hide()
        
    def crear_formato_texto(self, color, size=12, bold=False, italic=False):
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        font = QFont("Arial", size)
        font.setBold(bold)
        font.setItalic(italic)
        format.setFont(font)
        return format

    def configurar_controles(self, parent):
        btn_size = (int(80 * self.scale_factor), int(80 * self.scale_factor))
        
        # Botones modificados: 
        botones_info = [
            ("btn_iniciar.png", self.iniciar_arena, True),
            ("btn_ronda.png", self.siguiente_ronda, False),
            ("btn_heroico.png", lambda: self.evaluar_accion("heroica"), False),
            ("btn_deshonroso.png", lambda: self.evaluar_accion("deshonrosa"), False),
            ("btn_con_musica.png", self.desactivar_musica, True),
            ("btn_reiniciar.png", self.reiniciar_arena, True),
            ("btn_reglas.png", self.mostrar_reglas, True)
        ]

        self.botones = []
        for i, (imagen, comando, habilitado) in enumerate(botones_info):
            btn = self._crear_boton_control(parent, imagen, btn_size, comando, habilitado)
            self.botones.append(btn)

        # Referencias a botones específicos
        self.btn_iniciar, self.btn_ronda, self.btn_heroico, self.btn_deshonroso, \
        self.btn_musica_on, self.btn_reiniciar, self.btn_reglas = self.botones
        
        # Crear botón de música desactivada (btn_sin_musica)
        self.btn_musica_off = self._crear_boton_control(parent, "btn_sin_musica.png", btn_size, self.activar_musica, True)
        self.btn_musica_off.move(self.btn_musica_on.pos())
        self.btn_musica_off.hide()
        
    def _crear_boton_control(self, parent, imagen, tamaño, comando, habilitado):
        """Método helper para crear botones de control"""
        btn = QPushButton(parent)
        # Guardar el nombre de la imagen para poder recargarla si es necesario
        btn.image_name = imagen
        
        # Cargar imagen con el tamaño base
        pixmap = self.cargar_imagen(imagen, tamaño)
        
        if pixmap:
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(QSize(tamaño[0], tamaño[1]))
            btn.pixmap = pixmap  # Guardar referencia al pixmap
        else:
            btn.setText("?")
            
        btn.setFixedSize(tamaño[0], tamaño[1])
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                border: none;
                color: white;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
        """)
        btn.setEnabled(habilitado)
        btn.clicked.connect(comando)
        
        return btn
    
    def actualizar_formatos_texto(self, scale_factor):
        """Actualizar los formatos de texto según el factor de escala"""
        # Definir tamaños base para 1920x1080
        base_sizes = {
            "titulo": 16,
            "recompensa": 13,
            "enemigo": 16,
            "lista": 12,
            "ronda": 14,
            "heroico": 13,
            "deshonroso": 13,
            "publico": 13,
            "efecto": 13,
            "critical": 13,
            "blink": 13,
            "apuesta": 13,
            "center": 14,
            "speaker": 14
        }
        
        # Aplicar escala a todos los tamaños
        formatos = {}
        for nombre, size in base_sizes.items():
            scaled_size = int(size * scale_factor)
            # Mantener los colores y estilos originales
            if nombre == "titulo":
                formatos[nombre] = ("#000000", scaled_size, True, False)
            elif nombre == "recompensa":
                formatos[nombre] = ("#006400", scaled_size, False, False)
            elif nombre == "enemigo":
                formatos[nombre] = ("#8B0000", scaled_size, True, False)
            # ... continuar con el resto de formatos
            
        # Actualizar los formatos
        for nombre, (color, size, bold, italic) in formatos.items():
            self.text_formats[nombre] = self.crear_formato_texto(color, size, bold, italic)

    def incrementar_nivel(self):
        if self.nivel_valor < 10:
            self.nivel_valor += 1
            self.nivel_label.setText(str(self.nivel_valor))

    def decrementar_nivel(self):
        if self.nivel_valor > 1:
            self.nivel_valor -= 1
            self.nivel_label.setText(str(self.nivel_valor))

    def incrementar_apuesta(self):
        if self.apuesta_valor < 500:
            self.apuesta_valor = min(500, self.apuesta_valor + 10)
            self.apuesta_label.setText(str(self.apuesta_valor))

    def decrementar_apuesta(self):
        if self.apuesta_valor > 0:
            self.apuesta_valor = max(0, self.apuesta_valor - 10)
            self.apuesta_label.setText(str(self.apuesta_valor))

    def iniciar_efecto_parpadeo(self):
        self.blink_state = False
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_effect)
        self.blink_timer.start(500)

    def blink_effect(self):
        if hasattr(self, 'text_formats'):
            current_color = self.text_formats["critical"].foreground().color()
            new_color = QColor("#FFCCCB") if current_color.name() == "#8b0000" else QColor("#8b0000")
            self.text_formats["critical"].setForeground(new_color)
            self.blink_state = not self.blink_state

    def mostrar_mensaje_log(self, mensaje, tag=None):
        cursor = self.event_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if tag == "critical":
            cursor.insertText("¡" * 10 + " ATENCIÓN " + "¡" * 10 + "\n", self.text_formats["blink"])
            cursor.insertText(mensaje + "\n", self.text_formats[tag])
            cursor.insertText("¡" * 30 + "\n", self.text_formats["blink"])
        else:
            cursor.insertText(mensaje + "\n", self.text_formats.get(tag, self.text_formats["center"]))
        
        self.event_log.setTextCursor(cursor)
        self.event_log.ensureCursorVisible()

    def mostrar_mensaje_bienvenida(self):
        self.mostrar_mensaje_log("\n=== BIENVENIDO A LA ARENA DE LORAINIA ===", "titulo")
        self.mostrar_mensaje_log("¡Atención, ciudadanos de Lorainia! Aventureros de las Tierras Antiguas,\n"
                                 "estáis bajo la atenta mirada de los dioses y del gran rey Logan III. Aquí hallaréis muerte o gloria.", "publico")
        self.mostrar_mensaje_log("Reglamento escrito por José Manuel Arena v1.3 y aplicacion por Omar Nieto (DETION)","enemigo")

    def inicializar_estados(self):
        # Usar valores de configuración si están disponibles
        limites = self.estados_config.get("limites", {})
        self.moral_grupo = limites.get("moral_max", 10)
        self.cordura = limites.get("cordura_max", 10)
        
        # Reiniciar otros estados
        self.heroes_nivel = None
        self.ronda_actual = 1
        self.encuentro_actual = None
        self.encuentros = {}
        self.acciones_heroicas = 0
        self.acciones_deshonrosas = 0
        self.bonif_critico = False
        self.apuesta_activa = False
        self.apuesta_monedas = 0
        self.reward_log_visible = False

    def reiniciar_arena(self):
        self.event_log.clear()
        self.event_log.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.inicializar_estados()
        
        if hasattr(self, 'reward_log'):
            self.reward_log.clear()
            self.reward_log.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.reward_log.hide()
            
        # Reiniciar estados de botones
        self.btn_iniciar.setEnabled(True)
        self.btn_ronda.setEnabled(False)
        self.btn_heroico.setEnabled(False)
        self.btn_deshonroso.setEnabled(False)
        
        # Reiniciar estado de música con pygame (activada por defecto)
        self.musica_activada = True
        self.btn_musica_off.hide()  # Asegurar que el botón OFF está oculto
        self.btn_musica_on.show()   # Asegurar que el botón ON está visible
        
        if hasattr(pygame, 'mixer') and pygame.mixer.get_init():
            pygame.mixer.music.unpause()
        else:
            self.inicializar_musica()
        
        # Reposicionar elementos
        self.aplicar_escalado_completo()
        
        self.mostrar_mensaje_bienvenida()
        self.mostrar_mensaje_log("\n=== ARENA REINICIADA ===", "titulo")

    def iniciar_arena(self):
        nivel = self.nivel_valor
        apuesta = self.apuesta_valor
        
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
                    self.heroes_nivel = f"{rango[0]}_{rango[1]}"
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
                self.encuentros = json.load(f)

            self.apuesta_monedas = apuesta
            self.apuesta_activa = apuesta > 0

            # Obtener el multiplicador de recompensas usando la clave correcta
            recompensa = self.recompensas.get(config_seleccionada["clave_recompensa"], {})
            multiplicador = recompensa.get("multiplicador_monedas", 1.0)
            
            # MOSTRAR MENSAJE DEL SPEAKER SOBRE LA APUESTA
            self.mostrar_mensaje_log("\n«¡Atención, nobles espectadores!»", "speaker")
            
            if self.apuesta_activa:
                ganancia_potencial = int(self.apuesta_monedas * multiplicador)
                self.mostrar_mensaje_log(f"«¡Nuestros valientes héroes han apostado {self.apuesta_monedas} monedas!»", "speaker")
                self.mostrar_mensaje_log(f"«Si logran la victoria, obtendrán {ganancia_potencial} monedas adicionales!»", "speaker")
            else:
                self.mostrar_mensaje_log("«¡Jajaja nuestros héroes no han apostado o eso quiere decir que solo les queda la vida!»", "speaker")
                self.mostrar_mensaje_log("«¡Una muestra de valentía o tal vez de locura!»", "speaker")
            
            self.mostrar_mensaje_log("«¡Que comience el espectáculo!»", "speaker")

            # Habilitar botones apropiados
            self.btn_iniciar.setEnabled(False)
            self.btn_ronda.setEnabled(True)
            self.btn_heroico.setEnabled(True)
            self.btn_deshonroso.setEnabled(True)
            
            self.mostrar_mensaje_log(f"\n=== HÉROES DE NIVEL {self.heroes_nivel.replace('_', '-')} ===", "titulo")
            if self.apuesta_activa:
                self.mostrar_mensaje_log(f"¡Has apostado {self.apuesta_monedas} monedas!", "apuesta")
            else:
                self.mostrar_mensaje_log("¡No has realizado ninguna apuesta!", "apuesta")
                
            self.ejecutar_ronda(1)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo iniciar la arena:\n{str(e)}")
            # Reactivar botón en caso de error
            self.btn_iniciar.setEnabled(True)

    def ejecutar_ronda(self, ronda):
            self.ronda_actual = ronda
            tipo_ronda = "Calentamiento" if ronda == 1 else "Desafío" if ronda == 2 else "Jefe Final"

            encuentros_ronda = self.encuentros[f"ronda_{ronda}"]
            tirada = random.randint(1, 100)

            for encuentro in encuentros_ronda:
                rango_min, rango_max = map(int, encuentro["rango"].split("-"))
                if rango_min <= tirada <= rango_max:
                    self.encuentro_actual = encuentro["enemigos"]
                    break
            else:
                # Si no se encuentra encuentro, usar el último por defecto
                self.encuentro_actual = encuentros_ronda[-1]["enemigos"]

            self.mostrar_mensaje_log(f"\n=== RONDA {ronda}: {tipo_ronda.upper()} ===", "ronda")
            self.mostrar_mensaje_log(f"Tirada: {tirada}", "enemigo")
            self.mostrar_enemigos()
            self.bonif_critico = False

    def mostrar_enemigos(self):
        enemigos = self.encuentro_actual.split(" y ")
        self.mostrar_mensaje_log("\nENEMIGOS EN LA ARENA:", "enemigo")
        
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
                    
            self.mostrar_mensaje_log(f"{icono} {enemigo.strip()}", "enemigo")

    def evaluar_accion(self, tipo_accion):
        if tipo_accion == "heroica":
            self.acciones_heroicas += 1
            tag = "heroico"
            tipo_reaccion = "apoyo"
            self.actualizar_estados("heroica")
        else:
            self.acciones_deshonrosas += 1
            tag = "deshonroso"
            tipo_reaccion = "desprecio"
            self.actualizar_estados("deshonrosa")

        reacciones = self.comportamiento["reacciones_publico"][tipo_reaccion]
        reaccion = random.choice(reacciones)

        self.mostrar_mensaje_log(f"\nLos héroes realizan una acción {tipo_accion}:", tag)
        self.mostrar_mensaje_log(f"» {reaccion['efecto']}", "critical" if reaccion['id'] > 15 else "efecto")

        self.aplicar_efecto_publico(reaccion['id'], tipo_accion == "heroica")
        self.btn_heroico.setEnabled(False)
        self.btn_deshonroso.setEnabled(False)

    def aplicar_efecto_publico(self, id_efecto, es_apoyo):
        if es_apoyo:
            if id_efecto == 4:
                self.bonif_critico = True
            elif id_efecto == 19:
                self.moral_grupo = min(self.estados_config["limites"]["moral_max"], self.moral_grupo + 1)
        else:
            if id_efecto == 4:
                self.moral_grupo = max(0, self.moral_grupo - 1)
            elif id_efecto == 5:
                self.cordura = max(0, self.cordura - 1)
        self.actualizar_estados()

    def actualizar_estados(self, accion=None):
        if accion == "heroica":
            self.moral_grupo = min(
                self.estados_config["limites"]["moral_max"],
                self.moral_grupo + self.estados_config["efectos"]["heroico"]["moral"]
            )
        elif accion == "deshonrosa":
            self.cordura = max(
                0,
                self.cordura + self.estados_config["efectos"]["deshonroso"]["cordura"]
            )

        self.mostrar_mensaje_log(
            f"\nMoral del Grupo: {self.moral_grupo}/{self.estados_config['limites']['moral_max']} "
            f"| Cordura: {self.cordura}/{self.estados_config['limites']['cordura_max']}",
            "efecto"
        )

    def mostrar_descanso(self):
        # Cambiar esto para que siempre sea descanso corto
        tipo = "corto"  # Eliminar la condición que determina el tipo
        descanso = self.descansos[tipo]

        self.mostrar_mensaje_log(f"\n=== {descanso['descripcion']} ===", "titulo")
        for beneficio in descanso["beneficios"]:
            self.mostrar_mensaje_log(beneficio, "lista")

        self.moral_grupo = min(
            self.estados_config["limites"]["moral_max"],
            self.moral_grupo + descanso["efectos"]["moral"]
        )
        
        # Parsear y aplicar efecto de cordura
        cordura_efecto = descanso["efectos"]["cordura"]
        if "d" in cordura_efecto:
            dado_cordura = int(cordura_efecto.split("d")[1])
            cordura_sumada = random.randint(1, dado_cordura)
        else:
            cordura_sumada = int(cordura_efecto)
            
        self.cordura = min(
            self.estados_config["limites"]["cordura_max"],
            self.cordura + cordura_sumada
        )
        self.actualizar_estados()

    def siguiente_ronda(self):
        if self.ronda_actual < 3:
            # Primero mostrar descanso después de la ronda actual
            if self.ronda_actual > 0:  # Mostrar descanso después de ronda 1 y 2
                self.mostrar_descanso()
            
            self.ronda_actual += 1
            self.ejecutar_ronda(self.ronda_actual)
            self.btn_heroico.setEnabled(True)
            self.btn_deshonroso.setEnabled(True)
        else:
            self.mostrar_recompensas()
            self.btn_heroico.setEnabled(False)
            self.btn_deshonroso.setEnabled(False)
            self.btn_ronda.setEnabled(False)

    def mostrar_recompensas(self):
        # Mapear el nivel a la clave correcta del JSON
        nivel_config = {
            "1_2": "nivel_1_2",
            "3_4": "nivel_3_4", 
            "5_6": "nivel_5_6",
            "7_10": "nivel_7_8"  # Los niveles 7-10 usan la clave "nivel_7_8"
        }
        
        clave_recompensa = nivel_config.get(self.heroes_nivel, "nivel_1_2")
        recompensa = self.recompensas.get(clave_recompensa, {})
        multiplicador = recompensa.get("multiplicador_monedas", 1.0)
        monedas_base = recompensa.get("monedas", 0)
        
        # Calcular monedas ganadas
        monedas_ganadas = monedas_base
        
        # Solo aplicar multiplicador si el usuario apostó algo
        if self.apuesta_activa and self.apuesta_monedas > 0:
            ganancia_apuesta = int(self.apuesta_monedas * multiplicador)
            monedas_ganadas += ganancia_apuesta

        experiencia_ganada = recompensa.get("experiencia", 0)
        tesoros_ganados = recompensa.get("tesoros", [])

        # MOSTRAR EN EL LOG DE RECOMPENSAS
        if hasattr(self, 'reward_log'):
            self.reward_log.clear()
            self.reward_log.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.reward_log.show()
            
            cursor = self.reward_log.textCursor()
            cursor.insertText("=== VICTORIA ===\n", self.text_formats["titulo"])
            cursor.insertText(f"» {monedas_ganadas} monedas de oro\n", self.text_formats["lista"])
            
            # Mostrar desglose de la apuesta si hubo apuesta
            if self.apuesta_activa and self.apuesta_monedas > 0:
                cursor.insertText(f"   - Base: {monedas_base} monedas\n", self.text_formats["lista"])
                cursor.insertText(f"   - Apuesta: +{int(self.apuesta_monedas * multiplicador)} monedas\n", self.text_formats["lista"])
            
            cursor.insertText(f"» {experiencia_ganada} puntos de experiencia\n", self.text_formats["lista"])
            
            # Añadir los tesoros ganados
            for tesoro in tesoros_ganados:
                cursor.insertText(f"» {tesoro}\n", self.text_formats["lista"])
                
            self.reward_log.setTextCursor(cursor)
            
    def mostrar_mensaje_recompensa(self, mensaje, tag=None):
        if hasattr(self, 'reward_log'):
            cursor = self.reward_log.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(mensaje + "\n", self.text_formats.get(tag, self.text_formats["center"]))
            self.reward_log.setTextCursor(cursor)
            self.reward_log.ensureCursorVisible()

    def mostrar_reglas(self):
        try:
            reglas_path = self.DATA_DIR / "Arena_V1.3.pdf"
            
            if reglas_path.exists():
                # Abrir PDF según el sistema operativo
                if sys.platform == "win32":
                    os.startfile(str(reglas_path))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(reglas_path)])
                else:
                    subprocess.run(["xdg-open", str(reglas_path)])
                
                self.mostrar_mensaje_log("\nAbriendo reglas de la arena...", "publico")
            else:
                QMessageBox.critical(self, "Error", f"El archivo de reglas no se encuentra en:\n{reglas_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo de reglas:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    window = ArenaApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()