module.exports = {
  "title": "SwiftDiffusion",
  "description": "A clean, fast, VRAM-friendly GUI for Stable Diffusion 1.5 — built with PyQt6. Optimized for 6GB VRAM GPUs.",
  "icon": "screens/screen main.png",
  "menu": [
    {
      "when": "{{!exists(path, '.installed')}}",
      "items": [
        {
          "type": "start",
          "text": "Install",
          "href": "install.js"
        }
      ]
    },
    {
      "when": "{{exists(path, '.installed')}}",
      "items": [
        {
          "type": "start",
          "text": "Start",
          "href": "start.js"
        },
        {
          "type": "start",
          "text": "Reinstall",
          "href": "install.js"
        }
      ]
    }
  ]
}
