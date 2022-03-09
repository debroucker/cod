# cod
Récupère et affiche les stats cod du multijoueur.

# configuration :
- installer python3.9
    - sous linux : `sudo apt install python3.9`
    - sous w10 : 
        - télécharger la version ici : https://www.python.org/downloads/windows/ 
        - /!\ lors de l'installation, cliquer sur "Add to Path"
- installer les librairies à partir d'un terminal :
    - `pip3 install callofduty.py`
    - `pip3 install schedule`
    - `pip3 install requests`
    - `pip3 install configparser`
- dans le fichier "login.conf" :
    - mettre comme `login` son addresse mail Activision 
    - mettre comme `pass` son mdp Activision
- suivre des joueurs : 
    - dans le fichier "players.json" dans le dossier "bd", ajouter l'username et le numéro de Platforme au format `json` :
        - 1 : BattleNet
        - 2 : PlayStation,
        - 3 : Xbox,
        - 4 : Steam,
        - 5 : Activision
- ajouter des modes ou des maps : 
    - pour les modes : dans le fichier "modes.json"
    - pour les maps : dans le fichier "maps.json"
    - ajouter l'id du mode (ou de la map), puis ajouter son libelle au format `json`
- pour le lancer :
    - sous linux : `python3 api.py` (à la racine du projet)
    - sous w10 : double cliquer sur "api.py" (on peut faire un raccourcis)
- résultats :
    - dans le dossier "res", il y a tous les résultats des joueurs