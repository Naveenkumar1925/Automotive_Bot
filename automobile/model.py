import torch.nn as nn
import torchvision.models as models

class CarModel(nn.Module):

    def __init__(self, nb, nm, ny, nc):
        super().__init__()

        base = models.convnext_tiny(weights="DEFAULT")
        self.backbone = base.features
        self.pool = nn.AdaptiveAvgPool2d((1,1))

        in_features = 768

        self.brand_head = nn.Linear(in_features, nb)
        self.model_head = nn.Linear(in_features, nm)
        self.year_head = nn.Linear(in_features, ny)
        self.color_head = nn.Linear(in_features, nc)

    def forward(self,x):

        f = self.backbone(x)
        f = self.pool(f)
        f = f.view(f.size(0), -1)

        return (
            self.brand_head(f),
            self.model_head(f),
            self.year_head(f),
            self.color_head(f)
        )