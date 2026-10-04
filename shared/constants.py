from shared.schemas import ObjectClass

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
DATA_DIR = "data"
EVIDENCE_DIR = "data/evidence"

COCO_PERSON_NAMES = {"person"}
COCO_VEHICLE_NAMES = {"bicycle", "car", "motorcycle", "bus", "truck", "train", "boat", "airplane"}
COCO_ANIMAL_NAMES = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}

COCO_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed",
    "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

def get_coco_group(name: str) -> ObjectClass:
    name_clean = name.lower()
    if name_clean in COCO_PERSON_NAMES:
        return ObjectClass.PERSON
    elif name_clean in COCO_VEHICLE_NAMES:
        return ObjectClass.VEHICLE
    elif name_clean in COCO_ANIMAL_NAMES:
        return ObjectClass.ANIMAL
    else:
        return ObjectClass.OBJECT

COCO_MAP = {
    idx: (name, get_coco_group(name))
    for idx, name in enumerate(COCO_NAMES)
}

GROUP_COLORS = {
    ObjectClass.PERSON: (0, 255, 0),     # Green (BGR)
    ObjectClass.VEHICLE: (0, 165, 255),  # Orange (BGR)
    ObjectClass.ANIMAL: (0, 255, 255),   # Yellow (BGR)
    ObjectClass.OBJECT: (211, 0, 148),   # Purple (BGR)
}

