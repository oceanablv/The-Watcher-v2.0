import threading
import winsound
import cv2
import imutils
import numpy as np
from PIL import Image, ImageTk
import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.style import Bootstyle

class TheWatcher:
    def __init__(self):
        # Initialize main window
        self.window = ttk.Window(
            themename="darkly",
            title="THE WATCHER v2.0",
            resizable=(False, False)
        )
        self.window.configure(bg='black')
        
        # Initialize video capture
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Initialize frame processing
        _, self.start_frame = self.cap.read()
        self.start_frame = self._process_frame(self.start_frame)
        
        # Initialize state variables
        self.alarm = False
        self.alarm_mode = False
        self.alarm_counter = 0
        self.recording = False
        self.video_writer = None
        
        # Setup UI and start video processing
        self._setup_ui()
        self._start_video_loops()

    def _setup_ui(self):
        """Set up the UI components for the surveillance system"""
        # Create main container
        main_container = ttk.Frame(self.window, padding=10)
        main_container.pack(fill=BOTH, expand=YES)

        # Create header
        header = ttk.Label(
            main_container,
            text="THE WATCHER v2.0",
            font=("Courier New", 24, "bold"),
            bootstyle="light"
        )
        header.pack(pady=10)

        # Create video feed container
        video_container = ttk.Frame(main_container)
        video_container.pack(fill=BOTH, expand=YES, pady=10)

        # Regular video feed
        regular_frame = ttk.Frame(video_container)
        regular_frame.pack(side=LEFT, padx=5)
        
        ttk.Label(
            regular_frame,
            text="LIVE FEED",
            font=("Courier New", 12),
            bootstyle="light"
        ).pack()
        
        self.regular_label = ttk.Label(regular_frame)
        self.regular_label.pack()

        # Motion detection feed
        motion_frame = ttk.Frame(video_container)
        motion_frame.pack(side=RIGHT, padx=5)
        
        ttk.Label(
            motion_frame,
            text="MOTION DETECTION",
            font=("Courier New", 12),
            bootstyle="light"
        ).pack()
        
        self.motion_label = ttk.Label(motion_frame)
        self.motion_label.pack()

        # Controls container
        controls_container = ttk.Frame(main_container)
        controls_container.pack(fill=X, pady=10)

        # Status and threat level
        status_frame = ttk.Frame(controls_container)
        status_frame.pack(fill=X)

        self.status_label = ttk.Label(
            status_frame,
            text="▶ SYSTEM READY",
            font=("Courier New", 12),
            bootstyle="success"
        )
        self.status_label.pack(side=LEFT)

        self.threat_label = ttk.Label(
            status_frame,
            text="THREAT LEVEL: 0%",
            font=("Courier New", 12),
            bootstyle="success"
        )
        self.threat_label.pack(side=RIGHT)

        # Threat meter
        self.threat_meter = ttk.Progressbar(
            controls_container,
            length=200,
            bootstyle="success-striped",
            maximum=100,
            value=0
        )
        self.threat_meter.pack(fill=X, pady=5)

        # Control buttons
        button_frame = ttk.Frame(controls_container)
        button_frame.pack(fill=X, pady=5)

        self.toggle_button = ttk.Button(
            button_frame,
            text="ACTIVATE SURVEILLANCE",
            command=self._toggle_alarm,
            bootstyle="danger-outline",
            width=25
        )
        self.toggle_button.pack()

        # Notification area
        self.notification_label = ttk.Label(
            main_container,
            text="System initialized and ready",
            font=("Courier New", 10),
            bootstyle="light"
        )
        self.notification_label.pack(fill=X, pady=10)

    def _add_timestamp(self, frame):
        """Add timestamp to the frame"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Add black background for text
        (text_width, text_height), _ = cv2.getTextSize(timestamp, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(frame, (10, frame.shape[0] - 40), 
                     (10 + text_width + 10, frame.shape[0] - 10), 
                     (0, 0, 0), -1)
        # Add white text
        cv2.putText(
            frame,
            timestamp,
            (15, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        return frame

    def _add_cyberpunk_overlay(self, frame):
        """Add cyberpunk-style visual elements to the frame"""
        # Add hex grid overlay with reduced opacity
        for y in range(0, frame.shape[0], 100):
            for x in range(0, frame.shape[1], 100):
                cv2.polylines(frame, [np.array([
                    [x, y],
                    [x + 50, y],
                    [x + 75, y + 43],
                    [x + 50, y + 87],
                    [x, y + 87],
                    [x - 25, y + 43],
                ])], True, (0, 255, 255), 1, cv2.LINE_AA)
        
        frame = self._add_timestamp(frame)
        return frame

    def _update_motion_frame(self):
        """Update the motion detection frame"""
        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = imutils.resize(frame, width=500)

        if self.alarm_mode:
            frame_bw = self._process_frame(frame)
            difference = cv2.absdiff(frame_bw, self.start_frame)
            threshold = cv2.threshold(difference, 25, 255, cv2.THRESH_BINARY)[1]
            self.start_frame = frame_bw

            if threshold.sum() > 300:
                self.alarm_counter += 1
                # Add intruder warning to the black and white frame
                cv2.putText(
                    threshold,
                    "! INTRUDER DETECTED !",
                    (int(threshold.shape[1]/2 - 150), int(threshold.shape[0]/2)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2
                )
                
                # Add hex grid to motion detection frame
                for i in range(0, threshold.shape[0], 30):
                    for j in range(0, threshold.shape[1], 30):
                        cv2.polylines(threshold, [np.array([[j, i], [j+15, i], [j+30, i+15],
                                                          [j+30, i+30], [j+15, i+30], [j, i+15]])],
                                    True, (255, 255, 255), 1)
                
                self._update_threat_meter()
            else:
                self.alarm_counter = max(0, self.alarm_counter - 1)
                self._update_threat_meter()

            if self.alarm_counter > 20 and not self.recording:
                self._start_recording()

            if self.recording and self.alarm_counter == 0:
                self._stop_recording()

            if self.recording:
                self.video_writer.write(frame)

            # Convert threshold to RGB for display
            threshold_rgb = cv2.cvtColor(threshold, cv2.COLOR_GRAY2RGB)
            # Add timestamp to threshold frame
            threshold_rgb = self._add_timestamp(threshold_rgb)
            
            img = Image.fromarray(threshold_rgb)
        else:
            frame = self._add_cyberpunk_overlay(frame)
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        photo = ImageTk.PhotoImage(image=img)
        self.motion_label.configure(image=photo)
        self.motion_label.image = photo
        self.motion_label.after(30, self._update_motion_frame)

    def _update_regular_frame(self):
        """Update the regular video feed frame"""
        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = imutils.resize(frame, width=500)
        # Only add timestamp to regular feed, no grid
        frame = self._add_timestamp(frame)
        
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        photo = ImageTk.PhotoImage(image=img)
        self.regular_label.configure(image=photo)
        self.regular_label.image = photo
        self.regular_label.after(30, self._update_regular_frame)

    def _update_threat_meter(self):
        """Update the threat meter UI based on alarm counter"""
        threat_level = min(100, self.alarm_counter * 4)
        self.threat_meter["value"] = threat_level
        self.threat_label.configure(text=f"THREAT LEVEL: {threat_level}%")
        
        if threat_level < 33:
            self.threat_meter.configure(bootstyle="success-striped")
            self.threat_label.configure(bootstyle="success")
        elif threat_level < 66:
            self.threat_meter.configure(bootstyle="warning-striped")
            self.threat_label.configure(bootstyle="warning")
        else:
            self.threat_meter.configure(bootstyle="danger-striped")
            self.threat_label.configure(bootstyle="danger")

    def _toggle_alarm(self):
        """Toggle the alarm mode on/off"""
        self.alarm_mode = not self.alarm_mode
        self.alarm_counter = 0
        self._update_threat_meter()
        
        if self.alarm_mode:
            self.toggle_button.configure(
                text="DEACTIVATE SURVEILLANCE",
                bootstyle="danger"
            )
            self.status_label.configure(
                text="▶ SURVEILLANCE ACTIVE",
                bootstyle="danger"
            )
            self._update_notification("Surveillance mode activated - Monitoring for intruders")
        else:
            self.toggle_button.configure(
                text="ACTIVATE SURVEILLANCE",
                bootstyle="danger-outline"
            )
            self.status_label.configure(
                text="▶ SYSTEM READY",
                bootstyle="success"
            )
            self._update_notification("Surveillance mode deactivated")

    def _update_notification(self, message):
        """Update the notification label with a timestamped message"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.notification_label.configure(text=f"[{timestamp}] {message}")

    def _process_frame(self, frame):
        """Process frame for motion detection"""
        frame = imutils.resize(frame, width=500)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(frame, (21, 21), 0)

    def _start_recording(self):
        """Start recording video when motion is detected"""
        if not self.recording:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"surveillance_{timestamp}.avi"
            self.video_writer = cv2.VideoWriter(
                filename,
                cv2.VideoWriter_fourcc(*'XVID'),
                20.0,
                (500, 375)
            )
            self.recording = True
            self._update_notification(f"⚠ INTRUDER DETECTED - Recording: {filename}")
            threading.Thread(target=self._beep_alarm).start()

    def _stop_recording(self):
        """Stop recording video when motion stops"""
        if self.recording:
            self.video_writer.release()
            self.video_writer = None
            self.recording = False
            self._update_notification("Motion stopped - Recording saved")

    def _beep_alarm(self):
        """Play alarm sound when motion is detected"""
        for _ in range(3):
            if not self.alarm_mode:
                break
            winsound.Beep(2500, 1000)

    def _start_video_loops(self):
        """Start the video processing loops"""
        self._update_motion_frame()
        self._update_regular_frame()

    def run(self):
        """Start the application"""
        self.window.mainloop()
        self.cap.release()
        if self.video_writer:
            self.video_writer.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = TheWatcher()
    app.run()