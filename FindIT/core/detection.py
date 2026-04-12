from functools import lru_cache
from pathlib import Path
import logging
import re
import tempfile

from ultralytics import YOLO

from .models import FoundItem


logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parents[1] / 'models' / 'ObjectDetectionModel' / 'my_model.pt'

CATEGORY_LABELS = dict(FoundItem.CATEGORY_CHOICES)

LABEL_TO_CATEGORY = {
    'backpack': 'bags',
    'bag': 'bags',
    'handbag': 'bags',
    'suitcase': 'bags',
    'bottle': 'bottle',
    'wallet': 'wallet',
    'keys': 'keys',
    'document': 'documents',
    'book': 'stationery',
    'note-book': 'stationery',
    'notebook': 'stationery',
    'pen': 'stationery',
    'pencil': 'stationery',
    'eraser': 'stationery',
    'ruler': 'stationery',
    'calculator': 'stationery',
    'sharpener': 'stationery',
    'scissors': 'stationery',
    'necklace': 'jewellery',
    'ring': 'jewellery',
    'pierce': 'jewellery',
    'watch': 'jewellery',
    'smartwatch': 'jewellery',
    'cell phone': 'electronics',
    'laptop': 'electronics',
    'charger': 'electronics',
    'keyboard': 'electronics',
    'mouse': 'electronics',
    'remote': 'electronics',
    'tvmonitor': 'electronics',
    'plug': 'electronics',
    'socket': 'electronics',
    'cable': 'electronics',
    'headphones': 'electronics',
    'flashdrive': 'electronics',
    'clothes top': 'clothing',
    'coat': 'clothing',
    'padded jacket': 'clothing',
    'pants': 'clothing',
    'skirt': 'clothing',
    'shoe': 'clothing',
    'shoes': 'clothing',
    'tie': 'clothing',
}

KEYWORD_TO_CATEGORY = {
    'book': 'stationery',
    'note': 'stationery',
    'pen': 'stationery',
    'pencil': 'stationery',
    'eraser': 'stationery',
    'ruler': 'stationery',
    'sharpener': 'stationery',
    'scissor': 'stationery',
    'calculator': 'stationery',
    'document': 'documents',
    'id': 'documents',
    'key': 'keys',
    'wallet': 'wallet',
    'bottle': 'bottle',
    'bag': 'bags',
    'backpack': 'bags',
    'suitcase': 'bags',
    'handbag': 'bags',
    'necklace': 'jewellery',
    'ring': 'jewellery',
    'pierce': 'jewellery',
    'earring': 'jewellery',
    'watch': 'jewellery',
    'phone': 'electronics',
    'laptop': 'electronics',
    'charger': 'electronics',
    'keyboard': 'electronics',
    'mouse': 'electronics',
    'remote': 'electronics',
    'headphone': 'electronics',
    'flashdrive': 'electronics',
    'cable': 'electronics',
    'plug': 'electronics',
    'socket': 'electronics',
    'shirt': 'clothing',
    'coat': 'clothing',
    'jacket': 'clothing',
    'pant': 'clothing',
    'skirt': 'clothing',
    'shoe': 'clothing',
    'tie': 'clothing',
}


def _normalize_label(raw_label):
    normalized = raw_label.lower().strip()
    normalized = normalized.replace('-', ' ').replace('_', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def _map_label_to_category(raw_label):
    normalized = _normalize_label(raw_label)

    direct_category = LABEL_TO_CATEGORY.get(normalized)
    if direct_category:
        return direct_category

    singular = normalized[:-1] if normalized.endswith('s') else normalized
    direct_singular = LABEL_TO_CATEGORY.get(singular)
    if direct_singular:
        return direct_singular

    for keyword, category in KEYWORD_TO_CATEGORY.items():
        if keyword in normalized or keyword in singular:
            return category

    return None


@lru_cache(maxsize=1)
def get_detection_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f'Detection model not found at {MODEL_PATH}')
    return YOLO(str(MODEL_PATH))


def detect_item_category(uploaded_image):
    model = get_detection_model()

    suffix = Path(getattr(uploaded_image, 'name', '')).suffix or '.jpg'
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_file.name)

    try:
        if hasattr(uploaded_image, 'seek'):
            uploaded_image.seek(0)

        for chunk in uploaded_image.chunks():
            temp_file.write(chunk)
        temp_file.flush()
        temp_file.close()

        result = model.predict(source=str(temp_path), verbose=False)[0]
        boxes = list(result.boxes) if getattr(result, 'boxes', None) is not None else []

        detections = []
        for box in boxes:
            class_id = int(box.cls[0])
            raw_label = str(result.names.get(class_id, '')).strip()
            confidence = float(box.conf[0])
            category_value = _map_label_to_category(raw_label)
            detections.append((confidence, raw_label, category_value))

        detections.sort(key=lambda item: item[0], reverse=True)

        if not detections:
            return {
                'raw_label': None,
                'confidence': 0.0,
                'category_value': 'other',
                'category_label': CATEGORY_LABELS.get('other', 'Other'),
                'message': 'No item could be detected. Category set to Other.',
            }

        selected_confidence, selected_label, selected_category = next(
            ((confidence, label, category) for confidence, label, category in detections if category),
            detections[0],
        )
        category_value = selected_category or 'other'
        category_label = CATEGORY_LABELS.get(category_value, CATEGORY_LABELS.get('other', 'Other'))

        if category_value == 'other':
            message = f'Detected {selected_label}. Category set to Other.'
        else:
            message = f'Detected {selected_label}. Category set to {category_label}.'

        return {
            'raw_label': selected_label,
            'confidence': selected_confidence,
            'category_value': category_value,
            'category_label': category_label,
            'message': message,
        }
    except Exception:
        logger.exception('Failed to detect item category from uploaded image')
        return {
            'raw_label': None,
            'confidence': 0.0,
            'category_value': 'other',
            'category_label': CATEGORY_LABELS.get('other', 'Other'),
            'message': 'Auto-detection failed. Category set to Other.',
        }
    finally:
        if hasattr(uploaded_image, 'seek'):
            try:
                uploaded_image.seek(0)
            except Exception:
                pass

        try:
            temp_file.close()
        except Exception:
            pass
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)