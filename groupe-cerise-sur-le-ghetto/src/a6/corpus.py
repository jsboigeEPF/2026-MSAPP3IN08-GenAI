"""Corpus synthétique original : aucune donnée réelle de client ou de salarié."""
import json
from pathlib import Path

# Le sens de chaque fait est fixé avant toute génération.
SCENARIOS = [
('logistique','La livraison du lot A17 est prévue le 14 novembre.','Le lot contient 24 capteurs.','La livraison ne comprend pas leur installation.'),
('logistique','Le colis B42 doit être retiré au dépôt Nord avant vendredi.','Le dépôt ferme à 17 heures.','Une pièce justificative est nécessaire pour le retrait.'),
('logistique','Le stock disponible est de 180 pièces.','La commande porte sur 200 pièces.','Les 20 pièces restantes ne seront disponibles que lundi.'),
('logistique','Le transport du lot C08 coûte 75 euros.','Le délai annoncé est de 3 jours ouvrés.','Ce tarif ne comprend pas une assurance supplémentaire.'),
('logistique','Le quai 4 sera fermé le 12 décembre.','Les réceptions seront déplacées au quai 2.','Les horaires habituels resteront inchangés.'),
('maintenance','La machine M12 doit être arrêtée mardi de 9 heures à 11 heures.','Le filtre doit être remplacé pendant cet arrêt.','La remise en service nécessite un contrôle de sécurité.'),
('maintenance','Le contrôle de la pompe P8 a relevé une fuite.','Une intervention est prévue le 18 novembre.','La pompe ne doit pas être utilisée avant cette intervention.'),
('maintenance','Le compteur de la machine T3 affiche 1200 heures.','Le prochain entretien est prévu à 1500 heures.','Aucune anomalie ne figure dans le dernier contrôle.'),
('maintenance','La pièce R6 peut être réparée pour 240 euros.','Une pièce neuve coûte 390 euros.','La réparation bénéficie de 6 mois de garantie.'),
('maintenance','La maintenance du convoyeur dure 45 minutes.','Elle doit commencer après la fin du dernier chargement.','Le redémarrage exige la présence du responsable de sécurité.'),
('formation','La formation Excel commence le 6 janvier à 9 heures.','Elle se déroule en salle B12.','Les participants doivent apporter leur ordinateur.'),
('formation','Le module comprend 4 séances de 2 heures.','Le contrôle final compte pour 60 pour cent de la note.','Les exercices comptent pour les 40 pour cent restants.'),
('formation','Les inscriptions ferment le 20 novembre.','La formation est limitée à 16 participants.','Une inscription après cette date ne garantit pas de place.'),
('formation','La bibliothèque ferme à 18 heures le mercredi.','Le prêt dure 21 jours.','Le renouvellement est impossible si le livre est réservé.'),
('formation','La session du 10 décembre est reportée au 17 décembre.','La salle reste la salle C5.','Le contenu et la durée ne changent pas.'),
('service','La demande D31 a été reçue le 8 novembre.','Une réponse est attendue sous 5 jours ouvrés.','La réception de la demande ne vaut pas acceptation.'),
('service','Le contrat S14 débute le 1 décembre.','Le tarif mensuel est de 45 euros.','La résiliation est possible avec un préavis de 30 jours.'),
('service','Le remboursement de 80 euros a été approuvé.','Le versement doit intervenir sous 10 jours ouvrés.','Aucun versement immédiat n’est garanti.'),
('service','Le rendez-vous est fixé mardi à 14 heures.','Il aura lieu en agence Centre.','Une modification doit être signalée au moins 24 heures avant.'),
('service','Le service téléphonique ouvre à 8 heures et ferme à 19 heures.','Il fonctionne du lundi au vendredi.','Aucun appel n’est traité le dimanche.'),
('industrie','Le lot Z5 comporte 500 pièces.','Le contrôle a relevé 8 pièces non conformes.','Le lot doit rester isolé jusqu’à la décision qualité.'),
('industrie','La ligne L2 produit 90 unités par heure.','Un arrêt de 30 minutes est prévu jeudi.','La cible de production n’a pas encore été révisée.'),
('industrie','Le fournisseur propose 3 prototypes pour 600 euros.','Le délai de fabrication est de 12 jours ouvrés.','La commande en série nécessite une validation distincte.'),
('industrie','La tolérance de la pièce est de 0,2 millimètre.','Le résultat mesuré est de 0,35 millimètre.','La pièce doit être refusée selon ce critère.'),
('industrie','La réunion qualité aura lieu le 22 novembre.','Les rapports doivent être transmis avant le 19 novembre.','Les résultats provisoires doivent être signalés comme tels.'),
('mobilite','Le train de 7 heures 40 est supprimé.','Un départ de remplacement est proposé à 8 heures 10.','La réservation initiale reste valable pour ce départ.'),
('mobilite','Le parking Est sera fermé pendant 2 jours.','Le parking Ouest restera accessible.','Les places réservées aux livraisons ne pourront pas être utilisées.'),
('mobilite','Le bus 12 change de trajet du 3 au 7 décembre.','L’arrêt Stade ne sera pas desservi.','L’arrêt Mairie reste accessible pendant cette période.'),
('mobilite','Le trajet entre les sites dure environ 35 minutes.','Une navette part toutes les 30 minutes.','Le temps annoncé ne comprend pas l’attente de la navette.'),
('mobilite','La location du véhicule coûte 65 euros par jour.','Le forfait comprend 100 kilomètres.','Chaque kilomètre supplémentaire coûte 0,25 euro.'),
('numerique','Le portail sera indisponible samedi de 2 heures à 4 heures.','Les données existantes seront conservées.','Aucune nouvelle demande ne pourra être déposée pendant cet arrêt.'),
('numerique','La version 3.2 corrige un problème d’export PDF.','La mise à jour est disponible depuis lundi.','Elle ne modifie pas les droits d’accès des utilisateurs.'),
('numerique','Le mot de passe doit contenir au moins 12 caractères.','Un second facteur est obligatoire pour les connexions externes.','Le mot de passe ne doit jamais être partagé.'),
('numerique','La sauvegarde s’exécute chaque nuit à 1 heure.','Les archives sont conservées pendant 30 jours.','Une restauration doit être demandée au service support.'),
('numerique','Le fichier importé doit être au format CSV.','La limite est fixée à 5 mégaoctets.','Les fichiers dépassant cette limite seront refusés.'),
('collectivite','La collecte du quartier Sud est déplacée au jeudi.','Ce changement commence le 5 décembre.','La collecte du verre reste organisée le mardi.'),
('collectivite','La salle municipale accueille au maximum 80 personnes.','La réservation doit être faite 7 jours avant l’événement.','La restauration n’est pas comprise dans la location.'),
('collectivite','La piscine ferme pour travaux du 2 au 16 janvier.','Les abonnements seront prolongés de 15 jours.','Aucun accès au bassin ne sera possible pendant les travaux.'),
('collectivite','La permanence ouvre mardi et jeudi de 10 heures à 16 heures.','La prise de rendez-vous est recommandée.','Les urgences ne sont pas prises en charge par cette permanence.'),
('collectivite','Le prêt de matériel est limité à 7 jours.','Une caution de 50 euros est demandée.','La caution est restituée si le matériel est rendu intact.'),
]
INTRO = [
'Dans le cadre de la coordination des opérations actuellement programmées, les éléments suivants doivent être portés à votre connaissance.',
'À la suite de l’examen des modalités de fonctionnement du service concerné, nous souhaitons communiquer les informations opérationnelles ci-dessous.',
'Afin de faciliter l’organisation des activités et de limiter les incompréhensions éventuelles, il convient de tenir compte des précisions suivantes.',
'Nous transmettons les indications relatives à cette opération pour permettre leur prise en considération dans la préparation des prochaines étapes.',
'Pour assurer une compréhension commune des conditions applicables, nous vous invitons à prendre connaissance des informations exposées dans ce message.',
]
TAIL = 'Ces informations constituent les éléments de référence pour cette opération.'

def build():
    result=[]
    for i,(domain,*facts) in enumerate(SCENARIOS):
        result.append(dict(id=f'T{i+1:02}',domain=domain,split='dev' if i%5==0 else 'test',
            source=INTRO[i%5]+' '+' '.join(facts)+' '+TAIL,
            facts=[dict(id=f'F{j+1}',text=f) for j,f in enumerate(facts)],
            provenance='Texte synthétique original préparé avec assistance IA ; aucune donnée réelle.'))
    return result

def write(path):
    Path(path).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in build()),encoding='utf8')
