import subprocess

def get_hdd_info(hdd):
    r = subprocess.run(["hdparm", "-I", hdd], capture_output=True)
    output = r.stdout.decode().splitlines()

    model_index = [i for i, s in enumerate(output) if 'Model Number:' in s]
    serial_index = [i for i, s in enumerate(output) if 'Serial Number:' in s]

    try:
        model = output[model_index[0]].split("Model Number:", 1)[1].strip()
    except Exception:
        model = "unavailable"
    
    try:
        serial = output[serial_index[0]].split("Serial Number:", 1)[1].strip()
    except Exception:
        serial = "unavailable"
    
    return {"model": model, "serial": serial}
