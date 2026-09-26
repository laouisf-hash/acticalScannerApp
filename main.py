import cv2
import numpy as np
import os
import json
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics.texture import Texture
from kivy.utils import platform

try:
    from plyer import gps
except ImportError:
    gps = None

# ------------------------------------------------------------------
# قاعدة بيانات الرموز والإشارات الأثرية والدلالات الميدانية
# ------------------------------------------------------------------
SYMBOL_DB = {
    "CUPMARK": {
        "name": "جرن / دائرة حفرية (Cupmark)",
        "meaning": "معصرة زيتون/خمر قديمة، نقطة تجميع مياه طقسية، أو إشارة جنائزية.",
        "target_structure": "ماجل مياه مدفون، معصرة رومانية، أو مدفن جنائزي قادوميات."
    },
    "RECTANGLE_WALL": {
        "name": "مستطيل / ساس مبني (Structural Wall)",
        "meaning": "أساسات جدار قديم، جدار حماية، أو زاوية بناء مسبوك.",
        "target_structure": "بقاياس مبنى أثري، غرفة تخزين، أو غار مسقوف."
    },
    "TURTLE_SHAPE": {
        "name": "فكرون / مجسم سلحفاة (Turtle Shape)",
        "meaning": "رمز الحماية والحدود الثابتة، أو دلالة على مصدر مياه قريبة في الصخر.",
        "target_structure": "منشأة مائية مغطاة، أو مدفن صخري محصن."
    },
    "SERPENT_LINE": {
        "name": "سيال ملتوي / حية (Serpentine Canal)",
        "meaning": "قناة مجرى مياه حجرية، أو إشارة توجيهية نحو عيون المياه.",
        "target_structure": "سقية مائية مدفونة، عين ماء، أو معلم استشفائي روماني."
    },
    "GENERIC_ANOMALY": {
        "name": "تغير تضاريسي / شق صخري (Surface Anomaly)",
        "meaning": "تغير في تضاريس التربة أو نمو غير عادي للنباتات فوق معالم مدفونة.",
        "target_structure": "ركام حجارة، حفرة ردم قديمة، أو شقف وفخار تحت التربة."
    }
}


