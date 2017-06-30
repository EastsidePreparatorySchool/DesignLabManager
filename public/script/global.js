function logout() {
    document.cookie = 'auth=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    location.reload();
}