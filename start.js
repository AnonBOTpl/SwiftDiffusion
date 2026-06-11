module.exports = {
  "run": [
    {
      "method": "shell.run",
      "params": {
        "message": ".venv-uv\\Scripts\\activate.bat && python main.py",
        "path": "{{path}}"
      }
    }
  ]
}
