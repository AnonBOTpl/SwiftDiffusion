module.exports = {
  "run": [
    // Step 1: Create venv using Pinokio's Python 3.12
    {
      "method": "shell.run",
      "params": {
        "message": "python -m venv .venv",
        "path": "{{path}}",
        "env": { "PYTHON_VERSION": "3.12" }
      }
    },
    // Step 2: PyTorch + CUDA 12.8
    {
      "method": "shell.run",
      "params": {
        "message": ".venv\\Scripts\\activate && pip install torch==2.7.1+cu128 torchvision==0.22.1+cu128 --extra-index-url https://download.pytorch.org/whl/cu128",
        "path": "{{path}}"
      }
    },
    // Step 3: xformers
    {
      "method": "shell.run",
      "params": {
        "message": ".venv\\Scripts\\activate && pip install xformers==0.0.31.post1 --extra-index-url https://download.pytorch.org/whl/cu128 --no-deps",
        "path": "{{path}}"
      }
    },
    // Step 4: requirements
    {
      "method": "shell.run",
      "params": {
        "message": ".venv\\Scripts\\activate && pip install -r requirements.txt",
        "path": "{{path}}"
      }
    },
    // Step 5: compel without jupyter bloat
    {
      "method": "shell.run",
      "params": {
        "message": ".venv\\Scripts\\activate && pip install compel --no-deps",
        "path": "{{path}}"
      }
    },
    // Step 6: Mark as installed
    {
      "method": "fs.write",
      "params": {
        "path": "{{path}}/.installed",
        "text": "ok"
      }
    }
  ]
}
