import os
import re
from core.text_to_speech import speak
# REMOVED: Unnecessary imports for the old workflow
# from core.voice_auth import cleanup_temp_voice
# from core.voice_capture import record_voice_dynamic
# import speech_recognition as sr

from core.whatsapp import send_whatsapp_message, extract_contact_and_message, extract_voice_note_command, send_whatsapp_voice_note
from core.youtube import play_top_youtube_video, search_and_type_on_site
from core.system_tasks import perform_system_task
from core.browser import open_any_website, close_application, search_in_chrome
from core.mail_assistant import handle_send_mail
from core.screen_recording import start_screen_recording, stop_screen_recording, view_recording, last_recording_path
from core.basic_features import change_volume, change_brightness, take_screenshot, view_screenshot, open_recycle_bin, empty_recycle_bin
from core.extra_skills import repeat_after_me, set_timer, tell_about_person, tell_about_topic, explain_meaning
from core.music import play_song_on_spotify
from core.gemini import get_gemini_response
from core.utils import resource_path
from core.phone import call_contact, open_app_on_phone, lock_phone_screen, is_phone_connected, send_phone_basic_action,help_command
from core.enroll_voice import update_embedding
# from core.firewall import start_firewall_monitor, stop_firewall_monitor, trace_last_threat
from core.network_safety import network_safety

