# Inventaire documentaire ETHAN — Phase A / Phase B (réorganisation)

Date : 2026-11-04  
Auteur : Codex (agent) — inventaire proposé, non validé  
Statut : **PROPOSED — en attente d’approbation humaine avant toute migration**  
Branche Git : `refactor/ethan-rebuild-p0`  
Commit de base observé : `9e57d1c0`  

Principe appliqué : `docs/` = documentation officielle destinée aux utilisateurs ; `Obsidian/` = documentation interne, technique, architecturale, ingénierie et mémoire opérationnelle.

## 1. Tableau principal

| ID | Chemin actuel | Titre | Catégorie | Destination | Action | Justification | Risque |
|---|---|---|---|---|---|---|---|
| DOC-0001 | `Obsidian/AGENTS.md` | AGENTS.md — Règles spécifiques à Obsidian/ | Gouvernance | Obsidian/ | Conserver | Index / gouvernance locale | Faible |
| DOC-0002 | `Obsidian/Archives/Conversations/cline/2026-06-12/1781261826788.md` | Tu es responsable du Plugin Engine.  Tu n'as pas le droit de modifier autre chos | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0003 | `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` | Tu es un Distinguished Software Architect (niveau CTO Palantir / Google).  Tu es | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0004 | `Obsidian/Archives/Conversations/cline/2026-06-12/1781265677020.md` | Tu es chargé de concevoir Osiris-Lab v2.  Ignore les implémentations existantes. | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0005 | `Obsidian/Archives/Conversations/cline/2026-06-13/1781324525374.md` | Tu es l’architecte logiciel principal du projet OSIRIS-Lab v2.  Tu dois considér | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0006 | `Obsidian/Archives/Conversations/cline/2026-06-13/1781326479958.md` | fais moi un docker-compose.yml | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0007 | `Obsidian/Archives/Conversations/cline/2026-06-14/1781438417220.md` | Tu es l’architecte logiciel principal du projet OSIRIS-Lab v2.  Tu dois considér | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0008 | `Obsidian/Archives/Conversations/cline/2026-06-14/1781440243749.md` | Quand tu modifies le projet OSIRIS :  - Tu dois identifier le module concerné da | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0009 | `Obsidian/Archives/Conversations/cline/2026-06-14/1781445007397.md` | Tu fais partie de l'équipe d'ingénierie d'Osiris-Lab v2.  Les fichiers contenus | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0010 | `Obsidian/Archives/Conversations/cline/2026-06-15/1781506386208.md` | # OSIRIS META ORCHESTRATION ENGINEER  ## 1. MISSION  Concevoir la couche supérie | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0011 | `Obsidian/Archives/Conversations/cline/2026-06-16/1781448124733.md` | Tu es le Chief Technology Officer (CTO) du projet Osiris-Lab v2.  Tu es responsa | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0012 | `Obsidian/Archives/Conversations/cline/2026-06-16/1781584795579.md` | Dockerfile:14  --------------------    12 \|     # Build the GEOINT worker binary | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0013 | `Obsidian/Archives/Conversations/cline/2026-06-17/1781619688061.md` | You are an Autonomous DevOps Engineer inside a system called "Osiris Self-Healin | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0014 | `Obsidian/Archives/Conversations/cline/2026-06-17/1781684089320.md` | You are a principal software architect (Google / Palantir / Microsoft-level).  Y | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0015 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781696790844.md` | ------  > [osiris-app internal] load metadata for docker.io/library/node:22-alpi | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0016 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781759466869.md` | Tu es un ingénieur senior spécialisé en architecture logicielle SOC/OSINT.  Anal | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0017 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781763556859.md` | Dockerfile.app:4  --------------------     2 \|     WORKDIR /app     3 \|     COPY | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0018 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781763556860.md` | Dockerfile.app:4  --------------------     2 \|     WORKDIR /app     3 \|     COPY | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0019 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781773490515.md` | Tu es chargé de concevoir Osiris-Lab, une plateforme d’intelligence modulaire de | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0020 | `Obsidian/Archives/Conversations/cline/2026-06-18/1781773629795.md` | Tu es chargé de concevoir Osiris-Lab, une plateforme d’intelligence modulaire de | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0021 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781790224363.md` | [+] up 3/4  ✔ Image osiris-intel:latest          Built | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0022 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781845301775.md` | Analyse entièrement ce dépôt.  Je veux que tu comprennes :  - l'architecture com | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0023 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781847538003.md` | Supprime toutes les traces de "Cline".  Inclut :  - texte - commentaires - varia | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0024 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781852108784.md` | Tu fais partie de l'équipe d'ingénierie d'Osiris-Lab v2.  Les fichiers contenus | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0025 | `Obsidian/Archives/Conversations/cline/2026-06-19/1781855138200.md` | Analyse la feature demandée en utilisant /docs.  1. Identifier modules impactés | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0026 | `Obsidian/Archives/Conversations/cline/2026-06-20/1781926691577.md` | zookeeper:   image: confluentinc/cp-zookeeper:7.6.0   ports:     - "2181:2181" | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0027 | `Obsidian/Archives/Conversations/cline/2026-06-20/1781927049974.md` | # PROMPT CODEX — CLEAN REPOSITORY & REBRAND TO OSIRIS-LAB  You are the Lead Soft | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0028 | `Obsidian/Archives/Conversations/cline/2026-06-21/1781928390660.md` | # Mission  Tu es un ingénieur DevOps et Software Architect senior.  Tu dois rest | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0029 | `Obsidian/Archives/Conversations/cline/2026-06-21/1782049607778.md` | You are a Senior Software Engineer responsible for safe refactoring of a product | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0030 | `Obsidian/Archives/Conversations/cline/2026-06-22/1782110267799.md` | # RFC-004 — Docker Foundation Clean Architecture  ## Role  You are a Senior Plat | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0031 | `Obsidian/Archives/Conversations/cline/2026-06-23/1782122303274.md` | # ADR-1003 — Single Entry Intent Model  ## Context  Multiple input types exist ( | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0032 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782236030293.md` | Design a full test suite for ETHAN CLI.  ---  # OBJECTIVE  Validate all CLI comm | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0033 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782277746766.md` | Design a full test suite for ETHAN CLI.  ---  # OBJECTIVE  Validate all CLI comm | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0034 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782282405489.md` | Set up the MCP server from https://github.com/VapiAI/mcp-server while adhering t | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0035 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782291853665.md` | Design a performance benchmark suite for ETHAN CLI.  ---  # OBJECTIVE  Measure C | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0036 | `Obsidian/Archives/Conversations/cline/2026-06-24/1782299082878.md` | Design a debug mode for ETHAN CLI.  ---  # OBJECTIVE  Allow developers to inspec | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0037 | `Obsidian/Archives/Conversations/cline/2026-06-26/1782299840579.md` | Tu es un architecte logiciel senior spécialisé dans les systèmes d'IA autonomes. | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0038 | `Obsidian/Archives/Conversations/cline/2026-07-08/1782460736319.md` | Tu es un architecte logiciel senior spécialisé dans les assistants IA autonomes. | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0039 | `Obsidian/Archives/Conversations/cline/2026-07-08/1783480315445.md` | # ETHAN Systemd Services Auditor & Repair Agent  Tu es un ingénieur DevOps spéci | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0040 | `Obsidian/Archives/Conversations/cline/2026-07-09/1783498502281.md` | # ETHAN - Phase 0 : Préparation de la refonte complète du WebUI  Tu es le Lead S | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0041 | `Obsidian/Archives/Conversations/cline/2026-07-12/1783841799690.md` | You are the Lead UX Designer and Frontend Architect for the ETHAN AI Operating S | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0042 | `Obsidian/Archives/Conversations/cline/2026-07-18/1783595051689.md` | # ROLE  Tu es le Lead CTO du projet ETHAN.  Tu es responsable de la qualité glob | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0043 | `Obsidian/Archives/Conversations/cline/2026-07-19/1784446073123.md` | MISSION  Refondre complètement la commande :  ./ethan doctor  OBJECTIF  Transfor | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0044 | `Obsidian/Archives/Conversations/cline/2026-07-19/1784465617197.md` | Tu agis comme un Principal Software Architect et CTO avec plus de 20 ans d'expér | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0045 | `Obsidian/Archives/Conversations/cline/2026-07-20/1784468478017.md` | Tu es un Principal Platform Engineer spécialisé dans les plateformes Linux distr | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0046 | `Obsidian/Archives/Conversations/cline/2026-07-21/1784553716546.md` | Tu interviens comme Chief Technology Officer (CTO), Enterprise Software Architec | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0047 | `Obsidian/Archives/Conversations/cline/2026-07-22/1784629956873.md` | Tu es le CTO responsable de la stabilisation du projet ETHAN.  Tu as accès aux r | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0048 | `Obsidian/Archives/Conversations/cline/2026-07-22/1784702896150.md` | Tu es un ingénieur DevOps/SRE senior.  Audit le runtime ETHAN.  Objectif : Faire | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0049 | `Obsidian/Archives/Conversations/cline/2026-07-22/1784714379731.md` | Tu es le CTO responsable de la stabilisation du projet ETHAN.  Tu as accès aux r | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0050 | `Obsidian/Archives/Conversations/cline/2026-07-23/1784720147277.md` | Tu es architecte logiciel.  Maintenant que Core fonctionne :  Analyse ETHAN pour | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0051 | `Obsidian/Archives/Conversations/cline/2026-07-23/1784780539134.md` | Tu es un Lead Frontend et un expert Next.js.  Mission :  Réaliser un audit compl | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0052 | `Obsidian/Archives/Conversations/cline/2026-07-30/1784803567417.md` | Tu es Lead Frontend, UX Architect et Architecte logiciel.  Le projet ETHAN possè | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0053 | `Obsidian/Archives/Conversations/cline/2026-07-31/1785382419039.md` | Tu es un ingénieur Senior SRE / Architecte Linux spécialisé en systemd, Docker C | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0054 | `Obsidian/Archives/Conversations/cline/2026-07-31/1785475619469.md` | Mission : auditer entièrement la séquence de démarrage ETHAN.  Contexte :  NATS | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0055 | `Obsidian/Archives/Conversations/cline/2026-07-31/1785478061904.md` | Session 1785478061904 | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0056 | `Obsidian/Archives/Conversations/cline/2026-07-31/1785497242482.md` | Tu es un Senior Staff Engineer SRE + Python Architect chargé de stabiliser ETHAN | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0057 | `Obsidian/Archives/Conversations/cline/2026-08-02/1785510775651.md` | Tu es expert React UI.  Mission :  Analyser uniquement la Sidebar.  Comparer ave | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0058 | `Obsidian/Archives/Conversations/cline/2026-08-02/1785663110020.md` | Tu es un architecte logiciel senior spécialisé dans les plateformes IA.  Analyse | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0059 | `Obsidian/Archives/Conversations/cline/2026-08-03/1785676074904.md` | Améliore l'interface Chat ETHAN.  Ajouter un sélecteur de moteur IA directement | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0060 | `Obsidian/Archives/Conversations/cline/2026-08-03/1785748404435.md` | # ETHAN Architecture Audit Agent  Tu es un architecte logiciel senior chargé d'a | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0061 | `Obsidian/Archives/Conversations/cline/2026-08-04/1785763683280.md` | # ETHAN Unified Configuration Agent  Mission :  Créer un système de configuratio | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0062 | `Obsidian/Archives/Conversations/cline/2026-08-11/1786194792842.md` | # CODEX PROMPT — STANDARDIZE ALL OSIRIS-LAB WORKERS  You are the Principal Go En | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0063 | `Obsidian/Archives/Conversations/cline/2026-08-11/1786441307139.md` | # CODEX PROMPT — STANDARDIZE ALL OSIRIS-LAB WORKERS  You are the Principal Go En | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0064 | `Obsidian/Archives/Conversations/cline/2026-08-12/1785821621715.md` | # ETHAN Interface Independence Validation  Mission :  Valider que les interfaces | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0065 | `Obsidian/Archives/Conversations/cline/2026-08-12/1786516782485.md` | Tu es le CTO / Principal Software Architect nouvellement responsable de la trans | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0066 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786520589377.md` | Tu es le CTO / Principal Engineer responsable de la refonte complète de la WebUI | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0067 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-01.md` | Tu es maintenant Principal Engineer spécialisé dans les plateformes AI/Agent et | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0068 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-02.md` | 1786588790163-part-02.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0069 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-03.md` | 1786588790163-part-03.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0070 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-04.md` | 1786588790163-part-04.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0071 | `Obsidian/Archives/Conversations/cline/2026-08-13/1786588790163-part-05.md` | 1786588790163-part-05.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0072 | `Obsidian/Archives/Conversations/cline/2026-08-14/1786592167914.md` | Tu es maintenant l'architecte principal chargé de concevoir la transformation Op | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0073 | `Obsidian/Archives/Conversations/cline/2026-08-14/1786689632319.md` | Tu es un Senior SRE / Principal Backend Engineer spécialisé dans Docker, FastAPI | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0074 | `Obsidian/Archives/Conversations/cline/2026-08-14/1786691977752.md` | Tu es le CTO responsable de transformer Open-WebUI en ETHAN WebUI.  Utilise tous | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0075 | `Obsidian/Archives/Conversations/cline/2026-08-14/1786694120897.md` | Tu es le CTO responsable de transformer Open-WebUI en ETHAN WebUI.  Utilise tous | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0076 | `Obsidian/Archives/Conversations/cline/2026-08-15/1786715813776.md` | Tu es le CTO / Principal Engineer d'ETHAN.  À chaque nouvelle session de travail | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0077 | `Obsidian/Archives/Conversations/cline/2026-08-15/1786767655858.md` | Tu es maintenant le Senior Engineer responsable de l'implémentation P0 du plan : | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0078 | `Obsidian/Archives/Conversations/cline/2026-08-15/1786771650555.md` | Tu es maintenant le CTO effectuant une revue indépendante du travail réalisé.  T | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0079 | `Obsidian/Archives/Conversations/cline/2026-08-17/1786773027890.md` | Tu travailles sur le projet ETHAN.  OBJECTIF  Nous voulons faire évoluer l'inter | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0080 | `Obsidian/Archives/Conversations/cline/2026-08-17/1786962026659.md` | Tu travailles sur le projet ETHAN.  OBJECTIF ARCHITECTURAL  Nous allons intégrer | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0081 | `Obsidian/Archives/Conversations/cline/2026-08-18/1786966184691.md` | Nous avons maintenant deux éléments distincts :  1. ETHAN 2. Open WebUI déployé | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0082 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787028404021.md` | # ETHAN — WEBUI PLAN EXECUTION / IMPLEMENTATION MODE  Tu travailles directement | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0083 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787031131780.md` | # ETHAN — APPLY EXISTING ARCHITECTURE  Tu travailles dans le repository ETHAN : | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0084 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787040529358.md` | # ETHAN WEBUI — TRUE OPEN WEBUI FORK STRATEGY  Tu travailles dans :  /home/fatsi | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0085 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787043334788.md` | # ETHAN WEBUI — IMPLEMENTATION FROM EXISTING SPECIFICATIONS  Repository:  /home/ | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0086 | `Obsidian/Archives/Conversations/cline/2026-08-18/1787050182381.md` | # ETHAN WEBUI — OPEN WEBUI FUNCTIONALITY  Utilise les fonctionnalités et mécanis | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0087 | `Obsidian/Archives/Conversations/cline/2026-08-19/1787051436064.md` | # ETHAN WEBUI — MASTER IMPLEMENTATION VERIFICATION  Repository:  /home/fatsio/AI | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0088 | `Obsidian/Archives/Conversations/cline/2026-08-23/1787143354523.md` | # ETHAN WEBUI — FUNCTIONALITY RESTORATION AND OPEN WEBUI FIDELITY  Repository: | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0089 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-01.md` | Gérer le cycle de vie d’Odin | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0090 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-02.md` | 01a16865-1f63-7e03-a356-f32e825a29c2-part-02.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0091 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-03.md` | 01a16865-1f63-7e03-a356-f32e825a29c2-part-03.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0092 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16865-1f63-7e03-a356-f32e825a29c2-part-04.md` | 01a16865-1f63-7e03-a356-f32e825a29c2-part-04.md | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0093 | `Obsidian/Archives/Conversations/codex/2026-10-23/01a16882-fc47-73c2-85e1-a6093f0dbfd9.md` | Migrer God’s Eye View vers Odin | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0094 | `Obsidian/Archives/Conversations/copilot/2026-04-24/b19268d9-cfc6-4cf3-b3cf-142ff2d72088.md` | Tu es un ingénieur logiciel senior expert en IA locale, systèmes d’agents LLM, R | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0095 | `Obsidian/Archives/Conversations/copilot/2026-05-25/36e60f5c-6fff-4b49-91db-77a2eb8078d6.md` | Construis maintenant le bootstrap COMPLET du projet Atas AI.  Génère UNIQUEMENT | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0096 | `Obsidian/Archives/Conversations/from-ethan-knowledge/cline/2026-08-13/1786588790163.md` | Tu es maintenant Principal Engineer spécialisé dans les plateformes AI/Agent et | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0097 | `Obsidian/Archives/Events/EVT-20261103T132131362051-OBSERVED-ethan-api-gateway-started.md` | ETHAN API gateway started | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0098 | `Obsidian/Archives/Events/EVT-20261103T150233966728-OBSERVED-ethan-api-gateway-started.md` | ETHAN API gateway started | Archive | Obsidian/ | Ne pas modifier | Archive historique | Faible |
| DOC-0099 | `Obsidian/INDEX.md` | INDEX — Mémoire technique ETHAN | Gouvernance | Obsidian/ | Conserver | Index / gouvernance locale | Faible |
| DOC-0100 | `Obsidian/Knowledge/Architecture/ADR-EM-001-engineering-memory-architecture.md` | ADR-EM-001 — Architecture Engineering Memory pour ETHAN | ADR | Obsidian/ | Conserver | ADR (décision d’architecture, mémoire) | Faible |
| DOC-0101 | `Obsidian/Knowledge/Architecture/ASR-EM-001-engineering-memory-security.md` | ASR-EM-001 — Exigences de sécurité de la mémoire technique | ASR | Obsidian/ | Conserver | ASR (exigence de sécurité, mémoire) | Faible |
| DOC-0102 | `Obsidian/Knowledge/Architecture/ECOSYSTEM_SHARED_INTELLIGENCE_ARCHITECTURE.md` | ETHAN — Architecture d'intelligence partagée pour les applications indépendantes | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0103 | `Obsidian/Knowledge/Architecture/EM-SERVICE-ARCHITECTURE.md` | ETHAN — Architecture du Engineering Memory Service | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0104 | `Obsidian/Knowledge/Architecture/ESR-EM-001-engineering-memory.md` | ESR-EM-001 — Exigences système de la mémoire technique | ESR | Obsidian/ | Conserver | ESR (exigence système, mémoire) | Faible |
| DOC-0105 | `Obsidian/Knowledge/Architecture/ETHAN_APPLICATION_INTEGRATION_CONTRACT.md` | ETHAN Application Integration Contract | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0106 | `Obsidian/Knowledge/Architecture/ETHAN_ENGINEERING_MEMORY_ARCHITECTURE.md` | ETHAN — Architecture de la mémoire technique | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0107 | `Obsidian/Knowledge/Architecture/MEMORY_DATA_MODEL.md` | ETHAN — Modèle de données de la mémoire technique | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0108 | `Obsidian/Knowledge/Architecture/RECORD_TEMPLATES.md` | ETHAN — Modèles d'enregistrement | Architecture | Obsidian/ | Conserver | Architecture technique (mémoire) | Faible |
| DOC-0109 | `Obsidian/Knowledge/INDEX_ETHAN_KNOWLEDGE.md` | ETHAN Knowledge Base — Index | Document | Obsidian/ | Conserver | Connaissance technique (Obsidian) | Faible |
| DOC-0110 | `Obsidian/Knowledge/Syntheses/by-agent/cline-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse — Cline | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0111 | `Obsidian/Knowledge/Syntheses/by-agent/cline-summary.md` | Synthèse — Cline | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0112 | `Obsidian/Knowledge/Syntheses/by-agent/codex-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse — Codex | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0113 | `Obsidian/Knowledge/Syntheses/by-agent/codex-summary.md` | Synthèse — Codex | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0114 | `Obsidian/Knowledge/Syntheses/by-agent/copilot-summary-ethan-knowledge-2026-10-28T11-29.md` | Synthèse — Copilot | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0115 | `Obsidian/Knowledge/Syntheses/by-agent/copilot-summary.md` | Synthèse — Copilot | Note | Obsidian/ | Conserver | Synthèse agent (résumé) | Faible |
| DOC-0116 | `Obsidian/Knowledge/Sécurité/PERMISSION_MODEL.md` | ETHAN — Modèle de permissions pour l'Engineering Memory | Document | Obsidian/ | Conserver | Modèle de permission / sécurité | Faible |
| DOC-0117 | `Obsidian/Metadata/REGISTRY.md` | ETHAN — Registre de routage de la mémoire | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0118 | `Obsidian/Operational-Memory/BLOCKERS.md` | BLOCKERS — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0119 | `Obsidian/Operational-Memory/DECISIONS.md` | DECISIONS — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0120 | `Obsidian/Operational-Memory/DOCUMENTATION_AUDIT_REPORT_2026-11-04.md` | Audit de la documentation ETHAN — Phase A / Phase B | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0121 | `Obsidian/Operational-Memory/DOCUMENTATION_INVENTORY.md` | Inventaire documentaire ETHAN — Phase A / Phase B | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0122 | `Obsidian/Operational-Memory/MEMORY_GOVERNANCE.md` | ETHAN — Gouvernance de la mémoire technique | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0123 | `Obsidian/Operational-Memory/PROJECT_STATE.md` | PROJECTSTATE — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0124 | `Obsidian/Operational-Memory/TASKS.md` | TASKS — ETHAN | Note | Obsidian/ | Conserver | Mémoire opérationnelle | Faible |
| DOC-0125 | `Obsidian/Operational-Memory/sources/docs-memory/DECISIONS.md` | Décisions — ETHAN | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0126 | `Obsidian/Operational-Memory/sources/docs-memory/PROJECT_STATE.md` | État courant — ETHAN | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0127 | `Obsidian/Operational-Memory/sources/docs-memory/README.md` | Mémoire inter-sessions Codex — ETHAN | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0128 | `Obsidian/Operational-Memory/sources/docs-memory/sessions/2026-11-01.md` | Archive de session — 2026-11-01 | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0129 | `Obsidian/Operational-Memory/sources/docs-memory/sessions/2026-11-02.md` | Session 2026-11-02 | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0130 | `Obsidian/Operational-Memory/sources/ethan-knowledge-meta/sync-state.json` | sync-state.json | Note | Obsidian/ | Référencer | Copie source de docs/memory ou snapshot externe | Faible |
| DOC-0131 | `Obsidian/README.md` | ETHAN — Mémoire technique consolidée | Gouvernance | Obsidian/ | Conserver | Index / gouvernance locale | Faible |
| DOC-0132 | `Obsidian/_meta/ADR_MEM_010_RECONCILIATION_REPORT.md` | ADR-MEM-010 RECONCILIATION REPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0133 | `Obsidian/_meta/ADR_MEM_011_RECONCILIATION_REPORT.md` | ADR-MEM-011 RECONCILIATION REPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0134 | `Obsidian/_meta/ADR_MEM_012_RECONCILIATION_REPORT.md` | ADR-MEM-012 RECONCILIATION REPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0135 | `Obsidian/_meta/AGENT_MEMORY_PROTOCOL_REPORT.md` | AGENTMEMORYPROTOCOLREPORT — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0136 | `Obsidian/_meta/ARCHITECTURE_OPTIONS.md` | ARCHITECTUREOPTIONS — ETHAN Engineering Memory | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0137 | `Obsidian/_meta/AUDIT-ARCHIVES_ODSIDIAN.md` | AUDIT-ARCHIVES — Base de connaissance ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0138 | `Obsidian/_meta/CLEANUP_REPORT.md` | CLEANUP REPORT — ETHAN / OBSIDIAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0139 | `Obsidian/_meta/CONSOLIDATION_REPORT.md` | CONSOLIDATION REPORT — ETHAN / OBSIDIAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0140 | `Obsidian/_meta/CTO_RECONSTRUCTION_REPORT.md` | CTO RECONSTRUCTION REPORT — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0141 | `Obsidian/_meta/DECISION_REGISTER.md` | DECISION REGISTER — ETHAN | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0142 | `Obsidian/_meta/DELIVERY_GATE_REPORT.md` | DELIVERYGATEREPORT — ETHAN Engineering Memory | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0143 | `Obsidian/_meta/ECOSYSTEM_ARCHITECTURE_VALIDATION_REPORT.md` | ECOSYSTEMARCHITECTUREVALIDATIONREPORT.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0144 | `Obsidian/_meta/ECOSYSTEM_CAPABILITY_MATRIX.md` | ECOSYSTEMCAPABILITYMATRIX.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0145 | `Obsidian/_meta/ECOSYSTEM_DECISION_GAPS.md` | ECOSYSTEMDECISIONGAPS.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0146 | `Obsidian/_meta/ECOSYSTEM_DECISION_WORKBOOK.md` | ECOSYSTEMDECISIONWORKBOOK — ETHAN | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0147 | `Obsidian/_meta/ETHAN_APPLICATION_INTEGRATION_COMPARISON.md` | ETHANAPPLICATIONINTEGRATIONCOMPARISON | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0148 | `Obsidian/_meta/ETHAN_PHASE_25_PLUGINS_UI_RELIABILITY.md` | ETHANPHASE25PLUGINSUIRELIABILITY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0149 | `Obsidian/_meta/ETHAN_PHASE_26_RICH_RESPONSE_UI.md` | ETHANPHASE26RICHRESPONSEUI | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0150 | `Obsidian/_meta/ETHAN_PHASE_27_RICH_RESPONSE_VALIDATION.md` | ETHANPHASE27RICHRESPONSEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0151 | `Obsidian/_meta/ETHAN_PHASE_28_PLUGINS_UI_REPAIR.md` | ETHANPHASE28PLUGINSUIREPAIR | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0152 | `Obsidian/_meta/ETHAN_PHASE_29_PLUGINS_TOOLS_SEPARATION.md` | ETHANPHASE29PLUGINSTOOLSSEPARATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0153 | `Obsidian/_meta/ETHAN_PHASE_30_AUTHENTICATED_RUNTIME_VALIDATION.md` | ETHANPHASE30AUTHENTICATEDRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0154 | `Obsidian/_meta/ETHAN_PHASE_30_PLUGINS_SYSTEM_RECOVERY.md` | ETHANPHASE30PLUGINSSYSTEMRECOVERY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0155 | `Obsidian/_meta/ETHAN_PHASE_31_RICH_RESPONSE_BROWSER_VALIDATION.md` | ETHANPHASE31RICHRESPONSEBROWSERVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0156 | `Obsidian/_meta/ETHAN_PHASE_32_FRAMES_OPERATIONAL_INTEGRATION.md` | ETHANPHASE32FRAMESOPERATIONALINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0157 | `Obsidian/_meta/ETHAN_PHASE_33_FRAMES_RUNTIME_VALIDATION.md` | ETHANPHASE33FRAMESRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0158 | `Obsidian/_meta/ETHAN_PHASE_36A_QUANTAR_RENAMING.md` | ETHANPHASE36AQUANTARRENAMING | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0159 | `Obsidian/_meta/ETHAN_PHASE_36_QUANTAR_FUNCTIONAL_IMPLEMENTATION.md` | ETHANPHASE36QUANTARFUNCTIONALIMPLEMENTATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0160 | `Obsidian/_meta/ETHAN_PHASE_37A_QUANTAR_SECURITY.md` | ETHANPHASE37AQUANTARSECURITY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0161 | `Obsidian/_meta/ETHAN_PHASE_37B_QUANTAR_RUNTIME_SECURITY.md` | ETHANPHASE37BQUANTARRUNTIMESECURITY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0162 | `Obsidian/_meta/ETHAN_PHASE_37_QUANTAR_SECURITY_RUNTIME.md` | ETHANPHASE37QUANTARSECURITYRUNTIME | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0163 | `Obsidian/_meta/ETHAN_PHASE_38_QUANTAR_RUNTIME_BOUNDARY.md` | ETHANPHASE38QUANTARRUNTIMEBOUNDARY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0164 | `Obsidian/_meta/ETHAN_PHASE_39_QUANTAR_DEDICATED_RUNTIME.md` | ETHANPHASE39QUANTARDEDICATEDRUNTIME | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0165 | `Obsidian/_meta/ETHAN_PHASE_40B_QUANTAR_E2E_VALIDATION.md` | ETHANPHASE40BQUANTARE2EVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0166 | `Obsidian/_meta/ETHAN_PHASE_40C_QUANTAR_APPLICATION_ACTIVATION.md` | ETHANPHASE40CQUANTARAPPLICATIONACTIVATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0167 | `Obsidian/_meta/ETHAN_PHASE_40E_QUANTAR_LIFECYCLE_IMPLEMENTATION.md` | ETHANPHASE40EQUANTARLIFECYCLEIMPLEMENTATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0168 | `Obsidian/_meta/ETHAN_PHASE_42_QUANTAR_ACTION.md` | ETHANPHASE42QUANTARACTION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0169 | `Obsidian/_meta/ETHAN_PHASE_42_QUANTAR_ACTIVATION.md` | ETHANPHASE42QUANTARACTIVATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0170 | `Obsidian/_meta/ETHAN_QUANTAR_COMPOSESERVICE_INTEGRATION.md` | ETHANQUANTARCOMPOSESERVICEINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0171 | `Obsidian/_meta/ETHAN_QUANTAR_ODIN_CONTROLLER_COMPARISON.md` | ETHANQUANTARODINCONTROLLERCOMPARISON | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0172 | `Obsidian/_meta/ETHAN_QUANTAR_PHASE_42E_RUNTIME_REPAIR.md` | ETHANQUANTARPHASE42ERUNTIMEREPAIR | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0173 | `Obsidian/_meta/ETHAN_QUANTAR_PHASE_43_CONTROLLER.md` | ETHANQUANTARPHASE43CONTROLLER | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0174 | `Obsidian/_meta/ETHAN_UNIFIED_CONTROLLER_STUDY.md` | ETHANUNIFIEDCONTROLLERSTUDY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0175 | `Obsidian/_meta/FILE_MANIFEST.csv` | FILE_MANIFEST.csv | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0176 | `Obsidian/_meta/INDEX_ODSIDIAN_SOURCE.md` | ETHAN Knowledge Base — Index | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0177 | `Obsidian/_meta/LINK_MANIFEST.csv` | LINK_MANIFEST.csv | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0178 | `Obsidian/_meta/MASTER_IMPLEMENTATION_ROADMAP.md` | MASTERIMPLEMENTATIONROADMAP — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0179 | `Obsidian/_meta/MEMORY_EVENT_LOG.ndjson` | MEMORY_EVENT_LOG.ndjson | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0180 | `Obsidian/_meta/MEM_013_REVISION_REPORT.md` | MEM013REVISIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0181 | `Obsidian/_meta/MEM_013_RUST_PYTHON_ARCHITECTURE_PROPOSAL.md` | MEM-013 — RUST/PYTHON ARCHITECTURE PROPOSAL | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0182 | `Obsidian/_meta/MEM_014_ARCHITECTURE_COHERENCE_AUDIT.md` | MEM014ARCHITECTURECOHERENCEAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0183 | `Obsidian/_meta/MEM_014_CAPABILITY_REGISTRY_REPORT.md` | MEM014CAPABILITYREGISTRYREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0184 | `Obsidian/_meta/MEM_014_COMPLIANCE_AUDIT_REPORT.md` | MEM014COMPLIANCEAUDITREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0185 | `Obsidian/_meta/MEM_014_FORMALIZATION_REPORT.md` | MEM-014 — Rapport de formalisation | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0186 | `Obsidian/_meta/MEM_014_FORMATION_REPORT.md` | MEM014FORMATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0187 | `Obsidian/_meta/MEM_014_GLOBAL_ARCHITECTURE_AUDIT.md` | MEM014GLOBALARCHITECTUREAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0188 | `Obsidian/_meta/MEM_014_HROT_HARDENING_REPORT.md` | MEM014HROTHARDENINGREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0189 | `Obsidian/_meta/MEM_014_HROT_OPERATIONAL_READINESS_REPORT.md` | MEM014HROTOPERATIONALREADINESSREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0190 | `Obsidian/_meta/MEM_014_HROT_PRODUCTION_CRYPTO_REPORT.md` | MEM014HROTPRODUCTIONCRYPTOREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0191 | `Obsidian/_meta/MEM_014_IMPLEMENTATION_READINESS_AUDIT.md` | MEM014IMPLEMENTATIONREADINESSAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0192 | `Obsidian/_meta/MEM_014_IMPLEMENTATION_ROADMAP.md` | MEM014IMPLEMENTATIONROADMAP | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0193 | `Obsidian/_meta/MEM_014_INTEGRATION_READINESS_ROADMAP.md` | MEM014INTEGRATIONREADINESSROADMAP | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0194 | `Obsidian/_meta/MEM_014_PERSISTENCE_IMPLEMENTATION_REPORT.md` | MEM014PERSISTENCEIMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0195 | `Obsidian/_meta/MEM_014_PHASE_12_SECURITY_AUDIT.md` | MEM014PHASE12SECURITYAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0196 | `Obsidian/_meta/MEM_014_PHASE_13_APPLICATION_INTEGRATION_READINESS.md` | MEM014PHASE13APPLICATIONINTEGRATIONREADINESS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0197 | `Obsidian/_meta/MEM_014_PHASE_14_END_TO_END_VALIDATION.md` | MEM014PHASE14ENDTOENDVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0198 | `Obsidian/_meta/MEM_014_PHASE_15_ODIN_PILOT_READINESS.md` | MEM014PHASE15ODINPILOTREADINESS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0199 | `Obsidian/_meta/MEM_014_PHASE_16_ODIN_PILOT_INTEGRATION.md` | MEM014PHASE16ODINPILOTINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0200 | `Obsidian/_meta/MEM_014_PHASE_17_ODIN_WEBUI_INTEGRATION.md` | MEM014PHASE17ODINWEBUIINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0201 | `Obsidian/_meta/MEM_014_PHASE_18_ODIN_OPERATIONAL_VALIDATION.md` | MEM014PHASE18ODINOPERATIONALVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0202 | `Obsidian/_meta/MEM_014_PHASE_19_3_AUTHENTICATED_RUNTIME_VALIDATION.md` | MEM014PHASE193AUTHENTICATEDRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0203 | `Obsidian/_meta/MEM_014_PHASE_19_ODIN_RUNTIME_VALIDATION.md` | MEM014PHASE19ODINRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0204 | `Obsidian/_meta/MEM_014_PHASE_1_IMPLEMENTATION_REPORT.md` | MEM014PHASE1IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0205 | `Obsidian/_meta/MEM_014_PHASE_20_FRAMES_PILOT_READINESS.md` | MEM014PHASE20FRAMESPILOTREADINESS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0206 | `Obsidian/_meta/MEM_014_PHASE_21_FRAMES_RUNTIME_VALIDATION.md` | MEM014PHASE21FRAMESRUNTIMEVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0207 | `Obsidian/_meta/MEM_014_PHASE_22_RUNTIME_AUTH_READINESS.md` | MEM014PHASE22RUNTIMEAUTHREADINESS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0208 | `Obsidian/_meta/MEM_014_PHASE_23_NATS_RUNTIME_ALIGNMENT.md` | MEM014PHASE23NATSRUNTIMEALIGNMENT | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0209 | `Obsidian/_meta/MEM_014_PHASE_24_AUTH_WEBUI_ODIN_VALIDATION.md` | MEM014PHASE24AUTHWEBUIODINVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0210 | `Obsidian/_meta/MEM_014_PHASE_2_IMPLEMENTATION_REPORT.md` | MEM014PHASE2IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0211 | `Obsidian/_meta/MEM_014_PHASE_34_QUANTAR_INTEGRATION.md` | MEM014PHASE34QUANTARINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0212 | `Obsidian/_meta/MEM_014_PHASE_35_QUANTAR_PILOT_INTEGRATION.md` | MEM014PHASE35QUANTARPILOTINTEGRATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0213 | `Obsidian/_meta/MEM_014_PHASE_3_IMPLEMENTATION_REPORT.md` | MEM014PHASE3IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0214 | `Obsidian/_meta/MEM_014_PHASE_41_APPLICATION_ECOSYSTEM.md` | MEM014PHASE41APPLICATIONECOSYSTEM | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0215 | `Obsidian/_meta/MEM_014_PHASE_4_IMPLEMENTATION_REPORT.md` | MEM014PHASE4IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0216 | `Obsidian/_meta/MEM_014_PHASE_5_IMPLEMENTATION_REPORT.md` | MEM014PHASE5IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0217 | `Obsidian/_meta/MEM_014_PHASE_6_IMPLEMENTATION_REPORT.md` | MEM014PHASE6IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0218 | `Obsidian/_meta/MEM_014_PHASE_7_IMPLEMENTATION_REPORT.md` | MEM014PHASE7IMPLEMENTATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0219 | `Obsidian/_meta/MIGRATION_REPORT.md` | MIGRATIONREPORT — Consolidation de la mémoire technique ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0220 | `Obsidian/_meta/PHASE_19_1_NATS_BACKEND_RECOVERY.md` | PHASE191NATSBACKENDRECOVERY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0221 | `Obsidian/_meta/PHASE_1_3_ARBITRATION_REPORT.md` | PHASE13ARBITRATIONREPORT — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0222 | `Obsidian/_meta/PHASE_2_VALIDATION_REPORT.md` | PHASE2VALIDATIONREPORT — ETHAN Engineering Memory | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0223 | `Obsidian/_meta/POST_MIGRATION_AUDIT.md` | POSTMIGRATIONAUDIT — ETHAN / Obsidian | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0224 | `Obsidian/_meta/PRODUCTION_READINESS_REPORT.md` | PRODUCTIONREADINESSREPORT — ETHAN Engineering Memory | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0225 | `Obsidian/_meta/QUANTAR_AUTHENTICATED_BROWSER_VALIDATION.md` | QUANTARAUTHENTICATEDBROWSERVALIDATION | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0226 | `Obsidian/_meta/QUANTAR_CLEAN_REBUILD_REPORT.md` | QUANTARCLEANREBUILDREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0227 | `Obsidian/_meta/QUANTAR_COMPOSE_CLEANUP.md` | QUANTARCOMPOSECLEANUP | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0228 | `Obsidian/_meta/QUANTAR_REAL_ACTIVATION_FIX.md` | QUANTARREALACTIVATIONFIX | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0229 | `Obsidian/_meta/QUANTAR_REAL_TASK_RUNTIME.md` | QUANTARREALTASKRUNTIME | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0230 | `Obsidian/_meta/QUANTAR_REBUILD_INVENTORY.md` | QUANTARREBUILDINVENTORY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0231 | `Obsidian/_meta/README_ODSIDIAN_SOURCE.md` | ETHAN Knowledge Base | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0232 | `Obsidian/_meta/RECONCILIATION_REPORT.md` | RECONCILIATIONREPORT — ETHAN / Obsidian | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0233 | `Obsidian/_meta/REGISTRY.md` | Registry pointer | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0234 | `Obsidian/_meta/SOURCE_INVENTORY.md` | SOURCEINVENTORY — Mémoire technique ETHAN | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0235 | `Obsidian/_meta/TRADINGAGENTS_API_CONTRACTS.md` | TRADINGAGENTSAPICONTRACTS.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0236 | `Obsidian/_meta/TRADINGAGENTS_ARCHITECTURE.md` | TRADINGAGENTSARCHITECTURE.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0237 | `Obsidian/_meta/TRADINGAGENTS_CAPABILITY_MATRIX.md` | TRADINGAGENTSCAPABILITYMATRIX | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0238 | `Obsidian/_meta/TRADINGAGENTS_CONTROLLER_DESIGN.md` | TRADINGAGENTSCONTROLLERDESIGN.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0239 | `Obsidian/_meta/TRADINGAGENTS_DEPENDENCY_INVENTORY.md` | TRADINGAGENTSDEPENDENCYINVENTORY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0240 | `Obsidian/_meta/TRADINGAGENTS_IMPLEMENTATION_ROADMAP.md` | TRADINGAGENTSIMPLEMENTATIONROADMAP.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0241 | `Obsidian/_meta/TRADINGAGENTS_INTEGRATION_GAPS.md` | TRADINGAGENTSINTEGRATIONGAPS | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0242 | `Obsidian/_meta/TRADINGAGENTS_PHASE_0_1_VALIDATION_REPORT.md` | TRADINGAGENTSPHASE01VALIDATIONREPORT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0243 | `Obsidian/_meta/TRADINGAGENTS_PHASE_1_1_REPORT.md` | TRADINGAGENTSPHASE11REPORT.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0244 | `Obsidian/_meta/TRADINGAGENTS_PHASE_1_REPORT.md` | TRADINGAGENTSPHASE1REPORT.md | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0245 | `Obsidian/_meta/TRADINGAGENTS_PROVIDER_COMPATIBILITY.md` | TRADINGAGENTSPROVIDERCOMPATIBILITY.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0246 | `Obsidian/_meta/TRADINGAGENTS_SECURITY_DESIGN.md` | TRADINGAGENTSSECURITYDESIGN.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0247 | `Obsidian/_meta/TRADINGAGENTS_TECHNICAL_AUDIT.md` | TRADINGAGENTSTECHNICALAUDIT | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0248 | `Obsidian/_meta/TRADINGAGENTS_UI_SPECIFICATION.md` | TRADINGAGENTSUISPECIFICATION.md | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0249 | `Obsidian/_meta/TRADINGAGENTS_UPSTREAM_RUNTIME_STUDY.md` | TRADINGAGENTSUPSTREAMRUNTIMESTUDY | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0250 | `Obsidian/_meta/VERIFICATION_MATRIX.md` | VERIFICATIONMATRIX — ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0251 | `Obsidian/_meta/odsidian-metadata/COVERAGE-REPORT.md` | Rapport de couverture — Base de connaissance ETHAN | Rapport | Obsidian/ | Conserver | Document racine (rapport/plan historique) | Faible |
| DOC-0252 | `Obsidian/_meta/odsidian-metadata/PARTS-INDEX.md` | Index des parties — Sessions découpées | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0253 | `Obsidian/_meta/odsidian-metadata/conventions.md` | Conventions de nommage | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0254 | `Obsidian/_meta/odsidian-metadata/sync-state.json` | sync-state.json | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0255 | `Obsidian/_meta/source-snapshots/ethan-knowledge/1786588790163.md` | Tu es maintenant Principal Engineer spécialisé dans les plateformes AI/Agent et | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0256 | `Obsidian/_meta/source-snapshots/ethan-knowledge/INDEX.md` | ETHAN Knowledge Base — Index | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0257 | `Obsidian/_meta/source-snapshots/ethan-knowledge/by-agent/cline-summary.md` | Synthèse — Cline | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0258 | `Obsidian/_meta/source-snapshots/ethan-knowledge/by-agent/codex-summary.md` | Synthèse — Codex | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0259 | `Obsidian/_meta/source-snapshots/ethan-knowledge/by-agent/copilot-summary.md` | Synthèse — Copilot | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0260 | `Obsidian/_meta/source-snapshots/ethan-knowledge/sync-state.json` | sync-state.json | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0261 | `Obsidian/_meta/source-snapshots/odsidian/INDEX.md` | ETHAN Knowledge Base — Index | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0262 | `Obsidian/_meta/source-snapshots/odsidian/by-agent/cline-summary.md` | Synthèse — Cline | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0263 | `Obsidian/_meta/source-snapshots/odsidian/by-agent/codex-summary.md` | Synthèse — Codex | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0264 | `Obsidian/_meta/source-snapshots/odsidian/by-agent/copilot-summary.md` | Synthèse — Copilot | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0265 | `Obsidian/_meta/source-snapshots/odsidian/sync-state.json` | sync-state.json | Note | Obsidian/ | Conserver | Métadonnées / gouvernance / registres | Faible |
| DOC-0266 | `docs/ACCOUNTS_SUMMARY.md` | Synthèse des Audits ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0267 | `docs/ARCHITECTURE_KERNEL_CORE.md` | Audit Architecture — Kernel & Core d'ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0268 | `docs/AUDIT_INTEGRATION_2026-10-08.md` | AUDITINTEGRATION2026-10-08 | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0269 | `docs/AUDIT_REPORT.md` | Audit de l'état du code ETHAN — WebUI / backend / Core | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0270 | `docs/AUDIT_SKILLS_ECC_INTEGRATION.md` | ETHAN — Phase 1: Audit d'intégration des skills ECC | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0271 | `docs/AUTH_ARCHITECTURE.md` | Architecture Cible Authentification ETHAN OS | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0272 | `docs/AUTH_FINAL_VALIDATION.md` | Validation Finale SRE — Authentification ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0273 | `docs/AUTH_FLOW_AUDIT.md` | Audit du Flux d'Authentification ETHAN | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0274 | `docs/Audit Architecture — WebUI vs Core Runtime.md` | Audit Architecture — WebUI vs Core/Runtime | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0275 | `docs/Audit Fonctionnel WebUI Dashboard (PLAN MODE).md` | 📋 Rapport Complet — Audit Fonctionnel WebUI Dashboard (PLAN MODE) | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0276 | `docs/DOUBLE_AUTH_AUDIT.md` | Audit des Systèmes d'Authentification (ETHAN OS) | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0277 | `docs/ETHAN_ENGINEERING_ROADMAP.md` | ETHAN Engineering Roadmap | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0278 | `docs/ETHAN_MASTER_PLAN.md` | ETHAN Technical Master Plan | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0279 | `docs/ETHAN_STABILITY_REPORT.md` | ETHANSTABILITYREPORT | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0280 | `docs/GITHUB_ISSUES.md` | ETHAN GitHub Issues - Tickets de Correction | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0281 | `docs/INDEX.md` | Documentation Architecture ETHAN — Index | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0282 | `docs/LLM_PROVIDERS_ARCHITECTURE.md` | Architecture Multi-Providers LLM — ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0283 | `docs/PRODUCTION_READINESS.md` | ETHAN — Rapport Go/No-Go Production (1 an autonome) | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0284 | `docs/Plan de Consolidation Architecture ETHAN.md` | Plan de Consolidation Architecture ETHAN | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0285 | `docs/README_CHANGELOG.md` | README Change Log — Refactor (Project Identity & Current Architecture) | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0286 | `docs/Rapport SRE & Architecture.md` | Rapport SRE & Architecture : Stabilisation ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0287 | `docs/Rapport_SRE_Stabilisation_Final.md` | Rapport SRE & Architecture : Stabilisation ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0288 | `docs/SECURITY_AUDIT.md` | Audit Sécurité ETHAN - OS IA Personnel | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0289 | `docs/SECURITY_AUDIT_REPORT.md` | Audit Sécurité ETHAN | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0290 | `docs/STABILITY_REPORT.md` | ETHAN Stability Report | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0291 | `docs/TECHNICAL_DEBT_ANALYSIS.md` | 📊 Analyse de la Dette Technique ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0292 | `docs/VALIDATION_FINALE_ODIN.md` | Validation Finale Intégration ETHAN ↔ Odin | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0293 | `docs/adr/ADR-001-agent-system.md` | ADR-001: Système d'Agents | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0294 | `docs/adr/ADR-1003-implementation.md` | ADR-1003 — Single Entry Intent Model — Implementation Report | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0295 | `docs/adr/ADR-1004-implementation.md` | ADR-1004 — Cognitive Loop Architecture — Implementation Report | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0296 | `docs/adr/ADR-1005-implementation.md` | ADR-1005 — Core Technology Independence — Implementation Report | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0297 | `docs/adr/ADR-1006-implementation.md` | ADR-1006 — Capability Composition Pattern — Implementation Report | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0298 | `docs/adr/ADR-1008-implementation.md` | ADR-1008 — Plugin Discovery & Loading — Implementation Report | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0299 | `docs/adr/ADR-1009-implementation.md` | ADR-1009 — Safety & Permission Model — Implementation Report | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0300 | `docs/adr/ADR-1010-rag-strategies.md` | ADR-1010 — Sélection de la stratégie de recherche RAG | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0301 | `docs/adr/ADR-1011-rag-strategy.md` | ADR-1011 — Stratégie RAG Knowledge | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0302 | `docs/adr/ADR-1012-document-vector-persistence.md` | ADR-1012 — Persistance documentaire et vectorielle | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0303 | `docs/adr/ADR-1013-frame-fork.md` | ADR-1013 — Fork Frame à partir d'HyperFrames | ADR | Obsidian/ | Fusionner après validation | ADR (décision d’architecture) | Élevé — collision de numérotation |
| DOC-0304 | `docs/adr/ADR-1013-knowledge-task-lifecycle.md` | ADR-1013 — Cycle de vie des tâches Knowledge | ADR | Obsidian/ | Fusionner après validation | ADR (décision d’architecture) | Élevé — collision de numérotation |
| DOC-0305 | `docs/adr/ADR-1014-frame-service-integration.md` | ADR-1014 — Service Frame dans ETHAN (modèle ODIN) | ADR | Obsidian/ | Fusionner après validation | ADR (décision d’architecture) | Élevé — collision de numérotation |
| DOC-0306 | `docs/adr/ADR-1014-retrieval-permission-scope.md` | ADR-1014 — Recherche et permissions | ADR | Obsidian/ | Fusionner après validation | ADR (décision d’architecture) | Élevé — collision de numérotation |
| DOC-0307 | `docs/adr/ADR-1015-embedding-model-compatibility.md` | ADR-1015 — Modèle d'embeddings et compatibilité index | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0308 | `docs/adr/ADR-1016-production-vector-backend.md` | ADR-1016 — Configuration vectorielle production | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0309 | `docs/adr/ADR-2001-implementation.md` | ADR-2001 — Memory is a Cognitive Layer — Implementation Report | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0310 | `docs/adr/ADR-MEM-014-HROT-PRODUCTION-CRYPTO.md` | ADR-MEM-014 Phase 10 — HROT Cryptography | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0311 | `docs/adr/ADR-MEM-014-PHASE-41-APPLICATION-ECOSYSTEM.md` | ADR — ETHAN Application Catalog (seclib) | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0312 | `docs/adr/ADR-MEM-014-PHASE-8-PERSISTENCE.md` | ADR-MEM-014 Phase 8 — Persistance durable SQLite | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0313 | `docs/adr/ADR-MEM-014-application-integration-governance-and-capabilities.md` | ADR-MEM-014 — Contrat d'interopérabilité, gouvernance et capacités des applications indépendantes | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0314 | `docs/api/CONTRACTS-API.md` | Contrats API — ETHAN (WebUI ↔ Core) | API | Obsidian/ | Déplacer | API / contrats / intégrations | Moyen — déplacement et liens à mettre à jour |
| DOC-0315 | `docs/api/ETHAN_REBUILD_P1_CONTRACTS.md` | ETHAN — Spécification de contrats API P1 (proposition, sans code) | API | Obsidian/ | Déplacer | API / contrats / intégrations | Moyen — déplacement et liens à mettre à jour |
| DOC-0316 | `docs/api/contract-v1.md` | Contrat API ETHAN v1 — État actuel (refonte Phase 0) | API | Obsidian/ | Déplacer | API / contrats / intégrations | Moyen — déplacement et liens à mettre à jour |
| DOC-0317 | `docs/api/openapi.v1.json` | openapi.v1.json | API | Obsidian/ | Déplacer | API / contrats / intégrations | Moyen — déplacement et liens à mettre à jour |
| DOC-0318 | `docs/api/openapi.yaml` | OpenAPI 3.1.0 — Jarvis OS API Reference | API | Obsidian/ | Déplacer | API / contrats / intégrations | Moyen — déplacement et liens à mettre à jour |
| DOC-0319 | `docs/architecture-audit.md` | Audit d'Architecture ETHAN — Rapport Actualisé | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0320 | `docs/architecture-decisions-summary.md` | Réunion Architecture — Décisions en attente | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0321 | `docs/architecture-decisions.md` | Décisions Architecture — Recommandations | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0322 | `docs/architecture.md` | Architecture d'Ethan | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0323 | `docs/architecture/ARCHITECTURE-CIBLE.md` | ETHAN — Architecture Cible Officielle | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0324 | `docs/architecture/C4-Event-Flow.md` | C4 Architecture — Event Flow | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0325 | `docs/architecture/C4-Level1-System-Context.md` | C4 Architecture — Level 1: System Context | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0326 | `docs/architecture/C4-Level2-Containers.md` | C4 Architecture — Level 2: Container Diagram | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0327 | `docs/architecture/C4-Level3-Components-Kernel.md` | C4 Architecture — Level 3: Component Diagram — Cognitive Kernel | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0328 | `docs/architecture/C4-Level4-Code-View.md` | C4 Architecture — Level 4: Code-Level View | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0329 | `docs/architecture/C4-README.md` | C4 Architecture Documentation — ETHAN Cognitive OS | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0330 | `docs/architecture/ETHAN_KNOWLEDGE_SKILLS_TOOLS_MCP.md` | ETHAN — Knowledge, Skills, Tools/MCP, Memory : Audit Open-WebUI vs ETHAN | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0331 | `docs/architecture/ETHAN_REBUILD_P1_REQUIREMENTS_MATRIX.md` | ETHAN — Matrice exigences → implémentation → tests → preuves (P1) | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0332 | `docs/architecture/ETHAN_REBUILD_P1_TARGET_ARCHITECTURE.md` | ETHAN — Architecture cible P1 (hybride Rust + Python, socle Open WebUI étudié) | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0333 | `docs/architecture/ETHAN_RESPONSE_RENDERER.md` | ETHAN Response Renderer — architecture | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0334 | `docs/architecture/ETHAN_WEBUI_TARGET_ARCHITECTURE.md` | ETHAN WebUI — Architecture cible | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0335 | `docs/architecture/OPENWEBUI_ETHAN_MAPPING.md` | Open-WebUI → ETHAN — Mapping des concepts | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0336 | `docs/architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md` | Migration — Backend Open-WebUI → ETHAN API | Architecture | Obsidian/ | Scinder | Architecture et descriptions de composants | Moyen — séparation contenu utilisateur/interne |
| DOC-0337 | `docs/architecture/README_ARCHITECTURE_REFERENCE.md` | ETHAN — Architecture Reference | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0338 | `docs/architecture/RUST-MIGRATION-AUDIT.md` | ETHAN — Audit de fiabilité et préparation d'une migration Rust progressive | Architecture | Obsidian/ | Scinder | Architecture et descriptions de composants | Moyen — séparation contenu utilisateur/interne |
| DOC-0339 | `docs/architecture/adr/ADR-3001-unified-record-store.md` | ADR-3001 — Unified Record Store | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0340 | `docs/architecture/adr/ADR-3002-providers-source-of-truth.md` | ADR-3002 — Providers : ProviderManager = seule source de vérité | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0341 | `docs/architecture/adr/ADR-3003-projects-domain.md` | ADR-3003 — Domaine Projects | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0342 | `docs/architecture/adr/ADR-3004-vector-store-record.md` | ADR-3004 — Back-end de vecteurs unique | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0343 | `docs/architecture/adr/ADR-3005-folders-vs-domains.md` | ADR-3005 — Folders (arborescence) vs Domains (étiquettes transverses) | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0344 | `docs/architecture/adr/ADR-3006-api-contracts.md` | ADR-3006 — Contrats API versionnés (OpenAPI + tests de contrat) | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0345 | `docs/architecture/adr/ADR-3007-deprecation-settings-legacy.md` | ADR-3007 — Dépréciation du record settings hérité (/v1/settings) | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0346 | `docs/architecture/adr/ADR-4001-capability-manager.md` | ADR-4001 — Capability Manager centralisé dans ETHAN Core | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0347 | `docs/architecture/adr/ADR-4002-install-on-demand.md` | ADR-4002 — Installation à la demande (supported ≠ installed ≠ running ≠ ready) | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0348 | `docs/architecture/adr/ADR-4003-data-lifecycle.md` | ADR-4003 — Cycle de vie des données : uninstall ≠ delete data | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0349 | `docs/architecture/adr/ADR-4004-core-source-of-truth.md` | ADR-4004 — Le Core, source de vérité de l'état des composants | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0350 | `docs/architecture/adr/ADR-4005-extension-trust-model.md` | ADR-4005 — Modèle de confiance des extensions (Skills, Plugins, MCP, Integrations) | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0351 | `docs/architecture/adr/ADR-4006-rebuild-target-architecture.md` | ADR-4006 — Architecture cible rebuild ETHAN (hybride Rust + Python, socle parallèle) | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0352 | `docs/architecture/adr/ADR-4007-open-webui-fork-license-gate.md` | ADR-4007 — Fork Open WebUI comme frontend : gate de licence et de marque | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0353 | `docs/architecture/adr/ADR-4008-rust-event-store-shadow-mode.md` | ADR-4008 — Shadow mode pour migration Rust de l'Event Store | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0354 | `docs/architecture/adr/README.md` | ADR — Architecture Decision Records (WebUI Platform) | ADR | Obsidian/ | Déplacer | ADR (décision d’architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0355 | `docs/architecture/agents.md` | Agentic Logic Primitive | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0356 | `docs/architecture/api-core-boundary-refactoring.md` | ETHAN — Refactoring Frontière API/Core | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0357 | `docs/architecture/channels.md` | Channels Architecture | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0358 | `docs/architecture/communication-graph.md` | Graphe de Communication ETHAN — Analyse SRE | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0359 | `docs/architecture/consolidation-plan.md` | ETHAN — Plan de Consolidation Architecture | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0360 | `docs/architecture/critical-analysis.md` | Analyse Critique de l'Architecture ETHAN | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0361 | `docs/architecture/current.md` | Architecture Actuelle — Ethan | Architecture | Obsidian/ | Scinder | Architecture et descriptions de composants | Moyen — séparation contenu utilisateur/interne |
| DOC-0362 | `docs/architecture/decisions.md` | Décisions Architecturale Critiques — ETHAN Core Daemon | Architecture | Obsidian/ | Scinder | Architecture et descriptions de composants | Moyen — séparation contenu utilisateur/interne |
| DOC-0363 | `docs/architecture/design-principles.md` | Design Principles | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0364 | `docs/architecture/duplicate-detection.md` | Duplicate Detection — Architecture | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0365 | `docs/architecture/engine.md` | Inference Engine Primitive | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0366 | `docs/architecture/file-folder-consolidation.md` | File/Folder Consolidation — Architecture | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0367 | `docs/architecture/intelligence.md` | Intelligence Primitive | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0368 | `docs/architecture/knowledge/document-pipeline.md` | ASR — Knowledge Document Pipeline (hypothèse) | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0369 | `docs/architecture/learning.md` | Learning & Traces | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0370 | `docs/architecture/llm-unification-plan.md` | ETHAN — Plan d'Unification LLM | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0371 | `docs/architecture/local-knowledge-api-contract.md` | ETHAN — Local Knowledge API Contract | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0372 | `docs/architecture/local-knowledge-domain.md` | ETHAN — Local Knowledge Domain Contract | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0373 | `docs/architecture/local-knowledge-storage-audit.md` | ETHAN — Local Knowledge Storage Audit | Architecture | Obsidian/ | Scinder | Architecture et descriptions de composants | Moyen — séparation contenu utilisateur/interne |
| DOC-0374 | `docs/architecture/memory.md` | Memory Primitive | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0375 | `docs/architecture/migration-report.md` | ETHAN — Rapport de Migration : core/providers/ → core/llm/providers/ | Architecture | Obsidian/ | Scinder | Architecture et descriptions de composants | Moyen — séparation contenu utilisateur/interne |
| DOC-0376 | `docs/architecture/osiris-port-management.md` | Osiris-Lab v2: Port Management & Allocation System | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0377 | `docs/architecture/overview.md` | Architecture Overview | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0378 | `docs/architecture/proposed.md` | Architecture Proposée — Jarvis OS | Architecture | Obsidian/ | Scinder | Architecture et descriptions de composants | Moyen — séparation contenu utilisateur/interne |
| DOC-0379 | `docs/architecture/query-flow.md` | Query Flow | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0380 | `docs/architecture/reviews/unified-ai-providers-review.md` | ETHAN — Unified AI Providers — Architecture Decision | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0381 | `docs/architecture/reviews/webui-platform-review.md` | ETHAN WebUI — Architecture Review | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0382 | `docs/architecture/security.md` | Security Architecture | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0383 | `docs/architecture/skills.md` | Skills Architecture | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0384 | `docs/architecture/terminal-webui.md` | Terminal WebUI — PTY distant servi par ETHAN Core | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0385 | `docs/architecture/webui-core-audit.md` | ETHAN — Audit WebUI / Core Boundary | Architecture | Obsidian/ | Scinder | Architecture et descriptions de composants | Moyen — séparation contenu utilisateur/interne |
| DOC-0386 | `docs/architecture/webui-platform-architecture-assessment.md` | ETHAN — WebUI Platform Architecture Assessment | Architecture | Obsidian/ | Déplacer | Architecture et descriptions de composants | Moyen — déplacement et liens à mettre à jour |
| DOC-0387 | `docs/assets/OpenJarvis_Architecture.png` | OpenJarvis_Architecture.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0388 | `docs/assets/showcase/README.md` | Showcase screenshots | Gouvernance | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0389 | `docs/assets/showcase/coding-assistant.png` | coding-assistant.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0390 | `docs/assets/showcase/cost-savings.png` | cost-savings.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0391 | `docs/assets/showcase/discord-companion.png` | discord-companion.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0392 | `docs/assets/showcase/morning-brief.png` | morning-brief.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0393 | `docs/assets/showcase/persistent-memory.png` | persistent-memory.png | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0394 | `docs/audit-boot-mechanism.md` | Audit d'Architecture — Mécanisme de Démarrage ETHAN | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0395 | `docs/audit-ethan-up-RESUME.md` | Audit ./ethan up — Résumé | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0396 | `docs/audit-ethan-up.md` | Audit de la commande ./ethan up | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0397 | `docs/audit-plugins.md` | Audit Système de Plugins ETHAN | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0398 | `docs/audit/CLINE_CHECKPOINT_INVENTORY.md` | Annexe — Inventaire des checkpoints Cline | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0399 | `docs/audit/CLINE_RECOVERY_ANALYSIS.md` | Analyse de récupération – checkpoints Cline ETHAN | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0400 | `docs/audit/ETHAN_API_HEALTHCHECK_DIAGNOSTIC.md` | ETHAN — Diagnostic API Healthcheck (running/unhealthy) | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0401 | `docs/audit/ETHAN_COMPONENT_INTERFACE_INVENTORY_P0.md` | ETHAN — Inventaire des interfaces entre composants (P0) | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0402 | `docs/audit/ETHAN_PERSISTENT_DATA_REGISTRY_P0.md` | ETHAN — Registre des données à préserver (P0, audit seulement) | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0403 | `docs/audit/ETHAN_PUBLIC_PRIVATE_INVENTORY.md` | ETHAN — Public/Private Inventory | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0404 | `docs/audit/ETHAN_PUBLIC_PRIVATE_SEPARATION.md` | ETHAN — Public/Private Separation and Publication Readiness | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0405 | `docs/audit/ETHAN_REBUILD_P0_AUDIT.md` | ETHAN — Audit factuel P0 avant refonte (hybride Rust + Python, Open WebUI) | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0406 | `docs/audit/ETHAN_REBUILD_P0_TRACEABILITY_MATRIX.csv` | ETHAN_REBUILD_P0_TRACEABILITY_MATRIX.csv | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0407 | `docs/audit/ETHAN_REBUILD_P1_RISK_REGISTER.md` | ETHAN — Registre des risques et décisions en attente (P1) | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0408 | `docs/audit/ETHAN_REBUILD_P2_FEASIBILITY.md` | ETHAN — Rapport de faisabilité P2 (fork WebUI isolé Open WebUI v0.9.1) | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0409 | `docs/audit/ETHAN_REBUILD_P3` | ETHAN_REBUILD_P3 | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0410 | `docs/audit/ETHAN_REBUILD_P3_VERTICAL_PROTOTYPE.md` | ETHAN — Rapport P3 prototype vertical Core hybride | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0411 | `docs/audit/ETHAN_REBUILD_P5_VALIDATION_GATE.md` | ETHAN — Rapport de validation P5 (gate avant intégration) | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0412 | `docs/audit/ETHAN_WEBUI_CTO_REVIEW.md` | Audit CTO — Revue Indépendante WebUI ETHAN | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0413 | `docs/audit/ETHAN_WEBUI_GAP_ANALYSIS.md` | ETHAN WebUI Gap Analysis | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0414 | `docs/audit/ETHAN_WEBUI_INITIAL_ARCHITECTURE_AUDIT.md` | ETHAN WebUI Initial Architecture Audit | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0415 | `docs/audit/GIT_BACKUP_AND_CONSOLIDATION_PLAN.md` | ETHAN — Plan de sauvegarde et consolidation Git | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0416 | `docs/audit/GIT_SECURITY_AND_HISTORY_AUDIT.md` | Audit Git – sécurité, historique et références ETHAN | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0417 | `docs/audit/OPENWEBUI_COMPONENT_REFERENCE.md` | Open-WebUI — Référence des composants et contrats | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0418 | `docs/audit/OPENWEBUI_FORK_FEASIBILITY.md` | Open-WebUI Fork Feasibility Analysis | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0419 | `docs/audit/OPENWEBUI_FUNCTIONAL_REFERENCE.md` | Open-WebUI — Référence fonctionnelle | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0420 | `docs/audit/OPENWEBUI_UX_REFERENCE.md` | Open-WebUI — Référence UX | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0421 | `docs/audit/WEBUI_CURRENT_STATE.md` | ETHAN WebUI — état actuel vérifié | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0422 | `docs/audit/WEBUI_DOCUMENTARY_INVENTORY.md` | ETHAN WebUI Documentary Inventory | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0423 | `docs/audit/WEBUI_IMPLEMENTATION_STATUS.md` | ETHAN WebUI Implementation Status | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0424 | `docs/audit/WEBUI_PRIORITIES.md` | ETHAN WebUI Implementation Priorities | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0425 | `docs/audit_rapport.md` | Rapport SRE & Architecture : Stabilisation ETHAN | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0426 | `docs/audits/CLI_PRODUCTION_AUDIT.md` | Revue de production du CLI ETHAN | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0427 | `docs/audits/api-startup-fix.md` | ETHAN API Startup Fix | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0428 | `docs/audits/duplicate-data-integrity.md` | Duplicate Data Integrity — Audit | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0429 | `docs/audits/file-management-regression.md` | File Management Regression — Audit & Correction | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0430 | `docs/audits/rag-settings-regression.md` | RAG Settings Regression — Audit & Restauration | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0431 | `docs/audits/reference-comparison-odysseus-canirun.md` | Reference Comparison — Odysseus & CanIRun.ai | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0432 | `docs/audits/transparency-readability-audit.md` | Audit — Suppression des effets de transparence (WebUI) | Audit | Obsidian/ | Déplacer | Audit (historique de travail et rapports d’agent) | Moyen — déplacement et liens à mettre à jour |
| DOC-0433 | `docs/auth_architecture_audit.md` | ETHAN OS — Authentication Architecture Audit & Migration Plan | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0434 | `docs/auth_audit_report_3.md` | ETHAN Authentication Audit Report | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0435 | `docs/auth_flow_audit.md` | ETHAN Auth Flow — Production Audit Report | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0436 | `docs/boot-dev-extensions.md` | Boot — Extensions développement | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0437 | `docs/boot-from-scratch.md` | Boot depuis un système vierge | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0438 | `docs/boot_sequence_audit.md` | 🔬 ETHAN Boot Sequence Audit — Verified Report | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0439 | `docs/cto-review-completed.md` | CTO Review — Corrections Appliquées | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0440 | `docs/deployment.md` | Déploiement ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0441 | `docs/deployment/api-server.md` | API Server | Installation | Obsidian/ | Déplacer | Déploiement / exploitation | Moyen — déplacement et liens à mettre à jour |
| DOC-0442 | `docs/deployment/docker.md` | Docker Deployment | Installation | Obsidian/ | Déplacer | Déploiement / exploitation | Moyen — déplacement et liens à mettre à jour |
| DOC-0443 | `docs/deployment/index.md` | Deployment | Installation | Obsidian/ | Déplacer | Déploiement / exploitation | Moyen — déplacement et liens à mettre à jour |
| DOC-0444 | `docs/deployment/launchd.md` | launchd Service (macOS) | Installation | Obsidian/ | Déplacer | Déploiement / exploitation | Moyen — déplacement et liens à mettre à jour |
| DOC-0445 | `docs/deployment/systemd.md` | systemd Service (Linux) | Installation | Obsidian/ | Déplacer | Déploiement / exploitation | Moyen — déplacement et liens à mettre à jour |
| DOC-0446 | `docs/design/2026-05-05-apple-silicon-pearl-mining-design.md` | Spec B — Apple Silicon enablement for Pearl mining | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0447 | `docs/design/2026-05-05-apple-silicon-pearl-mining-plan-v1.md` | Apple Silicon Pearl mining v1 — implementation plan | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0448 | `docs/design/2026-05-05-pearl-coordination-discussion-draft.md` | Pearl coordination thread — draft | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0449 | `docs/design/2026-05-05-vllm-pearl-mining-integration-design.md` | Spec A — vLLM-Pearl mining integration (v1) | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0450 | `docs/design/2026-05-05-vllm-pearl-mining-integration-plan.md` | vLLM-Pearl mining integration — implementation plan | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0451 | `docs/design/2026-09-30-cartographie-interfaciale.md` | Cartographie interfaciale — qui expose quelle capacité ETHAN | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0452 | `docs/design/2026-09-30-ux-refonte-cartographie.md` | WebUI — Cartographie UX (route → composant → API → Core) | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0453 | `docs/design/2026-09-30-webui-settings-honesty.md` | WebUI — Refonte Settings « honnête » (anti-fantôme) | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0454 | `docs/design/2026-10-01-cartographie-webui-ux.md` | Cartographie WebUI → API → Core (préalable obligatoire à la refonte UX) | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0455 | `docs/design/ETHAN_CAPABILITIES_UX.md` | ETHAN — Design UX des Capacités (Knowledge, Skills, Tools, Memory) | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0456 | `docs/design/ETHAN_WEBUI_UX_ANALYSIS.md` | Analyse UX — Open-WebUI comme référence visuelle pour ETHAN WebUI | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0457 | `docs/design/ETHAN_WEBUI_UX_PARITY_SPEC.md` | ETHAN WebUI — Spécification de parité UX avec Open-WebUI | Rapport | Obsidian/ | Scinder | Design technique / plan d’implémentation | Moyen — séparation contenu utilisateur/interne |
| DOC-0458 | `docs/desktop-auto-update.md` | Desktop auto-update | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0459 | `docs/development/ETHAN_WEBUI_FORK_STRATEGY.md` | Stratégie de Maintenance — Fork Open-WebUI → ETHAN WebUI | Document | Obsidian/ | Déplacer | Développement / contribution | Moyen — déplacement et liens à mettre à jour |
| DOC-0460 | `docs/development/contributing.md` | Contributing Guide | Document | Obsidian/ | Déplacer | Développement / contribution | Moyen — déplacement et liens à mettre à jour |
| DOC-0461 | `docs/development/mining-nvidia-validation.md` | NVIDIA Pearl Mining Validation Runbook | Document | Obsidian/ | Déplacer | Développement / contribution | Moyen — déplacement et liens à mettre à jour |
| DOC-0462 | `docs/development/mining.md` | Adding a Mining Provider | Document | Obsidian/ | Déplacer | Développement / contribution | Moyen — déplacement et liens à mettre à jour |
| DOC-0463 | `docs/development/pearl-model-enablement.md` | Pearl Model Enablement | Document | Obsidian/ | Déplacer | Développement / contribution | Moyen — déplacement et liens à mettre à jour |
| DOC-0464 | `docs/development/release-checklist.md` | Release Checklist | Document | Obsidian/ | Déplacer | Développement / contribution | Moyen — déplacement et liens à mettre à jour |
| DOC-0465 | `docs/development/roadmap.md` | Roadmap | Document | Obsidian/ | Déplacer | Développement / contribution | Moyen — déplacement et liens à mettre à jour |
| DOC-0466 | `docs/doctor.md` | ETHAN Doctor — Diagnostic de santé | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0467 | `docs/downloads.md` | Downloads | Documentation utilisateur | docs/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0468 | `docs/engineering/baseline/BASELINE_VALIDATION.md` | ETHAN — Baseline Validation | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0469 | `docs/engineering/baseline/ETHAN_ROADMAP.md` | ETHAN — Technical Roadmap Proposal | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0470 | `docs/engineering/baseline/ETHAN_SECURITY_ASSESSMENT.md` | ETHAN — Security Assessment | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0471 | `docs/engineering/baseline/ETHAN_TECHNICAL_BASELINE.md` | ETHAN — Technical Baseline | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0472 | `docs/engineering/baseline/ETHAN_TECHNICAL_DEBT.md` | ETHAN — Technical Debt | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0473 | `docs/engineering/baseline/ETHAN_TEST_BASELINE.md` | ETHAN — Test Baseline | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0474 | `docs/engineering/benchmarks/knowledge-bottleneck-analysis.md` | Knowledge Bottleneck Analysis | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0475 | `docs/engineering/benchmarks/knowledge-performance-baseline.md` | Knowledge Performance Baseline | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0476 | `docs/engineering/benchmarks/knowledge-postgres-environment.md` | Isolated PostgreSQL Test Environment — Knowledge/RAG | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0477 | `docs/engineering/benchmarks/knowledge-postgres-validation.md` | Knowledge PostgreSQL Validation - Current State | Document | Obsidian/ | Déplacer | Ingénierie / spécifications techniques | Moyen — déplacement et liens à mettre à jour |
| DOC-0478 | `docs/engineering/esr/ESR-001-capability-model.md` | ESR-001 — Capability Model | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0479 | `docs/engineering/esr/ESR-002-installation-engine.md` | ESR-002 — Installation Engine | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0480 | `docs/engineering/esr/ESR-003-docker-provisioning.md` | ESR-003 — Docker Provisioning | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0481 | `docs/engineering/esr/ESR-004-local-provisioning.md` | ESR-004 — Local Provisioning (Python, exécutables, intégrés) | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0482 | `docs/engineering/esr/ESR-005-webui-capability-manager.md` | ESR-005 — WebUI Capability Manager | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0483 | `docs/engineering/esr/ESR-006-security-model.md` | ESR-006 — Security Model | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0484 | `docs/engineering/esr/ESR-007-knowledge-collections.md` | ESR-007 — Knowledge Collections | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0485 | `docs/engineering/esr/ESR-008-knowledge-sources.md` | ESR-008 — Knowledge Sources | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0486 | `docs/engineering/esr/ESR-010-knowledge-index.md` | ESR-010 — Knowledge Index | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0487 | `docs/engineering/esr/ESR-011-knowledge-search.md` | ESR-011 — Knowledge Search | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0488 | `docs/engineering/esr/ESR-012-knowledge-rag-permissions.md` | ESR-012 — Knowledge RAG Permissions | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0489 | `docs/engineering/esr/ESR-013-knowledge-tasks.md` | ESR-013 — Knowledge Tasks | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0490 | `docs/engineering/esr/ESR-014-frame-fork.md` | ESR-014 — Préparation du fork Frame | ESR | Obsidian/ | Fusionner après validation | ESR (exigence système) | Élevé — collision de numérotation |
| DOC-0491 | `docs/engineering/esr/ESR-014-knowledge-observability.md` | ESR-014 — Knowledge Observability | ESR | Obsidian/ | Fusionner après validation | ESR (exigence système) | Élevé — collision de numérotation |
| DOC-0492 | `docs/engineering/esr/ESR-015-frame-service.md` | ESR-015 — Service Frame piloté par ETHAN | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0493 | `docs/engineering/esr/README.md` | ESR — Engineering Specifications & Requirements | ESR | Obsidian/ | Déplacer | ESR (exigence système) | Moyen — déplacement et liens à mettre à jour |
| DOC-0494 | `docs/ethan-launcher.md` | ETHAN — Lanceur officiel | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0495 | `docs/ethan-up.md` | Rapport d’intégration — Système de plugins conversationnels ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0496 | `docs/frontend_auth_audit.md` | Audit Complet — Flux Frontend Login ETHAN | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0497 | `docs/gen_install_script.py` | (source path, published URL path) | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0498 | `docs/gen_ref_pages.py` | gen_ref_pages.py | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0499 | `docs/getting-started/configuration.md` | Configuration | Configuration utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0500 | `docs/getting-started/install.md` | Installation | Installation | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0501 | `docs/getting-started/installation.md` | Installation | Installation | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0502 | `docs/getting-started/linux.md` | Linux Install | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0503 | `docs/getting-started/macos.md` | macOS Install | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0504 | `docs/getting-started/quickstart.md` | Quick Start | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0505 | `docs/getting-started/snippets.md` | Code Snippets | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0506 | `docs/getting-started/windows-native.md` | Native Windows (advanced) | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0507 | `docs/getting-started/wsl2.md` | WSL2 Install | Guide utilisateur | docs/ | Conserver | Guide d’installation / démarrage | Faible |
| DOC-0508 | `docs/gods-eye-view-integration.md` | Intégration God's Eye View (GEV) dans ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0509 | `docs/hardening.md` | ETHAN — Hardening & Correctifs de Sécurité | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0510 | `docs/implementation-guide-P0.md` | Guide d'Implémentation P0 — Actions Critiques | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0511 | `docs/implementation-guide-P1.md` | Guide d'Implémentation P1 — Actions Importantes | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0512 | `docs/implementation-guide-P2.md` | Guide d'Implémentation P2 — Améliorations | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0513 | `docs/implementation-guide-P3.md` | Guide d'Implémentation P3 — Optimisations | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0514 | `docs/incidents/RUNTIME-001.md` | INCIDENT RUNTIME-001 : NATS ne démarre pas | Document | Obsidian/ | Déplacer | Incident / post-mortem | Moyen — déplacement et liens à mettre à jour |
| DOC-0515 | `docs/includes/abbreviations.md` | abbreviations.md | Document | docs/ | Conserver | Inclusions MkDocs (snippets) | Faible |
| DOC-0516 | `docs/index.md` | Personal AI, On Personal Devices | Présentation | docs/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0517 | `docs/installation.md` | Installation d'ETHAN — Debian 13 (Trixie) | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0518 | `docs/javascripts/docsearch-init.js` | docsearch-init.js | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0519 | `docs/javascripts/leaderboard.js` | leaderboard.js | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0520 | `docs/leaderboard.md` | Savings Leaderboard | Documentation utilisateur | docs/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0521 | `docs/learning/ace.md` | ACE optimizer (Agentic Context Engineering) | Guide utilisateur | docs/ | Conserver | Mémoire opérationnelle (autre) | Faible |
| DOC-0522 | `docs/memory/DECISIONS.md` | Décisions — ETHAN | Note | Obsidian/ | Scinder | Mémoire inter-sessions Codex | Moyen — séparation contenu utilisateur/interne |
| DOC-0523 | `docs/memory/PROJECT_STATE.md` | État courant — ETHAN | Note | Obsidian/ | Scinder | Mémoire inter-sessions Codex | Moyen — séparation contenu utilisateur/interne |
| DOC-0524 | `docs/memory/README.md` | Mémoire inter-sessions Codex — ETHAN | Note | Obsidian/ | Déplacer | Mémoire inter-sessions Codex | Moyen — déplacement et liens à mettre à jour |
| DOC-0525 | `docs/memory/sessions/2026-11-01.md` | Archive de session — 2026-11-01 | Note | Obsidian/ | Déplacer | Mémoire inter-sessions Codex | Moyen — déplacement et liens à mettre à jour |
| DOC-0526 | `docs/memory/sessions/2026-11-02.md` | Session 2026-11-02 | Note | Obsidian/ | Déplacer | Mémoire inter-sessions Codex | Moyen — déplacement et liens à mettre à jour |
| DOC-0527 | `docs/memory/sessions/2026-11-03.md` | Session 2026-11-03 — MEM-014 Phase 1 | Note | Obsidian/ | Déplacer | Mémoire inter-sessions Codex | Moyen — déplacement et liens à mettre à jour |
| DOC-0528 | `docs/memory/sessions/2026-11-04.md` | Session 2026-11-04 — Quantar real task runtime | Note | Obsidian/ | Déplacer | Mémoire inter-sessions Codex | Moyen — déplacement et liens à mettre à jour |
| DOC-0529 | `docs/odin-direct-docker-compose.md` | Migration Odin — Architecture Docker directe (sans odin-controller) | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0530 | `docs/operations/ETHAN_REBUILD_P1_RUNBOOK.md` | ETHAN — Runbook P1 (installation, sauvegarde, restauration, diagnostic, rollback) | Runbook | Obsidian/ | Déplacer | Procédure d’exploitation / runbook | Moyen — déplacement et liens à mettre à jour |
| DOC-0531 | `docs/operations/backup-volumes-procedure.md` | Procédure de sauvegarde des volumes Docker ETHAN | Runbook | Obsidian/ | Déplacer | Procédure d’exploitation / runbook | Moyen — déplacement et liens à mettre à jour |
| DOC-0532 | `docs/operations/webui-refresh.md` | WebUI refresh procedure — no OS reboot | Runbook | Obsidian/ | Déplacer | Procédure d’exploitation / runbook | Moyen — déplacement et liens à mettre à jour |
| DOC-0533 | `docs/overrides/main.html` | main.html | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0534 | `docs/p1_audit_report.md` | P1 Audit Report — ETHAN WebUI | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0535 | `docs/plans/ETHAN_WEBUI_ARCHITECTURE_MATRIX.md` | Matrice architecturale — Frontière ETHAN ↔ ETHAN WebUI (base Open WebUI) | Audit | Obsidian/ | Scinder | Plan / migration / audit opérationnel | Moyen — séparation contenu utilisateur/interne |
| DOC-0536 | `docs/plans/ETHAN_WEBUI_MASTER_PLAN.md` | ETHAN WebUI — Master Implementation Plan | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0537 | `docs/plans/ETHAN_WEBUI_MIGRATION_STRATEGY.md` | Stratégie de migration — Ancienne WebUI ETHAN → ETHAN WebUI (fork Open WebUI) | Audit | Obsidian/ | Scinder | Plan / migration / audit opérationnel | Moyen — séparation contenu utilisateur/interne |
| DOC-0538 | `docs/plans/ETHAN_WEBUI_MODELS_PROVIDERS_ARCHITECTURE.md` | Architecture cible — Models & Providers ETHAN (inspiré Open WebUI) | Audit | Obsidian/ | Scinder | Plan / migration / audit opérationnel | Moyen — séparation contenu utilisateur/interne |
| DOC-0539 | `docs/plans/ETHAN_WEBUI_OPENWEBUI_MIGRATION.md`` | ETHAN WebUI $\rightarrow$ Open-WebUI Migration Plan | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0540 | `docs/plans/ETHAN_WEBUI_RAG_KNOWLEDGE_FILES_MCP_TOOLS_ARCHITECTURE.md` | Architecture cible — RAG, Knowledge, Files, MCP, Tools (inspiré Open WebUI) | Audit | Obsidian/ | Scinder | Plan / migration / audit opérationnel | Moyen — séparation contenu utilisateur/interne |
| DOC-0541 | `docs/plans/ETHAN_WEBUI_SETTINGS_ARCHITECTURE.md` | Architecture Settings ETHAN WebUI — inspirée Open WebUI | Audit | Obsidian/ | Scinder | Plan / migration / audit opérationnel | Moyen — séparation contenu utilisateur/interne |
| DOC-0542 | `docs/plans/ETHAN_WEBUI_V2_ARCHITECTURE.md` | ETHAN WebUI v2 – Architecture Overview | Audit | Obsidian/ | Scinder | Plan / migration / audit opérationnel | Moyen — séparation contenu utilisateur/interne |
| DOC-0543 | `docs/plans/OPENWEBUI_ETHAN_MIGRATION_ANALYSIS.md` | Analyse & Plan de Migration — Open WebUI → ETHAN WebUI | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0544 | `docs/plans/chat-agent-model-selector.md` | Sélecteurs Agent / Model du chat — WebUI ETHAN | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0545 | `docs/plans/chat-composer-simplification.md` | Simplification du composer de chat — WebUI ETHAN | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0546 | `docs/plans/chat-layout-visual-polish.md` | Chat Layout — Visual Polish (WebUI réel, port 3001) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0547 | `docs/plans/chat-ui-deduplication.md` | Dé-duplication des contrôles du chat — WebUI ETHAN | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0548 | `docs/plans/execution/00-ETAT-DES-LIEUX.md` | État des lieux — Analyse initiale du repository | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0549 | `docs/plans/execution/01-PHASE-A-CONSOLIDATION.md` | Phase A — Consolidation — Plan d'exécution | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0550 | `docs/plans/execution/02-PHASE-B-MCP.md` | Phase B — MCP — Plan d'exécution | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0551 | `docs/plans/execution/03-PHASE-C-SETTINGS.md` | Phase C — Settings & UX — Plan d'exécution | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0552 | `docs/plans/execution/04-PLAN-INTERPRETER-REPORT.md` | ETHAN WebUI — PLAN INTERPRETER REPORT | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0553 | `docs/plans/execution/SESSION-REPORT-2026-08-18.md` | Rapport de Clôture de Session — ETHAN WebUI | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0554 | `docs/plans/odysseus-cleanup-audit.md` | Odysseus Cleanup Audit Report | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0555 | `docs/plans/openwebui-ethan-ui-migration.md` | Open-WebUI → ETHAN — Analyse UX et Tableau de Migration | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0556 | `docs/plans/openwebui-migration-final-audit.md` | Audit final — Migration WebUI ETHAN vers l'expérience Open WebUI | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0557 | `docs/plans/openwebui-shell-migration.md` | ETHAN WebUI — Migration du shell vers Open WebUI | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0558 | `docs/plans/sidebar-openwebui-behavior.md` | Sidebar — comportement Open-WebUI (refonte v5) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0559 | `docs/plans/ui-agent-selector.md` | Sélecteur d'agent du chat — Implémentation | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0560 | `docs/plans/ui-chat-composer.md` | Refonte du Composer de chat ETHAN (inspiré Open-WebUI) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0561 | `docs/plans/ui-chat-context.md` | Barre de contexte actif du chat — ChatContextBar | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0562 | `docs/plans/ui-cleanup.md` | Nettoyage Frontend ETHAN WebUI — Rapport | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0563 | `docs/plans/ui-config-pages-refactor.md` | Refonte UX/UI des pages de configuration — card grid (inspiré Open-WebUI) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0564 | `docs/plans/ui-navigation.md` | ETHAN WebUI — Navigation Refondue (style Open-WebUI) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0565 | `docs/plans/ui-openwebui-agent-model-selectors.md` | ETHAN WebUI — Sélecteurs Agent + Model (niveau Open-WebUI) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0566 | `docs/plans/ui-openwebui-config-pages.md` | ETHAN WebUI — Refonte des pages vers les patterns Open-WebUI | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0567 | `docs/plans/ui-openwebui-final-audit.md` | Audit final — WebUI ETHAN post-refonte (cohérence Open-WebUI) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0568 | `docs/plans/ui-openwebui-refactor-audit.md` | Audit WebUI ETHAN — Refonte UX inspirée d'Open-WebUI | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0569 | `docs/plans/ui-openwebui-shell-implementation.md` | Implémentation — Refonte Shell WebUI (inspiration Open-WebUI) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0570 | `docs/plans/ui-openwebui-target-architecture.md` | Architecture UX cible — WebUI ETHAN (référence Open-WebUI) | Audit | Obsidian/ | Scinder | Plan / migration / audit opérationnel | Moyen — séparation contenu utilisateur/interne |
| DOC-0571 | `docs/plans/webui-navigation-first-experience.md` | Première expérience de navigation — WebUI ETHAN | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0572 | `docs/plans/webui-port-3001-validation.md` | WebUI ETHAN — Validation du port officiel 3001 | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0573 | `docs/plans/webui-port-3001.md` | Migration WebUI ETHAN → port 3001 | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0574 | `docs/plans/webui-ux-polish-audit.md` | Audit UX / Polish — WebUI ETHAN (phase TEST · CORRECTION · POLISH) | Audit | Obsidian/ | Déplacer | Plan / migration / audit opérationnel | Moyen — déplacement et liens à mettre à jour |
| DOC-0575 | `docs/plugins/gods-eye-view-ai.md` | God's Eye View — Adaptateur IA (ETHAN) | Fonctionnalité publique | docs/ | Conserver | Plugin / intégration | Faible |
| DOC-0576 | `docs/plugins/odin-compose-controller.md` | Gestion du cycle de vie Odin — architecture directe | Fonctionnalité publique | docs/ | Conserver | Plugin / intégration | Faible |
| DOC-0577 | `docs/pythonpath-fix.md` | Correction PYTHONPATH — Import core.kernel | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0578 | `docs/rfc/RFC-0001-email-inbox.md` | RFC-0001 — Email Inbox ETHAN | Spécification | Obsidian/ | Déplacer | RFC (proposition) | Moyen — déplacement et liens à mettre à jour |
| DOC-0579 | `docs/rfc/RFC-0002-deep-research.md` | RFC-0002 — Deep Research ETHAN | Spécification | Obsidian/ | Déplacer | RFC (proposition) | Moyen — déplacement et liens à mettre à jour |
| DOC-0580 | `docs/rfc/RFC-0003-cookbook.md` | RFC-0003 — Cookbook ETHAN (recettes de workflows) | Spécification | Obsidian/ | Déplacer | RFC (proposition) | Moyen — déplacement et liens à mettre à jour |
| DOC-0581 | `docs/roadmap-P0.md` | Roadmap P0 — Actions Critiques (Immédiat) | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0582 | `docs/roadmap-P1.md` | Roadmap P1 — Actions Importantes (Court terme) | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0583 | `docs/roadmap-P2.md` | Roadmap P2 — Améliorations (Moyen terme) | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0584 | `docs/roadmap-P3.md` | Roadmap P3 — Optimisations (Long terme) | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0585 | `docs/roadmap-global.md` | Roadmap Globale — Suivi des Actions Architecture | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0586 | `docs/runbook.md` | ETHAN - Runbook Opérationnel | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0587 | `docs/schemas/application-manifest.schema.json` | application-manifest.schema.json | Schéma | Obsidian/ | Déplacer | Schéma / contrat | Moyen — déplacement et liens à mettre à jour |
| DOC-0588 | `docs/security/01-security-audit.md` | ETHAN — Phase 01 · Audit Sécurité & Gouvernance | Architecture | Obsidian/ | Scinder | Sécurité (conception / architecture) | Moyen — séparation contenu utilisateur/interne |
| DOC-0589 | `docs/security/02-constitution-design.md` | Design de la Constitution ETHAN | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0590 | `docs/security/03-policy-hierarchy.md` | Hiérarchie des Politiques ETHAN | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0591 | `docs/security/04-policy-engine.md` | Policy Engine — Phase 04 | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0592 | `docs/security/05-capability-system.md` | Capability & Permission System — Phase 05 | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0593 | `docs/security/06-data-protection.md` | Data Protection & Anti-Exfiltration — Phase 06 | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0594 | `docs/security/07-ecosystem-integration.md` | 07 — Intégration Écosystème (Phase 07) | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0595 | `docs/security/08-control-plane-hardening.md` | 08 — Durcissement du plan de contrôle (RBAC) & politique d'egress | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0596 | `docs/security/09-extension-hardening.md` | 09 — Durcissement des extensions (skills, plugins, outils) | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0597 | `docs/security/10-secret-hygiene.md` | 10 — Hygiène des secrets dans les configurations persistées | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0598 | `docs/security/11-runtime-isolation.md` | 11 — Runtime Isolation & Durcissements Red Team | Architecture | Obsidian/ | Déplacer | Sécurité (conception / architecture) | Moyen — déplacement et liens à mettre à jour |
| DOC-0599 | `docs/security/CI_CD_SECURITY_ASSESSMENT.md` | CI/CD Security Assessment — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0600 | `docs/security/CTO_SECURITY_ARCHITECTURE_REVIEW.md` | CTO Security Architecture Review — ETHAN | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0601 | `docs/security/DEPENDENCY_SECURITY_INVENTORY.md` | Dependency Security Inventory — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0602 | `docs/security/DOCKER_IMAGE_SECURITY_ASSESSMENT.md` | Docker Image Security Assessment — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0603 | `docs/security/ETHAN_CONSTITUTION.md` | Constitution d'ETHAN | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0604 | `docs/security/GITHUB_SECURITY_ASSESSMENT.md` | GitHub Security Assessment — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0605 | `docs/security/RED_TEAM_SECURITY_REVIEW.md` | Red Team Security Review — ETHAN | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0606 | `docs/security/SECRET_EXPOSURE_ASSESSMENT.md` | Secret Exposure Assessment — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0607 | `docs/security/SECURITY_ASSET_INVENTORY.md` | Security Asset Inventory — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0608 | `docs/security/SECURITY_AUDIT_RECONCILIATION.md` | Security Audit Reconciliation — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0609 | `docs/security/SECURITY_BACKLOG.md` | ETHAN Security Backlog | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0610 | `docs/security/SECURITY_EVIDENCE_REGISTER.md` | Security Evidence Register — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0611 | `docs/security/SECURITY_PROGRAM_CHARTER.md` | Security Program Charter — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0612 | `docs/security/SECURITY_RISK_REGISTER.md` | Security Risk Register — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0613 | `docs/security/SECURITY_ROADMAP.md` | Security Roadmap — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0614 | `docs/security/SECURITY_TEST_PLAN.md` | Security Test Plan — ETHAN | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0615 | `docs/security/SECURITY_VERIFICATION_MATRIX.md` | Security Verification Matrix — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0616 | `docs/security/TRUST_BOUNDARIES_REGISTER.md` | Trust Boundaries Register — ETHAN | Audit | Obsidian/ | Scinder | Sécurité (audit/registre opérationnel) | Moyen — séparation contenu utilisateur/interne |
| DOC-0617 | `docs/security/WEBUI_AUTH_ARCHITECTURE.md` | ETHAN WebUI — Architecture d'Authentification Cryptographique | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0618 | `docs/security/WEBUI_AUTH_CURRENT_STATE.md` | ETHAN WebUI — État Actuel de l'Authentification | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0619 | `docs/security/WEBUI_AUTH_SETUP.md` | ETHAN WebUI — Guide de Setup Authentification Cryptographique | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0620 | `docs/security/WEBUI_AUTH_THREAT_MODEL.md` | ETHAN WebUI — Modèle de Menace Authentification | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0621 | `docs/security/public-release-allowlist-denylist.md` | Public Release Allowlist / Denylist | Sécurité | Obsidian/ | Déplacer | Sécurité (référence / procédure) | Moyen — déplacement et liens à mettre à jour |
| DOC-0622 | `docs/service-orchestration.md` | Orchestration des Services ETHAN | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0623 | `docs/showcase/CONTRIBUTING.md` | Contributing a Showcase Entry | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0624 | `docs/showcase/coding-assistant.md` | 🛠️ Offline Code Reviewer — code review on an airplane | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0625 | `docs/showcase/cost-savings.md` | 💸 Track Your Savings — the leaderboard that makes local-first feel real | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0626 | `docs/showcase/discord-companion.md` | 💬 Discord Companion — a personal assistant that lives in my Discord | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0627 | `docs/showcase/index.md` | Showcase | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0628 | `docs/showcase/morning-brief.md` | ☕ Morning Brief — Jarvis reads everything overnight so I don't have to | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0629 | `docs/showcase/persistent-memory.md` | 🧠 Memory That Doesn't Reset — Jarvis actually knows me | Présentation | docs/ | Conserver | Vitrine / exemples | Faible |
| DOC-0630 | `docs/specs/CLI_CONTRACT.md` | Contrat officiel du CLI ETHAN | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0631 | `docs/specs/application-capability-discovery.md` | Spécification — Découverte de capacités applicatives (MEM-014 Phase 2) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0632 | `docs/specs/application-catalog-phase41.md` | Contrat de catalogue applicatif — MEM-014 Phase 41 | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0633 | `docs/specs/application-compliance.md` | Spécification — Moteur de conformité (MEM-014 Phase 5) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0634 | `docs/specs/application-contract-validator.md` | Documentation — Validateur contractuel (MEM-014 Phase 1) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0635 | `docs/specs/application-identity.md` | Conventions d'identité applicative (MEM-014 Phase 1) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0636 | `docs/specs/application-integration-contract.md` | Spécification — Contrat d'intégration applicative (MEM-014 Phase 4) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0637 | `docs/specs/application-integration-readiness.md` | Spécification — Préparation à l'intégration applicative (MEM-014 Phase 13) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0638 | `docs/specs/application-manifest.md` | Spécification — Manifeste d'application ETHAN (MEM-014 Phase 1) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0639 | `docs/specs/application-observability-engineering-memory.md` | Spécification — Observabilité et Engineering Memory (MEM-014 Phase 7) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0640 | `docs/specs/application-permissions-hrot.md` | Spécification — Permissions et Human Root of Trust (MEM-014 Phase 3) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0641 | `docs/specs/application-persistence-mem014.md` | Spécification — Persistance durable MEM-014 (Phase 8) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0642 | `docs/specs/application-resilience-lifecycle.md` | Spécification — Résilience et cycle de vie (MEM-014 Phase 6) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0643 | `docs/specs/capability-registry.md` | Spécification — Capability Registry (MEM-014 Phase 9) | Spécification | Obsidian/ | Déplacer | Spécification technique | Moyen — déplacement et liens à mettre à jour |
| DOC-0644 | `docs/sre-runbook.md` | Runbook SRE — ETHAN Cognitive OS | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0645 | `docs/sre_stability_audit.md` | ETHAN SRE Stability Audit — 2026-08-02 | Rapport | Obsidian/ | Déplacer | Document racine (rapport/plan historique) | Moyen — déplacement et liens à mettre à jour |
| DOC-0646 | `docs/stylesheets/extra.css` | extra.css | Document | docs/ | Conserver | Ressource site (asset) | Faible |
| DOC-0647 | `docs/telemetry.md` | Telemetry | Note | Obsidian/ | Déplacer | Mémoire opérationnelle (autre) | Moyen — déplacement et liens à mettre à jour |
| DOC-0648 | `docs/testing/agent-qa-runbook.md` | Agent QA Runbook | Test | Obsidian/ | Déplacer | Tests / validation | Moyen — déplacement et liens à mettre à jour |
| DOC-0649 | `docs/tutorials/code-companion.md` | Code Companion | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0650 | `docs/tutorials/deep-research.md` | Deep Research Assistant | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0651 | `docs/tutorials/index.md` | Tutorials | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0652 | `docs/tutorials/messaging-hub.md` | Messaging Hub | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0653 | `docs/tutorials/scheduled-ops.md` | Scheduled Personal Ops | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0654 | `docs/tutorials/skills-workflow.md` | Skills Workflow Tutorial | Tutoriel utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0655 | `docs/user-guide/agent-traces.md` | ETHAN Knowledge Base — Guide d'utilisation | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0656 | `docs/user-guide/agents.md` | Agents | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0657 | `docs/user-guide/benchmarks.md` | Benchmarks | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0658 | `docs/user-guide/channels-and-connectors.md` | Channels & Connectors | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0659 | `docs/user-guide/channels.md` | Channels | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0660 | `docs/user-guide/chat-simple.md` | Simple Chat | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0661 | `docs/user-guide/cli.md` | CLI ETHAN | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0662 | `docs/user-guide/code-assistant.md` | Code Assistant | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0663 | `docs/user-guide/deep-research.md` | Deep Research | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0664 | `docs/user-guide/evaluations.md` | Evaluations | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0665 | `docs/user-guide/llm-guided-spec-search.md` | LLM-Guided Spec Search | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0666 | `docs/user-guide/mcp-external-servers.md` | External MCP Server Integration | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0667 | `docs/user-guide/memory.md` | Memory | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0668 | `docs/user-guide/mining-apple-silicon.md` | Mining Pearl on Apple Silicon (and other CPU hosts) | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0669 | `docs/user-guide/mining.md` | Pearl Mining | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0670 | `docs/user-guide/morning-digest.md` | Morning Digest | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0671 | `docs/user-guide/pearl.md` | Pearl CLI Integration | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0672 | `docs/user-guide/projects.md` | Projects | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0673 | `docs/user-guide/python-sdk.md` | Python SDK | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0674 | `docs/user-guide/rag-strategies.md` | RAG Retrieval Strategies | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0675 | `docs/user-guide/scheduled-monitor.md` | Scheduled Monitor | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0676 | `docs/user-guide/scheduler.md` | Task Scheduler | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0677 | `docs/user-guide/security.md` | Security | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0678 | `docs/user-guide/skills.md` | Skills | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0679 | `docs/user-guide/system-exec.md` | Exécution système contrôlée | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0680 | `docs/user-guide/telemetry.md` | Telemetry & Traces | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0681 | `docs/user-guide/tools.md` | Tools | Guide utilisateur | docs/ | Conserver | Guide utilisateur | Faible |
| DOC-0682 | `docs/webui/open-webui-migration-report.md` | Rapport de migration WebUI — référence Open-WebUI | Interface utilisateur | docs/ | Conserver | Documentation WebUI / interface | Faible |
| DOC-0683 | `docs/webui/open-webui-reference.md` | Open-WebUI comme référence d'implémentation — WebUI ETHAN | Interface utilisateur | docs/ | Conserver | Documentation WebUI / interface | Faible |

## 2. Fiches détaillées — cas complexes

Documents à scinder, à fusionner après validation, ou à examiner individuellement.

### DOC-0303 — `docs/adr/ADR-1013-frame-fork.md`

- **ID et chemin** : DOC-0303 — `docs/adr/ADR-1013-frame-fork.md`
- **Contenu concerné** : ADR (décision d’architecture)
- **Problème identifié** : ADR (décision d’architecture)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0304 — `docs/adr/ADR-1013-knowledge-task-lifecycle.md`

- **ID et chemin** : DOC-0304 — `docs/adr/ADR-1013-knowledge-task-lifecycle.md`
- **Contenu concerné** : ADR (décision d’architecture)
- **Problème identifié** : ADR (décision d’architecture)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0305 — `docs/adr/ADR-1014-frame-service-integration.md`

- **ID et chemin** : DOC-0305 — `docs/adr/ADR-1014-frame-service-integration.md`
- **Contenu concerné** : ADR (décision d’architecture)
- **Problème identifié** : ADR (décision d’architecture)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0306 — `docs/adr/ADR-1014-retrieval-permission-scope.md`

- **ID et chemin** : DOC-0306 — `docs/adr/ADR-1014-retrieval-permission-scope.md`
- **Contenu concerné** : ADR (décision d’architecture)
- **Problème identifié** : ADR (décision d’architecture)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0336 — `docs/architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md`

- **ID et chemin** : DOC-0336 — `docs/architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md`
- **Contenu concerné** : Architecture et descriptions de composants
- **Problème identifié** : Architecture et descriptions de composants
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0338 — `docs/architecture/RUST-MIGRATION-AUDIT.md`

- **ID et chemin** : DOC-0338 — `docs/architecture/RUST-MIGRATION-AUDIT.md`
- **Contenu concerné** : Architecture et descriptions de composants
- **Problème identifié** : Architecture et descriptions de composants
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0361 — `docs/architecture/current.md`

- **ID et chemin** : DOC-0361 — `docs/architecture/current.md`
- **Contenu concerné** : Architecture et descriptions de composants
- **Problème identifié** : Architecture et descriptions de composants
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0362 — `docs/architecture/decisions.md`

- **ID et chemin** : DOC-0362 — `docs/architecture/decisions.md`
- **Contenu concerné** : Architecture et descriptions de composants
- **Problème identifié** : Architecture et descriptions de composants
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0373 — `docs/architecture/local-knowledge-storage-audit.md`

- **ID et chemin** : DOC-0373 — `docs/architecture/local-knowledge-storage-audit.md`
- **Contenu concerné** : Architecture et descriptions de composants
- **Problème identifié** : Architecture et descriptions de composants
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0375 — `docs/architecture/migration-report.md`

- **ID et chemin** : DOC-0375 — `docs/architecture/migration-report.md`
- **Contenu concerné** : Architecture et descriptions de composants
- **Problème identifié** : Architecture et descriptions de composants
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0378 — `docs/architecture/proposed.md`

- **ID et chemin** : DOC-0378 — `docs/architecture/proposed.md`
- **Contenu concerné** : Architecture et descriptions de composants
- **Problème identifié** : Architecture et descriptions de composants
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0385 — `docs/architecture/webui-core-audit.md`

- **ID et chemin** : DOC-0385 — `docs/architecture/webui-core-audit.md`
- **Contenu concerné** : Architecture et descriptions de composants
- **Problème identifié** : Architecture et descriptions de composants
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0446 — `docs/design/2026-05-05-apple-silicon-pearl-mining-design.md`

- **ID et chemin** : DOC-0446 — `docs/design/2026-05-05-apple-silicon-pearl-mining-design.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : docs/design/2026-05-05-apple-silicon-pearl-mining-plan-v1.md ; docs/design/2026-05-05-pearl-coordination-discussion-draft.md ; docs/design/2026-05-05-vllm-pearl-mining-integration-design.md
- **Décision humaine requise** : oui

### DOC-0447 — `docs/design/2026-05-05-apple-silicon-pearl-mining-plan-v1.md`

- **ID et chemin** : DOC-0447 — `docs/design/2026-05-05-apple-silicon-pearl-mining-plan-v1.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0448 — `docs/design/2026-05-05-pearl-coordination-discussion-draft.md`

- **ID et chemin** : DOC-0448 — `docs/design/2026-05-05-pearl-coordination-discussion-draft.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0449 — `docs/design/2026-05-05-vllm-pearl-mining-integration-design.md`

- **ID et chemin** : DOC-0449 — `docs/design/2026-05-05-vllm-pearl-mining-integration-design.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : docs/design/2026-05-05-apple-silicon-pearl-mining-design.md
- **Décision humaine requise** : oui

### DOC-0450 — `docs/design/2026-05-05-vllm-pearl-mining-integration-plan.md`

- **ID et chemin** : DOC-0450 — `docs/design/2026-05-05-vllm-pearl-mining-integration-plan.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : docs/design/2026-05-05-vllm-pearl-mining-integration-design.md
- **Décision humaine requise** : oui

### DOC-0451 — `docs/design/2026-09-30-cartographie-interfaciale.md`

- **ID et chemin** : DOC-0451 — `docs/design/2026-09-30-cartographie-interfaciale.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0452 — `docs/design/2026-09-30-ux-refonte-cartographie.md`

- **ID et chemin** : DOC-0452 — `docs/design/2026-09-30-ux-refonte-cartographie.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0453 — `docs/design/2026-09-30-webui-settings-honesty.md`

- **ID et chemin** : DOC-0453 — `docs/design/2026-09-30-webui-settings-honesty.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0454 — `docs/design/2026-10-01-cartographie-webui-ux.md`

- **ID et chemin** : DOC-0454 — `docs/design/2026-10-01-cartographie-webui-ux.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0455 — `docs/design/ETHAN_CAPABILITIES_UX.md`

- **ID et chemin** : DOC-0455 — `docs/design/ETHAN_CAPABILITIES_UX.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0456 — `docs/design/ETHAN_WEBUI_UX_ANALYSIS.md`

- **ID et chemin** : DOC-0456 — `docs/design/ETHAN_WEBUI_UX_ANALYSIS.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0457 — `docs/design/ETHAN_WEBUI_UX_PARITY_SPEC.md`

- **ID et chemin** : DOC-0457 — `docs/design/ETHAN_WEBUI_UX_PARITY_SPEC.md`
- **Contenu concerné** : Design technique / plan d’implémentation
- **Problème identifié** : Design technique / plan d’implémentation
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0490 — `docs/engineering/esr/ESR-014-frame-fork.md`

- **ID et chemin** : DOC-0490 — `docs/engineering/esr/ESR-014-frame-fork.md`
- **Contenu concerné** : ESR (exigence système)
- **Problème identifié** : ESR (exigence système)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0491 — `docs/engineering/esr/ESR-014-knowledge-observability.md`

- **ID et chemin** : DOC-0491 — `docs/engineering/esr/ESR-014-knowledge-observability.md`
- **Contenu concerné** : ESR (exigence système)
- **Problème identifié** : ESR (exigence système)
- **Destination proposée** : Obsidian/
- **Action proposée** : Fusionner après validation
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0522 — `docs/memory/DECISIONS.md`

- **ID et chemin** : DOC-0522 — `docs/memory/DECISIONS.md`
- **Contenu concerné** : Mémoire inter-sessions Codex
- **Problème identifié** : Mémoire inter-sessions Codex
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0523 — `docs/memory/PROJECT_STATE.md`

- **ID et chemin** : DOC-0523 — `docs/memory/PROJECT_STATE.md`
- **Contenu concerné** : Mémoire inter-sessions Codex
- **Problème identifié** : Mémoire inter-sessions Codex
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0535 — `docs/plans/ETHAN_WEBUI_ARCHITECTURE_MATRIX.md`

- **ID et chemin** : DOC-0535 — `docs/plans/ETHAN_WEBUI_ARCHITECTURE_MATRIX.md`
- **Contenu concerné** : Plan / migration / audit opérationnel
- **Problème identifié** : Plan / migration / audit opérationnel
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0537 — `docs/plans/ETHAN_WEBUI_MIGRATION_STRATEGY.md`

- **ID et chemin** : DOC-0537 — `docs/plans/ETHAN_WEBUI_MIGRATION_STRATEGY.md`
- **Contenu concerné** : Plan / migration / audit opérationnel
- **Problème identifié** : Plan / migration / audit opérationnel
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0538 — `docs/plans/ETHAN_WEBUI_MODELS_PROVIDERS_ARCHITECTURE.md`

- **ID et chemin** : DOC-0538 — `docs/plans/ETHAN_WEBUI_MODELS_PROVIDERS_ARCHITECTURE.md`
- **Contenu concerné** : Plan / migration / audit opérationnel
- **Problème identifié** : Plan / migration / audit opérationnel
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0540 — `docs/plans/ETHAN_WEBUI_RAG_KNOWLEDGE_FILES_MCP_TOOLS_ARCHITECTURE.md`

- **ID et chemin** : DOC-0540 — `docs/plans/ETHAN_WEBUI_RAG_KNOWLEDGE_FILES_MCP_TOOLS_ARCHITECTURE.md`
- **Contenu concerné** : Plan / migration / audit opérationnel
- **Problème identifié** : Plan / migration / audit opérationnel
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0541 — `docs/plans/ETHAN_WEBUI_SETTINGS_ARCHITECTURE.md`

- **ID et chemin** : DOC-0541 — `docs/plans/ETHAN_WEBUI_SETTINGS_ARCHITECTURE.md`
- **Contenu concerné** : Plan / migration / audit opérationnel
- **Problème identifié** : Plan / migration / audit opérationnel
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0542 — `docs/plans/ETHAN_WEBUI_V2_ARCHITECTURE.md`

- **ID et chemin** : DOC-0542 — `docs/plans/ETHAN_WEBUI_V2_ARCHITECTURE.md`
- **Contenu concerné** : Plan / migration / audit opérationnel
- **Problème identifié** : Plan / migration / audit opérationnel
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0570 — `docs/plans/ui-openwebui-target-architecture.md`

- **ID et chemin** : DOC-0570 — `docs/plans/ui-openwebui-target-architecture.md`
- **Contenu concerné** : Plan / migration / audit opérationnel
- **Problème identifié** : Plan / migration / audit opérationnel
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0588 — `docs/security/01-security-audit.md`

- **ID et chemin** : DOC-0588 — `docs/security/01-security-audit.md`
- **Contenu concerné** : Sécurité (conception / architecture)
- **Problème identifié** : Sécurité (conception / architecture)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0599 — `docs/security/CI_CD_SECURITY_ASSESSMENT.md`

- **ID et chemin** : DOC-0599 — `docs/security/CI_CD_SECURITY_ASSESSMENT.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0601 — `docs/security/DEPENDENCY_SECURITY_INVENTORY.md`

- **ID et chemin** : DOC-0601 — `docs/security/DEPENDENCY_SECURITY_INVENTORY.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0602 — `docs/security/DOCKER_IMAGE_SECURITY_ASSESSMENT.md`

- **ID et chemin** : DOC-0602 — `docs/security/DOCKER_IMAGE_SECURITY_ASSESSMENT.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0604 — `docs/security/GITHUB_SECURITY_ASSESSMENT.md`

- **ID et chemin** : DOC-0604 — `docs/security/GITHUB_SECURITY_ASSESSMENT.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0606 — `docs/security/SECRET_EXPOSURE_ASSESSMENT.md`

- **ID et chemin** : DOC-0606 — `docs/security/SECRET_EXPOSURE_ASSESSMENT.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0607 — `docs/security/SECURITY_ASSET_INVENTORY.md`

- **ID et chemin** : DOC-0607 — `docs/security/SECURITY_ASSET_INVENTORY.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0608 — `docs/security/SECURITY_AUDIT_RECONCILIATION.md`

- **ID et chemin** : DOC-0608 — `docs/security/SECURITY_AUDIT_RECONCILIATION.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0609 — `docs/security/SECURITY_BACKLOG.md`

- **ID et chemin** : DOC-0609 — `docs/security/SECURITY_BACKLOG.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0610 — `docs/security/SECURITY_EVIDENCE_REGISTER.md`

- **ID et chemin** : DOC-0610 — `docs/security/SECURITY_EVIDENCE_REGISTER.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0611 — `docs/security/SECURITY_PROGRAM_CHARTER.md`

- **ID et chemin** : DOC-0611 — `docs/security/SECURITY_PROGRAM_CHARTER.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0612 — `docs/security/SECURITY_RISK_REGISTER.md`

- **ID et chemin** : DOC-0612 — `docs/security/SECURITY_RISK_REGISTER.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0613 — `docs/security/SECURITY_ROADMAP.md`

- **ID et chemin** : DOC-0613 — `docs/security/SECURITY_ROADMAP.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0615 — `docs/security/SECURITY_VERIFICATION_MATRIX.md`

- **ID et chemin** : DOC-0615 — `docs/security/SECURITY_VERIFICATION_MATRIX.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

### DOC-0616 — `docs/security/TRUST_BOUNDARIES_REGISTER.md`

- **ID et chemin** : DOC-0616 — `docs/security/TRUST_BOUNDARIES_REGISTER.md`
- **Contenu concerné** : Sécurité (audit/registre opérationnel)
- **Problème identifié** : Sécurité (audit/registre opérationnel)
- **Destination proposée** : Obsidian/
- **Action proposée** : Scinder
- **Éléments à préserver** : contenu source, provenance, historique Git, références
- **Liens à corriger** : Aucune référence interne identifiée
- **Décision humaine requise** : oui

## 3. Résumé de l’audit

- **Nombre total de documents examinés** : 683
  - `docs/` : 418
  - `Obsidian/` : 265

### Répartition par destination proposée

- `Obsidian/` : 614
- `docs/` : 69

### Documents contradictoires détectés

- DOC-0303 — `docs/adr/ADR-1013-frame-fork.md`
- DOC-0304 — `docs/adr/ADR-1013-knowledge-task-lifecycle.md`
- DOC-0305 — `docs/adr/ADR-1014-frame-service-integration.md`
- DOC-0306 — `docs/adr/ADR-1014-retrieval-permission-scope.md`
- DOC-0490 — `docs/engineering/esr/ESR-014-frame-fork.md`
- DOC-0491 — `docs/engineering/esr/ESR-014-knowledge-observability.md`
- Total : 6

### Actions proposées

- Conserver : 231
- Déplacer : 299
- Fusionner après validation : 6
- Ne pas modifier : 97
- Référencer : 6
- Scinder : 44

### Liens potentiellement cassés

- Nombre total de liens Markdown relatifs/locaux ne résolvant pas : **1118**
- Exemples (limités) :
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_LAB_V2_ARCHITECTURE_BLUEPRINT.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_KERNEL_DESIGN.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_LAB_UI_UX_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `handler`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_KERNEL_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_LAB_V2_ARCHITECTURE_BLUEPRINT.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_KERNEL_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_PLUGIN_ECOSYSTEM_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_KNOWLEDGE_GRAPH_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_PLUGIN_ECOSYSTEM_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_KERNEL_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_KERNEL_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_V2_KNOWLEDGE_GRAPH_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-12/1781262561008.md` → `OSIRIS_LAB_UI_UX_SPECIFICATION.md`
  - `Obsidian/Archives/Conversations/cline/2026-06-14/1781440243749.md` → `handler`
  - `Obsidian/Archives/Conversations/cline/2026-06-14/1781445007397.md` → `handler`
  - `Obsidian/Archives/Conversations/cline/2026-06-16/1781448124733.md` → `handler`
  - `Obsidian/Archives/Conversations/cline/2026-06-16/1781448124733.md` → `LICENSE`
  - `Obsidian/Archives/Conversations/cline/2026-06-18/1781763556860.md` → `[a-zA-Z0-9-]*[a-zA-Z0-9]`
  - `Obsidian/Archives/Conversations/cline/2026-06-18/1781763556860.md` → `[a-zA-Z0-9-]*[a-zA-Z0-9]`

### Décisions humaines nécessaires

- Confirmer la liste des documents à conserver en documentation officielle `docs/` (notamment `plugins/`, `webui/`, `learning/`, `deployment/`).
- Valider le scission des documents mixtes (architecture, sécurité, design, plans).
- Confirmer le déplacement des ADR/ESR/ASR/Architecture/API/Specifications vers Obsidian.
- Valider la fusion des ADR/ESR en collision (`ADR-1013`, `ADR-1014`, `ESR-014`).
- Décider du traitement des copies `sources/docs-memory` et de `docs/memory`.
- Valider l’absence de migration depuis Obsidian vers docs/ selon la séparation stricte.

### Limites de l’audit

- Le classement repose sur le contenu et la fonction réelle, mais reste proposé et non validé par un humain ;
- Les documents incertains sont marqués pour examen plutôt qu’imposés ;
- Les liens entrants/sortants automatiques sont limités aux références Markdown résolvables vers `docs/` ou `Obsidian/` ;
- Les fichiers hors de `docs/` et `Obsidian/` ne sont pas inventoriés ligne par ligne ;
- Aucune migration, suppression ou modification de contenu n’a été effectuée.

