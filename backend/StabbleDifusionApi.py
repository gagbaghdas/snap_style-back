import threading
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class SingletonMeta(type):
    """
    A Singleton metaclass that creates only one instance of a class.
    """
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class StableDiffusionApi:
    def __init__(self):
        self.img2imgUrl = 'https://modelslab.com/api/v5/controlnet'
        self.txt2imgUrl = 'https://stablediffusionapi.com/api/v3/txt2img'
        self.headers = {'Content-Type': 'application/json'}
        self.executor = ThreadPoolExecutor()
        self.futures = []
        self.API_KEY = os.getenv("STABLE_DIFFUSION_API_KEY")

    def send_post_request(self):
        """
        Submits a POST request to be sent in parallel. The request is non-blocking.
        Returns a future object representing the execution of the request.
        """
        future = self.executor.submit(self._request)
        self.futures.append(future)
        return future

    def _request(self, url, data):
        """
        Sends a POST request to the specified URL with the provided headers and data.
        """
        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(data))
            response_json = response.json()
            output = response_json.get("output", [])
            return {"status_code" : response.status_code, "output": output}
        except requests.exceptions.RequestException as e:
            return str(e)
        
    def sendImg2ImgRequest(self, data):
        return self._request(self.img2imgUrl, data)
    
    def sendTxt2ImgRequest(self, data):
        return self._request(self.txt2imgUrl, data)
    
    def img2img(self, prompt, negative_prompt, init_image, mask_image, control_image, width, height, samples):
        data = {
            "key": self.API_KEY,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "init_image": init_image,
            "mask_image": mask_image,
            "control_image": control_image,
            "controlnet_model": "inpaint",
            "controlnet_type" :"inpaint",
            "model_id": "ip_adapter",
            "auto_hint": "yes",
            "guess_mode" : "yes",
            "width": width,
            "height": height,
            "samples": samples,
            "num_inference_steps": "30",
            "safety_checker": "no",
            "enhance_prompt": "yes",
            "guidance_scale": 7.5,
            "strength": 0.7,
            "seed": None,
            "base64": "no",
            "webhook": None,
            "track_id": None
        }
        return self.sendImg2ImgRequest(data)

    def get_results(self):
        """
        Waits for all submitted requests to complete and returns their results.
        """
        results = [future.result() for future in as_completed(self.futures)]
        self.futures = []  # Reset the list for future requests
        return results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(wait=False)
