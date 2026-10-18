// Bravio ERP 统一 API 客户端网关 (docs/01 & docs/02)
const API_BASE = (window.location.port === "8000") ? "/api/v1" : "http://localhost:8000/api/v1";

class ApiClient {
  static getToken() {
    return localStorage.getItem("bravio_token");
  }

  static async request(endpoint, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };

    const token = ApiClient.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, config);
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error((data && (data.detail || data.message)) || `HTTP ${res.status}: 请求失败`);
      }
      return data;
    } catch (err) {
      console.error(`[API ERROR] ${endpoint}:`, err);
      throw err;
    }
  }

  static get(endpoint) {
    return ApiClient.request(endpoint, { method: "GET" });
  }

  static post(endpoint, body) {
    return ApiClient.request(endpoint, {
      method: "POST",
      body: JSON.stringify(body)
    });
  }

  static put(endpoint, body) {
    return ApiClient.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(body)
    });
  }

  static delete(endpoint) {
    return ApiClient.request(endpoint, { method: "DELETE" });
  }

  static async uploadFormData(endpoint, formData) {
    const token = ApiClient.getToken();
    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers,
      body: formData
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      throw new Error((data && (data.detail || data.message)) || `HTTP ${res.status}: 上传失败`);
    }
    return data;
  }
}

window.ApiClient = ApiClient;
