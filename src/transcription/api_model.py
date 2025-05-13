import os
import json
from groq import Groq


class ApiModel():
  def __init__(
    self, 
    model_name="whisper-large-v3", 
    prompt=None, 
    response_format="verbose_json", 
    timestamp_granularities=["segment"], 
    language=None, 
    temperature=None, 
    return_text_only=False
    ):
    self.model_name=model_name
    self.response_format = response_format
    self.timestamp_granularities = timestamp_granularities
    self.language = language
    self.temperature = temperature
    self.return_text_only = return_text_only

    if prompt is None:
      self.prompt = "You are translating podcasts held in Italian in which one or more speakers are talking. Please transcribe the audio in Italian."

  
  def transcribe(self, filename, return_text_only=None):
    client = Groq()

    if return_text_only is None:
      return_text_only = self.return_text_only
    
    with open(filename, "rb") as file:
        transcription = client.audio.transcriptions.create(
          file=(filename, file.read()),
          model=self.model_name,
          prompt=self.prompt,
          response_format=self.response_format,
          timestamp_granularities = self.timestamp_granularities, #["word", "segment"], # Optional (must set response_format to "json" to use and can specify "word", "segment" (default), or both)
          language=self.language,  # Optional
          temperature=self.temperature  # Optional
          )

    if self.return_text_only:
      return transcription.text
    else:
      return json.dumps(transcription, indent=2, default=str)
      