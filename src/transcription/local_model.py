import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import time


class Model:
    def __init__(self, model_name):
        self.model_name = model_name
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f'Using device: {device}')
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    def load_model(self):
        self.processor = AutoProcessor.from_pretrained(self.model_name)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        ).to(device)

        self.model.generation_config.language = "<|it|>"

        # Create a pipeline for preprocessing and transcribing speech data
        self.pipeline = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=device,
        )

        print(f"Loaded model: {self.model_name}")

    def transcribe(self, audio_samples):

        start = time.monotonic_ns()
        print(f"Transcribing {len(audio_samples)} audio samples")
        transcriptions = self.pipeline(audio_samples, batch_size=len(audio_samples), return_timestamps=True)
        end = time.monotonic_ns()
        print(
            f"Transcribed {len(audio_samples)} samples in {round((end - start) / 1e9, 2)}s"
        )
        return transcriptions

