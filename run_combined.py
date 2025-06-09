import multiprocessing
import subprocess

def run_backend():
    subprocess.run(["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"])

def run_webapp():
    subprocess.run(["python", "webapp/run_webapp.py"])

def run_nginx():
    subprocess.run(["nginx", "-g", "daemon off;"])

if __name__ == "__main__":
    processes = [
        multiprocessing.Process(target=run_backend),
        multiprocessing.Process(target=run_webapp),
        multiprocessing.Process(target=run_nginx)
    ]

    for p in processes:
        p.start()
    for p in processes:
        p.join()