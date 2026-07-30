from gui import PatternGuardApp

if __name__ == "__main__":
    try:
        # Set DPI awareness on Windows if available so UI scales correctly on high-DPI displays.
        # Use getattr to avoid static-analysis warnings when the symbol isn't present.
        from ctypes import windll
        shcore = getattr(windll, 'shcore', None)
        if shcore is not None:
            func = getattr(shcore, 'SetProcessDpiAwareness', None)
            if callable(func):
                # 1 == PROCESS_SYSTEM_DPI_AWARE
                try:
                    func(1)
                except Exception:
                    # Calling the function may still fail at runtime on some Windows versions.
                    pass
        else:
            # Fallback: older Windows may expose SetProcessDPIAware on user32
            user32 = getattr(windll, 'user32', None)
            if user32 is not None:
                func2 = getattr(user32, 'SetProcessDPIAware', None)
                if callable(func2):
                    try:
                        func2()
                    except Exception:
                        pass
    except Exception:
        pass

    app = PatternGuardApp()
    app.mainloop()
