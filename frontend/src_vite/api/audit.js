import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const auditText = async (text) => {
    try {
        const response = await axios.post(`${API_URL}/audit`, { text });
        return response.data;
    } catch (error) {
        console.error("Audit failed", error);
        throw error;
    }
};
