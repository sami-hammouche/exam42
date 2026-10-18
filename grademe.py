#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import shutil
import tempfile
import re
from datetime import datetime, timedelta

if sys.platform == 'win32':
    os.system('')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, '.state.json')
SUBJECTS_DIR = os.path.join(BASE_DIR, 'subjects')
RENDU_DIR = os.path.join(BASE_DIR, 'rendu')
TOTAL_LEVELS = 10
GCC_EXE = r'C:\msys64\mingw64\bin\gcc.exe'

R = '\033[1;31m'
G = '\033[1;32m'
Y = '\033[1;33m'
B = '\033[1;34m'
D = '\033[90m'
E = '\033[0m'

CRASH_CODES = {
    0xC0000005: 'SEGFAULT — accès mémoire invalide',
    0xC00000FD: 'STACK OVERFLOW — récursion infinie ?',
    0xC0000094: 'DIVISION PAR ZERO',
    0xC000001D: 'INSTRUCTION ILLEGALE',
    -1073741819: 'SEGFAULT — accès mémoire invalide',
    -1073741571: 'STACK OVERFLOW — récursion infinie ?',
    -1073741674: 'DIVISION PAR ZERO',
}


def gcc_env():
    env = os.environ.copy()
    env['PATH'] = r'C:\msys64\mingw64\bin;' + env.get('PATH', '')
    env['MSYSTEM'] = 'MINGW64'
    return env


def get_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, encoding='utf-8-sig') as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_meta(level):
    with open(os.path.join(SUBJECTS_DIR, f'{level:02d}', 'meta.json')) as f:
        return json.load(f)


def create_rendu_folder(name):
    os.makedirs(os.path.join(RENDU_DIR, name), exist_ok=True)


def find_gcc():
    if os.path.exists(GCC_EXE):
        return GCC_EXE
    for p in [r'C:\Program Files\Git\mingw64\bin\gcc.exe',
              r'C:\mingw64\bin\gcc.exe', r'C:\TDM-GCC-64\bin\gcc.exe']:
        if os.path.exists(p):
            return p
    return None


def has_main(filepath):
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        return bool(re.search(r'\bint\s+main\s*\(', f.read()))


def find_function_defs(filepath):
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        content = f.read()
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'//[^\n]*', '', content)
    pattern = r'^(?!static\s)([\w][\w\s\*]*\s+)(\w+)\s*\([^;{]*\)\s*(?:\n\s*)?\{'
    found = re.findall(pattern, content, re.MULTILINE)
    keywords = {'if', 'while', 'for', 'switch', 'else', 'do'}
    return [name for _, name in found if name not in keywords]


def detect_crash(returncode):
    return CRASH_CODES.get(returncode, None)


def step(n, total, label):
    print(f'\n{B}  [{n}/{total}] {label}{E}')
    print(f'{D}  {"─" * 46}{E}')


def check_compile(gcc, src_files, tmp_exec, required_files):
    step(1, 2, 'Compilation  gcc -Wall -Wextra -Werror')
    cmd = [gcc, '-Wall', '-Wextra', '-Werror'] + src_files + ['-o', tmp_exec]
    r = subprocess.run(cmd, capture_output=True, text=True, env=gcc_env())

    if r.returncode != 0:
        err = (r.stderr + r.stdout).strip()
        print(f'  {R}[ECHEC]{E}')
        if err:
            for line in err.splitlines():
                print(f'  {line}')
        else:
            print(f'  {Y}(pas de message — vérifie que ton fichier est valide){E}')
        return False

    print(f'  {G}OK{E}')
    return True


def check_tests(tmp_exec, tests_dir):
    step(2, 2, 'Tests')
    test_files = sorted(f for f in os.listdir(tests_dir) if f.endswith('.expected'))

    if not test_files:
        print(f'  {Y}Aucun test défini — compilation suffisante.{E}')
        return True

    all_passed = True
    for i, tf in enumerate(test_files):
        expected_path = os.path.join(tests_dir, tf)
        input_path = expected_path.replace('.expected', '.input')

        with open(expected_path, 'rb') as f:
            expected = f.read()

        stdin_data = None
        if os.path.exists(input_path):
            with open(input_path, 'rb') as f:
                stdin_data = f.read()

        try:
            res = subprocess.run([tmp_exec], input=stdin_data,
                                 capture_output=True, timeout=5, env=gcc_env())

            crash = detect_crash(res.returncode)
            if crash:
                print(f'  {R}Test {i+1}/{len(test_files)} : {crash}{E}')
                all_passed = False
                continue

            actual = res.stdout.replace(b'\r\n', b'\n')

        except subprocess.TimeoutExpired:
            print(f'  {R}Test {i+1}/{len(test_files)} : TIMEOUT — boucle infinie ?{E}')
            all_passed = False
            continue

        if actual == expected:
            print(f'  {G}Test {i+1}/{len(test_files)} : OK{E}')
        else:
            print(f'  {R}Test {i+1}/{len(test_files)} : ECHEC{E}')
            print(f'  {D}  Attendu : {repr(expected.decode(errors="replace"))}{E}')
            print(f'  {D}  Obtenu  : {repr(actual.decode(errors="replace"))}{E}')
            all_passed = False

    return all_passed


