import subprocess
import threading
import time
import requests
import os
from stem import Signal
from stem.control import Controller
from stem.process import launch_tor_with_config
import socket
import socks
from core.text_to_speech import speak
import geocoder
import folium

# ---------- 🔧 Configuration ---------- #
TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051
TOR_PASSWORD = "HornetTor123"  # Change this to your password

# Network modes
NETWORK_MODE_STANDARD = "standard"
NETWORK_MODE_ONION = "onion"
NETWORK_MODE_ADVANCED = "advanced"

class NetworkSafety:
    def __init__(self):
        self.current_mode = NETWORK_MODE_STANDARD
        self.tor_process = None
        self.controller = None
        self.ip_rotation_thread = None
        self.stop_rotation = False
        self.original_ip = None
        self.current_ip = None
        self.ip_history = []
        
    def get_public_ip(self):
        """Get current public IP address"""
        try:
            # Try multiple services for redundancy
            services = [
                'https://api.ipify.org',
                'https://icanhazip.com',
                'https://ident.me'
            ]
            
            # Use Tor proxy if in onion or advanced mode
            proxies = None
            if self.current_mode in [NETWORK_MODE_ONION, NETWORK_MODE_ADVANCED]:
                proxies = {
                    'http': f'socks5://127.0.0.1:{TOR_SOCKS_PORT}',
                    'https': f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                }
            
            for service in services:
                try:
                    response = requests.get(service, timeout=15, proxies=proxies)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        # Validate IP format
                        import re
                        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                            return ip
                except requests.exceptions.RequestException as e:
                    print(f"[NetworkSafety] Service {service} failed: {e}")
                    continue
                except Exception as e:
                    print(f"[NetworkSafety] Unexpected error with {service}: {e}")
                    continue
                    
            return "Unable to fetch IP"
        except Exception as e:
            print(f"[NetworkSafety] Error getting IP: {e}")
            return "Error fetching IP"
    
    def setup_tor_config(self):
        """Create torrc configuration file"""
        torrc_content = f"""
SocksPort {TOR_SOCKS_PORT}
ControlPort {TOR_CONTROL_PORT}
HashedControlPassword {self._hash_password(TOR_PASSWORD)}
MaxCircuitDirtiness 10
NewCircuitPeriod 10
CircuitBuildTimeout 10
LearnCircuitBuildTimeout 0
CircuitStreamTimeout 10
"""
        
        torrc_path = os.path.join(os.path.dirname(__file__), "torrc")
        with open(torrc_path, 'w') as f:
            f.write(torrc_content)
        return torrc_path
    
    def _hash_password(self, password):
        """Hash password for TOR control authentication"""
        try:
            # Try to find tor executable first
            tor_path = self._find_tor_executable()
            if tor_path:
                result = subprocess.run(
                    [tor_path, "--hash-password", password],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    hash_line = result.stdout.strip().split('\n')[-1]
                    print(f"[NetworkSafety] Generated hash: {hash_line}")
                    return hash_line
        except Exception as e:
            print(f"[NetworkSafety] Error generating hash: {e}")
        
        # Fallback: try with system tor
        try:
            result = subprocess.run(
                ["tor", "--hash-password", password],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                hash_line = result.stdout.strip().split('\n')[-1]
                print(f"[NetworkSafety] Generated hash (system): {hash_line}")
                return hash_line
        except Exception as e:
            print(f"[NetworkSafety] System tor hash failed: {e}")
        
        # Generate hash manually using stem
        try:
            from stem.util import connection
            from stem.util.system import pid_by_name
            import hashlib
            import base64
            import os
            
            # Generate salt
            salt = os.urandom(8)
            # Create hash
            hash_obj = hashlib.sha1()
            hash_obj.update(password.encode('utf-8'))
            hash_obj.update(salt)
            hashed = hash_obj.digest()
            
            # Encode in base64
            salt_b64 = base64.b64encode(salt).decode('ascii')
            hash_b64 = base64.b64encode(hashed).decode('ascii')
            
            manual_hash = f"16:{salt_b64}{hash_b64}"
            print(f"[NetworkSafety] Manual hash generated: {manual_hash}")
            return manual_hash
        except Exception as e:
            print(f"[NetworkSafety] Manual hash failed: {e}")
        
        # Last resort: use known working hash for 'HornetTor123'
        print("[NetworkSafety] Using default hash for 'HornetTor123'")
        return "16:044B948F29794C8260358C6E3F79A4429FCEB8CC3F3DA09705962A9363"
    
    def start_tor(self):
        """Start TOR service"""
        try:
            # Kill any existing TOR processes first
            self._kill_existing_tor()
            
            # Check if TOR is already running on the port
            if self._is_port_in_use(TOR_CONTROL_PORT):
                print("[NetworkSafety] Port already in use, attempting to connect...")
                try:
                    self.controller = Controller.from_port(port=TOR_CONTROL_PORT)
                    # Try different authentication methods
                    auth_success = self._try_authentication()
                    if auth_success:
                        print("[NetworkSafety] Connected to existing TOR instance")
                        return True
                except Exception as e:
                    print(f"[NetworkSafety] Failed to connect to existing TOR: {e}")
                    self._kill_existing_tor()
            
            # Start TOR with custom config
            torrc_path = self.setup_tor_config()
            print(f"[NetworkSafety] Starting TOR with config: {torrc_path}")
            
            # For Windows, try to use tor.exe
            if os.name == 'nt':
                tor_path = self._find_tor_executable()
                if tor_path:
                    print(f"[NetworkSafety] Using TOR executable: {tor_path}")
                    # Change to core directory before starting TOR
                    core_dir = os.path.dirname(__file__)
                    self.tor_process = subprocess.Popen(
                        [tor_path, "-f", torrc_path, "--quiet"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=core_dir,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                else:
                    speak("TOR executable not found. Please install TOR.")
                    return False
            else:
                # For Linux/Mac
                self.tor_process = subprocess.Popen(
                    ["tor", "-f", torrc_path, "--quiet"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait longer for TOR to start and bootstrap
            print("[NetworkSafety] Waiting for TOR to bootstrap...")
            for i in range(15):  # Wait up to 15 seconds
                time.sleep(1)
                if self._is_port_in_use(TOR_CONTROL_PORT):
                    break
                print(f"[NetworkSafety] TOR bootstrap progress: {i+1}/15")
            
            # Connect to control port
            try:
                self.controller = Controller.from_port(port=TOR_CONTROL_PORT)
                auth_success = self._try_authentication()
                
                if auth_success:
                    print("[NetworkSafety] TOR started and authenticated successfully")
                    speak("TOR network initialized")
                    return True
                else:
                    print("[NetworkSafety] TOR started but authentication failed")
                    return False
                    
            except Exception as e:
                print(f"[NetworkSafety] Failed to connect to TOR control port: {e}")
                return False
            
        except Exception as e:
            print(f"[NetworkSafety] Failed to start TOR: {e}")
            speak("Failed to start TOR network")
            return False
    
    def _kill_existing_tor(self):
        """Kill any existing TOR processes"""
        try:
            if os.name == 'nt':
                subprocess.run(["taskkill", "/f", "/im", "tor.exe"], 
                             capture_output=True, check=False)
            else:
                subprocess.run(["pkill", "-f", "tor"], 
                             capture_output=True, check=False)
            time.sleep(1)
        except Exception as e:
            print(f"[NetworkSafety] Error killing existing TOR: {e}")
    
    def _is_port_in_use(self, port):
        """Check if a port is in use"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex(('127.0.0.1', port))
            test_socket.close()
            return result == 0
        except:
            return False
    
    def _try_authentication(self):
        """Try different authentication methods"""
        auth_methods = [
            # Method 1: Use configured password
            lambda: self.controller.authenticate(password=TOR_PASSWORD),
            # Method 2: Try no authentication
            lambda: self.controller.authenticate(),
            # Method 3: Try cookie authentication
            lambda: self._try_cookie_auth(),
            # Method 4: Try empty password
            lambda: self.controller.authenticate(password="")
        ]
        
        for i, method in enumerate(auth_methods):
            try:
                method()
                print(f"[NetworkSafety] Authentication successful with method {i+1}")
                return True
            except Exception as e:
                print(f"[NetworkSafety] Auth method {i+1} failed: {e}")
                continue
        
        return False
    
    def _try_cookie_auth(self):
        """Try cookie-based authentication"""
        try:
            # Common cookie file locations
            cookie_paths = [
                os.path.join(os.path.expanduser("~"), ".tor", "control_auth_cookie"),
                os.path.join(os.getenv('APPDATA', ''), 'tor', 'control_auth_cookie'),
                "/var/lib/tor/control_auth_cookie",
                "/tmp/tor_control_cookie"
            ]
            
            for cookie_path in cookie_paths:
                if os.path.exists(cookie_path):
                    with open(cookie_path, 'rb') as cookie_file:
                        cookie = cookie_file.read()
                    self.controller.authenticate(cookie)
                    return True
        except Exception as e:
            print(f"[NetworkSafety] Cookie auth failed: {e}")
            raise
    
    def _find_tor_executable(self):
        """Find TOR executable on Windows"""
        # Check in the same directory first
        local_tor = os.path.join(os.path.dirname(__file__), "tor", "tor.exe")
        if os.path.exists(local_tor):
            return local_tor
            
        possible_paths = [
            r"C:\Tor\tor.exe",
            r"C:\Program Files\Tor\tor.exe",
            r"C:\Program Files (x86)\Tor\tor.exe",
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Tor', 'tor.exe')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(["where", "tor"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
            
        return None
    
    def configure_tor_proxy(self):
        """Configure system to use TOR proxy"""
        # Set up SOCKS proxy for Python applications
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", TOR_SOCKS_PORT)
        socket.socket = socks.socksocket
        
        # Configure requests to use TOR
        session = requests.Session()
        session.proxies = {
            'http': f'socks5://127.0.0.1:{TOR_SOCKS_PORT}',
            'https': f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
        }
        
        # Configure system-wide proxy settings (Windows)
        if os.name == 'nt':
            self._set_windows_system_proxy(True)
        
        return session
    
    def _set_windows_system_proxy(self, enable=True):
        """Configure Windows system-wide proxy settings"""
        try:
            import winreg
            
            # Registry path for Internet Settings
            registry_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    # Enable proxy
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                    # Set SOCKS proxy (format: socks=127.0.0.1:9050)
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"socks=127.0.0.1:{TOR_SOCKS_PORT}")
                    # Bypass proxy for local addresses
                    winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "127.*;192.168.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;localhost")
                    print("[NetworkSafety] System-wide proxy enabled")
                    speak("System-wide proxy enabled. All traffic will route through Tor.")
                    
                    # Also set environment variables for command-line tools
                    self._set_proxy_environment_variables(True)
                    
                else:
                    # Disable proxy
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
                    winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "")
                    print("[NetworkSafety] System-wide proxy disabled")
                    speak("System-wide proxy disabled. Normal internet connection restored.")
                    
                    # Clear environment variables
                    self._set_proxy_environment_variables(False)
            
            # Refresh Internet Settings
            self._refresh_internet_settings()
            
        except Exception as e:
            print(f"[NetworkSafety] Failed to configure system proxy: {e}")
            speak("Failed to configure system-wide proxy settings")
    
    def _set_proxy_environment_variables(self, enable=True):
        """Set proxy environment variables for command-line tools"""
        try:
            if enable:
                # Set proxy environment variables
                os.environ['HTTP_PROXY'] = f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                os.environ['HTTPS_PROXY'] = f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                os.environ['FTP_PROXY'] = f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                os.environ['SOCKS_PROXY'] = f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                
                # Also try lowercase versions (some tools prefer these)
                os.environ['http_proxy'] = f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                os.environ['https_proxy'] = f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                os.environ['ftp_proxy'] = f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                os.environ['socks_proxy'] = f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                
                print("[NetworkSafety] Proxy environment variables set")
            else:
                # Clear proxy environment variables
                proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'FTP_PROXY', 'SOCKS_PROXY',
                             'http_proxy', 'https_proxy', 'ftp_proxy', 'socks_proxy']
                for var in proxy_vars:
                    if var in os.environ:
                        del os.environ[var]
                print("[NetworkSafety] Proxy environment variables cleared")
                
        except Exception as e:
            print(f"[NetworkSafety] Failed to set proxy environment variables: {e}")
    
    def _refresh_internet_settings(self):
        """Refresh Windows Internet Settings to apply proxy changes"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Constants for InternetSetOption
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            INTERNET_OPTION_REFRESH = 37
            
            # Load wininet.dll
            wininet = ctypes.windll.wininet
            
            # Notify that settings have changed
            wininet.InternetSetOptionW(None, INTERNET_OPTION_SETTINGS_CHANGED, None, 0)
            wininet.InternetSetOptionW(None, INTERNET_OPTION_REFRESH, None, 0)
            
            print("[NetworkSafety] Internet settings refreshed")
            
        except Exception as e:
            print(f"[NetworkSafety] Failed to refresh internet settings: {e}")
    
    def switch_identity(self):
        """Switch TOR identity (get new IP)"""
        try:
            if self.controller:
                # Check if controller is still connected
                if not self.controller.is_alive():
                    print("[NetworkSafety] Controller disconnected, reconnecting...")
                    try:
                        self.controller = Controller.from_port(port=TOR_CONTROL_PORT)
                        self.controller.authenticate(password=TOR_PASSWORD)
                    except Exception as reconnect_error:
                        print(f"[NetworkSafety] Failed to reconnect controller: {reconnect_error}")
                        return False
                
                self.controller.signal(Signal.NEWNYM)
                time.sleep(5)  # Wait longer for new circuit to establish
                new_ip = self.get_public_ip()
                
                # Only update if we got a valid new IP
                if new_ip and new_ip not in ["Unable to fetch IP", "Error fetching IP"]:
                    self.current_ip = new_ip
                    self.ip_history.append(new_ip)
                    print(f"[NetworkSafety] Switched to new IP: {new_ip}")
                    return True
                else:
                    print("[NetworkSafety] Failed to get new IP after identity switch")
                    return False
        except Exception as e:
            print(f"[NetworkSafety] Failed to switch identity: {e}")
            # Try to recover connection
            try:
                if self.controller:
                    self.controller.close()
                self.controller = Controller.from_port(port=TOR_CONTROL_PORT)
                self.controller.authenticate(password=TOR_PASSWORD)
                print("[NetworkSafety] Controller connection recovered")
            except:
                print("[NetworkSafety] Could not recover controller connection")
            return False
    
    def start_advanced_mode(self):
        """Start automatic IP rotation every 10 seconds"""
        if self.current_mode != NETWORK_MODE_ADVANCED:
            self.current_mode = NETWORK_MODE_ADVANCED
            self.stop_rotation = False
            
            def rotate_ip():
                consecutive_failures = 0
                while not self.stop_rotation:
                    try:
                        success = self.switch_identity()
                        if success:
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            
                        # If too many failures, pause longer
                        if consecutive_failures >= 3:
                            print("[NetworkSafety] Multiple identity switch failures, pausing...")
                            time.sleep(30)  # Wait 30 seconds before retrying
                            consecutive_failures = 0
                        else:
                            time.sleep(10)
                    except Exception as e:
                        print(f"[NetworkSafety] Error in IP rotation thread: {e}")
                        time.sleep(10)
            
            self.ip_rotation_thread = threading.Thread(target=rotate_ip, daemon=True)
            self.ip_rotation_thread.start()
            
            speak("Advanced mode activated. IP will rotate every 10 seconds.")
            print("[NetworkSafety] Advanced mode activated")
    
    def stop_advanced_mode(self):
        """Stop automatic IP rotation"""
        self.stop_rotation = True
        if self.ip_rotation_thread:
            self.ip_rotation_thread.join(timeout=2)
        speak("Advanced mode deactivated")
        print("[NetworkSafety] Advanced mode deactivated")
    
    def switch_mode(self, mode):
        """Switch between network safety modes"""
        # Store original IP if not already stored
        if not self.original_ip:
            self.original_ip = self.get_public_ip()
        
        print(f"[NetworkSafety] Switching from {self.current_mode} to {mode}")
        
        if mode == NETWORK_MODE_STANDARD:
            self.stop_advanced_mode()
            self.stop_tor()
            self.current_mode = NETWORK_MODE_STANDARD
            speak("Switched to standard mode")
            
        elif mode == NETWORK_MODE_ONION:
            self.stop_advanced_mode()
            if self.start_tor():
                self.configure_tor_proxy()
                self.current_mode = NETWORK_MODE_ONION
                print(f"[NetworkSafety] Successfully switched to onion mode")
                speak("Switched to onion routing mode")
            else:
                print(f"[NetworkSafety] Failed to switch to onion mode")
                speak("Failed to enable onion routing")
            
        elif mode == NETWORK_MODE_ADVANCED:
            if self.current_mode != NETWORK_MODE_ONION:
                self.start_tor()
                self.configure_tor_proxy()
            self.start_advanced_mode()
    
    def stop_tor(self):
        """Stop TOR service and completely cleanup proxies"""
        try:
            # Disable system-wide proxy first
            if os.name == 'nt':
                self._set_windows_system_proxy(False)
            
            if self.controller:
                try:
                    self.controller.close()
                except:
                    pass
                self.controller = None
            
            if self.tor_process:
                try:
                    self.tor_process.terminate()
                    self.tor_process.wait(timeout=5)
                except:
                    try:
                        self.tor_process.kill()
                    except:
                        pass
                self.tor_process = None
            
            # Complete socket reset
            self._reset_sockets()
            
            # Force clear all proxy settings
            self._force_clear_proxy_settings()
            
            print("[NetworkSafety] TOR stopped and proxies cleared")
        except Exception as e:
            print(f"[NetworkSafety] Error stopping TOR: {e}")
    
    def _reset_sockets(self):
        """Completely reset socket configuration to default"""
        try:
            # Reset socks module
            import socket as _socket
            socket.socket = _socket.socket
            
            # Clear any socks configuration
            socks.set_default_proxy()
            
            print("[NetworkSafety] Sockets reset to default")
        except Exception as e:
            print(f"[NetworkSafety] Error resetting sockets: {e}")
    
    def _force_clear_proxy_settings(self):
        """Force clear all proxy settings including environment and Windows registry"""
        try:
            # Clear environment variables
            self._set_proxy_environment_variables(False)
            
            # Additional environment variables to clear
            additional_proxy_vars = [
                'all_proxy', 'ALL_PROXY', 'no_proxy', 'NO_PROXY',
                'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'
            ]
            for var in additional_proxy_vars:
                if var in os.environ:
                    del os.environ[var]
            
            # Force Windows registry cleanup
            if os.name == 'nt':
                try:
                    import winreg
                    registry_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
                        winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "")
                    
                    # Force refresh
                    self._refresh_internet_settings()
                except Exception as e:
                    print(f"[NetworkSafety] Registry cleanup error: {e}")
            
            print("[NetworkSafety] All proxy settings force cleared")
        except Exception as e:
            print(f"[NetworkSafety] Error force clearing proxy settings: {e}")
    
    def get_network_status(self):
        """Get current network safety status"""
        status = {
            "mode": self.current_mode,
            "current_ip": self.get_public_ip(),
            "original_ip": self.original_ip,
            "tor_active": self.controller is not None,
            "ip_rotation_active": not self.stop_rotation and self.current_mode == NETWORK_MODE_ADVANCED,
            "ip_history": self.ip_history[-10:]  # Last 10 IPs
        }
        return status
    
    def show_tor_circuit(self):
        """Show the 3-layer TOR circuit protection"""
        if self.current_mode != NETWORK_MODE_ONION and self.current_mode != NETWORK_MODE_ADVANCED:
            speak("Please enable onion mode first to see TOR circuit protection")
            return None
        
        try:
            if not self.controller:
                speak("TOR controller not available")
                return None
            
            # Get current circuit information
            circuits = list(self.controller.get_circuits())
            if not circuits:
                speak("No active TOR circuits found")
                return None
            
            # Get the most recent circuit
            current_circuit = circuits[-1]
            circuit_id = current_circuit.id
            path = current_circuit.path
            
            if len(path) < 3:
                speak("Circuit not fully established yet. Please wait.")
                return None
            
            print(f"\n🛡️ YOUR 3-LAYER TOR PROTECTION")
            print("=" * 50)
            print(f"Circuit ID: {circuit_id}")
            print(f"Status: {current_circuit.status}")
            
            # Show the 3 layers
            layer_names = ["🚪 ENTRY (Guard)", "🔄 MIDDLE (Relay)", "🌐 EXIT (Final)"]
            protection_info = []
            
            for i, (fingerprint, nickname) in enumerate(path[:3]):
                layer_name = layer_names[i]
                print(f"\n{layer_name}:")
                print(f"  Nickname: {nickname}")
                print(f"  Fingerprint: {fingerprint[:16]}...")
                
                # Get relay information
                try:
                    relay_desc = self.controller.get_network_status(fingerprint)
                    if relay_desc:
                        country = getattr(relay_desc, 'country', 'Unknown')
                        print(f"  Country: {country}")
                        protection_info.append({
                            'layer': i + 1,
                            'type': layer_name,
                            'nickname': nickname,
                            'country': country,
                            'fingerprint': fingerprint[:16]
                        })
                except:
                    protection_info.append({
                        'layer': i + 1,
                        'type': layer_name,
                        'nickname': nickname,
                        'country': 'Unknown',
                        'fingerprint': fingerprint[:16]
                    })
            
            print(f"\n🔐 ENCRYPTION LAYERS EXPLANATION:")
            print("─" * 40)
            print("Layer 1 (Entry): Only knows your real IP, not your destination")
            print("Layer 2 (Middle): Knows neither your IP nor destination")
            print("Layer 3 (Exit): Only knows destination, not your real IP")
            
            print(f"\n🛡️ PROTECTION SUMMARY:")
            print("─" * 40)
            print("✅ Your real IP is hidden from websites")
            print("✅ Websites can't trace back to you")
            print("✅ Each relay only knows one piece of the puzzle")
            print("✅ All traffic is encrypted 3 times")
            
            # Voice explanation
            if protection_info and len(protection_info) >= 3:
                entry_country = protection_info[0]['country']
                middle_country = protection_info[1]['country']
                exit_country = protection_info[2]['country']
                
                speak(f"Your traffic is protected by 3 layers. Entry relay in {entry_country}, middle relay in {middle_country}, and exit relay in {exit_country}. Each layer only knows one piece of the puzzle.")
            else:
                speak("Your traffic is protected by 3 TOR encryption layers. No single relay knows both your identity and destination.")
            
            return protection_info
            
        except Exception as e:
            print(f"[NetworkSafety] Error showing TOR circuit: {e}")
            speak("Error retrieving TOR circuit information")
            return None
    
    def trace_ip_location(self, ip=None):
        """Trace IP location and show on map"""
        if not ip:
            ip = self.current_ip or self.get_public_ip()
        
        try:
            # Try multiple IP geolocation services to avoid rate limits
            location_data = self._get_ip_location_data(ip)
            
            if location_data:
                lat, lon = location_data['lat'], location_data['lon']
                city = location_data['city']
                country = location_data['country']
                
                # Create map
                m = folium.Map(location=[lat, lon], zoom_start=10)
                folium.Marker(
                    [lat, lon],
                    popup=f"IP: {ip}<br>Location: {city}, {country}<br>Coords: {lat}, {lon}",
                    tooltip=f"{ip} - {city}, {country}"
                ).add_to(m)
                
                # Save and open map
                map_path = os.path.join(os.path.dirname(__file__), "ip_location.html")
                m.save(map_path)
                
                # Open in browser
                import webbrowser
                webbrowser.open(f"file:///{map_path}")
                
                speak(f"IP {ip} traced to {city}, {country}")
                return location_data
            else:
                speak("Could not trace IP location")
                return None
        except Exception as e:
            print(f"[NetworkSafety] Error tracing IP: {e}")
            speak("Error tracing IP location")
            return None
    
    def _get_ip_location_data(self, ip):
        """Get IP location data from multiple services to avoid rate limits"""
        # Service 1: Try ip-api.com (free, high rate limit)
        try:
            proxies = None
            if self.current_mode in [NETWORK_MODE_ONION, NETWORK_MODE_ADVANCED]:
                proxies = {
                    'http': f'socks5://127.0.0.1:{TOR_SOCKS_PORT}',
                    'https': f'socks5://127.0.0.1:{TOR_SOCKS_PORT}'
                }
            
            response = requests.get(f'http://ip-api.com/json/{ip}', proxies=proxies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'city': data.get('city', 'Unknown'),
                        'country': data.get('country', 'Unknown'),
                        'region': data.get('regionName', ''),
                        'isp': data.get('isp', ''),
                        'service': 'ip-api.com'
                    }
        except Exception as e:
            print(f"[NetworkSafety] ip-api.com failed: {e}")
        
        # Service 2: Try ipapi.co (backup)
        try:
            response = requests.get(f'https://ipapi.co/{ip}/json/', proxies=proxies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude'),
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'region': data.get('region', ''),
                    'isp': data.get('org', ''),
                    'service': 'ipapi.co'
                }
        except Exception as e:
            print(f"[NetworkSafety] ipapi.co failed: {e}")
        
        # Service 3: Try geocoder as last resort (uses ipinfo.io)
        try:
            g = geocoder.ip(ip)
            if g.latlng:
                return {
                    'lat': g.latlng[0],
                    'lon': g.latlng[1],
                    'city': g.city or 'Unknown',
                    'country': g.country or 'Unknown',
                    'region': g.state or '',
                    'isp': '',
                    'service': 'geocoder/ipinfo.io'
                }
        except Exception as e:
            print(f"[NetworkSafety] geocoder failed: {e}")
        
        # If all services fail, return None
        print(f"[NetworkSafety] All IP location services failed for {ip}")
        return None

# Global instance
network_safety = NetworkSafety()
