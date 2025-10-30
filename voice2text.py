import sys
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QFileDialog, QLabel, QComboBox,
    QProgressBar
)
from PySide6.QtCore import Slot, Signal, QObject
import whisper
import torch

class WorkerSignals(QObject):
    """워커 스레드에서 메인 스레드로 신호를 보내기 위한 클래스"""
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(str)

class VoiceToTextApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎤 Whisper 음성 전사 프로그램")
        self.setGeometry(100, 100, 900, 700)
        
        # GPU 사용 가능 여부 확인
        self.gpu_available = torch.cuda.is_available()
        
        # 메인 위젯 및 레이아웃 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # GPU 상태 표시
        gpu_status = f"🖥️ GPU: {'사용 가능 (' + torch.cuda.get_device_name(0) + ')' if self.gpu_available else '사용 불가 (CPU 사용)'}"
        gpu_label = QLabel(gpu_status)
        main_layout.addWidget(gpu_label)
        
        # 모델 선택 영역
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("모델 선택:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny (가장 빠름)", "base (기본)", "small (추천)", "medium (고품질)", "large (최고품질)"])
        self.model_combo.setCurrentIndex(2)  # small 기본 선택
        model_layout.addWidget(self.model_combo)
        main_layout.addLayout(model_layout)
        
        # 파일 입력 영역
        file_input_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit("음성/영상 파일을 선택하세요")
        self.file_path_edit.setReadOnly(True)
        file_input_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("🎤 파일 선택")
        self.browse_button.clicked.connect(self.browse_file)
        file_input_layout.addWidget(self.browse_button)
        main_layout.addLayout(file_input_layout)
        
        # 실행 버튼
        self.transcribe_button = QPushButton("▶️ 전사 시작")
        self.transcribe_button.clicked.connect(self.start_transcription_thread)
        self.transcribe_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        main_layout.addWidget(self.transcribe_button)
        
        # 진행 상태 표시
        self.progress_label = QLabel("대기 중...")
        main_layout.addWidget(self.progress_label)
        
        # 출력 표시 영역
        main_layout.addWidget(QLabel("📝 전사 결과 (타임스탬프 포함):"))
        self.transcript_output = QTextEdit()
        self.transcript_output.setReadOnly(True)
        self.transcript_output.setStyleSheet("font-family: 'Malgun Gothic', sans-serif; font-size: 11pt;")
        main_layout.addWidget(self.transcript_output)
        
        # 하단 버튼 영역
        button_layout = QHBoxLayout()
        
        self.save_txt_button = QPushButton("💾 TXT 파일 저장")
        self.save_txt_button.clicked.connect(lambda: self.save_transcript("txt"))
        button_layout.addWidget(self.save_txt_button)
        
        self.save_srt_button = QPushButton("💾 SRT 자막 저장")
        self.save_srt_button.clicked.connect(lambda: self.save_transcript("srt"))
        button_layout.addWidget(self.save_srt_button)
        
        main_layout.addLayout(button_layout)
        
        # 워커 시그널 초기화
        self.signals = WorkerSignals()
        self.signals.finished.connect(self.on_transcription_finished)
        self.signals.error.connect(self.on_transcription_error)
        self.signals.progress.connect(self.on_progress_update)
        
        # 결과 데이터 저장
        self.current_segments = []

    @Slot()
    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "음성/영상 파일 선택", "", 
            "미디어 파일 (*.mp3 *.wav *.mp4 *.webm *.m4a *.flac);;모든 파일 (*)"
        )
        if file_name:
            self.file_path_edit.setText(file_name)

    @Slot()
    def start_transcription_thread(self):
        audio_file = self.file_path_edit.text()
        
        if not audio_file or audio_file == "음성/영상 파일을 선택하세요":
            self.transcript_output.setText("❌ 유효한 음성/영상 파일을 선택하세요.")
            return

        # 모델 크기 선택
        model_text = self.model_combo.currentText()
        model_size = model_text.split()[0]  # "small (추천)" -> "small"
        
        self.transcribe_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.transcript_output.setText("🔄 전사를 시작합니다...\n모델 로딩 중...")
        self.progress_label.setText("⏳ 처리 중...")
        
        # 작업 스레드 시작
        threading.Thread(
            target=self.transcribe_task, 
            args=(audio_file, model_size), 
            daemon=True
        ).start()

    def transcribe_task(self, audio_file, model_size):
        try:
            self.signals.progress.emit(f"📥 {model_size} 모델 로딩 중...")
            
            # Whisper 모델 로드
            model = whisper.load_model(model_size)
            
            self.signals.progress.emit("🎯 음성 전사 시작... (시간이 소요될 수 있습니다)")
            
            # 전사 실행
            result = model.transcribe(
                audio_file,
                language="ko",
                fp16=self.gpu_available,
                verbose=False
            )
            
            # 세그먼트 저장
            self.current_segments = result['segments']
            
            # 결과 포맷팅
            formatted_text = ""
            for segment in result['segments']:
                start_time = self.format_time(segment['start'])
                end_time = self.format_time(segment['end'])
                text = segment['text'].strip()
                formatted_text += f"[{start_time} → {end_time}] {text}\n\n"
            
            self.signals.finished.emit(formatted_text)
            
        except Exception as e:
            self.signals.error.emit(str(e))

    def format_time(self, seconds):
        """초를 HH:MM:SS.ms 형식으로 변환"""
        ms = int((seconds * 1000) % 1000)
        s = int(seconds % 60)
        m = int((seconds // 60) % 60)
        h = int(seconds // 3600)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    
    def format_time_srt(self, seconds):
        """SRT 자막 형식으로 시간 변환 (HH:MM:SS,ms)"""
        ms = int((seconds * 1000) % 1000)
        s = int(seconds % 60)
        m = int((seconds // 60) % 60)
        h = int(seconds // 3600)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @Slot(str)
    def on_transcription_finished(self, result):
        self.transcript_output.setText(result)
        self.progress_label.setText("✅ 전사 완료!")
        self.transcribe_button.setEnabled(True)
        self.browse_button.setEnabled(True)

    @Slot(str)
    def on_transcription_error(self, error_msg):
        self.transcript_output.setText(f"❌ 전사 오류 발생:\n{error_msg}\n\n힌트: FFmpeg가 설치되어 있는지 확인하세요.")
        self.progress_label.setText("❌ 오류 발생")
        self.transcribe_button.setEnabled(True)
        self.browse_button.setEnabled(True)

    @Slot(str)
    def on_progress_update(self, message):
        self.progress_label.setText(message)

    @Slot()
    def save_transcript(self, file_type):
        if not self.current_segments:
            self.transcript_output.setText("❌ 저장할 전사 결과가 없습니다. 먼저 전사를 실행하세요.")
            return

        if file_type == "txt":
            file_name, _ = QFileDialog.getSaveFileName(
                self, "TXT 파일 저장", "transcript.txt", 
                "텍스트 파일 (*.txt)"
            )
            
            if file_name:
                try:
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write(self.transcript_output.toPlainText())
                    self.progress_label.setText(f"✅ 저장 완료: {file_name}")
                except Exception as e:
                    self.progress_label.setText(f"❌ 저장 오류: {e}")
        
        elif file_type == "srt":
            file_name, _ = QFileDialog.getSaveFileName(
                self, "SRT 자막 파일 저장", "transcript.srt", 
                "SRT 자막 파일 (*.srt)"
            )
            
            if file_name:
                try:
                    with open(file_name, 'w', encoding='utf-8') as f:
                        for i, segment in enumerate(self.current_segments, 1):
                            start_time = self.format_time_srt(segment['start'])
                            end_time = self.format_time_srt(segment['end'])
                            text = segment['text'].strip()
                            
                            f.write(f"{i}\n")
                            f.write(f"{start_time} --> {end_time}\n")
                            f.write(f"{text}\n\n")
                    
                    self.progress_label.setText(f"✅ SRT 저장 완료: {file_name}")
                except Exception as e:
                    self.progress_label.setText(f"❌ 저장 오류: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VoiceToTextApp()
    window.show()
    sys.exit(app.exec())