def show_score(state):
    start = datetime.fromisoformat(state['start_time'])
    duration = state['duration_minutes']
    end = start + timedelta(minutes=duration)
    now = datetime.now()

    elapsed = min(now, end) - start
    elapsed_min = int(elapsed.total_seconds()) // 60
    elapsed_sec = int(elapsed.total_seconds()) % 60

    completed = state.get('current_level', 1) - 1
    if state.get('status') == 'completed':
        completed = TOTAL_LEVELS

    attempts = state.get('attempts', {})

    print(f'\n{B}{"=" * 54}')
    print(f'  SCORE FINAL')
    print(f'{"=" * 54}{E}')
    print(f'\n  Niveaux validés : {G}{completed}/{TOTAL_LEVELS}{E}')
    print(f'  Temps écoulé   : {elapsed_min:02d}m{elapsed_sec:02d}s / {duration}min\n')

    for lvl in range(1, TOTAL_LEVELS + 1):
        meta = get_meta(lvl)
        name = meta['name']
        nb_attempts = attempts.get(str(lvl), 0)
        if lvl < (completed + 1 if state.get('status') != 'completed' else TOTAL_LEVELS + 1):
            if state.get('status') == 'completed' or lvl <= completed:
                tries = f'({nb_attempts} essai{"s" if nb_attempts > 1 else ""})'
                print(f'  {G}  ✓ Niveau {lvl:02d} — {name:35s} {tries}{E}')
            else:
                print(f'  {R}  ✗ Niveau {lvl:02d} — {name}{E}')
        elif lvl == completed + 1 and state.get('status') not in ('completed',):
            nb = attempts.get(str(lvl), 0)
            tries = f'({nb} essai{"s" if nb > 1 else ""})' if nb else ''
            print(f'  {Y}  ● Niveau {lvl:02d} — {name:35s} {tries}{E}')
        else:
            print(f'  {D}  · Niveau {lvl:02d} — {name}{E}')

    print()
    if state.get('status') == 'completed':
        print(f'  {G}Félicitations ! Tous les exercices complétés !{E}')
    elif state.get('status') == 'finished':
        print(f'  {R}Temps écoulé.{E}')
    print(f'{B}{"=" * 54}{E}\n')


def compile_and_test(level, gcc):
    meta = get_meta(level)
    name = meta['name']
    ex_type = meta.get('type', 'function')
    subject_dir = os.path.join(SUBJECTS_DIR, f'{level:02d}')
    test_main = os.path.join(subject_dir, '_test_main.c')
    tests_dir = os.path.join(subject_dir, 'tests')
    rendu_folder = os.path.join(RENDU_DIR, name)

    required_files = meta.get('files', [f'{name}.c'])
    student_files = [os.path.join(rendu_folder, f) for f in required_files]

    for sf in student_files:
        if not os.path.exists(sf):
            print(f'\n  {R}[ERREUR] Fichier manquant : rendu/{name}/{os.path.basename(sf)}{E}')
            print(f'  {Y}Crée ce fichier dans le dossier rendu/{name}/ puis réessaie.{E}')
            return False

    if ex_type == 'function':
        for sf in student_files:
            if has_main(sf):
                print(f'\n  {R}[ERREUR] main() détecté dans ton fichier.{E}')
                print(f'  {Y}Pour un exercice fonction, ne mets pas de main().{E}')
                return False
            expected_funcs = meta.get('expected_functions', [meta['name']])
            found_funcs = find_function_defs(sf)
            extra = [f for f in found_funcs if f not in expected_funcs]
            if extra:
                print(f'\n  {R}[ERREUR] Fonctions non attendues dans {os.path.basename(sf)} :{E}')
                for fn in extra:
                    print(f'  {R}  → {fn}(){E}')
                print(f'  {Y}Ce fichier doit contenir uniquement : {", ".join(expected_funcs)}(){E}')
                return False

    tmp_fd, tmp_exec = tempfile.mkstemp(suffix='.exe')
    os.close(tmp_fd)

    src_files = ([test_main] + student_files) if ex_type == 'function' else student_files

    if not check_compile(gcc, src_files, tmp_exec, required_files):
        if os.path.exists(tmp_exec):
            os.unlink(tmp_exec)
        return False

    passed = check_tests(tmp_exec, tests_dir)
    os.unlink(tmp_exec)
    return passed


def run():
    state = get_state()
    if not state:
        print(f'{R}Aucun examen en cours.{E}')
        return False
    if state.get('status') == 'finished':
        show_score(state)
        return False
    if state.get('status') == 'completed':
        show_score(state)
        return False

    gcc = find_gcc()
    if not gcc:
        print(f'{R}[ERREUR] gcc introuvable.{E}')
        print('  Installe MSYS2 puis : pacman -S mingw-w64-x86_64-gcc')
        return False

    level = state['current_level']
    meta = get_meta(level)

    # Compter les tentatives
    attempts = state.get('attempts', {})
    attempts[str(level)] = attempts.get(str(level), 0) + 1
    state['attempts'] = attempts

    print(f'\n{B}{"=" * 50}')
    print(f'  GRADEME  |  Niveau {level}/{TOTAL_LEVELS}  |  {meta["name"]}')
    essais = attempts[str(level)]
    print(f'  Tentative {essais}')
    print(f'{"=" * 50}{E}')

    if compile_and_test(level, gcc):
        print(f'\n{G}{"=" * 50}')
        print(f'  BRAVO ! Niveau {level} validé !')
        print(f'{"=" * 50}{E}')
        if level >= TOTAL_LEVELS:
            state['status'] = 'completed'
            save_state(state)
            show_score(state)
        else:
            state['current_level'] = level + 1
            next_meta = get_meta(level + 1)
            create_rendu_folder(next_meta['name'])
            print(f'{G}  → Dossier rendu/{next_meta["name"]}/ créé.{E}')
            print(f'{G}  → Passage au niveau {level + 1}.{E}')
            save_state(state)
        return True
    else:
        print(f'\n{R}{"=" * 50}')
        print(f'  CORRECTION ECHOUEE — corrige et réessaie [g]')
        print(f'{"=" * 50}{E}')
        save_state(state)
        return False


if __name__ == '__main__':
    run()
