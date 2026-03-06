---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: ['these_tomasini.pdf', 'ISO22716.pdf', 'DLE_juno.pdf', 'client-call-transcript']
session_topic: 'Architecture et implémentation technique de DLE-SaaS (dossier de lot électronique cosmétique)'
session_goals: 'Définir une architecture SaaS saine, rapide à exécuter, crédible pour un pilote client, et extensible à plusieurs usines du même groupe'
selected_approach: 'decision-oriented-architecture-review'
techniques_used: ['First Principles Thinking', 'Competitive Benchmarking', 'Risk Review', 'Stack Decision Framing']
ideas_generated: [0]
context_file: ''
technique_execution_complete: true
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Axel  
**Date:** 2026-03-05

## Session Overview

**Topic:** Architecture et implémentation technique de DLE-SaaS pour l'industrie cosmétique  
**Goal:** Définir une base produit et technique cohérente pour un outil de dossier de lot électronique, avec une première version montrable rapidement à la direction du client, sans compromettre la capacité d'évolution vers un vrai SaaS multi-usines.

### Why This Document Exists

Ce document synthétise les décisions d'architecture et de produit à partir de trois sources:
- la compréhension métier du dossier de lot électronique en environnement cosmétique BPF / ISO 22716
- le besoin concret exprimé par un premier client industriel lors d'un appel de découverte
- l'objectif fondateur de construire dès le départ une base logicielle saine, modulaire, testable, et extensible

Ce document est volontairement **self-contained**: il présente le contexte, les arbitrages, les choix retenus, les risques, et le périmètre de la première version sans supposer la lecture d'une version antérieure.

## Business Context and Client Signal

### What the First Client Actually Asked For

Le premier client est une usine cosmétique d'un groupe. Le site fonctionne aujourd'hui avec des dossiers de lot papier.

Les points saillants exprimés lors de l'appel:
- le référentiel attendu est **BPF cosmétique / ISO 22716**
- l'usine veut une exécution documentaire **propre, rigoureuse, proche des pratiques pharma**, sans pour autant fabriquer de produits pharmaceutiques
- le problème principal n'est pas un rappel produit ou une défaillance process majeure, mais la **qualité documentaire du dossier de lot**
- les dossiers sont parfois mal remplis, incomplets, mal signés, ou relus trop tard
- un audit BPF est attendu dans les prochains mois
- le client ne veut pas un ERP lourd, mais un outil plus léger, paramétré sur son dossier de lot maître existant
- les opérateurs disposent déjà d'**un ordinateur par ligne**, donc un outil web sur poste fixe est réaliste
- le site utilise déjà un ERP et un WMS, mais aucune intégration n'est exigée pour un premier pilote
- il existe plusieurs produits et formats, mais un format représente la majorité du volume, ce qui ouvre la voie à un pilote ciblé

### Product Interpretation

Le produit à construire n'est pas un MES complet. La première valeur à délivrer est:
- sécuriser le remplissage du dossier de lot
- rendre les étapes plus guidées et plus complètes que le papier
- rendre la revue et la libération plus lisibles
- produire un historique informatique crédible pour les audits

En conséquence, la première version doit être pensée comme un **outil de sécurisation et de revue du dossier de lot**, pas comme une plateforme industrielle universelle dès le jour 1.

## Architectural Principles

### Principle 1: Build for Evolvability, Not for Maximal Initial Scope

Une architecture saine ne consiste pas à embarquer toutes les capacités futures dans la première livraison. Elle consiste à:
- choisir des fondations difficiles à regretter
- séparer clairement le domaine métier, l'infrastructure et l'UX
- rendre les invariants critiques explicites
- éviter les dépendances qui capturent inutilement le produit

### Principle 2: The Hardest Decisions Are Not the Same as the Most Visible Decisions

Les décisions les plus difficiles à changer plus tard sont:
1. le modèle métier du dossier de lot
2. la stratégie de configuration des templates
3. le framework backend
4. l'approche frontend
5. la structure des workflows de signature, revue, correction et archivage

Le fournisseur cloud et la surcouche de déploiement sont importants, mais moins structurants si l'application reste portable.

### Principle 3: Cosmetics with Pharma-Like Rigor

Le client n'a pas demandé un produit pharmaceutique au sens réglementaire strict. En revanche, il a explicitement signalé une attente de rigueur documentaire élevée, proche des usages pharma.

