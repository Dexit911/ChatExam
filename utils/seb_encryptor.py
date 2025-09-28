#!/usr/bin/env python3
"""
Safe Exam Browser Configuration Encryptor
Encrypts XML configuration files into SEB format based on the Safe Exam Browser codebase.
"""

import gzip
import base64
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets


def compress_gzip(data):
    """
    Compress data using gzip
    """
    try:
        return gzip.compress(data)
    except Exception as e:
        print(f"Error compressing data: {e}")
        return None


def add_prefix_to_data(data, prefix):
    """
    Add a 4-character prefix to data
    """
    prefix_bytes = prefix.encode('utf-8')
    if len(prefix_bytes) != 4:
        raise ValueError("Prefix must be exactly 4 characters")

    return prefix_bytes + data


def encrypt_with_password(data, password):
    """
    Encrypt data with password using AES (mimicking SEB's password encryption)
    This is a simplified version - SEB uses more complex key derivation
    """
    try:
        # Create a salt
        salt = secrets.token_bytes(16)

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))

        # Create IV
        iv = secrets.token_bytes(16)

        # Pad the data to AES block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data)
        padded_data += padder.finalize()

        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # Return salt + iv + encrypted_data
        return salt + iv + encrypted_data

    except Exception as e:
        print(f"Error encrypting with password: {e}")
        return None


def validate_xml(xml_data):
    """
    Validate that the input is valid XML
    """
    try:
        ET.fromstring(xml_data)
        return True
    except ET.ParseError as e:
        print(f"Invalid XML: {e}")
        return False


def clean_xml(xml_string):
    """
    Clean XML by replacing self-closing tags with proper empty tags (SEB format requirement)
    """
    cleaned = xml_string.replace("<array />", "<array></array>")
    cleaned = cleaned.replace("<dict />", "<dict></dict>")
    cleaned = cleaned.replace("<data />", "<data></data>")
    return cleaned


def encrypt_seb_config(xml_data, password=None, encryption_mode="plain"):
    """
    Main encryption function that follows the SEB encryption logic

    Args:
        xml_data: XML configuration data as bytes or string
        password: Password for encryption (optional)
        encryption_mode: "plain", "password", or "password_config"
    """

    # Convert to bytes if string
    if isinstance(xml_data, str):
        xml_data = xml_data.encode('utf-8')

    print(f"Input XML data length: {len(xml_data)} bytes")

    # Validate XML
    if not validate_xml(xml_data):
        return None

    # Clean XML (SEB format requirement)
    xml_string = xml_data.decode('utf-8')
    cleaned_xml = clean_xml(xml_string)
    seb_data = cleaned_xml.encode('utf-8')

    print(f"Cleaned XML data length: {len(seb_data)} bytes")

    # First, gzip compress the XML data
    compressed_data = compress_gzip(seb_data)
    if compressed_data is None:
        print("Failed to compress XML data")
        return None

    print(f"Compressed data length: {len(compressed_data)} bytes")

    # Apply encryption based on mode
    if encryption_mode == "password" and password:
        print("Encrypting with password...")
        encrypted_data = encrypt_with_password(compressed_data, password)
        if encrypted_data is None:
            return None

        # Add password mode prefix
        prefixed_data = add_prefix_to_data(encrypted_data, "pswd")

    elif encryption_mode == "password_config" and password:
        print("Encrypting with password for client configuration...")
        # Hash the password for client configuration mode
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest().upper()
        encrypted_data = encrypt_with_password(compressed_data, password_hash)
        if encrypted_data is None:
            return None

        # Add password configuring client mode prefix
        prefixed_data = add_prefix_to_data(encrypted_data, "pwcc")

    else:
        # Plain data mode (no encryption)
        print("Using plain data mode (no encryption)...")
        prefixed_data = add_prefix_to_data(compressed_data, "plnd")

    # Finally, gzip the entire result (outer layer compression)
    final_data = compress_gzip(prefixed_data)
    if final_data is None:
        print("Failed to compress final data")
        return None

    print(f"Final encrypted data length: {len(final_data)} bytes")
    return final_data


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python seb_encrypt.py <xml_file> [password] [mode]")
        print("Where:")
        print("  xml_file: Path to XML configuration file")
        print("  password: Optional password for encryption")
        print("  mode: 'plain' (default), 'password', or 'password_config'")
        print("")
        print("Examples:")
        print("  python seb_encrypt.py config.xml")
        print("  python seb_encrypt.py config.xml mypassword password")
        print("  python seb_encrypt.py config.xml admin123 password_config")
        sys.exit(1)

    xml_file = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    mode = sys.argv[3] if len(sys.argv) > 3 else "plain"

    if mode not in ["plain", "password", "password_config"]:
        print("Error: Mode must be 'plain', 'password', or 'password_config'")
        sys.exit(1)

    if mode != "plain" and not password:
        print("Error: Password required for encryption modes")
        sys.exit(1)

    # Read XML file
    if not os.path.isfile(xml_file):
        print(f"Error: File '{xml_file}' not found")
        sys.exit(1)

    print(f"Reading XML file: {xml_file}")

    try:
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_data = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Encrypt the configuration
    encrypted_data = encrypt_seb_config(xml_data, password, mode)

    if encrypted_data is None:
        print("Encryption failed")
        sys.exit(1)

    # Generate output filename
    base_name = os.path.splitext(xml_file)[0]
    output_file = f"{base_name}.seb"

    # Write encrypted data to .seb file
    try:
        with open(output_file, 'wb') as f:
            f.write(encrypted_data)

        print(f"\nSEB configuration created successfully: {output_file}")
        print(f"Encryption mode: {mode}")
        if password:
            print("Password protection: Enabled")
        else:
            print("Password protection: None (plain data)")

    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()