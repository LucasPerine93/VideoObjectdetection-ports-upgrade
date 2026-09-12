import cv2
import asyncio
import websockets
import numpy as np

class Camera:
    def __init__(self, id_camera: int, resolucao_w: int, resolucao_h: int):
        self.id_camera = id_camera
        self.resolucao_w = resolucao_w
        self.resolucao_h = resolucao_h

        self.cam = cv2.VideoCapture(self.id_camera)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolucao_h)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolucao_w)

    def pegar_video(self) -> np.ndarray | None:
        _, buffer = self.cam.read()
        return buffer


class Frame:
    def __init__(self, qualidade_img):
        self.qualidade_img = qualidade_img

    def juntar_frame(self, frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray | None:
        if frame1.shape[0] == frame2.shape[0]:
            imagem_combinada = cv2.hconcat([frame1, frame2])
            _, frame = cv2.imencode('.jpg', imagem_combinada, [cv2.IMWRITE_JPEG_QUALITY, self.qualidade_img])

            return frame

        else:
            print("Erro: As imagens têm alturas diferentes! É necessário redimensionar antes.")

class Servidor:
    def __init__(self, ip, porta, cam1, cam2, juntar):
        self.ip = ip
        self.porta = porta

        self.uri = f"ws://{self.ip}:{self.porta}?raw=true"

        self.cam1 = cam1
        self.cam2 = cam2
        self.juntar = juntar

    async def enviar_frames(self):

        while True:
            try:
                print(f"Conectando ao UNO Q em {self.uri}")
                async with websockets.connect(self.uri) as ws:
                    print("Conectado a placa UNO Q")
                    while True:

                        img = self.juntar.juntar_frame(self.cam1.pegar_video(), self.cam2.pegar_video())

                        await ws.send(img.tobytes())
                        await asyncio.sleep(0.033)

            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError, OSError) as e:
                print(f"[ERRO]: Conexão perdida ({e}). Tentando reconectar em 2 segundos")
                await asyncio.sleep(2)

if __name__ == "__main__":

    cam1 = Camera(
        id_camera=1, 
        resolucao_w=460, 
        resolucao_h=400
    )
                                                                
    cam2 = Camera(
        id_camera=1,
        resolucao_w=460, 
        resolucao_h=400
    )
                                                                
    juntar = Frame(qualidade_img=35)

    transmitir = Servidor(porta=9393, ip="192.168.0.113", cam1=cam1, cam2=cam2, juntar=juntar)
    asyncio.run(transmitir.enviar_frames())


