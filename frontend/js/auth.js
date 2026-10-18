// Bravio ERP 身份认证与立体权限中枢 (docs/03)
class AuthService {
  static getCurrentUser() {
    try {
      const u = localStorage.getItem("bravio_user");
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  }

  static async login(username, password) {
    const data = await ApiClient.post("/auth/login", { username, password });
    localStorage.setItem("bravio_token", data.token.access_token);
    localStorage.setItem("bravio_user", JSON.stringify(data.user));
    return data.user;
  }

  static logout() {
    localStorage.removeItem("bravio_token");
    localStorage.removeItem("bravio_user");
    window.location.reload();
  }

  static async verifySession() {
    const token = ApiClient.getToken();
    if (!token) return null;
    try {
      const user = await ApiClient.get("/auth/me");
      localStorage.setItem("bravio_user", JSON.stringify(user));
      return user;
    } catch {
      AuthService.logout();
      return null;
    }
  }

  static getRoleBadge(user) {
    if (!user) return "GUEST";
    if (user.is_superuser || user.role === "admin") return "系统超级管理员";
    if (user.username === "gm") return "陈总裁 · 集团总经理";
    if (user.username === "pe") return "王工程 · 产品工程师";
    if (user.username === "qe") return "刘质保 · 质量工程师";
    if (user.username === "supplier") return "张供应 · 供应商专员";
    return (user.full_name || user.username);
  }

  static isSuperAdmin(user) {
    return Boolean(user && (user.is_superuser || user.role === "admin"));
  }
}

window.AuthService = AuthService;
