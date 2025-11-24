import axios from 'axios';

const api = axios.create({
    baseURL: '/api', // Relative path works when served from same origin
});

export default api;