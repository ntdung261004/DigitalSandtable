# File: src/ui/components/canvas.py

import math
from PySide6.QtWidgets import QGraphicsView, QGraphicsPathItem, QMessageBox, QGraphicsItem, QStyle
from PySide6.QtGui import QPainter, QColor, QWheelEvent, QPen, QPainterPath, QBrush, QTransform, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRectF, QPointF

class DraggableShape(QGraphicsPathItem):
    def __init__(self, shape_type, w, h, pen, brush=None, initial_path=None, main_window=None):
        super().__init__()
        self.shape_type = shape_type
        self.w = w
        self.h = h
        self.main_window = main_window
        self.setPen(pen)
        self.setBrush(brush if brush else QBrush(Qt.BrushStyle.NoBrush))
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        self.interaction_mode = None
        self.action_info = ""

        # Hệ thống Tag (Nhãn)
        self.has_tag = False
        self.tag_text = "Tên Nhãn"
        self.tag_pos = 'b' 
        self.tag_bg = "#e67e22"
        self.tag_fg = "#ffffff"
        self.tag_size = 12
        self.tag_offset = 8 
        self.tag_rect_cache = None

        self.orig_w = w
        self.orig_h = h
        self.orig_pos = QPointF(0, 0)
        self.start_mouse_scene = QPointF(0, 0)

        if self.shape_type == "draw" and initial_path:
            self.orig_drawn_path = initial_path
            rect = initial_path.boundingRect()
            self.w = max(10, rect.width())
            self.h = max(10, rect.height())
            self.orig_w = self.w
            self.orig_h = self.h
            self.update_path()
        else:
            self.update_path()

    def update_path(self):
        self.prepareGeometryChange() 
        path = QPainterPath()
        rect = QRectF(-self.w/2, -self.h/2, self.w, self.h)

        if self.shape_type == "line":
            path.moveTo(-self.w/2, 0); path.lineTo(self.w/2, 0)
        elif self.shape_type == "draw":
            if hasattr(self, 'orig_drawn_path') and self.orig_drawn_path:
                orig_rect = self.orig_drawn_path.boundingRect()
                if orig_rect.width() > 0.1 and orig_rect.height() > 0.1:
                    sx = self.w / orig_rect.width()
                    sy = self.h / orig_rect.height()
                    transform = QTransform().scale(sx, sy)
                    translated_path = self.orig_drawn_path.translated(-orig_rect.center())
                    path = transform.map(translated_path)
        elif self.shape_type == "rect": path.addRect(rect)
        elif self.shape_type == "ellipse": path.addEllipse(rect)
        elif self.shape_type == "triangle":
            path.moveTo(0, rect.top()); path.lineTo(rect.right(), rect.bottom()); path.lineTo(rect.left(), rect.bottom()); path.closeSubpath()
        elif self.shape_type == "diamond":
            path.moveTo(0, rect.top()); path.lineTo(rect.right(), 0); path.lineTo(0, rect.bottom()); path.lineTo(rect.left(), 0); path.closeSubpath()
        elif self.shape_type == "pentagon":
            path.moveTo(0, rect.top()); path.lineTo(rect.right(), rect.top() + rect.height() * 0.4)
            path.lineTo(rect.left() + rect.width() * 0.8, rect.bottom()); path.lineTo(rect.left() + rect.width() * 0.2, rect.bottom())
            path.lineTo(rect.left(), rect.top() + rect.height() * 0.4); path.closeSubpath()
        elif self.shape_type == "hexagon": 
            path.moveTo(0, rect.top()); path.lineTo(rect.right(), rect.top() + rect.height() * 0.25)
            path.lineTo(rect.right(), rect.bottom() - rect.height() * 0.25); path.lineTo(0, rect.bottom())
            path.lineTo(rect.left(), rect.bottom() - rect.height() * 0.25); path.lineTo(rect.left(), rect.top() + rect.height() * 0.25); path.closeSubpath()
        elif self.shape_type == "star":
            path.moveTo(0, rect.top()); path.lineTo(rect.left() + rect.width()*0.65, rect.bottom())
            path.lineTo(rect.left(), rect.top() + rect.height()*0.38); path.lineTo(rect.right(), rect.top() + rect.height()*0.38)
            path.lineTo(rect.left() + rect.width()*0.35, rect.bottom()); path.closeSubpath()
        
        self.setPath(path)
        self.setTransformOriginPoint(0, 0)

    def shape(self):
        path = QPainterPath()
        rect = QRectF(-self.w/2, -self.h/2, self.w, self.h)
        if self.shape_type == 'draw': rect = self.path().boundingRect()
        
        if self.shape_type == 'line': path.addRect(rect.adjusted(-20, -30, 20, 50))
        else: path.addRect(rect.adjusted(-15, -15, 15, 45))
        
        if self.has_tag and self.tag_rect_cache:
            path.addRect(self.tag_rect_cache)
            
        return path

    def get_handle_rects(self):
        rect = QRectF(-self.w/2, -self.h/2, self.w, self.h)
        if self.shape_type == 'draw': rect = self.path().boundingRect()
        
        c = 12         
        ew, eh = 14, 6 
        
        handles = { 'rotate': QRectF(-c/2, rect.bottom() + 20, c, c) }
        
        if self.shape_type == "line":
            handles['l'] = QRectF(rect.left() - c/2, -c/2, c, c)
            handles['r'] = QRectF(rect.right() - c/2, -c/2, c, c)
        else:
            handles.update({
                'tl': QRectF(rect.left() - c/2, rect.top() - c/2, c, c),
                'tr': QRectF(rect.right() - c/2, rect.top() - c/2, c, c),
                'bl': QRectF(rect.left() - c/2, rect.bottom() - c/2, c, c),
                'br': QRectF(rect.right() - c/2, rect.bottom() - c/2, c, c),
                't': QRectF(0 - ew/2, rect.top() - eh/2, ew, eh),
                'b': QRectF(0 - ew/2, rect.bottom() - eh/2, ew, eh),
                'l': QRectF(rect.left() - eh/2, 0 - ew/2, eh, ew),
                'r': QRectF(rect.right() - eh/2, 0 - ew/2, eh, ew)
            })
        return handles

    def boundingRect(self):
        rect = super().boundingRect()
        return rect.adjusted(-150, -150, 150, 150)

    def paint(self, painter, option, widget=None):
        option.state &= ~QStyle.State_Selected
        super().paint(painter, option, widget)
        
        # --- VẼ TAG (NHÃN) ---
        if self.has_tag:
            font = QFont("Arial", self.tag_size)
            font.setBold(True)
            fm = QFontMetrics(font)
            tw = fm.horizontalAdvance(self.tag_text) + 16
            th = fm.height() + 8
            
            handles = self.get_handle_rects()
            anchor_pos = handles.get(self.tag_pos, handles.get('b', QRectF(0,0,0,0))).center()
            
            off_x, off_y = 0, 0
            if 't' in self.tag_pos: off_y = -th - self.tag_offset
            elif 'b' in self.tag_pos: off_y = self.tag_offset
            if 'l' in self.tag_pos: off_x = -tw - self.tag_offset
            elif 'r' in self.tag_pos: off_x = self.tag_offset
            
            tag_rect = QRectF(anchor_pos.x() + off_x - tw/2, anchor_pos.y() + off_y - th/2, tw, th)
            self.tag_rect_cache = tag_rect 
            
            painter.setBrush(QColor(self.tag_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(tag_rect, 4, 4)
            
            painter.setPen(QColor(self.tag_fg))
            painter.setFont(font)
            painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, self.tag_text)

        # --- VẼ KHUNG CHỌN ---
        if self.isSelected():
            rect = QRectF(-self.w/2, -self.h/2, self.w, self.h)
            if self.shape_type == 'draw': rect = self.path().boundingRect()
            
            handles = self.get_handle_rects()
            
            if self.shape_type == 'line':
                painter.setPen(QPen(QColor("#8e44ad"), 1.2, Qt.PenStyle.DashLine))
                painter.drawLine(rect.left(), 0, rect.right(), 0)
            else:
                painter.setPen(QPen(QColor("#8e44ad"), 1.2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
            
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(QPen(QColor("#8e44ad"), 1.2))
            
            for key, h_rect in handles.items():
                if key in ['tl', 'tr', 'bl', 'br', 'rotate']:
                    painter.drawEllipse(h_rect)
                elif key in ['l', 'r']:
                    if self.shape_type == 'line': painter.drawEllipse(h_rect)
                    else: painter.drawRoundedRect(h_rect, 2, 2)
                elif key in ['t', 'b']:
                    painter.drawRoundedRect(h_rect, 2, 2)
                    
            if self.shape_type == 'line':
                painter.drawLine(0, 0, 0, rect.bottom() + 20)
            else:
                painter.drawLine(0, rect.bottom(), 0, rect.bottom() + 20)

    def hoverMoveEvent(self, event):
        if self.isSelected():
            pos = event.pos()
            handles = self.get_handle_rects()
            if self.has_tag and self.tag_rect_cache and self.tag_rect_cache.contains(pos):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            elif 'br' in handles and (handles['br'].contains(pos) or handles['tl'].contains(pos)): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif 'tr' in handles and (handles['tr'].contains(pos) or handles['bl'].contains(pos)): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif 't' in handles and (handles['t'].contains(pos) or handles['b'].contains(pos)): self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif 'l' in handles and (handles['l'].contains(pos) or handles['r'].contains(pos)): 
                self.setCursor(Qt.CursorShape.SizeAllCursor if self.shape_type == "line" else Qt.CursorShape.SizeHorCursor)
            elif 'rotate' in handles and handles['rotate'].contains(pos): self.setCursor(Qt.CursorShape.PointingHandCursor)
            else: self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
            if self.has_tag and self.tag_rect_cache and self.tag_rect_cache.contains(pos):
                if not self.isSelected():
                    self.scene().clearSelection()
                    self.setSelected(True)
                
                self.interaction_mode = 'drag_tag'
                event.accept()
                return

            if self.isSelected():
                handles = self.get_handle_rects()
                for key, rect in handles.items():
                    if rect.contains(pos):
                        self.interaction_mode = key
                        self.orig_w = self.w
                        self.orig_h = self.h
                        self.orig_pos = self.scenePos()
                        self.start_mouse_scene = event.scenePos() 
                        
                        if self.shape_type == "line":
                            if key == 'r': self.fixed_scene_pos = self.mapToScene(QPointF(-self.w/2, 0))
                            elif key == 'l': self.fixed_scene_pos = self.mapToScene(QPointF(self.w/2, 0))

                        event.accept()
                        return
        
        self.interaction_mode = 'move'
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.interaction_mode == 'drag_tag':
            self.prepareGeometryChange()
            pos = event.pos()
            handles = self.get_handle_rects()
            min_dist = float('inf')
            best_snap = self.tag_pos
            for key in ['tl', 't', 'tr', 'l', 'r', 'bl', 'b', 'br']:
                if key in handles:
                    h_center = handles[key].center()
                    dist = math.hypot(h_center.x() - pos.x(), h_center.y() - pos.y())
                    if dist < min_dist:
                        min_dist = dist
                        best_snap = key
            
            self.tag_pos = best_snap
            self.update()
            event.accept()
            return

        if self.shape_type == "line" and self.interaction_mode in ['l', 'r']:
            self.prepareGeometryChange()
            dragged_scene_pos = event.scenePos()
            
            dx = dragged_scene_pos.x() - self.fixed_scene_pos.x()
            dy = dragged_scene_pos.y() - self.fixed_scene_pos.y()
            
            length = math.hypot(dx, dy)
            angle = math.degrees(math.atan2(dy, dx))
            
            if self.interaction_mode == 'l': angle += 180
                
            new_center_x = (self.fixed_scene_pos.x() + dragged_scene_pos.x()) / 2
            new_center_y = (self.fixed_scene_pos.y() + dragged_scene_pos.y()) / 2
            
            self.w = max(5.0, length)
            self.update_path()
            self.setRotation(angle)
            self.setPos(new_center_x, new_center_y)
            
            self.action_info = f"↔ {int(self.w)}px | ↻ {int(angle % 360)}°"
            self.notify_active()
            event.accept()
            return

        if self.interaction_mode in ['tl', 'tr', 'bl', 'br', 't', 'b', 'l', 'r']:
            self.prepareGeometryChange()
            
            current_mouse_scene = event.scenePos()
            delta_x_scene = current_mouse_scene.x() - self.start_mouse_scene.x()
            delta_y_scene = current_mouse_scene.y() - self.start_mouse_scene.y()
            
            angle_rad = math.radians(-self.rotation())
            dx = delta_x_scene * math.cos(angle_rad) - delta_y_scene * math.sin(angle_rad)
            dy = delta_x_scene * math.sin(angle_rad) + delta_y_scene * math.cos(angle_rad)
            
            new_w, new_h = self.orig_w, self.orig_h
            
            if 'r' in self.interaction_mode: new_w = self.orig_w + dx
            if 'l' in self.interaction_mode: new_w = self.orig_w - dx
            if 'b' in self.interaction_mode: new_h = self.orig_h + dy
            if 't' in self.interaction_mode: new_h = self.orig_h - dy

            if new_w >= 10 and new_h >= 10:
                self.w = new_w
                self.h = new_h
                self.update_path()
                
                shift_x, shift_y = 0.0, 0.0
                if self.interaction_mode == 'r': shift_x = dx / 2
                elif self.interaction_mode == 'l': shift_x = dx / 2
                elif self.interaction_mode == 'b': shift_y = dy / 2
                elif self.interaction_mode == 't': shift_y = dy / 2
                elif self.interaction_mode == 'br':
                    scale_w = new_w / self.orig_w; scale_h = new_h / self.orig_h
                    shift_x = (new_w - self.orig_w) / 2; shift_y = (new_h - self.orig_h) / 2
                elif self.interaction_mode == 'tl':
                    shift_x = -(new_w - self.orig_w) / 2; shift_y = -(new_h - self.orig_h) / 2
                elif self.interaction_mode == 'tr':
                    shift_x = (new_w - self.orig_w) / 2; shift_y = -(new_h - self.orig_h) / 2
                elif self.interaction_mode == 'bl':
                    shift_x = -(new_w - self.orig_w) / 2; shift_y = (new_h - self.orig_h) / 2

                rot_rad = math.radians(self.rotation())
                scene_dx = shift_x * math.cos(rot_rad) - shift_y * math.sin(rot_rad)
                scene_dy = shift_x * math.sin(rot_rad) + shift_y * math.cos(rot_rad)
                self.setPos(self.orig_pos.x() + scene_dx, self.orig_pos.y() + scene_dy)

            self.action_info = f"↔ {int(self.w)} x {int(self.h)}"
            self.notify_active()
            event.accept()
            
        elif self.interaction_mode == 'rotate':
            center_scene = self.scenePos()
            mouse_scene = event.scenePos()
            dx = mouse_scene.x() - center_scene.x()
            dy = mouse_scene.y() - center_scene.y()
            angle = math.degrees(math.atan2(dy, dx)) - 90
            self.setRotation(angle)
            self.action_info = f"↻ {int(angle % 360)}°"
            self.notify_active()
            event.accept()
            
        else:
            super().mouseMoveEvent(event)
            self.action_info = f"X: {int(self.scenePos().x())} | Y: {int(self.scenePos().y())}"
            self.notify_active()

    def mouseReleaseEvent(self, event):
        self.interaction_mode = None
        self.action_info = ""
        if self.main_window:
            self.main_window.update_right_panel_from_item(self)
        self.scene().update()
        super().mouseReleaseEvent(event)

    def notify_active(self):
        if self.main_window:
            self.main_window.view.active_item = self
            self.main_window.update_right_panel_from_item(self)
            if hasattr(self.main_window, 'update_quick_action_bar_pos'):
                self.main_window.update_quick_action_bar_pos(self)
        self.scene().update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.main_window:
            self.main_window.update_right_panel_from_item(self)
            if hasattr(self.main_window, 'update_quick_action_bar_pos'):
                self.main_window.update_quick_action_bar_pos(self)
        return super().itemChange(change, value)


class InteractiveMapView(QGraphicsView):
    def __init__(self, scene, main_window=None, is_projector=False, parent=None):
        super().__init__(scene, parent)
        self.main_window = main_window 
        self.is_projector = is_projector
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) 
        
        self.grid_size = 100 
        self.show_grid = False
        self.select_region_mode = False
        self.selection_start_pos = None

        self.current_tool = "cursor" 
        self.is_drawing_freehand = False
        self.current_draw_item = None
        self.current_path = None
        self.active_item = None 

    def wheelEvent(self, event: QWheelEvent):
        if self.is_projector: return 
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        if event.angleDelta().y() > 0: self.scale(zoom_in_factor, zoom_in_factor)
        else: self.scale(zoom_out_factor, zoom_out_factor)
        
        if self.main_window and self.active_item and self.active_item.isSelected():
            if hasattr(self.main_window, 'update_quick_action_bar_pos'):
                self.main_window.update_quick_action_bar_pos(self.active_item)

    def mousePressEvent(self, event):
        if not self.is_projector and event.button() == Qt.MouseButton.LeftButton:
            if self.select_region_mode:
                self.selection_start_pos = self.mapToScene(event.pos())
                super().mousePressEvent(event)
                return
            
            if self.current_tool == "cursor":
                item = self.itemAt(event.pos())
                if item or self.scene().selectedItems():
                    self.setDragMode(QGraphicsView.DragMode.NoDrag)
                else:
                    self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            
            if self.current_tool == "draw":
                if self.main_window and hasattr(self.main_window, 'quick_action_bar'):
                    self.main_window.quick_action_bar.hide()
                    
                self.is_drawing_freehand = True
                self.draw_start_pos = self.mapToScene(event.pos())
                pen = QPen(QColor("#bdc3c7")) 
                pen.setWidth(3); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                self.current_path = QPainterPath(self.draw_start_pos)
                self.current_draw_item = self.scene().addPath(self.current_path, pen)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing_freehand and self.current_draw_item:
            self.current_path.lineTo(self.mapToScene(event.pos()))
            self.current_draw_item.setPath(self.current_path)
            event.accept()
            return
            
        super().mouseMoveEvent(event)
        
        if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag and event.buttons() == Qt.MouseButton.LeftButton:
            if self.main_window and self.active_item and self.active_item.isSelected():
                if hasattr(self.main_window, 'update_quick_action_bar_pos'):
                    self.main_window.update_quick_action_bar_pos(self.active_item)

    def mouseReleaseEvent(self, event):
        if self.current_tool == "cursor":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        if self.is_drawing_freehand and event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing_freehand = False
            if self.current_draw_item:
                final_path = self.current_draw_item.path()
                pen = self.current_draw_item.pen()
                self.scene().removeItem(self.current_draw_item)
                
                rect = final_path.boundingRect()
                if rect.width() < 2 and rect.height() < 2:
                    self.current_draw_item = None
                    event.accept()
                    return

                center = rect.center()
                final_shape = DraggableShape("draw", rect.width(), rect.height(), pen, initial_path=final_path, main_window=self.main_window)
                final_shape.setPos(center)
                self.scene().addItem(final_shape)
                self.scene().clearSelection()
                final_shape.setSelected(True)
                
            self.current_draw_item = None
            
            if self.main_window:
                self.main_window.tool_category_group.button(0).setChecked(True)
                self.main_window.change_tool("cursor")

            event.accept()
            return
            
        super().mouseReleaseEvent(event)
        
        if self.select_region_mode and event.button() == Qt.MouseButton.LeftButton and self.selection_start_pos:
            selection_end_pos = self.mapToScene(event.pos())
            rect = QRectF(self.selection_start_pos, selection_end_pos).normalized()
            if rect.width() > 50 and rect.height() > 50 and self.main_window:
                self.main_window.set_projection_region(rect)
            self.selection_start_pos = None

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        
        if self.show_grid and self.scene() and self.grid_size > 0:
            scene_rect = self.scene().sceneRect()
            left, right = int(scene_rect.left()), int(scene_rect.right())
            top, bottom = int(scene_rect.top()), int(scene_rect.bottom())

            pen = QPen(QColor(0, 255, 255, 120))
            pen.setWidth(1); pen.setCosmetic(True) 
            painter.setPen(pen)

            for x in range(left, right, self.grid_size): painter.drawLine(x, top, x, bottom)
            for y in range(top, bottom, self.grid_size): painter.drawLine(left, y, right, y)

            font = painter.font(); font.setPixelSize(14); font.setBold(True)
            painter.setFont(font); painter.setPen(QColor(0, 255, 255, 220))
            col = 1
            for x in range(left, right, self.grid_size):
                row = 1
                for y in range(top, bottom, self.grid_size):
                    letter = chr(64 + min(row, 26)) if row <= 26 else str(row)
                    painter.drawText(x + 5, y + 20, f"{letter}-{col:02d}")
                    row += 1
                col += 1

        if self.active_item and self.active_item.action_info:
            pos = self.active_item.scenePos()
            scene_rect = self.scene().sceneRect()
            
            guide_pen = QPen(QColor(255, 255, 255, 90), 1, Qt.PenStyle.DashLine)
            painter.setPen(guide_pen)
            painter.drawLine(scene_rect.left(), pos.y(), scene_rect.right(), pos.y())
            painter.drawLine(pos.x(), scene_rect.top(), pos.x(), scene_rect.bottom())
            
            text_bg_rect = QRectF(pos.x() + 20, pos.y() - 40, 130, 26)
            painter.setBrush(QColor(0, 0, 0, 190))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(text_bg_rect, 4, 4)
            
            painter.setPen(QColor("#f1c40f")) 
            font = painter.font(); font.setPixelSize(13); font.setBold(True)
            painter.setFont(font)
            painter.drawText(text_bg_rect, Qt.AlignmentFlag.AlignCenter, self.active_item.action_info)