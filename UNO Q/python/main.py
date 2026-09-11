from arduino.app_utils import App, Bridge
from video_object_detection import VideoObjectDetection
from arduino.app_peripherals.camera import WebSocketCamera
from arduino.app_bricks.telegram_bot import TelegramBot, Sender
from arduino.app_bricks.web_ui import WebUI
from PIL import Image, ImageDraw

import io
import math

ID_chat = 8996760139
senha = 937389

servidor_bloqueado = 1 # 0 Bloqueado 1 Liberado

matrix = True # T: matrix é utilizada | F: matrix não é utilizada

num_dispositivos = 0 # Dispositivos conectados

bot = TelegramBot()

cam1 = WebSocketCamera(port=8080, resolution=(320, 240), fps=15)
cam2 = WebSocketCamera(port=9393, resolution=(320, 240), fps=15)

deteccao1 = VideoObjectDetection(
    cam1, 
    confidence=0.6, 
    debounce_sec=0, 
    camera_preview=True, 
    stream_port=5050, 
    service="ei-video-obj-detection-runner1",
)

deteccao2 = VideoObjectDetection(
    cam2, 
    confidence=0.6, 
    debounce_sec=0, 
    camera_preview=True,
    stream_port=5051, 
    service="ei-video-obj-detection-runner2",
)

ui = WebUI()

class Detectar:
    def __init__(self, camera_deteccao: str, limite_movimento):
        self.posicao_anterior = None
        self.camera_deteccao = camera_deteccao
        self.limite_movimento = limite_movimento
        
    def pessoa_detectada(self, specs_frame, frame=None):
        global matrix
        
        if frame is None:
            return
        try:
            x1, y1, x2, y2 = specs_frame.get('bounding_box_xyxy') # Pega as cordenadas x e y do retangulo
            
            centro_atual = ((x1 + x2) / 2, (y1 + y2) / 2) # Acha o centro do retangulo
    
            if self.posicao_anterior is not None:
                distancia = math.dist(centro_atual, self.posicao_anterior) # Calcula a distancia do centro atual para a distancia anterior
                if distancia < self.limite_movimento: # Se for menor que o limite de movimento não manda a imagem
                    return
    
            img = Image.open(io.BytesIO(frame)).convert('RGB')
            ImageDraw.Draw(img).rectangle([x1, y1, x2, y2], outline="red", width=3)
    
            bytes_imagem_com_caixas = io.BytesIO()
            img.save(bytes_imagem_com_caixas, format="JPEG")
            imagem_com_caixas = bytes_imagem_com_caixas.getvalue()
                
            bot.send_photo(ID_chat, imagem_com_caixas, f"Pessoa detectada na {self.camera_deteccao}")
    
            if matrix == True: 
                Bridge.call("pessoaDetectada")
    
            self.posicao_anterior = centro_atual
            
        except Exception as e:
            print(f"[ERRO]: {e}")

espiao1 = Detectar(camera_deteccao="camera 1", limite_movimento=55)
espiao2 = Detectar(camera_deteccao="camera 2", limite_movimento=40)


def callback_deteccao1(specs_frame, frame=None):
    espiao1.pessoa_detectada(specs_frame, frame)
    
def callback_deteccao2(specs_frame, frame=None):
    espiao2.pessoa_detectada(specs_frame, frame)
    

def esconder_matrix(Sender, _):
    global matrix
    matrix = False

    Sender.reply("Modo espião ativado")

def mostrar_matrix(Sender, _):
    global matrix
    matrix = True

    Sender.reply("Modo espião desativado")

def verificar_senha(_, data):
    codigo = data.get("senha")
    
    if codigo == senha:
        ui.send_message("liberar", {})

    else:
        ui.send_message("bloquear", {})

def bloquear_servidor(Sender, _):
    global servidor_bloqueado
    
    ui.send_message("bloquear_servidor", {})
    servidor_bloqueado = 0 # Indica ao JS que o servidor deve ser bloqueado

    Sender.reply("Servidor bloqueado")

def desbloquear_servidor(Sender, _):
    global servidor_bloqueado
    
    ui.send_message("desbloquear_servidor", {})
    servidor_bloqueado = 1 # Indica ao JS que o servidor deve ser liberado
    
    Sender.reply("Sevidor desbloqueado")

def enviar_permissao(*args):
    global servidorBloqueado
    ui.send_message("permissao", {"servidor": servidor_bloqueado})

def mostrar_comandos(Sender, _):
    comandos = str("/espiao \n /desativar_espiao \n /bloquear_servidor \n /desbloquear_servidor \n /dispositivos \n /comandos")
    
    Sender.reply("Comandos: ")
    Sender.reply(comandos)

def disp_conectado(sid):
    global num_dispositivos
    print(f"Dispositivo {sid} foi conectado")
    
    num_dispositivos += 1

    if num_dispositivos <= 1:
        bot.send_message(ID_chat, str(f"{num_dispositivos} dispositivo conectado"))

    else:
        bot.send_message(ID_chat, str(f"{num_dispositivos} dispositivos conectados"))
        

def disp_desconectado(sid):
    global num_dispositivos
    print(f"Dispositivo {sid} foi desconectado")
    
    num_dispositivos -= 1
    bot.send_message(ID_chat, str("Um dispositivo foi desconectado"))

def apr_conectados(Sender, _):
    Sender.reply(f"Numero de dispositivos conectados: {num_dispositivos} | Executar: /bloquear_servidor ?")
    
    
deteccao1.on_detect("person", callback_deteccao1)
deteccao2.on_detect("person", callback_deteccao2)

ui.on_message("senha", verificar_senha)
ui.on_message("liberar", enviar_permissao)
ui.on_connect(disp_conectado)
ui.on_disconnect(disp_desconectado)

bot.add_command("espiao", esconder_matrix)
bot.add_command("desativar_espiao", mostrar_matrix)
bot.add_command("bloquear_servidor", bloquear_servidor)
bot.add_command("desbloquear_servidor", desbloquear_servidor)
bot.add_command("comandos", mostrar_comandos)
bot.add_command("dispositivos", apr_conectados)

App.run()
