#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 Skill 

 Skill 
"""
# Copyright (c) 2026 WorkBuddy Skills. All rights reserved.
# Skill: tax-policy-knowledge | Version: 1.4.2
# Author: QQ 1817694478 | Q-Group: 972156177
# Unauthorized copying, modification, or distribution is prohibited.
# This software is provided "as is" without warranty of any kind.
import os
import shutil
import zipfile
import json
import datetime
from pathlib import Path
def create_install_package():
    """"""
    print("[TARGET]  Skill...")
    
    # 
    skill_dir = Path(".")
    output_dir = skill_dir / "dist"
    output_dir.mkdir(exist_ok=True)
    
    # 
    version = "1.4.2"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"tax-policy-knowledge-v{version}-{timestamp}"
    
    # 1.  zip 
    zip_path = output_dir / f"{package_name}.zip"
    print(f"[PKG] : {zip_path.name}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 
        include_patterns = [
            "*.md", "*.yaml", "*.py",
            "assets/*", "references/*", "scripts/*"
        ]
        
        files_added = 0
        for pattern in include_patterns:
            for file_path in skill_dir.glob(pattern):
                if file_path.is_file():
                    arcname = str(file_path.relative_to(skill_dir))
                    zipf.write(file_path, arcname)
                    files_added += 1
                    print(f"  [FILE] : {arcname}")
    
    # 2. 
    install_guide = output_dir / "INSTALL.md"
    install_content = f"""#  Skill 
## [PKG] 
- ****: {package_name}.zip
- ****: {version}
- ****: {timestamp}
- ****: {files_added} 
- ****: Windows/macOS/Linux
## [TOOL] 
### AiPy 
1.  `{package_name}.zip` 
2.  `tax-policy-knowledge`  AiPy  skills 
   - Windows: `%APPDATA%\\.aipyapp\\skills\\`
   - macOS/Linux: `~/.aipyapp/skills/`
3.  AiPy 
4. 
### 
1.  `{package_name}.zip` 
2. 
3. 
```bash
cd tax-policy-knowledge/scripts
python tax_policy_calculator.py vat --sales 150000
```
## [FOLDER] 
```
tax-policy-knowledge/
 SKILL.md                          # 
 skill.yaml                        # 
 README.md                         # 
 assets/                           # 
    wechat-qr.png                # 
    policy-overview.html         # 
    wechat-qr-preview.html       # 
 references/                       # 
    tax-policy-database.md       # 
 scripts/                          # 
     tax_policy_calculator.py     # 
     test_calculator.py           # 
```
## [TARGET] 
[OK] 
[OK] 
[OK] 
[OK] 
[OK] 
[OK] 4
## [PHONE] 

- QQ: 1817694478
- :  assets/wechat-qr.png
---
****: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
****: 
"""
    
    with open(install_guide, 'w', encoding='utf-8') as f:
        f.write(install_content)
    print(f"[NOTE] : {install_guide.name}")
    
    # 3. 
    checksum_file = output_dir / "CHECKSUM.md5"
    import hashlib
    with open(zip_path, 'rb') as f:
        md5_hash = hashlib.md5(f.read()).hexdigest()
    
    checksum_content = f"""# 
: {zip_path.name}
MD5: {md5_hash}
: {zip_path.stat().st_size} 
: {timestamp}
: {version}
:
```bash
# Windows
certutil -hashfile "{zip_path.name}" MD5
# macOS/Linux
md5sum "{zip_path.name}"
```
"""
    
    with open(checksum_file, 'w', encoding='utf-8') as f:
        f.write(checksum_content)
    print(f"[SEARCH] : {checksum_file.name}")
    
    # 4.  package.json  npm 
    package_json = {
        "name": "tax-policy-knowledge",
        "version": version,
        "description": "Skill",
        "main": "SKILL.md",
        "author": "AiPy Team",
        "license": "MIT",
        "keywords": ["tax", "policy", "china", "vat", "corporate-tax", "income-tax"],
        "files": [
            "SKILL.md",
            "skill.yaml",
            "README.md",
            "assets/",
            "references/",
            "scripts/"
        ],
        "install": "copy to ~/.aipyapp/skills/",
        "created": timestamp
    }
    
    package_json_path = output_dir / "package.json"
    with open(package_json_path, 'w', encoding='utf-8') as f:
        json.dump(package_json, f, indent=2, ensure_ascii=False)
    print(f"[LIST]  package.json: {package_json_path.name}")
    
    # 5. 
    install_script = output_dir / "install.sh"
    install_script_content = """#!/bin/bash
