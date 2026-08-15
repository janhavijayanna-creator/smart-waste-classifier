const API_BASE = "https://smart-waste-classifier-production-580f.up.railway.app";

const existingToken =
    localStorage.getItem("authToken");

if (
    existingToken &&
    (
        window.location.pathname.endsWith("login.html") ||
        window.location.pathname.endsWith("register.html")
    )
) {
    window.location.href = "index.html";
}


document
    .querySelectorAll(".password-toggle")
    .forEach(button => {
        button.addEventListener(
            "click",
            () => {
                const targetId =
                    button.dataset.target;

                const input =
                    document.getElementById(
                        targetId
                    );

                const showing =
                    input.type === "text";

                input.type =
                    showing
                        ? "password"
                        : "text";

                button.textContent =
                    showing
                        ? "Show"
                        : "Hide";
            }
        );
    });


const loginForm =
    document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener(
        "submit",
        async event => {
            event.preventDefault();

            const email =
                document
                    .getElementById("loginEmail")
                    .value
                    .trim();

            const password =
                document
                    .getElementById("loginPassword")
                    .value;

            const message =
                document.getElementById(
                    "loginMessage"
                );

            const button =
                document.getElementById(
                    "loginButton"
                );

            button.disabled = true;
            button.textContent = "Logging in...";
            message.textContent = "";
            message.className = "form-message";

            try {
                const response = await fetch(
                    `${API_BASE}/login`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            email,
                            password
                        })
                    }
                );

                const data =
                    await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Login failed."
                    );
                }

                saveSession(
                    data.token,
                    data.user
                );

                message.textContent =
                    "Login successful.";

                message.className =
                    "form-message success-message";

                window.setTimeout(
                    () => {
                        window.location.href =
                            "index.html";
                    },
                    500
                );

            } catch (error) {
                message.textContent =
                    error.message;

                message.className =
                    "form-message error-message";

            } finally {
                button.disabled = false;
                button.textContent = "Login";
            }
        }
    );
}


const registerForm =
    document.getElementById(
        "registerForm"
    );

if (registerForm) {
    registerForm.addEventListener(
        "submit",
        async event => {
            event.preventDefault();

            const name =
                document
                    .getElementById(
                        "registerName"
                    )
                    .value
                    .trim();

            const email =
                document
                    .getElementById(
                        "registerEmail"
                    )
                    .value
                    .trim();

            const password =
                document
                    .getElementById(
                        "registerPassword"
                    )
                    .value;

            const message =
                document.getElementById(
                    "registerMessage"
                );

            const button =
                document.getElementById(
                    "registerButton"
                );

            button.disabled = true;
            button.textContent =
                "Creating account...";

            message.textContent = "";
            message.className =
                "form-message";

            try {
                const response = await fetch(
                    `${API_BASE}/register`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            name,
                            email,
                            password
                        })
                    }
                );

                const data =
                    await response.json();
                    console.log(
    "LOGIN RESPONSE:",
    data
);

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Registration failed."
                    );
                }

                saveSession(
                    data.token,
                    data.user
                );

                message.textContent =
                    "Account created successfully.";

                message.className =
                    "form-message success-message";

                window.setTimeout(
                    () => {
                        window.location.href =
                            "index.html";
                    },
                    500
                );

            } catch (error) {
                message.textContent =
                    error.message;

                message.className =
                    "form-message error-message";

            } finally {
                button.disabled = false;
                button.textContent =
                    "Create Account";
            }
        }
    );
}


function saveSession(
    token,
    user
) {
    console.log(
        "TOKEN RECEIVED:",
        token
    );

    console.log(
        "USER RECEIVED:",
        user
    );

    if (!token) {
        console.error(
            "No token received from backend!"
        );

        return;
    }

    localStorage.setItem(
        "authToken",
        token
    );

    localStorage.setItem(
        "authUser",
        JSON.stringify(user)
    );

    console.log(
        "TOKEN SAVED:",
        localStorage.getItem(
            "authToken"
        )
    );
}