import librosa
import librosa.display
import librosa.feature  
from scipy.signal import resample
import numpy as np
import torch
from torchvision import transforms
from PIL import Image
class CChordRec():
    def __init__(self,path="./model.pth"):
        self.device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model=torch.load(path,weights_only=False)
        self.classes=["c","dm","em","f","g","am"]
        self.preprocess = transforms.Compose([
			transforms.Grayscale(num_output_channels=3),
			transforms.ToTensor(),
			transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
		])
        self.model.eval()
        self.model.to(self.device)
    def normalize_chroma(self,chromagram):
        chromagram_resized = resample(chromagram, 224, axis=1)
        chromagram_resized = resample(chromagram_resized, 224, axis=0)
        min_val = np.min(chromagram_resized)
        max_val = np.max(chromagram_resized)
        chromagram_normalized = (chromagram_resized - min_val) / (max_val - min_val) * 255
        chromagram_uint8 = chromagram_normalized.astype(np.uint8)
        return Image.fromarray(chromagram_uint8)
    def predictChord(self,audio_path):
        audio,sr=librosa.load(audio_path,sr=None)
        chromagram=librosa.feature.chroma_stft(y=audio, sr=sr)
        input=self.preprocess(self.normalize_chroma(chromagram))
        input=input.to(self.device)
        output=self.model(input.unsqueeze(0))
        pred=output.argmax(dim=1,keepdim=True)
        return self.classes[pred.item()]
    def predictProb(self,audio_path):
        audio,sr=librosa.load(audio_path,sr=None)
        chromagram=librosa.feature.chroma_stft(y=audio, sr=sr)
        input=self.preprocess(self.normalize_chroma(chromagram))
        input=input.to(self.device)
        output=self.model(input.unsqueeze(0))
        probs=torch.softmax(output,dim=1)
        result={}
        for i in self.classes:
            result[i]=probs[0][self.classes.index(i)].item()
        return result
if __name__=="__main__":
    obj=CChordRec()
    print(obj.predictChord("./test.wav"))
    print(obj.predictProb("./test.wav"))