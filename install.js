module.exports = {
  "run": [
    // Step 1: Install uv if not present
    {
      "method": "shell.run",
      "params": {
        "message": "uv --version",
        "on_error": [
          {
            "method": "shell.run",
            "params": {
              "message": "powershell -ExecutionPolicy Bypass -c \"& {[System.Net.ServicePointManager]::SecurityProtocol = 3072; Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -UseBasicParsing | Invoke-Expression}\""
            }
          }
        ]
      }
    },
    // Step 2: Create virtual environment
    {
      "method": "shell.run",
      "params": {
        "message": "uv venv .venv-uv",
        "path": "{{path}}"
      }
    },
    // Step 3: PyTorch + CUDA 12.8
    {
      "method": "shell.run",
      "params": {
        "message": ".venv-uv\\Scripts\\activate.bat && uv pip install torch==2.7.1+cu128 torchvision==0.22.1+cu128 --extra-index-url https://download.pytorch.org/whl/cu128",
        "path": "{{path}}"
      }
    },
    // Step 4: xformers
    {
      "method": "shell.run",
      "params": {
        "message": ".venv-uv\\Scripts\\activate.bat && uv pip install xformers==0.0.31.post1 --extra-index-url https://download.pytorch.org/whl/cu128 --no-deps",
        "path": "{{path}}"
      }
    },
    // Step 5: requirements
    {
      "method": "shell.run",
      "params": {
        "message": ".venv-uv\\Scripts\\activate.bat && uv pip install -r requirements-uv.txt && uv pip install compel --no-deps",
        "path": "{{path}}"
      }
    }
  ]
}