class CommandHandler:
    def __init__(self, gui_instance):
        self.gui = gui_instance

    # REMOVED: The old handle() method is no longer needed.
    # Its logic has been moved into the main Hornet.py file for better efficiency.

    def handle_text(self, command):
        """
        This is the main function that processes the transcribed text command.
        """
        command = command.lower().strip()
        self.gui.add_text("You: " + command)
        phone_connected = is_phone_connected()

        # ✅ PHONE HANDLING
        if phone_connected:
            if command.startswith("call "):
                name = command.replace("call", "").strip()
                speak(f"Calling {name} from phone.")
                self.gui.add_text(f"Calling {name} via phone.")
                call_contact(name)
                return
            if "help" in command or "emergency" in command:
                speak("Emergency help activated. Sending your location and IP to your contacts.")
                self.gui.add_text("[Phone] 🚨 Emergency help triggered")
                help_command()
                return


            if command.startswith("open app ") or command.startswith("open "):
                app = command.replace("open app", "").replace("open", "").replace("in my phone", "").replace("on my phone", "").strip()
                speak(f"Opening {app} on your phone.")
                self.gui.add_text(f"Opening app on phone: {app}")
                open_app_on_phone(app)
                return

            if "lock phone" in command or "lock screen" in command:
                speak("Locking your phone now.")
                self.gui.add_text("[Phone] Locking the screen.")
                lock_phone_screen()
                return

            if "wifi on" in command or "wi-fi on" in command:
                speak("Turning on Wi-Fi on your phone.")
                self.gui.add_text("[Phone] Wi-Fi on")
                send_phone_basic_action("wifi_on")
                return

            if "wifi off" in command or "wi-fi off" in command:
                speak("Turning off Wi-Fi on your phone.")
                self.gui.add_text("[Phone] Wi-Fi off")
                send_phone_basic_action("wifi_off")
                return

            if "bluetooth on" in command:
                speak("Turning on Bluetooth on your phone.")
                self.gui.add_text("[Phone] Bluetooth on")
                send_phone_basic_action("bt_on")
                return

            if "bluetooth off" in command:
                speak("Turning off Bluetooth on your phone.")
                self.gui.add_text("[Phone] Bluetooth off")
                send_phone_basic_action("bt_off")
                return

            if "pause music" in command or "pause song" in command:
                speak("Pausing music on your phone.")
                self.gui.add_text("[Phone] Pause music")
                send_phone_basic_action("pause_music")
                return

            if "play music" in command or "resume song" in command:
                speak("Resuming music on your phone.")
                self.gui.add_text("[Phone] Play music")
                send_phone_basic_action("play_music")
                return

            if "what's the battery" in command or "battery percentage" in command:
                speak("Fetching battery level on your phone.")
                self.gui.add_text("[Phone] Requesting battery status")
                send_phone_basic_action("get_battery")
                return

            if match := re.search(r"set volume to (\d+)", command):
                percent = int(match.group(1))
                speak(f"Setting phone volume to {percent} percent.")
                self.gui.add_text(f"[Phone] Volume set to {percent}%")
                send_phone_basic_action(f"volume_{percent}")
                return

        # ✅ PC-SPECIFIC HANDLING
        if command == "network error":
            self.gui.add_text("[System] Network error")
            speak("Network error.")
            return

        if "launch v1" in command:
            speak("Launching Jarvis version one. Buckle up.")
            os.system("python jarvis_ui.py")
            return
            


        voice_contact, voice_message = extract_voice_note_command(command)
        if voice_contact and voice_message:
            self.gui.add_text(f"Sending voice note to {voice_contact}: {voice_message}")
            speak(f"Sending your voice note to {voice_contact}")
            try:
                send_whatsapp_voice_note(voice_contact, voice_message)
            except Exception as e:
                speak("Failed to send the voice note.")
                self.gui.add_text(f"[Error] {e}")
            return
            
        contact, message = extract_contact_and_message(command)
        if contact and message:
            self.gui.add_text(f"Sending WhatsApp message to {contact}: {message}")
            speak(f"Sending your message to {contact}")
            try:
                send_whatsapp_message(contact, message)
            except Exception as e:
                speak("Failed to send the WhatsApp message.")
                self.gui.add_text(f"[Error] {e}")
            return
            
        # if "start firewall mode" in command or "enable hornet firewall" in command:
        #     speak("Enabling Hornet Firewall Mode.")
        #     self.gui.add_text("[Firewall] 🔥 Starting Hornet Firewall...")
        #     start_firewall_monitor(self.gui)
        #     return

        # if "stop firewall mode" in command or "disable hornet firewall" in command:
        #     speak("Disabling Hornet Firewall Mode.")
        #     self.gui.add_text("[Firewall] 🛑 Stopping Hornet Firewall...")
        #     stop_firewall_monitor()
        #     return

        # if "trace last attack" in command or "trace threat" in command:
        #     speak("Tracing the origin of the last threat.")
        #     self.gui.add_text("[Firewall] 🌍 Visualizing threat IP...")
        #     trace_last_threat()
        #     return
        
        # Network Safety Commands
        if "what is my ip" in command or "what is my current ip" in command or "show my ip" in command:
            current_ip = network_safety.get_public_ip()
            speak(f"Your current public IP address is {current_ip}")
            self.gui.add_text(f"[Network] Current IP: {current_ip}")
            return
        
        if "go advanced mode" in command or "enable advanced mode" in command:
            speak("Activating advanced network mode")
            self.gui.add_text("[Network] 🧅 Switching to advanced mode...")
            network_safety.switch_mode("advanced")
            return
        
        if "stop advanced mode" in command or "disable advanced mode" in command:
            speak("Deactivating advanced network mode")
            self.gui.add_text("[Network] Switching to standard mode...")
            network_safety.switch_mode("standard")
            return
        
        if any(phrase in command for phrase in ["go standard mode", "switch to standard mode", "disable onion mode", "turn off tor", "normal mode", "standard network", "disable tor", "stop onion"]):
            speak("Switching to standard network mode")
            self.gui.add_text("[Network] 🔄 Switching to standard mode...")
            network_safety.switch_mode("standard")
            return
        
        if "enable onion mode" in command or "start onion routing" in command:
            speak("Enabling onion routing mode")
            self.gui.add_text("[Network] 🧅 Enabling TOR network...")
            network_safety.switch_mode("onion")
            return
        
        if "network status" in command or "show network status" in command:
            status = network_safety.get_network_status()
            mode = status['mode']
            current_ip = status['current_ip']
            tor_active = "active" if status['tor_active'] else "inactive"
            rotation = "enabled" if status['ip_rotation_active'] else "disabled"
            
            status_msg = f"Network mode: {mode}. Current IP: {current_ip}. TOR is {tor_active}. IP rotation is {rotation}."
            speak(status_msg)
            self.gui.add_text(f"[Network] {status_msg}")
            return
        
        if "switch ip" in command or "change ip" in command or "new identity" in command:
            if network_safety.current_mode == "standard":
                speak("Please enable onion mode or advanced mode first")
                return
            speak("Switching to new identity")
            self.gui.add_text("[Network] 🔄 Switching IP...")
            network_safety.switch_identity()
            return
        
        if "trace my ip" in command or "show my location" in command:
            speak("Tracing your current IP location")
            self.gui.add_text("[Network] 📍 Tracing IP location...")
            network_safety.trace_ip_location()
            return
        
        if any(phrase in command for phrase in ["show my 3 layer protection", "show my three layer protection", "show tor circuit", "show my tor protection", "display circuit layers"]):
            speak("Displaying your TOR circuit protection layers")
            self.gui.add_text("[Network] 🔐 Analyzing TOR circuit layers...")
            network_safety.show_tor_circuit()
            return
        
        # if "list firewall blocks" in command or "show blocked ips" in command:
        #     from core.firewall import blocked_ips
        #     if blocked_ips:
        #         blocked_list = ", ".join(blocked_ips)
        #         speak(f"Currently blocked IPs: {blocked_list}")
        #         self.gui.add_text(f"[Firewall] Blocked IPs: {blocked_list}")
        #     else:
        #         speak("No IPs are currently blocked")
        #         self.gui.add_text("[Firewall] No blocked IPs")
        #     return
        
        # if "demo firewall" in command or "firewall demo" in command or "demo mode" in command:
        #     speak("Starting firewall demo mode")
        #     self.gui.add_text("[Firewall] Starting demo mode...")
        #     from core.firewall import start_firewall_monitor
        #     start_firewall_monitor(self.gui, demo=True)
        #     return
        
        # if "scan traffic" in command or "analyze traffic" in command or "scan incoming traffic" in command:
        #     from core.firewall import analyze_incoming_traffic
        #     analyze_incoming_traffic(self.gui)
        #     return
        
        # if "firewall stats" in command or "firewall statistics" in command:
        #     from core.firewall import get_firewall_stats
        #     stats = get_firewall_stats()
        #     speak(f"Firewall statistics: {stats['blocked_ips']} IPs blocked. Monitoring is {'active' if stats['monitoring_active'] else 'inactive'}.")
        #     self.gui.add_text(f"[Firewall Stats] Blocked: {stats['blocked_ips']} IPs, Status: {'Active' if stats['monitoring_active'] else 'Inactive'}")
        #     return

        if "generate project" in command or "create project" in command or "make project" in command:
           from core.ai_code_generator import generate_code_project
           prompt = command.replace("generate project", "").replace("create project", "").replace("make project", "").strip()
           if not prompt:
             speak("Please specify what kind of project you want.")
             return
           speak(f"Creating project for: {prompt}")
           generate_code_project(prompt)
           return

        if hasattr(self.gui, 'waiting_for_video_prompt') and self.gui.waiting_for_video_prompt:
            self.gui.waiting_for_video_prompt = False
            follow_up = command.replace("play", "").strip()
            if hasattr(self.gui, 'last_search_query') and hasattr(self.gui, 'youtube_driver'):
                combined = f"{self.gui.last_search_query} {follow_up}"
                speak(f"Playing top YouTube video for {combined}")
                play_top_youtube_video(combined, self.gui.youtube_driver)
            else:
                speak("I couldn't remember your last search.")
            return

        if "open" in command and "and search" in command:
            parts = command.replace("open", "").split("and search")
            website = parts[0].strip()
            query = parts[1].strip()
            speak(f"Opening {website} and searching for {query}")
            search_and_type_on_site(website, query)
            return

        if perform_system_task(command):
            return

        if "search" in command and "for" in command:
            parts = command.split("for")
            site_part = parts[0].replace("search", "").strip()
            query = parts[1].strip()

            for site in ["youtube", "instagram", "chatgpt", "twitter", "wikipedia"]:
                if site in site_part:
                    speak(f"Searching {site} for {query}")
                    driver = search_and_type_on_site(site, query)

                    if site == "youtube":
                        self.gui.last_search_query = query
                        self.gui.youtube_driver = driver
                        speak("Do you want me to play a specific video?")
                        self.gui.waiting_for_video_prompt = True
                    return

        elif "search" in command:
            search_term = command.replace("search", "").strip()
            speak(f"Searching for {search_term}")
            search_in_chrome(search_term)
            return

        if "view screenshot" in command or "show screenshot" in command:
            view_screenshot()
            return
            
        if "open recycle bin" in command:
            open_recycle_bin()
            return

        if "empty recycle bin" in command:
            empty_recycle_bin()
            return

        if "screenshot" in command:
            take_screenshot()
            return

        if "view recording" in command:
            view_recording()
            return

        if "screen" in command and "start" in command and "record" in command:
            start_screen_recording()
            return

        if "stop" in command and "record" in command:
            stop_screen_recording()
            return

        if "view screen recording" in command:
            if last_recording_path and os.path.exists(last_recording_path):
                os.startfile(last_recording_path)
                speak("Opening your screen recording.")
            else:
                speak("I couldn't find a recording to show.")
            return

        if "send a mail to" in command:
            handle_send_mail(command)
            return

        if "volume up" in command:
            change_volume("up")
            return

        if "volume down" in command:
            change_volume("down")
            return

        if re.search(r"set volume to (\d+)", command):
            percent = int(re.search(r"set volume to (\d+)", command).group(1))
            change_volume(percent=percent)
            return

        if "brightness up" in command:
            change_brightness("up")
            return

        if "brightness down" in command:
            change_brightness("down")
            return

        if re.search(r"set brightness to (\d+)", command):
            percent = int(re.search(r"set brightness to (\d+)", command).group(1))
            change_brightness(percent=percent)
            return
            
        if "open" in command:
            if open_any_website(command):
                return

        if "close" in command:
            close_application(command)
            return

        if "timer" in command:
            set_timer(command)
            return

        if repeat_after_me(command):
            return

        if explain_meaning(command):
            return

        if tell_about_topic(command):
            return

        if "tell me about" in command or "who is" in command:
            tell_about_person(command)
            return

        if "play" in command and "spotify" in command:
            play_song_on_spotify(command)
            return

        if "exit" in command:
            self.gui.add_text("[System] Exiting...")
            stop_firewall_monitor()
            speak("Goodbye!")
            self.gui.root.quit()
            return

        # # Gemini fallback
        # speak("I'm not sure how to do that, but let me ask my generative AI.")
        # self.gui.add_text("AI is thinking...")
        # gemini_response = get_gemini_response(command)
        # speak(gemini_response)
        # self.gui.add_text("AI: " + gemini_response)
