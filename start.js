module.exports = {
  "run": [
    {
      "method": "shell.run",
      "params": {
        "message": ".venv\\Scripts\\activate && python main.py",
        "path": "{{path}}"
      }
    }
  ]
}
