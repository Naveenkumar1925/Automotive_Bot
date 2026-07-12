import torch
import torchvision.transforms as T
from PIL import Image
import sys
from model import CarModel
import config

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

labels = torch.load(config.LABELS_SAVE_PATH)

inv_brand = {v:k for k,v in labels["brand"].items()}
inv_model = {v:k for k,v in labels["model"].items()}
inv_year = {v:k for k,v in labels["year"].items()}
inv_color = {v:k for k,v in labels["color"].items()}

model = CarModel(
    len(inv_brand),
    len(inv_model),
    len(inv_year),
    len(inv_color)
).to(device)

model.load_state_dict(torch.load(config.MODEL_SAVE_PATH))
model.eval()

img = Image.open(sys.argv[1]).convert("RGB")


transform = T.Compose([
    T.Resize((config.IMAGE_SIZE, config.IMAGE_SIZE)),
    T.ToTensor()
])

x = transform(img).unsqueeze(0).to(device)

with torch.no_grad():
    b,m,y,c = model(x)

print("Brand:", inv_brand[b.argmax().item()])
print("Model:", inv_model[m.argmax().item()])
print("Year:", inv_year[y.argmax().item()])
print("Color:", inv_color[c.argmax().item()])

#python predict.py 'A:\automobile\1\resized_DVM\BMW\1 Series\2004\Blue\BMW$$1 Series$$2004$$Blue$$8_1$$46$$image_0.jpg'
#python predict.py 'A:\automobile\1\resized_DVM\BMW\1 Series\2008\Brown\BMW$$1 Series$$2008$$Brown$$8_1$$373$$image_1.jpg'