import os
import subprocess
import threading
from werkzeug.utils import secure_filename

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

class ImageProcessor(metaclass=SingletonMeta):
    def __init__(self):
        self.input_dir = "closes-segmentation/input"
        self.output_dir = "closes-segmentation/output"
        self.process_script_path = "closes-segmentation/process.py"
        self.lock = threading.Lock()

    def save_image(self, image, filename):
        """
        Saves the uploaded image data to the input directory.
        Ensures the input directory exists before saving.
        """
        with self.lock:  # Ensure that saving is thread-safe
            # Create the input directory if it doesn't exist
            os.makedirs(self.input_dir, exist_ok=True)

            filename = secure_filename(filename)
            input_path = os.path.join(self.input_dir, filename)
            image.save(input_path)
            # with open(input_path, 'wb') as image_file:
            #     image_file.write(image_data)
            return input_path


    def process_image(self, input_path, user_id):
        """
        Processes the image by invoking the external script in a non-blocking manner.
        """
        # Start a new thread to handle the image processing
        thread = threading.Thread(target=self._run_processing_script, args=(input_path,user_id))
        thread.start()
        thread.join()
        return thread

    def _run_processing_script(self, input_path, user_id):
        """
        The actual method that runs the processing script.
        """
        command = f'python3 {self.process_script_path} --image {input_path} --user_id {user_id}'
        subprocess.run(command, shell=True)

    def get_processed_images(self):
        """
        Retrieves the paths of the processed images from the output directory.
        """
        with self.lock:  # Ensure that access to the output directory is thread-safe
            return [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir) if f.endswith('.jpg') or f.endswith('.png')]
