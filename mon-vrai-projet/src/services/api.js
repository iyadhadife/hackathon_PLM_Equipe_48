import axios from 'axios';

// On crée une instance d'Axios configurée pour ton Backend Flask
const api = axios.create({
  baseURL: 'http://127.0.0.1:5000', // C'est le port par défaut de Flask
});

export default api;