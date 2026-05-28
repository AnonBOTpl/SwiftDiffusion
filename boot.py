import sys
import subprocess
import threading

print("[BOOT] Swift Diffusion starting...")

_test_proc = subprocess.Popen(
    [sys.executable, "-c", "import torch; torch.cuda.device_count(); print('OK')"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
try:
    _out, _ = _test_proc.communicate(timeout=45)
    if _out.strip() != b"OK":
        print(f"[BOOT] torch test failed: {_out.decode()}")
        _test_proc.terminate()
except subprocess.TimeoutExpired:
    _test_proc.kill()
    _test_proc.communicate()
    print("[BOOT] torch/CUDA hangs at startup. GPU driver in bad state.")
    print("[BOOT] Please restart your computer to reset the GPU driver.")
    sys.exit(1)

print("[BOOT] torch/CUDA initialized successfully.")


def _check_cuda_health():
    print("[STARTUP] Checking CUDA health...")
    result = [True]
    done = threading.Event()
    def test():
        try:
            import torch
            if torch.cuda.is_available():
                _ = torch.cuda.get_device_properties(0)
            result[0] = True
        except Exception:
            result[0] = False
        done.set()
    t = threading.Thread(target=test, daemon=True)
    t.start()
    if not done.wait(timeout=30):
        print("[STARTUP] CUDA not responding (30s timeout). GPU driver in bad state.")
        print("[STARTUP] Please restart your computer to reset the GPU driver.")
        sys.exit(1)
    print("[STARTUP] CUDA health check passed.")

_check_cuda_health()
print("[STARTUP] CUDA health check done. Initializing Qt...")
