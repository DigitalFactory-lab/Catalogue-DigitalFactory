# Catalogue des ateliers de la Digital Factory

Présentation des six ateliers de la Digital Factory du Forem à Liège, destinée aux partenaires : Visites, Premiers pas, Immersion, Métier augmenté, Culture numérique et Face caméra.

## Consulter le catalogue

- **En ligne** : https://digitalfactory-lab.github.io/Catalogue-DigitalFactory/
  On avance avec les flèches du clavier, un clic ou un glissement du doigt. La touche F passe en plein écran. Le numéro de la diapositive s'affiche dans l'adresse : `#3` ouvre directement la troisième.
- **PowerPoint** : [Types-ateliers-Digital-Factory.pptx](Types-ateliers-Digital-Factory.pptx). Le fichier utilise la police Poppins. Si elle n'est pas installée sur l'ordinateur, PowerPoint la remplace par une autre police.

## Contenu du dépôt

| Élément | Rôle |
|---|---|
| `index.html` | Version web autonome, qui ne fait appel à aucun service externe |
| `fonts/` | Police Poppins, sous licence SIL Open Font License 1.1 (`OFL.txt`) |
| `Types-ateliers-Digital-Factory.pptx` | Version PowerPoint |
| `source/` | Fichiers de la présentation : une diapositive par fichier HTML, styles communs dans `deck.css` |
| `outils/` | Scripts qui produisent les diapositives, la version web et le PowerPoint |

## Mettre à jour

La page `index.html` se reconstruit à partir du dossier `source/` (Python 3) :

```
python3 outils/web.py source index.html fonts
```

Les diapositives sont générées par `outils/build.py` (Python 3 et fontTools) : `DECK_PROJECT=source python3 outils/build.py`. Les scripts de `outils/powerpoint/` ont servi à produire le PowerPoint.

Ces scripts contiennent encore des chemins propres à l'environnement où ils ont été écrits (police Poppins, dossiers de travail) : il faut les adapter avant de les réutiliser.
