# INF232 --- Educational Analytics Platform (Thème D : Établissement Scolaire Secondaire)

Ce projet est une application web d'analyse de données éducatives conçue pour aider la direction d'un établissement d'enseignement secondaire à analyser les performances scolaires de ses élèves de terminale, à identifier des profils comportementaux homogènes et à suggérer des orientations scolaires (Scientifique vs Littéraire) à l'aide de techniques de statistiques descriptives, d'apprentissage automatique (clustering et classification).

---

## 👥 Informations sur le Groupe et les Données

*   **Code du Cours :** INF232 (Statistiques et Analyse de Données)
*   **Thème choisi :** **Thème D (Établissement scolaire secondaire)**
*   **Membres du Groupe :**
    *   KANA DJOWALE Durel Bright
    *   LIENOU KAMGANG Stephy Laure 
    *  MAGAKOUONTCHOUAudreyArèle
    *  TCHOMKEMWAMBESalomonMarcel
    *  FOTSOFAMDLEEnzoBrayann
    *  DJIATOGUEULEWOUELeslieSorelle
    *  MBEGAEYEMETERuth
    *  MELONGTSAWARosvel
    *  NGUEAGHOKRYSDeHugo
    *  IFOUFOPAAnge
*   **Nom du Chef de Groupe (graine) :** `KANA DJOWALE DUREL BRIGHT LIENOU KAMGANG STEPHY LAURE`
*   **Graine Numérique Générée (SHA-256) :** `3857731347` (reproductible, dérivée de la conversion déterministe du nom)
*   **Taille de la Cohorte Générée :** 250 élèves

---

## 🚀 Fonctionnalités Principales

L'application est structurée autour d'un tableau de bord moderne et interactif (Dashboard) proposant :
1.  **Synthèse Globale (KPIs) :** Vue immédiate sur la taille de la cohorte, les scores moyens, le taux d'assiduité global et la répartition par orientation recommandée.
2.  **Analyse Univariée (Question 1) :** Calcul complet des statistiques de performance (`Exam_Score`) : moyenne, médiane, écart-type, quartiles, asymétrie (*skewness*), aplatissement (*kurtosis*), et détection automatique des valeurs atypiques (*outliers*) via la règle de Tukey ($1.5 \times IQR$).
3.  **Analyse de Relation et Régression (Question 2) :**
    *   Matrice de corrélation linéaire de Pearson et Spearman.
    *   Modélisation par régression linéaire multiple pour quantifier l'effet conjoint des heures d'étude, de l'assiduité et des devoirs continus sur la note d'examen final.
    *   Simulateur de prédiction de note finale avec avertissements en cas d'extrapolation (valeurs hors-limites).
4.  **Segmentation Non Supervisée (Question 3) :**
    *   Partitionnement par l'algorithme des $K$-moyennes (*K-Means*).
    *   Sélection du nombre de clusters optimal ($K=2$) guidée par le score de silhouette moyenne et la méthode du coude (*elbow method*).
    *   Profilage détaillé des groupes d'élèves identifiés (Élèves performants vs Élèves à accompagner) et recommandations pédagogiques automatiques.
5.  **Système de Suggestion d'Orientation (Question 4) :**
    *   Comparaison de performance de 4 algorithmes de classification supervisée : *Régression Logistique*, *Arbres de Décision*, *Forêts Aléatoires* et *$K$ plus proches voisins (KNN)*.
    *   Rapport de performance complet pour le meilleur modèle (*Régression Logistique* : Exactitude de 88%, score $F_1$, matrice de confusion, courbe ROC, AUC, importance relative des caractéristiques).
    *   Module interactif de simulation d'orientation pour un nouvel élève.
6.  **Génération et Export de Rapports :**
    *   Téléchargement d'un rapport PDF complet et formaté de manière professionnelle (intégrant la synthèse et les tableaux de résultats).
    *   Export de toutes les données générées au format CSV.
    *   Téléchargement d'une archive ZIP contenant tous les graphiques générés (histogramme de notes, heatmap de corrélations, graphe des résidus de régression, radar de profils, matrice de confusion, courbe ROC) en format haute définition PNG pour insertion externe.

---

## 🛠️ Architecture du Code et Technologies

L'application est construite en Python avec une architecture propre et découplée :
*   **Framework Web :** Flask 3.1.0+ (utilisant des Blueprints modulaires pour chaque question)
*   **Calcul et ML :** Pandas (gestion de données), NumPy (manipulation vectorielle), scikit-learn (modélisation prédictive et clustering), SciPy (statistiques et tests)
*   **Visualisations :** Plotly (graphiques dynamiques) convertis en images statiques de haute qualité via Kaleido
*   **Génération PDF :** ReportLab
*   **Interface Utilisateur :** HTML5 sémantique, CSS moderne (système de design soigné, mode sombre/clair, micro-animations) et Bootstrap 5.

---

## 💻 Installation et Démarrage Local

Pour exécuter ce projet sur votre machine locale, assurez-vous d'avoir Python 3.12 ou supérieur installé.

### 1. Cloner le projet ou extraire l'archive
Placez-vous dans le dossier du projet :
```powershell
cd /chemin/vers/INF232_TP_GROUPEXX
```

### 2. Créer et activer un environnement virtuel
*   **Sur Windows (PowerShell) :**
    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
*   **Sur macOS / Linux :**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 3. Installer les dépendances
Installez les bibliothèques requises :
```bash
pip install -r requirements.txt
```

### 4. Lancer le serveur Flask
Démarrez l'application web :
```bash
python app.py
```
Le serveur démarrera en mode développement. Par défaut, l'application est accessible à l'adresse suivante dans votre navigateur web :
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 📄 Génération du Rapport LaTeX

Le code source LaTeX complet du rapport est disponible dans le dossier `reports/rapport.tex`. Il contient l'ensemble des formules mathématiques, des explications conceptuelles, des tableaux de métriques et des interprétations pédagogiques issues de l'analyse du jeu de données du groupe.

Pour compiler ce fichier en PDF sur votre machine (nécessite une installation locale de LaTeX comme MiKTeX, TeX Live ou en utilisant la plateforme en ligne [Overleaf](https://www.overleaf.com)) :
```bash
pdflatex reports/rapport.tex
```

---

## 📝 Mode d'Emploi Simplifié pour l'Exécution (Rendu)
1. Ouvrez l'application à l'adresse `http://localhost:5000`.
2. Sur la page d'accueil de génération de données, saisissez le nom complet du chef de groupe : `KANA DJOWALE DUREL BRIGHT LIENOU KAMGANG STEPHY LAURE` et définissez la taille de l'échantillon à `250`.
3. Cliquez sur **Générer** : l'ensemble des modules analytiques se synchronise automatiquement.
4. Naviguez à travers les onglets du menu latéral pour répondre aux Questions 1 à 4, visualiser les graphiques interactifs et faire des simulations.
5. Accédez à la page **Rapports** pour télécharger les rapports au format PDF, les données brutes CSV et l'ensemble des graphiques d'analyse PNG.
