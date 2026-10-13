# exam42

Une réplique de l'**examshell** de 42, pour s'entraîner aux examens depuis chez soi, dans les mêmes conditions qu'en salle.

## Pourquoi ce projet

À 42, l'examen se passe dans un terminal qui impose son rythme : un sujet à la fois, un chrono qui tourne, un dossier de rendu imposé, et un correcteur qui refuse tout ce qui ne compile pas exactement comme demandé. On ne peut pas s'y entraîner en dehors des clusters.

J'ai donc refait l'outil pour pouvoir me mettre en condition chez moi, autant de fois que je veux.

## Comment ça marche

```
examshell          lance l'examen
examshell reset    efface la progression et recommence
```

L'écran affiche le niveau en cours, le temps restant et le sujet :

```
==============================================================
  EXAMSHELL 42  |  Niveau 3/10  |  00:47:12
==============================================================

=============================================
Exercice : ft_print_reverse_alphabet
Fichier  : ft_print_reverse_alphabet.c
=============================================

Écrire une fonction qui affiche l'alphabet en minuscules,
sur une seule ligne, dans l'ordre décroissant.

Tu dois utiliser write() et rien d'autre.

Prototype : void    ft_print_reverse_alphabet(void);

Sortie attendue :
  zyxwvutsrqponmlkjihgfedcba

  Ton dossier : rendu/ft_print_reverse_alphabet/
    └─ ft_print_reverse_alphabet.c

  [g] soumettre   [q] quitter
```

Tu écris ton code dans le dossier `rendu/` indiqué, puis tu appuies sur `g` pour soumettre. Le chrono passe en rouge dans les dix dernières minutes.

## La correction

Le `grademe` reproduit la sévérité du correcteur de 42 :

| Étape | Ce qui est vérifié |
|---|---|
| Fichiers | le fichier demandé est présent, et porte exactement le bon nom |
| Interdits | un `main` dans un exercice de type fonction est refusé, et seule la fonction demandée doit être définie |
| Compilation | `gcc -Wall -Wextra -Werror` : le moindre avertissement fait échouer |
| Exécution | la sortie est comparée caractère par caractère à la sortie attendue, avec un `main` de test fourni par l'exercice |
| Crash | les segfaults et les débordements sont détectés via le code de retour |
| Temps | si le chrono est écoulé, la soumission est refusée |

Une réussite fait passer au niveau suivant, un échec laisse au même niveau : comme en examen.

## Les 10 niveaux

Ils suivent la progression de la piscine, du plus simple au plus exigeant :

`ft_putchar` · `ft_print_alphabet` · `ft_print_reverse_alphabet` · `ft_print_numbers` · `ft_is_negative` · `ft_strlen` · `ft_putstr` · `ft_swap` · `ft_putnbr` · `ft_recursive_factorial`

Chaque niveau tient dans un dossier de `subjects/` : son énoncé (`subject.txt`), son `main` de test (`_test_main.c`), sa fiche (`meta.json`) qui indique le nom, les fichiers attendus et le type d'exercice, et un dossier `tests/` contenant les sorties attendues (`.expected`) et, si besoin, les entrées à fournir (`.input`).

## Organisation

```
examshell.py     l'examen : chrono, affichage du sujet, progression
grademe.py       la correction : compilation, tests, score
config.json      la durée de l'examen, 60 minutes par défaut
subjects/        les 10 exercices
rendu/           créé au lancement, c'est là que tu écris ton code
```

## Pré-requis

- Windows, avec Python 3.10 ou plus récent
- `gcc`, via MSYS2, MinGW ou Git for Windows — le script cherche les emplacements habituels tout seul

## Ajouter ses propres exercices

Crée un dossier numéroté dans `subjects/`, avec les trois fichiers :

```json
{
  "name": "ft_strlen",
  "files": ["ft_strlen.c"],
  "type": "function"
}
```

Le `type` vaut `function` pour un exercice sans `main`, ou `program` pour un exercice qui en demande un.