#  Skill 
echo "[TOOL]  Skill..."
echo "=========================================="
# 
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    # Linux  macOS
    SKILLS_DIR="$HOME/.aipyapp/skills"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash)
    SKILLS_DIR="$APPDATA/.aipyapp/skills"
else
    echo "[FAIL] : $OSTYPE"
    exit 1
fi
# 
mkdir -p "$SKILLS_DIR"
# 
echo "[FOLDER] : $SKILLS_DIR/tax-policy-knowledge"
cp -r tax-policy-knowledge "$SKILLS_DIR/"
# 
chmod -R 755 "$SKILLS_DIR/tax-policy-knowledge/scripts"/*.py 2>/dev/null
echo "[OK] "
echo ""
echo "[TARGET] :"
echo "1.  AiPy "
echo "2. :"
echo "   - "
echo "   - "
echo "   - "
echo "   - "
echo "3. :"
echo "   cd $SKILLS_DIR/tax-policy-knowledge/scripts"
echo "   python tax_policy_calculator.py vat --sales 150000"
echo ""
echo "[PHONE] : QQ 1817694478"
"""
    
    with open(install_script, 'w', encoding='utf-8') as f:
        f.write(install_script_content)
    # 
    if os.name != 'nt':  #  Windows 
        os.chmod(install_script, 0o755)
    print(f"[FAST] : {install_script.name}")
    
    # 6.  Windows 
    install_bat = output_dir / "install.bat"
    install_bat_content = """@echo off
REM  Skill Windows 
echo [TOOL]  Skill...
echo ==========================================
REM 
set "SKILLS_DIR=%APPDATA%\\.aipyapp\\skills"
REM 
if not exist "%SKILLS_DIR%" mkdir "%SKILLS_DIR%"
REM 
echo [FOLDER] : %SKILLS_DIR%\\tax-policy-knowledge
xcopy /E /I /Y tax-policy-knowledge "%SKILLS_DIR%\\tax-policy-knowledge"
echo [OK] 
echo.
echo [TARGET] :
echo 1.  AiPy 
echo 2. :
echo    - 
echo    - 
echo    - 
echo    - 
echo 3. :
echo    cd %SKILLS_DIR%\\tax-policy-knowledge\\scripts
echo    python tax_policy_calculator.py vat --sales 150000
echo.
echo [PHONE] : QQ 1817694478
pause
"""
    
    with open(install_bat, 'w', encoding='utf-8') as f:
        f.write(install_bat_content)
    print(f"🪟  Windows : {install_bat.name}")
    
    # 
    print("\n" + "="*60)
    print("[CELEBRATE] ")
    print("="*60)
    print(f"[PKG] : {zip_path.name}")
    print(f"[EMOJI] : {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"[FILE] : {files_added} ")
    print(f"[FOLDER] : {output_dir.absolute()}")
    print("\n[LIST] :")
    for file in output_dir.iterdir():
        size_kb = file.stat().st_size / 1024
        print(f"  • {file.name} ({size_kb:.1f} KB)")
    
    return {
        "package_name": package_name,
        "zip_path": zip_path,
        "files_added": files_added,
        "output_dir": output_dir
    }
if __name__ == "__main__":
    try:
        result = create_install_package()
        print("\n[OK]   ")
        print("[PKG] ")
    except Exception as e:
        print(f"[FAIL] : {e}")
        import traceback
        traceback.print_exc()