class ArchaeologyScanner(App):
    def build(self):
        self.is_paused = False
        self.capture = None
        self.current_frame = None
        self.location_data = {"lat": "Unknown", "lon": "Unknown"}

        self.layout = BoxLayout(orientation="vertical", spacing=5, padding=5)
        self.camera_view = Image(size_hint=(1, 0.68))
        
        self.info = Label(
            text="✅ READY - Scan the terrain",
            size_hint=(1, 0.17),
            font_size="15sp",
            halign="center",
            valign="middle"
        )
        self.info.bind(size=self.info.setter('text_size'))

        btn_layout = GridLayout(cols=3, size_hint=(1, 0.15), spacing=5)
        self.scan_button = Button(text="🔎 ANALYZE", background_color=(0.1, 0.5, 0.8, 1), bold=True)
        self.resume_button = Button(text="▶️ RESUME", background_color=(0.2, 0.7, 0.3, 1), bold=True)
        self.report_button = Button(text="📄 SAVE REPORT", background_color=(0.8, 0.2, 0.2, 1), bold=True)

        btn_layout.add_widget(self.scan_button)
        btn_layout.add_widget(self.resume_button)
        btn_layout.add_widget(self.report_button)

        self.layout.add_widget(self.camera_view)
        self.layout.add_widget(self.info)
        self.layout.add_widget(btn_layout)

        self.scan_button.bind(on_press=self.start_scan)
        self.resume_button.bind(on_press=self.resume_camera)
        self.report_button.bind(on_press=self.save_report)

        self.analysis = {}
        return self.layout

    def on_start(self):
        if platform == "android":
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ], self.permissions_callback)
        else:
            self.initialize_hardware()

    def permissions_callback(self, permissions, grants):
        if all(grants):
            self.initialize_hardware()

    def initialize_hardware(self):
        if gps:
            try:
                gps.configure(on_location=self.on_location)
                gps.start(1000, 0)
            except: pass

        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            self.capture = cv2.VideoCapture(1)

        Clock.schedule_interval(self.update_camera, 1.0 / 30.0)

    def on_location(self, **kwargs):
        self.location_data["lat"] = str(kwargs.get('lat', 'Unknown'))
        self.location_data["lon"] = str(kwargs.get('lon', 'Unknown'))

    def update_camera(self, dt):
        if self.capture is None or self.is_paused:
            return

        ok, frame = self.capture.read()
        if not ok: return

        self.current_frame = frame.copy()
        self.display_frame(frame)

    def display_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.flip(rgb, 0)
        texture = Texture.create(size=(rgb.shape[1], rgb.shape[0]), colorfmt="rgb")
        texture.blit_buffer(rgb.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
        self.camera_view.texture = texture

    def resume_camera(self, instance):
        self.is_paused = False
        self.info.text = "✅ READY - Scan the terrain"

    def classify_shape(self, contour, area, perimeter):
        """تحليل هندسي فريد لربط الشكل بأقرب رمز تاريخي"""
        if perimeter == 0: return SYMBOL_DB["GENERIC_ANOMALY"]
        
        # درجة الاستدارة (Circularity)
        circularity = (4 * np.pi * area) / (perimeter ** 2)
        
        # نسبة الطول للعرض (Aspect Ratio)
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / max(h, 1)

        # عدد الزوايا المتوقعة
        approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
        vertices = len(approx)

        if circularity > 0.65:
            return SYMBOL_DB["CUPMARK"]
        elif 4 <= vertices <= 6 and 0.6 < aspect_ratio < 1.6:
            return SYMBOL_DB["RECTANGLE_WALL"]
        elif aspect_ratio > 2.2 or aspect_ratio < 0.45:
            return SYMBOL_DB["SERPENT_LINE"]
        elif 0.7 < aspect_ratio < 1.3 and vertices > 6:
            return SYMBOL_DB["TURTLE_SHAPE"]
        else:
            return SYMBOL_DB["GENERIC_ANOMALY"]

    def start_scan(self, instance):
        if self.current_frame is None: return

        self.is_paused = True
        frame = self.current_frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blur, 40, 120)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = gray.shape
        image_area = h * w
        valid_objects = []
        detected_symbol_info = SYMBOL_DB["GENERIC_ANOMALY"]
        geometric_score = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < image_area * 0.004 or area > image_area * 0.4:
                continue

            perimeter = cv2.arcLength(contour, True)
            symbol_matched = self.classify_shape(contour, area, perimeter)
            
            # نختار الرمز الأكثر تعقيداً إذا وجد
            if symbol_matched != SYMBOL_DB["GENERIC_ANOMALY"]:
                detected_symbol_info = symbol_matched
                geometric_score += 25
            else:
                geometric_score += 10

            valid_objects.append(contour)

        geometric_score = min(geometric_score, 100)

        # ExGI Vegetation & Surface Texture
        b, g, r = cv2.split(frame)
        exg = 2 * g.astype(np.float32) - r.astype(np.float32) - b.astype(np.float32)
        vegetation_anomaly = min(float(np.std(exg)), 100)

        local_mean = cv2.blur(gray.astype(np.float32), (31, 31))
        surface_anomaly = min(float(np.mean(np.abs(gray.astype(np.float32) - local_mean))) * 4, 100)

        archaeological_score = round((geometric_score * 0.45) + (surface_anomaly * 0.35) + (vegetation_anomaly * 0.20), 1)

        # إعداد بيانات التقرير
        self.analysis = {
            "timestamp": datetime.now().isoformat(),
            "gps_coordinates": self.location_data,
            "archaeological_score": archaeological_score,
            "detected_symbol": detected_symbol_info["name"],
            "symbol_meaning": detected_symbol_info["meaning"],
            "target_structure": detected_symbol_info["target_structure"],
            "objects_detected": len(valid_objects),
            "scores_breakdown": {
                "geometric": round(geometric_score, 1),
                "surface_texture": round(surface_anomaly, 1),
                "vegetation_index": round(vegetation_anomaly, 1)
            }
        }

        # Draw output on screen
        output = frame.copy()
        for contour in valid_objects:
            cv2.drawContours(output, [contour], -1, (0, 0, 255), 3)

        cv2.rectangle(output, (0, 0), (w, 90), (0, 0, 0), -1)
        cv2.putText(output, f"SCORE: {archaeological_score}/100", (15, 35), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)
        cv2.putText(output, f"SYMBOL: {detected_symbol_info['name']}", (15, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        self.display_frame(output)

        gps_str = f"📍 {self.location_data['lat'][:7]}, {self.location_data['lon'][:7]}" if self.location_data['lat'] != "Unknown" else "📍 No GPS"
        self.info.text = (
            f"Score: {archaeological_score}/100 | {gps_str}\n"
            f"الرمز: {detected_symbol_info['name']}\n"
            f"المعلم المحتمل: {detected_symbol_info['target_structure']}"
        )

    def save_report(self, instance):
        if not self.is_paused or self.current_frame is None:
            self.info.text = "❌ Run ANALYSIS first before saving!"
            return

        if platform == "android":
            from android.storage import primary_external_storage_path
            folder = os.path.join(primary_external_storage_path(), "Download", "ArchaeologyReports")
        else:
            folder = "ArchaeologyReports"

        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        image_file = os.path.join(folder, f"scan_{timestamp}.jpg")
        report_file = os.path.join(folder, f"report_{timestamp}.json")

        rgb = cv2.cvtColor(np.frombuffer(self.camera_view.texture.pixels, dtype=np.uint8).reshape(self.camera_view.texture.height, self.camera_view.texture.width, 4), cv2.COLOR_RGBA2BGR)
        rgb = cv2.flip(rgb, 0)
        cv2.imwrite(image_file, rgb)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.analysis, f, indent=4, ensure_ascii=False)

        self.info.text = f"✅ Saved to Downloads/ArchaeologyReports"

    def on_stop(self):
        if self.capture is not None: self.capture.release()
        if gps:
            try: gps.stop()
            except: pass

if __name__ == "__main__":
    ArchaeologyScanner().run()