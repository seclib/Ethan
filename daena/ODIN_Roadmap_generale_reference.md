# ODIN --- Roadmap générale du chantier

**Version de référence : 9 novembre 2026**

## 1. Orientation générale

Faire évoluer ODIN vers une plateforme géospatiale / GEOINT complète, en
conservant son architecture native, son template visuel et Cesium comme
moteur de rendu.

RustGIS sert uniquement de référence fonctionnelle pour identifier des
capacités SIG intéressantes. **Aucune intégration de RustGIS, aucun
portage de son code Rust et aucune dépendance à RustGIS ne sont
prévus.** Les fonctionnalités retenues seront développées nativement
dans ODIN.

## 2. État connu des phases

-   **C0 --- Architecture & Discovery :** terminé.
-   **C1 --- Geospatial Core :** terminé.
-   **C2 --- Public API & Boundaries :** terminé.
-   **C2.1 à C2.4 --- Git consolidation :** terminé.
-   **C3 --- Geospatial API Adoption :** terminé.
    -   C3.17 transitFeeds reste différé conformément à DEC-2026-003 ;
        ne pas rouvrir sans changement architectural justifié.
-   **C4 --- Geospatial Foundation Expansion :** en cours.
    -   C4.1 livré : greatCirclePathKm, greatCirclePathMeters,
        polygonPerimeterKm, polygonAreaKm2, circularAreaKm2.
-   **C5 --- Rendering Architecture :** prévu, pas encore ouvert.

Les phases et états doivent être revérifiés dans le dépôt avant toute
nouvelle planification. Ne pas considérer les propositions ci-dessous
comme des phases officiellement ouvertes.

## 3. Axes fonctionnels ODIN

### ODIN Earth

Globe 3D, imagerie satellite, relief, terrain, bâtiments et modèles
d'altitude.

### ODIN Maps

Recherche, géocodage, itinéraires, POI, navigation, couches
cartographiques et sources de tuiles.

### ODIN Intelligence

AIS, aviation, météo, environnement, événements et flux dynamiques.

### ODIN Analysis

Mesures, trajectoires, zones, superpositions, corrélations et
géotraitements.

## 4. Capacités SIG à étudier et développer nativement

### Géotraitement vectoriel

-   Buffer
-   Clip
-   Intersect
-   Union
-   Dissolve
-   Spatial Join
-   Near et sélection spatiale

### Raster et terrain

-   Lecture et exploitation GeoTIFF / COG
-   Statistiques raster
-   Modèles numériques de terrain
-   Pente, exposition et profils altimétriques

### Hydrologie

-   Direction et accumulation des écoulements
-   Délimitation des bassins versants

### Visibilité et 3D

-   Viewshed
-   Ligne de visée
-   LiDAR et nuages de points
-   Surfaces et analyses 3D

### Analyse spatiale

-   IDW
-   Kriging
-   Statistiques zonales
-   Suitability / analyse multicritère

### Production cartographique

-   Mises en page
-   Atlas / Map Series
-   Export PDF
-   Rapports cartographiques

### Formats et sources

-   GeoPackage
-   GeoParquet
-   PostGIS
-   STAC

### Automatisation d'analyse

-   ModelBuilder
-   Chaînes de traitements reproductibles

Ces éléments constituent un catalogue de capacités candidates. Avant de
les planifier, auditer le code ODIN et confirmer ce qui existe déjà,
partiellement ou pas du tout. Les affirmations sur RustGIS doivent aussi
distinguer code présent, tests, documentation et fonctionnement
réellement validé.

## 5. Chantier visuel et template

Directive : - Conserver le template actuel, l'identité visuelle, le logo
et le nom ODIN. - Ne pas lancer de refonte graphique complète. - Réduire
les deux barres supérieures après vérification de leurs
responsabilités. - Identifier précisément la barre droite avant toute
décision de suppression. - Masquer la description permanente si elle
n'apporte pas de valeur opérationnelle. - Ajouter des panneaux latéraux
ou flottants contextuels. - Prévoir des fenêtres d'information et
d'action avec animations courtes. - Garder une densité d'information
maîtrisée. - Respecter `prefers-reduced-motion`.

Évolutions d'interface candidates : - Panneaux contextuels liés à
l'objet sélectionné. - Gestionnaire de couches. - Outils flottants de
mesure, sélection et analyse. - Chronologie pour les données
temporelles.

## 6. C5 --- Rendu et performances

À traiter après consolidation des capacités géospatiales : - Gestion
cohérente des couches et de leur visibilité. - Chargement progressif des
données volumineuses. - Gestion du terrain et des objets 3D. -
Optimisation des entités nombreuses et des trajectoires. - Gestion du
temps et des couches dynamiques. - Cohérence entre vues 2D et 3D.

**Cesium reste le moteur de rendu.** Aucun remplacement sans décision
explicite.

## 7. Séquencement proposé --- non encore validé

1.  Terminer et consolider C4.
2.  Auditer et consolider les quatre domaines fonctionnels.
3.  Ouvrir C5 pour le rendu et les performances.
4.  Faire évoluer progressivement l'interface sans remplacer le
    template.
5.  Développer les capacités GEOINT avancées et les analyses combinées.
6.  Ajouter les outils de production cartographique, formats et
    automatisation.
7.  Réaliser une validation générale : tests, sécurité, performances,
    stabilité, expérience utilisateur et documentation.

Ce séquencement est une proposition de travail, pas une ouverture
officielle de phases.

## 8. Règles de conduite

-   Chaque phase doit avoir un périmètre, des critères d'acceptation et
    un état vérifiable.
-   Préférer les corrections ciblées aux réécritures générales.
-   Ne pas dupliquer managers, registres ou services.
-   Ne pas intégrer RustGIS et ne pas reprendre son code.
-   Conserver l'architecture ODIN et Cesium.
-   Ne pas modifier le template sans décision explicite.
-   Préserver les modifications Git existantes.
-   Distinguer fonctionnalité codée, testée, compilée et validée dans le
    navigateur.
-   Ne pas déclarer une capacité opérationnelle sur la seule présence de
    code.
-   Vérifier l'état réel du dépôt avant de planifier une phase ou de
    déclarer un travail terminé.

## 9. Prochaine étape recommandée

Réaliser un audit factuel du dépôt ODIN : capacités présentes,
partielles, absentes et non vérifiées. Produire ensuite un backlog
priorisé avec identifiants de phases et sous-phases, dépendances,
preuves dans le code et critères d'acceptation.
