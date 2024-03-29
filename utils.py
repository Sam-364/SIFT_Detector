from typing import List, Tuple

import torch
from PIL import Image  # type: ignore
import torchvision.transforms.v2.functional as TF  # type: ignore
from torchvision.utils import draw_keypoints  # type: ignore


def unormalize_points(image_size: Tuple[int, int], keypoints: torch.Tensor):
    keypoints[..., 0] = (keypoints[..., 0] + 1) * image_size[-1] / 2
    keypoints[..., 1] = (keypoints[..., 1] + 1) * image_size[-2] / 2
    return keypoints


def visualize_keypoints(image, keypoints, color="red", radius=2):
    image = TF.to_dtype(image, dtype=torch.uint8)
    keypoints = unormalize_points(image.shape[-2:], keypoints.clone())
    image = draw_keypoints(image, keypoints, colors=color, radius=radius)
    image = TF.to_pil_image(image)
    return image


def draw_match_lines(image1, image2, kps1, kps2):
    image1 = image1.cpu()
    image2 = image2.cpu()
    kps1 = kps1.cpu()
    kps2 = kps2.cpu()
    kps1 = unormalize_points(image1.shape[-2:], kps1.clone())
    kps2 = unormalize_points(image2.shape[-2:], kps2.clone())
    kps2 = kps2 + torch.tensor([image1.shape[-1], 0])
    all_kps = torch.cat([kps1, kps2], dim=0)
    all_kps = all_kps.unsqueeze(0)
    connectivity = torch.stack(
        [torch.arange(len(kps1)), torch.arange(len(kps2)) + len(kps1)], dim=1
    )
    connectivity = connectivity.tolist()

    side_by_side = torch.cat([image1, image2], dim=-1)
    image = draw_keypoints(side_by_side, all_kps, connectivity, colors="red", radius=2)
    image = TF.to_pil_image(image)
    return image


def draw_transfrom_points(
    index_image,
    query_image,
    H,
    selected_X,
    selected_Y,
):
    padded_X = torch.cat(
        [selected_X, torch.ones(selected_X.shape[0], 1, device=selected_X.device)],
        dim=-1,
    )

    projected_X = torch.matmul(padded_X, H.transpose(-1, -2))
    projected_X = projected_X[..., :2] / projected_X[..., 2:]

    index_image = visualize_keypoints(index_image, selected_X.unsqueeze(0))
    query_image = visualize_keypoints(query_image, selected_Y.unsqueeze(0))
    query_image = TF.pil_to_tensor(query_image)

    query_image = visualize_keypoints(query_image, projected_X, color="blue")
    side_by_side = concat(index_image, query_image, dim=1)
    return side_by_side


def concat(im1, im2, dim=1):
    dest = None
    if dim == 1:
        dest = Image.new("RGB", (im1.width + im2.width, im1.height))
        dest.paste(im1, (0, 0))
        dest.paste(im2, (im1.width, 0))
    else:
        dest = Image.new("RGB", (im1.width, im1.height + im2.height))
        dest.paste(im1, (0, 0))
        dest.paste(im2, (0, im1.height))
    return dest
