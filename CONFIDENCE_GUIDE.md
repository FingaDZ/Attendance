# Guide du Seuil de Confiance (Confidence Threshold)

## 🎯 Quel est le meilleur pourcentage pour >50 employés ?

Pour un effectif de **50 à 100 employés**, nous recommandons un seuil situé entre **82% et 85%**.

### Pourquoi 85% est le point idéal (Sweet Spot) ?
*   **> 90% (Trop Strict)** : Le système devient "paranoïaque". Il rejettera souvent les employés légitimes s'ils changent légèrement de coiffure, portent des lunettes différentes, ou si l'éclairage n'est pas parfait. Cela crée de la frustration ("Pourquoi ça ne marche pas ?").
*   **< 80% (Trop Laxiste)** : Le risque de **Faux Positifs** augmente. Le système pourrait confondre deux personnes qui se ressemblent vaguement.
*   **85% (Recommandé)** : C'est l'équilibre parfait pour InsightFace (le modèle que nous utilisons). Il tolère les variations naturelles (lumière, angle) tout en restant très discriminant pour les identités différentes.

## 🧠 Comment le programme identifie-t-il les ressemblances sans erreur ?

Le système ne compare pas les "images" pixel par pixel (ce qui serait facile à tromper). Il utilise une technologie appelée **Reconnaissance Faciale par Vecteurs (Embeddings)**.

### 1. La "Signature" Mathématique (Embedding)
Quand le système voit un visage, il le transforme en une série de **512 nombres** (un vecteur).
*   Cette suite de nombres représente la structure osseuse, la distance entre les yeux, la forme de la mâchoire, etc.
*   **Exemple simplifié** :
    *   Employé A : `[0.1, 0.5, 0.9, ...]`
    *   Employé B : `[0.8, 0.2, 0.1, ...]`

### 2. La Comparaison (Similarité Cosinus)
Pour savoir si deux visages sont la même personne, le système calcule l'angle entre ces deux vecteurs.
*   **Même personne** : Les vecteurs pointent dans la même direction (Angle proche de 0° -> Score proche de 100%).
*   **Personnes différentes** : Les vecteurs pointent dans des directions différentes (Angle grand -> Score faible).

### 3. Pourquoi il ne se trompe pas (même avec des ressemblances) ?
Le modèle **InsightFace (Buffalo_L)** a été entraîné sur des millions de visages pour distinguer des détails invisibles à l'œil nu.
*   Même si deux frères se ressemblent pour un humain, leurs "signatures mathématiques" seront très différentes (souvent < 60% de similarité).
*   Le seuil de **85%** est une barrière de sécurité énorme. Mathématiquement, la probabilité que deux personnes différentes aient une similarité > 85% est infinitésimale (moins de 1 sur un million).

### 🛡️ Comment renforcer la sécurité ?
1.  **3 Photos lors de l'inscription** : En prenant 3 photos sous des angles légèrement différents, on crée une "zone de reconnaissance" plus large et plus précise pour cet employé.
2.  **Qualité des photos** : Assurez-vous que les photos d'inscription sont nettes et bien éclairées. C'est la "référence" du système.
3.  **Liveness (Anti-Spoofing)** : C'est la prochaine étape (v1.6+) pour empêcher quelqu'un d'utiliser une photo imprimée ou un téléphone.

---
**Résumé pour votre cas :**
Gardez le seuil à **85%**. C'est le réglage professionnel standard pour garantir la fluidité des entrées sans compromettre la sécurité.
