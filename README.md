# 🐝 Hornet AI 

Hornet is a **fully local, voice-driven AI assistant** and **custom OS bootloader**, built from scratch with a focus on:
- **Privacy** → 100% on-device (no cloud dependency)
- **Performance** → GPU-accelerated for low-latency responses
- **Accessibility** → Hands-free, voice-first computing from pre-boot to everyday tasks

---

## 🚀 Features

### Hornet AI
- 🎤 **Voice Commands** → Control apps, system, and workflows naturally
- 🔑 **Speaker Verification** → ECAPA-TDNN biometric authentication
- 🗣️ **Speech-to-Text** → Offline transcription with Fast-Whisper
- 🗣️ **Text-to-Speech** → VITS voice cloning for personalized responses
- 📱 **Cross-Platform Control** → Syncs with Android via native Kotlin app
- ⚡ **Automation** → Automates WhatsApp, Email, VS Code project creation, and more

### Hornet OS
- 🖥️ **Custom Bootloader** → Voice-controlled booting into Linux/Windows
- 🔒 **Secure Environment** → Early-layer biometric authentication
- 🌍 **Accessibility** → Boot and navigate your PC entirely hands-free

---

## 📊 Benchmarks

- **Response Time**: 3.5–5s (with security enabled)  
- **Privacy**: 100% on-device, no data sent to external servers  
- **Comparison**: Faster and more secure than cloud-only assistants like Gemini (6–9s, cloud-dependent)  

---

## 📹 Demo Videos

- 🎥 [Hornet AI Demo](https://youtu.be/79rBn9pySeA)  
- 🎥 [Hornet OS Demo](https://youtu.be/9AZXhmtRzU0)  

---

## 🛠️ Tech Stack

### Languages & Frameworks
- **Python** → Core assistant logic, AI/ML integration, and automation
- **Kotlin (Android)** → Native mobile app for cross-platform device control
- **PowerShell / Bash** → System-level automation scripts

### Machine Learning & AI
- **Local LLM (Llama / GPT models)** → Fully offline text generation and reasoning
- **ECAPA-TDNN (SpeechBrain)** → Real-time speaker verification and biometric authentication
- **Faster-Whisper** → High-speed, GPU-accelerated offline speech-to-text
- **VITS** → Neural TTS for hyper-realistic voice cloning
- **PyTorch & CUDA** → Deep learning framework with GPU acceleration
- **Numpy / Scipy / Librosa** → Audio signal processing and feature extraction

### Voice & Audio Processing
- **Picovoice Porcupine** → On-device wake word detection ("Hey Hornet")
- **PyAudio / sounddevice** → Real-time audio I/O management
- **Fast whisper** → Speech-to-text pipeline integration
- **gTTS** → Voice note generation for messaging apps

### OS & System Tools
- **Arch Linux** → Base for Hornet OS bootloader
- **GRUB / Custom Bootloader Scripts** → Voice-controlled OS selection at boot
- **ADB Bridge** → Secure Python ↔ Android communication
- **pywin32 / pycaw** → Low-level Windows control (audio, system settings)

### Security & Networking
- **Tor Integration** → Voice-controlled anonymity and onion routing
- **Multi-layered Security Stack** → Biometric checks, replay-attack detection
- **Custom IDS (Roadmap)** → AI-assisted intrusion detection and firewall
- **Automatic IP Switching & Onion Routing** → Network-level privacy

### Software Engineering & Automation
- **CommandHandler (custom framework)** → Routes natural language commands to actions
- **Selenium / PyAutoGUI** → Browser and GUI automation
- **WhatsApp & Email Automation** → Task-specific communication automation
- **VS Code Project Generator** → AI-assisted project and code generation

### DevOps & Version Control
- **Git / GitHub** → Source code management
- **Virtual Environments (venv)** → Python dependency isolation
- **Gradle** → Android app build automation


