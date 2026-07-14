VERSION_INFO_CONTENT = """# -*- coding: utf-8 -*-
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 1, 0, 0),
    prodvers=(1, 1, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', "Steve's Khmer Apps"),
            StringStruct('FileDescription', 'KeyBeam Barcode Bridge'),
            StringStruct('FileVersion', '1.1.0.0'),
            StringStruct('InternalName', 'KeyBeam'),
            StringStruct('LegalCopyright', 'Copyright (c) 2026 Steve. All rights reserved.'),
            StringStruct('OriginalFilename', 'KeyBeam.exe'),
            StringStruct('ProductName', 'KeyBeam'),
            StringStruct('ProductVersion', '1.1.0.0')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""

def generate_version_file(output_path="version_info.txt"):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(VERSION_INFO_CONTENT)
    print(f"Generated PyInstaller version info template at: {output_path}")

if __name__ == "__main__":
    generate_version_file()