La bonne réponse produit est donc:
- **viser une rigueur pharma-like dans le logiciel**
- **ne pas sur-promettre une conformité pharma complète** sans validation documentaire, qualité et gouvernance adéquates

Concrètement, cela implique dès la base:
- audit trail sérieux
- signature électronique interne propre
- correction avec motif obligatoire
- identité, date, heure et signification affichées
- séparation claire entre exécution, revue et libération
- archivage lisible et défendable

## Core Domain Model

### Canonical Record Lifecycle

Le système est structuré autour de trois objets métier principaux:
- **MMR (Master Manufacturing Record)**: le dossier maître, c'est-à-dire le template validé
- **BMR (Batch Manufacturing Record)**: l'instance d'exécution d'un lot à partir d'un template figé
- **DDL (Dossier de Lot)**: le dossier complet consultable, relisible, exportable et archivable

Le cycle de vie minimal retenu est:
1. édition du MMR
2. activation d'une version
3. instanciation d'un BMR pour un lot
4. remplissage guidé par les opérateurs
5. signatures sur les étapes requises
6. revue
7. libération ou rejet
8. archivage

### Non-Negotiable Invariants

Les invariants suivants sont considérés comme fondamentaux:
- un lot référence toujours une version précise du template utilisée au moment de son démarrage
- un template modifié n'altère jamais rétroactivement un lot en cours
- toute donnée modifiée après une validation doit être historisée avec motif
- chaque signature est liée à un utilisateur identifié, une date/heure, une signification, et un état précis des données au moment de la signature
- le système doit rester lisible pour un auditeur sans dépendre d'une interprétation technique complexe

## Final Stack Decision

### Chosen Stack

```text
Backend:    Django 5.2 LTS + Django REST Framework + drf-spectacular
Frontend:   React + TypeScript + Vite
Database:   PostgreSQL
Infra:      Docker Compose portable, déployable chez Scaleway
Ops:        Dokploy possible comme surcouche d'exploitation, mais non structurant pour le produit
```

### Why Django Was Chosen

Django est retenu comme framework backend principal pour cinq raisons:
- il fournit immédiatement les briques de base nécessaires: auth, sessions, groupes, permissions, admin interne, ORM mature
- il permet d'aller vite sur un domaine métier fortement structuré
- il est particulièrement adapté à un produit avec back-office interne, workflows documentaires, et objets métier riches
- il s'intègre bien avec PostgreSQL et une logique d'audit côté base
- il est très compatible avec une stratégie de développement assistée par IA grâce à son haut niveau de conventions

Django est donc choisi non pas parce qu'il est le plus “moderne” sur le papier, mais parce qu'il maximise le rapport:
- vitesse de construction
- robustesse structurelle
- lisibilité du code
- capacité d'évolution

### Why React Was Chosen

React est retenu pour la couche frontend car le produit vise à terme un vrai moteur de dossier configurable.

Les arguments principaux sont:
- l'interface opérateur est un **step-by-step guided UI**, pas une simple succession de pages HTML statiques
- le futur moteur MMR/BMR devra rendre dynamiquement des champs, des validations, des états, des instructions et des signatures
- React facilite mieux qu'une approche HTML minimale la composition d'interfaces pilotées par schéma
- TypeScript apporte une sécurité utile sur le contrat d'API et les composants UI
- Vite réduit la friction de développement et de build

### Why PostgreSQL Was Chosen

PostgreSQL est retenu comme base unique parce qu'il couvre simultanément:
- les besoins relationnels forts du domaine: utilisateurs, rôles, lots, signatures, versions, événements
- les besoins configurables du moteur de templates via `jsonb`
- les besoins d'audit et de contrôle fin au niveau base
- une grande portabilité d'hébergement

La base cible n'est ni un simple store de formulaires ni un pur moteur documentaire: c'est un système métier avec invariants forts et parties configurables.

### Why Docker Compose Was Chosen as the Deployment Baseline

Docker Compose est retenu comme vérité de déploiement initiale car il permet:
- un environnement local reproductible
- une démo rapide
- une portabilité forte entre machines et fournisseurs cloud
- une réduction du couplage à une plateforme spécifique

### Why Scaleway Remains a Good Default

Scaleway reste un bon choix initial si les critères suivants comptent:
- hébergement en France
- discours de souveraineté pour des clients industriels français
- coût raisonnable
- simplicité de mise en place

