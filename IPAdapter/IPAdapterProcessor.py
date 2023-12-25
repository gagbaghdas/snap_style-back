import torch
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline, StableDiffusionInpaintPipeline, DDIMScheduler, AutoencoderKL, ControlNetModel, StableDiffusionControlNetPipeline, UniPCMultistepScheduler, AutoPipelineForInpainting
from PIL import Image
import os
from IPAdapter.ip_adapter.ip_adapter import IPAdapter
import requests
import numpy as np
from diffusers.utils import load_image

class IPAdapterProcessor:
    def __init__(self):
        self.noise_scheduler = DDIMScheduler(
            num_train_timesteps=1000,
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="scaled_linear",
            clip_sample=False,
            set_alpha_to_one=False,
            steps_offset=1,
        )
        self.vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse").to(dtype=torch.float32)
        self.base_model_path =  "runwayml/stable-diffusion-v1-5"
        self.image_encoder_path = "IPAdapter/models/image_encoder/"
        self.ip_ckpt = "IPAdapter/models/ip-adapter_sd15.bin"
        self.device = "cpu"

    def imageVariations(self, initial_image):
        pipe = StableDiffusionPipeline.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float32,
            scheduler=self.noise_scheduler,
            vae=self.vae,
            feature_extractor=None,
            safety_checker=None
        )
        ip_model = IPAdapter(pipe, self.image_encoder_path, self.ip_ckpt, self.device)
        images = ip_model.generate(pil_image=initial_image, num_samples=1, num_inference_steps=30, seed=42)
        for i, img in enumerate(images):
           img.show()

    def img2img(self, initial_image, prompt_image):
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float32,
            scheduler=self.noise_scheduler,
            vae=self.vae,
            feature_extractor=None,
            safety_checker=None
        )
        ip_model = IPAdapter(pipe, self.image_encoder_path, self.ip_ckpt, self.device)
        images = ip_model.generate(pil_image=initial_image, num_samples=1, num_inference_steps=30, seed=42, image=prompt_image, strength=0.6)
        for i, img in enumerate(images):
           img.show()

    def make_inpaint_condition(self, image, image_mask):
        image = np.array(image.convert("RGB")).astype(np.float32) / 255.0
        image_mask = np.array(image_mask.convert("L")).astype(np.float32) / 255.0

        assert image.shape[0:1] == image_mask.shape[0:1]
        image[image_mask > 0.5] = -1.0  # set as masked pixel
        image = np.expand_dims(image, 0).transpose(0, 3, 1, 2)
        image = torch.from_numpy(image)
        return image
    
    def inPaintingUsingIPAdapter(self, initial_image_url, prompt_image_url, mask_image_url):
        
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float32,
            scheduler=self.noise_scheduler,
            vae=self.vae,
            feature_extractor=None,
            safety_checker=None
        )
        
        ip_model = IPAdapter(pipe, self.image_encoder_path, self.ip_ckpt, self.device)
        initial_image = load_image(initial_image_url).resize((512, 768))
        prompt_image = load_image(prompt_image_url).resize((512, 768))
        mask_image = load_image(mask_image_url).resize((512, 768))

        images = ip_model.generate(pil_image=prompt_image, num_samples=1, num_inference_steps=50, seed=42, image=initial_image, mask_image=mask_image, strength=1)
        for i, img in enumerate(images):
            images[i] = img.resize((512, 768))
        return images

    def inPainting(self, initial_image_url, prompt_image_url, mask_image_url, output_dir):
        # load controlnet
        # controlnet_model_path = "lllyasviel/control_v11p_sd15_inpaint"
        # controlnet = ControlNetModel.from_pretrained(controlnet_model_path, torch_dtype=torch.float32)
        # load SD pipeline
        # pipe = StableDiffusionControlNetPipeline.from_pretrained(
        #     self.base_model_path,
        #     controlnet=controlnet,
        #     torch_dtype=torch.float32,
        #     # scheduler=self.noise_scheduler,
        #     # vae=self.vae,
        #     # feature_extractor=None,
        #     # safety_checker=None
        # )
        pipe = AutoPipelineForInpainting.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float32).to("cpu")

        # pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
        # pipe.enable_model_cpu_offload()
        pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models", weight_name="ip-adapter_sd15.bin")
        # pipe = StableDiffusionInpaintPipelineLegacy.from_pretrained(
        #     self.base_model_path,
        #     torch_dtype=torch.float32,
        #     scheduler=self.noise_scheduler,
        #     vae=self.vae,
        #     feature_extractor=None,
        #     safety_checker=None
        # )

        
        # ip_model = IPAdapter(pipe, self.image_encoder_path, self.ip_ckpt, self.device)
        # initial_image = load_image(initial_image_url).resize((512, 768))
        # initial_image.show()
        # prompt_image = load_image(prompt_image_url).resize((512, 768))
        # prompt_image.show()
        # mask_image = load_image(mask_image_url).resize((512, 768))
        # mask_image.show()
        initial_image = load_image("https://huggingface.co/datasets/YiYiXu/testing-images/resolve/main/inpaint_image.png")
        initial_image.show()
        mask_image = load_image("https://huggingface.co/datasets/YiYiXu/testing-images/resolve/main/mask.png")
        mask_image.show()
        prompt_image = load_image("https://i.pinimg.com/736x/4a/7c/2b/4a7c2b3e29cd998ca1e07d685995b888.jpg")
        prompt_image.show()

        initial_image = initial_image.resize((512, 768))
        mask_image = mask_image.resize((512, 768))
        os.makedirs("images/", exist_ok=True)
        # control_image = self.make_inpaint_condition(initial_image, mask_image)

        generator = torch.Generator(device="cpu").manual_seed(33)
        images = pipe(
            prompt='best quality, high quality', 
            image=initial_image,
            ip_adapter_image=prompt_image,
            mask_image=mask_image,
            negative_prompt="lowres, bad anatomy, worst quality, low quality", 
            num_inference_steps=50,
            generator=generator,
            strength=0.5,
        ).images

        # images = ip_model.generate(pil_image=prompt_image, num_samples=1, num_inference_steps=50, seed=42, image=initial_image, mask_image=mask_image, strength=0.7, ip_adapter_image=prompt_image)
        for i, img in enumerate(images):
           img.resize((512, 768)).show()

        # grid = self.image_grid(images, 1, 1)
        # grid.show()
        #grid.save(os.path.join(output_dir, "inPainting.png"))

    # @staticmethod
    # def image_grid(imgs, rows, cols):
    #     assert len(imgs) == rows*cols
    #     w, h = imgs[0].size
    #     grid = Image.new('RGB', size=(cols*w, rows*h))
    #     grid_w, grid_h = grid.size
    #     for i, img in enumerate(imgs):
    #         grid.paste(img, box=(i%cols*w, i//cols*h))
    #     return grid
