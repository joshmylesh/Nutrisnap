import os
from functools import lru_cache
from io import BytesIO

from PIL import Image, UnidentifiedImageError


DEFAULT_MODEL_ID = 'waltertaya/kenyan-food-13'


class InvalidFoodImageError(ValueError):
    pass


@lru_cache(maxsize=2)
def _load_model(model_id):
    import torch
    from transformers import AutoImageProcessor, AutoModelForImageClassification

    processor = AutoImageProcessor.from_pretrained(model_id)
    model = AutoModelForImageClassification.from_pretrained(model_id)
    model.to('cpu')
    model.eval()
    return processor, model, torch


def classify_image(image_bytes, top_k=5):
    model_id = os.environ.get('FOOD_MODEL_ID', DEFAULT_MODEL_ID)
    processor, model, torch = _load_model(model_id)

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            image = source.convert('RGB')
    except (UnidentifiedImageError, OSError) as error:
        raise InvalidFoodImageError('The uploaded file is not a valid image') from error

    inputs = processor(images=image, return_tensors='pt')
    with torch.inference_mode():
        probabilities = model(**inputs).logits[0].softmax(dim=-1)

    scores, indices = probabilities.topk(min(top_k, probabilities.shape[-1]))
    labels = model.config.id2label
    return [
        {
            'label': labels.get(str(index), labels.get(index, str(index))),
            'score': float(score),
        }
        for score, index in zip(scores.tolist(), indices.tolist())
    ]