### Why Dokploy Is Not a Foundational Product Decision

Dokploy peut accélérer l'exploitation et le déploiement. En revanche, le produit ne doit pas dépendre de Dokploy pour exister.

La décision structurante est donc:
- **le produit doit rester déployable sans Dokploy**
- Dokploy peut être utilisé comme **outil d'exploitation**, pas comme hypothèse d'architecture métier

## Alternatives Considered and Rejected

### Backend Alternatives Considered

#### FastAPI

FastAPI est un très bon framework d'API, mais il a été écarté comme choix principal pour ce SaaS car:
- il apporte moins de structure globale pour un domaine riche avec auth, admin interne et objets métier nombreux
- il demanderait de reconstruire davantage de conventions et de back-office
- il est excellent pour une API pure, moins avantageux ici qu'un framework full-stack structurant

#### NestJS

NestJS a été écarté pour ce cas car:
- le full TypeScript n'apporte pas ici assez de valeur pour compenser la glue supplémentaire côté backend
- l'outillage standard autour de l'auth, du back-office interne et des workflows documentaires est moins immédiatement rentable que Django
- l'écosystème audit / historique DB-centric est moins naturel pour ce besoin

#### Rails / Hotwire

Rails reste une alternative crédible en termes de productivité, mais il n'a pas été retenu car:
- l'écosystème Python est plus aligné avec les pistes déjà étudiées
- l'orientation backend/documentaire du produit s'intègre mieux à Django dans le contexte actuel
- la courbe de cohérence avec les travaux déjà menés serait moins bonne

### Frontend Alternatives Considered

#### HTMX / Hotwire

Une approche plus légère côté frontend a été sérieusement envisagée. Elle a été écartée pour la version cible car le produit doit évoluer vers:
- un rendu UI piloté par schéma
- des composants d'étape riches
- des validations conditionnelles structurées
- un moteur réutilisable entre plusieurs templates

Pour une démo simple, HTMX aurait pu suffire. Pour le produit visé, React est jugé plus adapté.

#### Next.js

Next.js n'apporte pas suffisamment de valeur dans ce cas:
- pas de besoin SEO
- pas de besoin SSR structurant
- complexité supplémentaire inutile pour une application authentifiée de type poste opérateur / back-office

### Platform Alternatives Considered

#### Supabase

Supabase a été écarté comme fondation principale car:
- le domaine métier impose des règles applicatives spécifiques autour des signatures, de la revue et de l'audit
- le produit gagnera à garder la maîtrise complète de la couche métier et de la couche base
- les gains de vitesse initiaux ne compensent pas le risque de modèle contraint par la plateforme

#### Camunda / Temporal

Ces outils sont puissants pour des workflows complexes et distribués, mais ils ont été écartés pour la fondation v1 car:
- la première valeur à délivrer n'est pas l'orchestration longue durée inter-systèmes
- ils ajoutent une complexité très supérieure au besoin immédiat

## Data and Configuration Strategy

### Template Engine Strategy

Le système doit être configuré à partir de templates métier, pas codé produit par produit.

La stratégie retenue est:
- stocker les définitions de MMR sous forme structurée en base
- rendre les étapes dans le frontend React à partir de cette définition
- figer un snapshot du template lors de la création d'un lot
- stocker les données d'exécution du lot sous forme structurée, tout en gardant des entités relationnelles fortes autour

### Hybrid Relational + JSONB Model

Le modèle retenu est hybride:
- **relationnel** pour les entités critiques et fréquemment requêtées
- **jsonb** pour les parties variables du template et des données d'étape

Les tables relationnelles attendues dès la base:
- users
- roles / groups
- mmr
- mmr_versions
- batches / lots
- batch_steps
- signatures
- review_events
- release_events
- audit_events
- attachments

Les zones configurables peuvent vivre en `jsonb`:
- définition des sections
- définition des champs
- règles de validation
- instructions d'étape
- structure détaillée des réponses

### Calculation Strategy

Les calculs métier issus d'Excel ne doivent pas être disséminés dans le frontend.

La stratégie retenue est:
- expressions ou fonctions métier versionnées côté backend
- référence à ces calculs depuis les définitions de template
- exécution déterministe côté serveur
- affichage des résultats calculés côté UI

