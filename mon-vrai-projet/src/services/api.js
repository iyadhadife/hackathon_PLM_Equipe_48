// On définit l'URL du backend en dur ici pour l'utiliser partout
export const BACKEND_URL = "http://localhost:5000";

/**
 * Récupère la liste des fichiers depuis le backend Flask
 */
export const fetchFilesFromApi = async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/files`);
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error(`Erreur serveur: ${response.status}`);
    }
  } catch (error) {
    console.error("Erreur API fetchFiles:", error);
    throw error;
  }
};

/**
 * Envoie un fichier vers le backend Flask
 * @param {File} file - L'objet fichier à uploader
 */
export const uploadFileToApi = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      return await response.json();
    } else {
      // Gestion fine des erreurs retournées par Flask
      let errorMessage = `Erreur ${response.status}`;
      try {
        const errData = await response.json();
        if (errData && errData.error) errorMessage = errData.error;
      } catch (e) {
        // Ignorer si le JSON est malformé
      }
      throw new Error(errorMessage);
    }
  } catch (error) {
    console.error("Erreur API uploadFile:", error);
    throw error;
  }
};

/**
 * Construit l'URL complète pour afficher une image
 * @param {string} urlPath - Le chemin relatif (ex: /uploads/image.png)
 */
export const getFileUrl = (urlPath) => {
  if (!urlPath) return '';
  if (urlPath.startsWith('http')) return urlPath;
  return `${BACKEND_URL}${urlPath}`;
};