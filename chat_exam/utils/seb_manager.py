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
    def create_configuration_file(config: str) -> None:
       """
       Create encrypted SEB exam file. When this file is started, you drop to the exam.

       :param config: string SEB configuration file in xml format
       """

       encrypted_config = encrypt_seb_config(config)


       with open("exam.seb", "wb") as f:
           f.write(encrypted_config)