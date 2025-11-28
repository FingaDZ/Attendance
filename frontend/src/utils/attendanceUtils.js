/**
 * Parse attendance API response to determine status and visual feedback.
 * Unified logic for both Face Recognition and PIN Authentication.
 */
export const parseAttendanceResponse = (data) => {
    // 1. Succès
    if (data.status === 'logged' || data.status === 'verified') {
        return {
            success: true,
            type: data.type,
            user: data.name,
            timestamp: new Date().toLocaleTimeString()
        };
    }

    // 2. Blocage (Erreur Logique Métier)
    if (data.status === 'blocked') {
        const msg = data.message || "";
        let blockReason = "Log Blocked";
        let blockSubtext = msg;
        let color = "#FF0000"; // Rouge par défaut

        // Analyse du message d'erreur (Miroir du backend)
        if (msg.includes("entrées sont autorisées uniquement entre")) {
            blockReason = "Heure Entrée Dépassée";
            blockSubtext = "Entrée: 03h00-13h30";
            color = "#FF0000"; // Rouge
        }
        else if (msg.includes("sorties sont autorisées uniquement entre")) {
            blockReason = "Heure Sortie Dépassée";
            blockSubtext = "Sortie: 12h00-23h59";
            color = "#FF0000"; // Rouge
        }
        else if (msg.toLowerCase().includes("attendre") && msg.toLowerCase().includes("minutes")) {
            blockReason = "Temps de Travail minimum non achevé";
            color = "#FFA500"; // Orange

            // Extraire les minutes si possible
            const match = msg.match(/(\d+)\s+minutes/);
            if (match) {
                blockSubtext = `Attendre ${match[1]} minutes`;
            } else {
                blockSubtext = "Attendre quelques minutes";
            }
        }
        else if (msg.toLowerCase().includes("déjà enregistré")) {
            blockReason = "Detection Déjà Effectué";
            blockSubtext = "1 entrée/sortie max";
            color = "#0099FF"; // Bleu
        }

        return {
            success: false,
            blocked: true,
            reason: blockReason,
            subtext: blockSubtext,
            color: color
        };
    }

    // 3. Erreur Inconnue / Autre
    return {
        success: false,
        blocked: false, // Pas un blocage métier, mais une erreur technique ou auth
        reason: "Erreur",
        subtext: data.detail || "Erreur inconnue",
        color: "#FF0000"
    };
};
