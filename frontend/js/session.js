const AUTH_API_BASE = "https://web-production-f1235.up.railway.app";

function getAuthToken() {
    return localStorage.getItem("authToken");
}

function getStoredUser() {
    const userText =
        localStorage.getItem("authUser");

    if (!userText) {
        return null;
    }

    try {
        return JSON.parse(userText);
    } catch (error) {
        return null;
    }
}

function requireLogin() {
    const token = getAuthToken();

    if (!token) {
        window.location.href = "login.html";
        return false;
    }

    return true;
}

function getAuthHeaders(
    extraHeaders = {}
) {
    const token = getAuthToken();

    return {
        ...extraHeaders,
        Authorization: `Bearer ${token}`
    };
}

async function logoutUser() {
    const token = getAuthToken();

    try {
        if (token) {
            await fetch(
                `${AUTH_API_BASE}/logout`,
                {
                    method: "POST",
                    headers: {
                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );
        }
    } catch (error) {
        console.error(
            "Logout request failed:",
            error
        );
    }

    localStorage.removeItem("authToken");
    localStorage.removeItem("authUser");

    window.location.href = "login.html";
}

function setupUserNavbar() {
    const user =
        getStoredUser();

    const userNameElement =
        document.getElementById(
            "navbarUserName"
        );

    const logoutButton =
        document.getElementById(
            "logoutButton"
        );

    if (
        userNameElement &&
        user
    ) {
        userNameElement.textContent =
            user.name;
    }

    if (logoutButton) {
        logoutButton.addEventListener(
            "click",
            logoutUser
        );
    }
}

requireLogin();

document.addEventListener(
    "DOMContentLoaded",
    setupUserNavbar
);