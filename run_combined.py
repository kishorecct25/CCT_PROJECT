import multiprocessing
import subprocess

def run_backend():
    subprocess.run([
        "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"
    ])

def run_webapp():
    subprocess.run([
        "python", "webapp/run_webapp.py"
    ])

if __name__ == "__main__":
    backend_process = multiprocessing.Process(target=run_backend)
    webapp_process = multiprocessing.Process(target=run_webapp)

    backend_process.start()
    webapp_process.start()

    backend_process.join()
    webapp_process.join()