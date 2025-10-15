import os

from pathlib import Path

from chat_exam.utils.seb_encryptor import encrypt_seb_config


class Seb_manager:

    @staticmethod
    def generate_seb_file(settings: dict, attempt_id: int, exam_code: str, token: str, encrypt: bool = True) -> str:
        """
        Generates individual SEB file for student with their own token url.

        :param settings: (dict) with keys for settings. Example ->
            "browserViewMode": None <- or "on",
            "allowQuit": None <- or "on",
            "allowClipboard": None <- or "on",
        :param attempt_id: (int) id of the attempt
        :param exam_code: (str) string with exam code
        :param token: (str) with token for url
        :param encrypt: (bool) True to encrypt SEB configuration

        :return: (str) path to SEB config file
        """

        # === Get settings for xml string ===
        view_mode = "1" if settings.get("browserViewMode") else "0"
        allow_quit = "true" if settings.get("allowQuit") else "false"
        allow_clipboard = "true" if settings.get("allowClipboard") else "false"

        # === Generate tokenized url for xml string ===
        exam_url = Seb_manager.generate_exam_url(
            exam_code=exam_code,
            token=token,
        )

        # === Put every thing in this template ===
        xml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
          <key>startURL</key>
          <string>{exam_url}</string>
        
          <key>sebConfigPurpose</key>
          <integer>0</integer>
        
          <key>browserViewMode</key>
          <integer>{view_mode}</integer>
        
          <key>allowQuit</key>
          <{allow_quit}/>
        
          <key>allowClipboard</key>
          <{allow_clipboard}/>
            
          <key>ignoreServerCertificate</key>
          <true/>

          <key>allowBrowsingBackForward</key>
          <true/>
          
          <key>enableJavaScript</key>
          <true/>
          
          <key>blockPopUpWindows</key>
          <true/>
          
          <key>allowDownloads</key>
          <true/>
        
          <key>additionalResources</key><array/>

          <key>allowURLFilter</key>
          <false/>
          
          <key>allowQuitURL</key>
          <true/>
          
          <key>quitURL</key>
          <string>safeexambrowser://quit</string>
          
          <key>allowContentReload</key>
          <true/>
          
          <key>ignoreServerCertificate</key>
          <true/>
          
          
        </dict>
        </plist>"""

        # === Save config and return its path ===
        Seb_manager.save_seb_file(
            xml_str=xml_str,
            attempt_id=attempt_id,
            encrypt=encrypt,
        )

    @staticmethod
    def generate_exam_url(exam_code: str, token: str) -> str:
        return f"localhost:80/student/exam/{exam_code}?token={token}"""

    @staticmethod
    def save_seb_file(xml_str: str, attempt_id: int, encrypt: bool = True):
        """
        Saves exam file with attempt id in its name

        :param xml_str: (str) xml string
        :param attempt_id: (int) id of the attempt
        :param encrypt: (bool) True to encrypt SEB configuration
        """
        # Encrypt if needed
        if encrypt:
            xml_str = encrypt_seb_config(xml_str)

        # Create seb_config in project root (one level above chat_exam)
        base_dir = Path(__file__).resolve().parents[2]  # → chat_exam/
        seb_dir = base_dir / "instance" / "seb_config"
        seb_dir.mkdir(parents=True, exist_ok=True)
        seb_path = seb_dir / f"exam_{attempt_id}.seb"

        # Write down .seb file and save it
        with open(seb_path, "w") as f:
            f.write(xml_str)

    @staticmethod
    def delete_seb_file(attempt_id: int) -> None:
        """
        Delete a SEB config file safely.
        :param attempt_id: (int) id of the attempt
        """

        base_dir = Path(__file__).resolve().parents[2]  # → chat_exam/
        seb_dir = base_dir / "instance" / "seb_config"
        seb_dir.mkdir(parents=True, exist_ok=True)
        seb_path = seb_dir / f"exam_{attempt_id}.seb"

        try:
            os.remove(seb_path)
            print(f"[ OK ] Deleted SEB file: {seb_path}")
        except FileNotFoundError:
            print(f"[ WARN ] SEB file already deleted: {seb_path}")
        except Exception as e:
            print(f"[ ERROR ] Could not delete SEB file {seb_path}: {e}")
