from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsPathItem, QWidget
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap, QUndoStack, QUndoCommand, QPainterPath, QImage
)
from PIL import Image as PILImage
from utils import qimage_to_pil


class DrawCommand(QUndoCommand):
    def __init__(self, scene, path_item):
        super().__init__()
        self.scene = scene
        self.path_item = path_item
    def redo(self):
        self.scene.addItem(self.path_item)
    def undo(self):
        self.scene.removeItem(self.path_item)


class InpaintCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setBackgroundBrush(QBrush(QColor(26, 26, 26)))

        self.base_pixmap_item = QGraphicsPixmapItem()
        self.base_pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.scene.addItem(self.base_pixmap_item)
        self._original_pixmap = None

        self.undo_stack = QUndoStack(self)
        self.brush_size = 20
        self.current_path_item = None
        self.last_point = QPoint()

    def set_base_image(self, pixmap):
        self._original_pixmap = pixmap
        self.base_pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.fitInView(self.base_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.undo_stack.clear()
        for item in self.scene.items():
            if isinstance(item, QGraphicsPathItem):
                self.scene.removeItem(item)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.base_pixmap_item.pixmap() and not self.base_pixmap_item.pixmap().isNull():
            self.fitInView(self.base_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.last_point = scene_pos
            path = QPainterPath()
            path.moveTo(scene_pos)

            self.current_path_item = QGraphicsPathItem()
            self.current_path_item.setPath(path)
            self.current_path_item.setPen(QPen(Qt.GlobalColor.white, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            self.scene.addItem(self.current_path_item)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.current_path_item:
            scene_pos = self.mapToScene(event.pos())
            path = self.current_path_item.path()
            path.lineTo(scene_pos)
            self.current_path_item.setPath(path)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_path_item:
            item = self.current_path_item
            self.current_path_item = None
            self.scene.removeItem(item)
            command = DrawCommand(self.scene, item)
            self.undo_stack.push(command)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                self.undo_stack.undo()
            elif event.key() == Qt.Key.Key_Y:
                self.undo_stack.redo()
        super().keyPressEvent(event)

    def get_mask_pil(self):
        size = self.scene.sceneRect().size().toSize()
        if size.isEmpty(): return PILImage.new("L", (512, 512), 0)

        mask_image = QImage(size, QImage.Format.Format_RGBA8888)
        mask_image.fill(Qt.GlobalColor.black)

        painter = QPainter(mask_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.base_pixmap_item.hide()
        self.scene.render(painter)
        self.base_pixmap_item.show()
        painter.end()

        pil_mask = qimage_to_pil(mask_image).convert("L")
        binary_mask = pil_mask.point(lambda p: 255 if p > 10 else 0)
        binary_mask.save("output/debug_mask.png")
        return binary_mask

    def get_image_pil(self):
        if self._original_pixmap is not None and not self._original_pixmap.isNull():
            return qimage_to_pil(self._original_pixmap.toImage())
        pix = self.base_pixmap_item.pixmap()
        if pix.isNull(): return PILImage.new("RGB", (512, 512), (0,0,0))
        return qimage_to_pil(pix.toImage())
