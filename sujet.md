
La cour de cassation nous fournit une partie de ses décisions via ce dépôt:
[https://echanges.dila.gouv.fr/OPENDATA/CASS/].

Ce dépôt contient des archives avec des fichiers XML correspondant chacun à une
décision rendue par la cour de cassation.
- [ ] faire un premier script afin de récupérer et stocker les décisions de
      la cour de cassation.
- [ ] API REST permettant d’exposer ces décisions. L’API doit gérer les cas
      suivants :
  - [ ] Renvoyer une liste de toutes les décisions de cour de cassation 
        (afficher uniquement l’identifiant et le titre de la décision)
  - [ ] Pouvoir filtrer les décisions par chambre (dans le document XML voir
        élément FORMATION: TEXTEJURIJUDI > META > METASPEC > METAJURI_JUDI > FORMATION)
  - [ ] Renvoyer le contenu d’une décision (identifiant, titre et contenu) en 
        fonction d’un identifiant de décision
  - [ ] L’API doit être accessible uniquement en utilisant un login / mot de passe
  - [ ] L’API doit renvoyer les données en JSON
  - [ ] [BONUS] Faire une recherche textuelle basique qui retourne les décisions 
        correspondantes triées par score de pertinence

Ce qui est attendu:
- [ ] L’application doit pouvoir se lancer en utilisant docker
- [ ] Le code source doit être hébergé dans un dépôt Git privé (i.e. Gitlab, Github …) 
  et un lien devra nous être transmis
- Nous nous attendons à un niveau de qualité de code qui pourrait aller en production

Ce travail devrait te prendre quelques heures (4h - 6h). Le but est d'évaluer ton 
savoir-faire, mais aussi et surtout ta démarche de travail, en voyant ce que tu peux mettre 
en œuvre pendant ce laps de temps.

Les prérequis techniques sont volontairement indéfinis, ce qui te laisse libre dans tes choix
techniques.

S’il y a des choses que tu aurais aimé faire mais que tu n’a pas eu le temps, n’hésites pas
à les documenter.
