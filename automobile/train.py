import torch
from torch.utils.data import DataLoader
import torchvision.transforms as T
from dataset import CarDataset
from model import CarModel
import config
from tqdm import tqdm
import os
import glob

os.makedirs(config.CHECKPOINT_DIR, exist_ok=True)

def save_checkpoint(model, optimizer, epoch, best_loss):

    save_path = f"{config.CHECKPOINT_DIR}/epoch_{epoch}.pt"

    torch.save({
        "epoch": epoch,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "best_loss": best_loss
    }, save_path)

    print(f"Saved checkpoint: {save_path}")

def load_latest_checkpoint(model, optimizer):

    import glob

    checkpoint_files = glob.glob(f"{config.CHECKPOINT_DIR}/epoch_*.pt")

    if len(checkpoint_files) == 0:
        print("No checkpoint found — starting fresh")
        return 0, float("inf")

    latest = max(
        checkpoint_files,
        key=lambda x: int(x.split("_")[-1].replace(".pt",""))
    )

    print(f"Resuming from {latest}")

    checkpoint = torch.load(latest)

    model.load_state_dict(checkpoint["model_state"])
    optimizer.load_state_dict(checkpoint["optimizer_state"])

    start_epoch = checkpoint.get("epoch", 0)

    # 🔥 Safe fallback if best_loss not present
    best_loss = checkpoint.get("best_loss", float("inf"))

    return start_epoch, best_loss

def main():

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.backends.cudnn.benchmark = True

    transform = T.Compose([
        T.Resize((config.IMAGE_SIZE, config.IMAGE_SIZE)),
        T.ToTensor()
    ])

    dataset = CarDataset(config.DATASET_PATH, transform)

    loader = DataLoader(
        dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )

    model = CarModel(
        len(dataset.brand_to_idx),
        len(dataset.model_to_idx),
        len(dataset.year_to_idx),
        len(dataset.color_to_idx)
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=config.LR)
    criterion = torch.nn.CrossEntropyLoss()

    scaler = torch.amp.GradScaler("cuda")

    start_epoch, best_loss = load_latest_checkpoint(model, optimizer)

    for epoch in range(start_epoch, config.EPOCHS):

        model.train()
        running_loss = 0

        loop = tqdm(loader, desc=f"Epoch [{epoch+1}/{config.EPOCHS}]")

        for imgs,b,m,y,c in loop:

            imgs = imgs.to(device, non_blocking=True)
            b,m,y,c = b.to(device),m.to(device),y.to(device),c.to(device)

            optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast("cuda"):
                pb,pm,py,pc = model(imgs)

                loss = (
                    criterion(pb,b) +
                    criterion(pm,m) +
                    criterion(py,y) +
                    criterion(pc,c)
                )

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            loop.set_postfix(loss=loss.item())

        torch.cuda.synchronize()

        avg_loss = running_loss / len(loader)
        print(f"Epoch {epoch+1} Avg Loss: {avg_loss:.4f}")

        save_checkpoint(model, optimizer, epoch+1, best_loss)

        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), config.MODEL_SAVE_PATH)
            print("Best model updated")

    torch.save({
        "brand": dataset.brand_to_idx,
        "model": dataset.model_to_idx,
        "year": dataset.year_to_idx,
        "color": dataset.color_to_idx
    }, config.LABELS_SAVE_PATH)

    print("Training Complete")


if __name__ == "__main__":
    main()