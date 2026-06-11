module.exports = {
  "run": [
    {
      "method": "shell.run",
      "params": {
        "message": "conda run -n swiftdiffusion python main.py",
        "path": "{{path}}"
      }
    }
  ]
}
