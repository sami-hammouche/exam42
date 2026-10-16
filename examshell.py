#!/usr/bin/env python3
import sys
import os
import json
import time
import subprocess
import msvcrt
from datetime import datetime, timedelta

if sys.platform == 'win32':
    os.system('')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, '.state.json')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
SUBJECTS_DIR = os.path.join(BASE_DIR, 'subjects')
RENDU_DIR = os.path.join(BASE_DIR, 'rendu')
GRADEME = os.path.join(BASE_DIR, 'grademe.py')
TOTAL_LEVELS = 10


def get_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, encoding='utf-8-sig') as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def get_config():
    if not os.path.exists(CONFIG_FILE):
        return {'duration_minutes': 60}
    with open(CONFIG_FILE) as f:
        return json.load(f)


def get_meta(level):
    path = os.path.join(SUBJECTS_DIR, f'{level:02d}', 'meta.json')
    with open(path) as f:
        return json.load(f)


def get_remaining(state):
    start = datetime.fromisoformat(state['start_time'])
    end = start + timedelta(minutes=state['duration_minutes'])
    return end - datetime.now()


def fmt_time(td):
    total = max(0, int(td.total_seconds()))
    return f'{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}'


def read_subject(level):
    path = os.path.join(SUBJECTS_DIR, f'{level:02d}', 'subject.txt')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    return 'Sujet introuvable.'


def get_rendu_contents(name):
    folder = os.path.join(RENDU_DIR, name)
    if not os.path.exists(folder):
        return []
    return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]


def create_rendu_folder(name):
    os.makedirs(os.path.join(RENDU_DIR, name), exist_ok=True)


def init_exam():
    config = get_config()
    duration = config.get('duration_minutes', 60)
    state = {
        'start_time': datetime.now().isoformat(),
        'duration_minutes': duration,
        'current_level': 1,
        'status': 'running'
    }
    save_state(state)
    meta = get_meta(1)
    create_rendu_folder(meta['name'])
    return state


def display(state):
    remaining = get_remaining(state)
    level = state['current_level']
    meta = get_meta(level)
    name = meta['name']
    contents = get_rendu_contents(name)

    os.system('cls')

    if remaining.total_seconds() <= 0:
        timer = '\033[1;31m00:00:00  TEMPS ECOULE\033[1;34m'
    elif remaining.total_seconds() < 600:
        timer = f'\033[1;31m{fmt_time(remaining)}\033[1;34m'
    else:
        timer = fmt_time(remaining)

    print(f'\033[1;34m{"=" * 62}')
    print(f'  EXAMSHELL 42  |  Niveau {level}/{TOTAL_LEVELS}  |  {timer}')
    print(f'{"=" * 62}\033[0m')
    print()
    print(read_subject(level))
    print()
    print(f'\033[1;33m  Ton dossier : rendu/{name}/\033[0m')
    if contents:
        for f in contents:
            print(f'    └─ {f}')
    else:
        print('\033[90m    (vide)\033[0m')
    print()
    print('\033[90m  [g] soumettre   [q] quitter\033[0m', flush=True)


def run_grademe():
    os.system('cls')
    subprocess.run([sys.executable, GRADEME])
    print('\n\033[90m  Appuie sur une touche pour continuer...\033[0m', flush=True)
    msvcrt.getch()


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == 'reset':
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        if os.path.exists(RENDU_DIR):
            import shutil
            shutil.rmtree(RENDU_DIR)
        print('\033[1;32mExamen réinitialisé. Lance examshell pour recommencer.\033[0m')
        return

    state = get_state()
    if state and state['status'] in ('completed', 'finished'):
        subprocess.run([sys.executable, GRADEME])
        return
    if not state or state['status'] != 'running':
        state = init_exam()
        print(f'\033[1;32mExamen démarré ! Durée : {state["duration_minutes"]} min\033[0m')
        time.sleep(1)

    try:
        while True:
            state = get_state()
            if not state:
                break

            remaining = get_remaining(state)
            if remaining.total_seconds() <= 0 and state['status'] == 'running':
                state['status'] = 'finished'
                save_state(state)

            display(state)

            action = None
            start = time.time()
            while time.time() - start < 1.0:
                if msvcrt.kbhit():
                    key = msvcrt.getch().lower()
                    if key == b'q':
                        action = 'quit'
                    elif key == b'g':
                        action = 'grademe'
                    break
                time.sleep(0.05)

            if action == 'quit':
                os.system('cls')
                print('\033[1;33m  Examen en pause. Relance examshell pour continuer.\033[0m')
                return
            elif action == 'grademe':
                run_grademe()
                state = get_state()
                if state and state.get('status') in ('completed', 'finished'):
                    return

    except KeyboardInterrupt:
        os.system('cls')
        print('\033[1;33m  Examen en pause. Relance examshell pour continuer.\033[0m')


if __name__ == '__main__':
    main()
