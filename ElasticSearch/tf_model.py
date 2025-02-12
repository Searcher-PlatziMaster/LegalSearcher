# import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text
import numpy as np
from os import path


root_folder = "LegalSearcher/SentenceEncoder"
embedd_model = f'{root_folder}/model/'
filepath = path.abspath(path.join('','..', '..',embedd_model))
embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3")


##### EMBEDDING #####
def embed_text(text):
    vectors = embed(text)[0].numpy()
    return [vector.tolist() for vector in vectors]
   
# if __name__ == "__main__":
#     embed = load_model('filepath')