import cv2
import torch
import numpy as np
from PIL import Image
from diffusers.utils import load_image
from diffusers.models import ControlNetModel
from insightface.app import FaceAnalysis
from InstantID.pipeline_stable_diffusion_xl_instantid import StableDiffusionXLInstantIDPipeline, draw_kps

class FaceEmbeddingGenerator:
    def __init__(self):
        self.app = FaceAnalysis(name='antelopev2', root='../InstantID/', 
                                providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        controlnet_path = '../InstantID/checkpoints/ControlNetModel'
        self.controlnet = ControlNetModel.from_pretrained(controlnet_path, torch_dtype=torch.float16)
        base_model = 'wangqixun/YamerMIX_v8'  # Replace with your model
        self.pipe = StableDiffusionXLInstantIDPipeline.from_pretrained(
            base_model,
            controlnet=self.controlnet,
            torch_dtype=torch.float16
        )
        # self.pipe.to("mps")
        self.pipe.cuda()
        face_adapter = '../InstantID/checkpoints/ip-adapter.bin'
        self.pipe.load_ip_adapter_instantid(face_adapter)

    def generate_image(self, image_path, prompt, negative_prompt):
        try:
            face_image = load_image(image_path)
            face_info = self.app.get(cv2.cvtColor(np.array(face_image), cv2.COLOR_RGB2BGR))
            face_info = sorted(face_info, key=lambda x: (x['bbox'][2]-x['bbox'][0])*x['bbox'][3]-x['bbox'][1])[-1]
            face_emb = face_info['embedding']
            face_kps = draw_kps(face_image, face_info['kps'])

            image = self.pipe(
                prompt,
                image_embeds=face_emb,
                image=face_kps,
                controlnet_conditioning_scale=0.8,
                ip_adapter_scale=0.8,
            ).images[0]

            return image
        except Exception as e:
            print(f"Error during image generation: {e}")
            return None

