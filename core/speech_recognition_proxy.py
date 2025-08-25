import speech_recognition as sr
import socket
import socks
import os
import time
from core.text_to_speech import speak

class ProxyAwareSpeechRecognition:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.original_socket = socket.socket
        
    def _is_proxy_enabled(self):
        """Check if proxy is currently enabled"""
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        return any(var in os.environ for var in proxy_vars)
    
    def _temporarily_disable_proxy(self):
        """Temporarily disable proxy for speech recognition"""
        # Store current proxy settings
        proxy_backup = {}
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'SOCKS_PROXY',
                     'http_proxy', 'https_proxy', 'ftp_proxy', 'socks_proxy']
        
        for var in proxy_vars:
            if var in os.environ:
                proxy_backup[var] = os.environ[var]
                del os.environ[var]
        
        # Reset socket to default
        socket.socket = self.original_socket
        
        return proxy_backup
    
    def _restore_proxy(self, proxy_backup):
        """Restore proxy settings"""
        for var, value in proxy_backup.items():
            os.environ[var] = value
        
        # If SOCKS proxy was enabled, restore it
        if any('socks' in var.lower() for var in proxy_backup.keys()):
            try:
                socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
                socket.socket = socks.socksocket
            except Exception as e:
                print(f"[SpeechRecognition] Failed to restore SOCKS proxy: {e}")
    
    def recognize_audio(self, audio_file_path, retries=3):
        """Recognize speech from audio file with proxy handling and retries"""
        for attempt in range(retries):
            try:
                # First try with current network settings
                with sr.AudioFile(audio_file_path) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.record(source)
                
                # Try recognition
                command = self.recognizer.recognize_google(audio)
                print(f"[SpeechRecognition] Recognized: {command}")
                return command.lower()
                
            except sr.RequestError as e:
                print(f"[SpeechRecognition] Request error (attempt {attempt + 1}): {e}")
                
                # If this is a connection error and proxy is enabled, try without proxy
                if "connection" in str(e).lower() and self._is_proxy_enabled():
                    try:
                        print("[SpeechRecognition] Trying without proxy...")
                        proxy_backup = self._temporarily_disable_proxy()
                        
                        # Retry recognition without proxy
                        with sr.AudioFile(audio_file_path) as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                            audio = self.recognizer.record(source)
                        
                        command = self.recognizer.recognize_google(audio)
                        print(f"[SpeechRecognition] Recognized without proxy: {command}")
                        
                        # Restore proxy settings
                        self._restore_proxy(proxy_backup)
                        
                        return command.lower()
                        
                    except Exception as proxy_error:
                        print(f"[SpeechRecognition] Proxy bypass failed: {proxy_error}")
                        # Restore proxy settings even if failed
                        try:
                            self._restore_proxy(proxy_backup)
                        except:
                            pass
                
                # Wait before retry
                if attempt < retries - 1:
                    time.sleep(1)
                    
            except sr.UnknownValueError:
                print("[SpeechRecognition] Could not understand audio")
                return ""
            except Exception as e:
                print(f"[SpeechRecognition] Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(1)
        
        # All attempts failed
        print("[SpeechRecognition] All recognition attempts failed")
        speak("Speech recognition error. Please try again.")
        return "network error"
    
    def listen_with_microphone(self, timeout=5, phrase_time_limit=3, retries=2):
        """Listen to microphone with proxy handling"""
        for attempt in range(retries):
            try:
                with sr.Microphone() as source:
                    print("🎧 Listening...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
                # Try recognition
                try:
                    command = self.recognizer.recognize_google(audio)
                    print(f"[SpeechRecognition] Heard: {command}")
                    return command.lower()
                except sr.RequestError as e:
                    print(f"[SpeechRecognition] Request error: {e}")
                    
                    # If proxy is enabled, try without proxy
                    if self._is_proxy_enabled():
                        proxy_backup = self._temporarily_disable_proxy()
                        try:
                            command = self.recognizer.recognize_google(audio)
                            print(f"[SpeechRecognition] Recognized without proxy: {command}")
                            self._restore_proxy(proxy_backup)
                            return command.lower()
                        except Exception as proxy_error:
                            print(f"[SpeechRecognition] Proxy bypass failed: {proxy_error}")
                            self._restore_proxy(proxy_backup)
                
            except sr.WaitTimeoutError:
                print("[SpeechRecognition] Listening timeout")
                return ""
            except sr.UnknownValueError:
                print("[SpeechRecognition] Could not understand audio")
                return ""
            except Exception as e:
                print(f"[SpeechRecognition] Microphone error (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(0.5)
        
        return "error"

# Global instance
proxy_aware_sr = ProxyAwareSpeechRecognition()
