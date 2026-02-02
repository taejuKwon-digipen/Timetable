import sys
import traceback

def excepthook(etype, value, tb):
    traceback.print_exception(etype, value, tb)
    input("엔터를 누르면 종료합니다...")

def main():
    sys.excepthook = excepthook
    try:
        from PyQt6.QtWidgets import QApplication
        from main_window import MainWindow

        app = QApplication(sys.argv)
        w = MainWindow()
        w.show()
        w.raise_()
        w.activateWindow()
        sys.exit(app.exec())
    except Exception as e:
        print("오류 발생:", e)
        traceback.print_exc()
        input("엔터를 누르면 종료합니다...")
        sys.exit(1)


if __name__ == "__main__":
    main()
