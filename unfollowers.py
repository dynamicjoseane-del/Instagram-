#!/usr/bin/env python3
"""Descobre quem deixou de te seguir no Instagram, usando a exportação oficial
("Baixar suas informações", formato JSON). Não pede senha nem acessa a internet.

Uso:
  # 1 exportação: quem você segue e não te segue de volta
  python3 unfollowers.py export.zip

  # 2 exportações (antiga e nova): quem deixou de te seguir entre as duas
  python3 unfollowers.py export_antigo.zip export_novo.zip

Cada argumento pode ser o .zip baixado ou a pasta já descompactada.
"""
import json
import sys
import zipfile
from pathlib import Path


def _read_files(source):
    """Retorna {nome_do_arquivo: conteúdo} dos JSONs de seguidores/seguindo."""
    p = Path(source)
    out = {}
    if p.is_file() and zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            for name in z.namelist():
                base = name.rsplit("/", 1)[-1]
                if base.startswith(("followers", "following")) and base.endswith(".json"):
                    out[name] = z.read(name).decode("utf-8")
    elif p.is_dir():
        for f in p.rglob("*.json"):
            if f.name.startswith(("followers", "following")):
                out[str(f)] = f.read_text(encoding="utf-8")
    else:
        sys.exit(f"Não encontrei zip ou pasta em: {source}")
    return out


def _usernames(entries):
    names = set()
    for e in entries:
        for s in e.get("string_list_data", []):
            if s.get("value"):
                names.add(s["value"].lower())
                break
        else:
            # Exportações recentes às vezes guardam o nome só em "title".
            if e.get("title"):
                names.add(e["title"].lower())
    return names


def load(source):
    followers, following = set(), set()
    for name, text in _read_files(source).items():
        base = name.replace("\\", "/").rsplit("/", 1)[-1]
        data = json.loads(text)
        if base.startswith("followers"):
            entries = data if isinstance(data, list) else data.get("relationships_followers", [])
            followers |= _usernames(entries)
        elif base == "following.json":
            entries = data.get("relationships_following", []) if isinstance(data, dict) else data
            following |= _usernames(entries)
    if not followers:
        sys.exit(f"Nenhum seguidor encontrado em {source}. A exportação foi pedida em formato JSON?")
    return followers, following


def show(title, names):
    print(f"\n{title} ({len(names)}):")
    for n in sorted(names):
        print(f"  @{n}  https://instagram.com/{n}")
    if not names:
        print("  (ninguém)")


def main(args):
    if len(args) == 1:
        followers, following = load(args[0])
        print(f"Seguidores: {len(followers)} | Seguindo: {len(following)}")
        show("Você segue, mas não te seguem de volta", following - followers)
    elif len(args) == 2:
        old_f, _ = load(args[0])
        new_f, new_following = load(args[1])
        print(f"Seguidores antes: {len(old_f)} | agora: {len(new_f)}")
        show("Deixaram de te seguir", old_f - new_f)
        show("Novos seguidores", new_f - old_f)
        show("Você segue, mas não te seguem de volta (hoje)", new_following - new_f)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
