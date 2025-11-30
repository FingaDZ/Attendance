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
        let sound = null;

        // Analyse du message d'erreur (Miroir du backend)
        if (msg.includes("entrées sont autorisées uniquement entre")) {
            blockReason = "Heure Entrée Dépassée / وقت الدخول انتهى";
            blockSubtext = "Entrée: 03h00-13h30 / الدخول: 03:00-13:30";
            color = "#FF0000"; // Rouge
        }
        else if (msg.includes("sorties sont autorisées uniquement entre")) {
            blockReason = "Heure Sortie Dépassée / وقت الخروج انتهى";
            blockSubtext = "Sortie: 12h00-23h59 / الخروج: 12:00-23:59";
            color = "#FF0000"; // Rouge
        }
        else if (msg.toLowerCase().includes("attendre") && msg.toLowerCase().includes("minutes")) {
            blockReason = "Temps minimum non achevé / الحد الأدنى للعمل لم يكتمل";
            color = "#FFA500"; // Orange
            sound = "MIN_TIME"; // Trigger mintime.wav

            // Extraire les minutes si possible
            const match = msg.match(/(\d+)\s+minutes/);
            if (match) {
                blockSubtext = `Attendre ${match[1]} minutes / انتظر ${match[1]} دقائق`;
            } else {
                blockSubtext = "Attendre quelques minutes / انتظر بضع دقائق";
            }
        }
        else if (msg.toLowerCase().includes("sortie déjà enregistrée")) {
            blockReason = "Sortie déjà enregistrée / تم تسجيل الخروج مسبقاً";
            blockSubtext = "1 sortie max par jour / خروج واحد كحد أقصى";
            color = "#0099FF"; // Bleu
            sound = "EXIT_ALREADY_LOGGED"; // Trigger exitok.wav
        }
        else if (msg.toLowerCase().includes("déjà enregistré")) {
            blockReason = "Déjà enregistré / تم التسجيل مسبقاً";
            blockSubtext = "1 entrée/sortie max / تسجيل واحد كحد أقصى";
            color = "#0099FF"; // Bleu
            sound = "ALREADY_LOGGED"; // Trigger inok.wav
        }

        return {
            success: false,
            blocked: true,
            reason: blockReason,
            subtext: blockSubtext,
            color: color,
            sound: sound || null
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