Objectif: éviter qu'un calcul critique repose sur une logique frontend difficile à auditer.

## Electronic Signatures Strategy

### What the Product Needs

Le client a explicitement demandé comment fonctionnerait la signature électronique dans le dossier de lot.

La stratégie retenue est de construire une **signature électronique interne au produit**, adaptée à un contexte d'atelier et de revue qualité.

Cette signature doit inclure:
- identité du signataire
- date et heure serveur
- signification de la signature
- ré-authentification au moment de signer
- lien fort avec l'étape et les données signées

### What the Product Does Not Need

Le produit n'a pas besoin d'une solution de signature documentaire externe de type contrat ou parapheur.

En particulier:
- pas de Yousign / DocuSign comme fondation métier de la signature d'exécution
- pas de dépendance à une signature qualifiée externe pour les gestes opérateur du quotidien

### Practical Authentication Model

Le modèle cible retenu pour la suite est:
- authentification de session simple et exploitable en atelier
- ré-authentification au moment de signer
- journalisation systématique de la signature

Le détail exact du mécanisme de session peut rester ajustable tant que les invariants de signature sont respectés.

## Audit Trail Strategy

### Minimum Serious Audit Baseline

Le socle minimal jugé nécessaire comprend:
- historique des créations, modifications et validations sur les objets critiques
- identité utilisateur
- date/heure serveur
- type d'action
- ancienne valeur / nouvelle valeur quand pertinent
- motif de correction quand une donnée validée est modifiée

### What Is Deliberately Deferred

Le document ne retient pas comme prérequis immédiat:
- une hash-chain cryptographique custom dans l'audit trail
- une preuve cryptographique avancée au-delà de ce qui est nécessaire pour une première version crédible

Ces idées restent intéressantes, mais elles ne font pas partie du socle à figer avant la première démonstration fonctionnelle.

## Frontend and UX Strategy

### Interface Philosophy

L'UX retenue est explicitement orientée atelier:
- parcours étape par étape
- une seule action claire à l'écran quand c'est possible
- validation explicite avant passage à la suite
- affichage lisible des erreurs, statuts, signatures et blocs manquants
- vitesse d'usage plus importante que richesse visuelle

### Primary Surfaces

Le frontend React doit à terme couvrir trois surfaces distinctes:
- **Opérateur**: saisie guidée pendant fabrication / conditionnement
- **Qualité / revue**: contrôle, corrections, libération, traçabilité
- **Administration interne**: paramétrage, versions, utilisateurs, configuration

### Why the Operator UX Is the Main Product Risk

Le risque principal n'est pas la stack. Le risque principal est l'acceptation terrain.

Si l'interface est plus lente, plus confuse, ou plus fragile que le papier, le projet échoue même si l'architecture est excellente.

La stratégie produit doit donc imposer très tôt:
- un prototype réel sur un vrai dossier maître
- une exécution bout en bout sur un cas pilote
- une revue terrain avec les personnes qui rempliront réellement le dossier

## Scope of the First Functional Demonstration

### Goal of the First Demonstration

La première démonstration n'a pas pour but de prouver que tout le futur SaaS existe. Elle doit prouver qu'une base crédible fonctionne sur un cas concret client.

La démonstration fonctionnelle visée doit permettre de montrer à la direction:
- un dossier de lot maître transposé en version électronique
- un lot instancié à partir du dossier maître
- une saisie guidée sur plusieurs étapes représentatives
- une signature électronique interne cohérente
- une revue visible
- un export ou rendu de dossier lisible

### In Scope for the First Demonstration

- un seul client
- un seul site
- un seul template représentatif
- un seul flux principal fabrication ou conditionnement
- comptes utilisateurs de démonstration
- rendu step-by-step
- validations de base
- historique minimal sérieux
- signature interne sur les étapes clés
- vue revue / qualité
- export PDF ou rendu dossier consultable

### Out of Scope for the First Demonstration

- intégration ERP / WMS
- multi-tenant actif
- multi-site groupe complet
- form builder visuel complet
- orchestration workflow avancée
- offline mode
- moteur de qualification complexe
- automatisation documentaire qualité complète
- reporting BI avancé
- hash-chain custom

## Multi-Site and SaaS Evolution Strategy

### What Must Be Designed Now

Même si la première démonstration est mono-site, l'architecture doit être pensée pour:
- plusieurs usines d'un même groupe
- plusieurs templates
- plusieurs versions d'un template
- gouvernance progressive des droits et de la revue

