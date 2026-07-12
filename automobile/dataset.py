import os
from torch.utils.data import Dataset
from PIL import Image

class CarDataset(Dataset):

    def __init__(self, root, transform=None):
        self.samples = []
        self.transform = transform

        brands, models, years, colors = set(), set(), set(), set()

        for brand in os.listdir(root):
            brand_path = os.path.join(root, brand)
            if not os.path.isdir(brand_path): continue

            for model in os.listdir(brand_path):
                model_path = os.path.join(brand_path, model)
                if not os.path.isdir(model_path): continue

                for year in os.listdir(model_path):
                    year_path = os.path.join(model_path, year)
                    if not os.path.isdir(year_path): continue

                    for color in os.listdir(year_path):
                        color_path = os.path.join(year_path, color)
                        if not os.path.isdir(color_path): continue

                        for img in os.listdir(color_path):
                            path = os.path.join(color_path, img)

                            self.samples.append((path, brand, model, year, color))

                            brands.add(brand)
                            models.add(model)
                            years.add(year)
                            colors.add(color)

        self.brand_to_idx = {v:i for i,v in enumerate(sorted(brands))}
        self.model_to_idx = {v:i for i,v in enumerate(sorted(models))}
        self.year_to_idx = {v:i for i,v in enumerate(sorted(years))}
        self.color_to_idx = {v:i for i,v in enumerate(sorted(colors))}

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, brand, model, year, color = self.samples[idx]

        img = Image.open(path).convert("RGB")

        if self.transform:
            img = self.transform(img)

        return (
            img,
            self.brand_to_idx[brand],
            self.model_to_idx[model],
            self.year_to_idx[year],
            self.color_to_idx[color]
        )