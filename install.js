module.exports = {
  "run": [
    // Step 1: Create conda environment with Python 3.12
    {
      "method": "shell.run",
      "params": {
        "message": "conda create -n swiftdiffusion python=3.12 -y",
        "path": "{{path}}"
      }
    },
    // Step 2: PyTorch + CUDA 12.8
    {
      "method": "shell.run",
      "params": {
        "message": "conda run -n swiftdiffusion pip install torch==2.7.1+cu128 torchvision==0.22.1+cu128 --extra-index-url https://download.pytorch.org/whl/cu128",
        "path": "{{path}}"
      }
    },
    // Step 3: xformers
    {
      "method": "shell.run",
      "params": {
        "message": "conda run -n swiftdiffusion pip install xformers==0.0.31.post1 --extra-index-url https://download.pytorch.org/whl/cu128 --no-deps",
        "path": "{{path}}"
      }
    },
    // Step 4: requirements
    {
      "method": "shell.run",
      "params": {
        "message": "conda run -n swiftdiffusion pip install -r requirements.txt",
        "path": "{{path}}"
      }
    },
    // Step 5: compel (no deps to avoid jupyter bloat)
    {
      "method": "shell.run",
      "params": {
        "message": "conda run -n swiftdiffusion pip install compel --no-deps",
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