### What Must Not Be Forced Too Early

En revanche, il n'est pas nécessaire de figer dès maintenant:
- une stratégie multi-tenant active en production
- une séparation technique complexe entre usines
- une gouvernance groupe complète

La bonne posture est:
- concevoir des modèles compatibles avec l'extension
- ne pas surcharger la première livraison de complexité non encore demandée

## Regulatory Positioning

### Target Positioning

Le produit vise un positionnement de rigueur élevée pour un environnement cosmétique BPF.

Le message correct est:
- le logiciel est conçu pour une exécution documentaire rigoureuse, inspirée des bonnes pratiques observées dans des environnements plus exigeants
- le produit n'affirme pas, par défaut et sans dispositif complet, une conformité pharmaceutique globale au sens large

### Practical Consequence

Le produit doit être présenté comme:
- adapté au besoin cosmétique du client
- structuré pour supporter une traçabilité et une discipline documentaire élevées
- extensible vers des exigences plus fortes si le contexte l'impose plus tard

## Risks

### Risk 1: Over-Engineering the First Version

Le risque le plus sérieux côté architecture est de construire trop de fondations avancées avant d'avoir validé le flux métier principal.

### Risk 2: Underestimating Template Translation Effort

Le vrai coût initial est probablement la transformation du dossier maître papier, des annexes, des calculs et des checklists en modèle exécutable.

### Risk 3: UI Accepted by Management but Rejected by Operators

Une démo réussie à la direction ne garantit pas une adoption réelle en atelier.

### Risk 4: Ambiguity Around Signature Expectations

Le terme “signature électronique” peut recouvrir des attentes très différentes. Il faut verrouiller rapidement ce que le client attend concrètement.

### Risk 5: Confusing Product Quality with Regulatory Perfection

Un produit très propre techniquement ne devient pas automatiquement “pharma-compliant”. Une partie importante de la crédibilité future dépendra aussi de la documentation, des SOP, de la validation et du dispositif qualité.

## Open Questions

Les points suivants doivent encore être clarifiés avec le client ou par analyse complémentaire:
- quelle est la structure exacte du dossier maître pilote
- quelles sont les erreurs documentaires les plus fréquentes aujourd'hui
- que recouvrent précisément les étiquettes collées “début, milieu, fin”
- quelle est la granularité réelle attendue des signatures
- quel flux doit servir de pilote: fabrication, conditionnement, ou un sous-ensemble représentatif
- quelle part des calculs Excel doit être reproduite dès la première démonstration
- quelle gouvernance groupe sera pertinente si une deuxième usine rejoint le produit

## Final Decision Summary

### Final Technical Decisions Frozen at This Stage

Les décisions suivantes sont considérées comme fixées:
- backend en **Django 5.2 LTS**
- API en **Django REST Framework** avec **drf-spectacular**
- frontend en **React + TypeScript + Vite**
- base en **PostgreSQL**
- modèle hybride **relationnel + jsonb**
- déploiement canonique via **Docker Compose**
- hébergement initial compatible **Scaleway**
- Dokploy autorisé comme outil d'exploitation, mais non structurant

### Decisions Explicitly Left Open

Les décisions suivantes restent ouvertes ou différées:
- mécanisme précis d'authentification de session en atelier
- modèle de multi-site / multi-tenant activé en production
- forme définitive du moteur de calcul métier
- niveau de sophistication du form builder futur
- niveau de sophistication cryptographique de l'audit trail

## Recommended Next Steps

1. obtenir le dossier maître pilote et les annexes réelles du client
2. choisir le flux pilote le plus représentatif et le plus simple
3. modéliser un premier template MMR exécutable
4. construire une démonstration bout en bout sur ce seul flux
5. figer la mécanique de signature interne avant de montrer l'outil au client
6. faire relire la démonstration d'abord comme outil de direction, puis comme outil de terrain

## Closing Note

Le choix de stack retenu n'est pas un compromis par défaut. C'est un choix volontaire en faveur d'une architecture:
- saine
- modulaire
- portable
- rapide à construire
- lisible pour l'équipe et pour l'IA
- crédible pour un pilote industriel
- extensible vers un vrai SaaS multi-usines

La combinaison **Django + React + PostgreSQL** est donc retenue comme fondation du produit.
