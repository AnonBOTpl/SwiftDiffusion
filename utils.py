from PyQt6.QtGui import QImage
from PIL import Image as PILImage

def prepare_image_for_img2img(pil_img, target_w, target_h):
    if pil_img.width == target_w and pil_img.height == target_h:
        return pil_img
    ratio = max(target_w / pil_img.width, target_h / pil_img.height)
    new_w = int(pil_img.width * ratio)
    new_h = int(pil_img.height * ratio)
    resized = pil_img.resize((new_w, new_h), PILImage.LANCZOS)
    left = max(0, (new_w - target_w) // 2)
    top = max(0, (new_h - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))

def qimage_to_pil(qimg):
    # Konwersja na format RGBA8888 dla spójności
    if qimg.format() != QImage.Format.Format_RGBA8888:
        qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)

    width = qimg.width()
    height = qimg.height()

    # Zero-Copy: odczyt bajtów bezpośrednio z pamięci QImage
    ptr = qimg.bits()
    ptr.setsize(qimg.sizeInBytes())
    arr = ptr.asstring()

    return PILImage.frombytes("RGBA", (width, height), arr, "raw", "RGBA").convert("RGB")

def pil_to_qimage(pil_img):
    # Konwersja na RGBA
    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")

    width, height = pil_img.size
    bytes_data = pil_img.tobytes("raw", "RGBA")

    # Tworzenie QImage z bajtów
    qim = QImage(bytes_data, width, height, QImage.Format.Format_RGBA8888)

    # WAŻNE: Zachowanie referencji do bajtów, aby uniknąć SegFault (GC)
    qim.bytes_ref = bytes_data
    return qim
