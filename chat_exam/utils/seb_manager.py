import os

from pathlib import Path

from chat_exam.utils.seb_encryptor import encrypt_seb_config


class Seb_manager:
    @staticmethod
    def create_config(settings: dict, exam_url: str) -> str:
        """
        This prepares string for SEB configuration file

        :param setting: dict with keys for settings. Example ->
        "browserViewMode": None <- or "on",
        "allowQuit": None <- or "on",
        "allowClipboard": None <- or "on",

        :param id: id of the exam
        :param debug: True or False, use if testing on local host

        :return: string with SEB configuration
        """
        view_mode = "1" if settings.get("browserViewMode") else "0"
        allow_quit = "true" if settings.get("allowQuit") else "false"
        allow_clipboard = "true" if settings.get("allowClipboard") else "false"

        url = exam_url
        url = url.replace("https://", "").replace("http://", "")
        print(f"=== SEB CONFIGURATION URL:\n{url}\n===")

        print(f"View Mode: {view_mode}\nAllow Quit: {allow_quit}\nallow Clipboard: {allow_clipboard}")

        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
          <key>startURL</key>
          <string>{url}</string>
        
          <key>sebConfigPurpose</key>
          <integer>0</integer>
        
          <key>browserViewMode</key>
          <integer>{view_mode}</integer>
        
          <key>allowQuit</key>
          <{allow_quit}/>
        
          <key>allowClipboard</key>
          <{allow_clipboard}/>
        
          <key>additionalResources</key>
          <array/>
        </dict>
        </plist>"""

    @staticmethod
    def save_configuration_file(xml_str: str, exam_id: int, encrypt: bool = True) -> None:
        """
        Create SEB exam file. When this file is started, you drop to the exam.
        :param xml_str: string with SEB configuration
        :param exam_id: id of the exam
        :param encrypt: True to encrypt SEB configuration
        """

        # Encrypt
        if encrypt:
            seb_config_str = encrypt_seb_config(xml_str)
        else:
            seb_config_str = xml_str

        # Create seb_config in project root (one level above chat_exam)
        base_dir = Path(__file__).resolve().parents[2]  # → chat_exam/
        seb_dir = base_dir / "instance" / "seb_config"
        seb_dir.mkdir(parents=True, exist_ok=True)

        seb_path = seb_dir / f"exam_{exam_id}.seb"

        # Write down .seb file and save it
        with open(seb_path, "w") as f:
            f.write(seb_config_str)
