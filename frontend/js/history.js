const API_URL = "https://web-production-f1235.up.railway.app";

const historyContainer =
    document.getElementById("historyContainer");

const emptyHistory =
    document.getElementById("emptyHistory");

const clearHistoryButton =
    document.getElementById("clearHistoryButton");

const exportCsvButton =
    document.getElementById("exportCsvButton");

const historySearch =
    document.getElementById("historySearch");

let allHistory = [];


/* =========================
   LOAD HISTORY
========================= */

async function loadHistory() {

    const token =
        localStorage.getItem("authToken");

    if (!token) {
        alert("Please log in first.");

        window.location.href =
            "login.html";

        return;
    }

    historyContainer.innerHTML = `
        <div class="history-loading">
            Loading prediction history...
        </div>
    `;

    try {

        const response = await fetch(
            `${API_URL}/history`,
            {
                method: "GET",

                headers: {
                    Authorization:
                        `Bearer ${token}`
                }
            }
        );

        const data =
            await response.json();


        /* LOGIN EXPIRED */

        if (response.status === 401) {

            localStorage.removeItem(
                "authToken"
            );

            localStorage.removeItem(
                "authUser"
            );

            alert(
                "Your login session has expired. Please log in again."
            );

            window.location.href =
                "login.html";

            return;
        }


        if (!response.ok) {
            throw new Error(
                data.error ||
                "Unable to load history."
            );
        }


        /*
        Backend may return either:

        [
           {...}
        ]

        OR

        {
           history: [...]
        }
        */

        if (Array.isArray(data)) {

            allHistory = data;

        } else if (
            Array.isArray(data.history)
        ) {

            allHistory =
                data.history;

        } else {

            allHistory = [];

        }


        renderHistory(allHistory);

    }

    catch (error) {

        console.error(
            "History error:",
            error
        );

        historyContainer.innerHTML = `
            <div class="history-loading">
                Unable to load history.
            </div>
        `;
    }
}


/* =========================
   RENDER HISTORY
========================= */

function renderHistory(history) {

    historyContainer.innerHTML = "";


    /* NO HISTORY */

    if (
        !history ||
        history.length === 0
    ) {

        emptyHistory.style.display =
            "block";

        clearHistoryButton.disabled =
            true;

        exportCsvButton.disabled =
            true;

        return;
    }


    emptyHistory.style.display =
        "none";

    clearHistoryButton.disabled =
        false;

    exportCsvButton.disabled =
        false;


    history.forEach(item => {

        const row =
            document.createElement("div");

        row.className =
            "history-row";


        const fileName =
            item.file_name ||
            item.filename ||
            "Uploaded image";


        const predictedClass =
            item.predicted_class ||
            item.prediction ||
            "Unknown";


        const confidence =
            Number(
                item.confidence || 0
            );


        const date =
            formatDate(
                item.created_at ||
                item.timestamp ||
                item.date
            );


        row.innerHTML = `

            <div class="history-file">

                <div class="history-file-icon">
                    ♻
                </div>

                <span>
                    ${escapeHtml(fileName)}
                </span>

            </div>


            <div class="history-prediction">

                <span class="prediction-badge">

                    ${escapeHtml(
                        formatClassName(
                            predictedClass
                        )
                    )}

                </span>

            </div>


            <div class="history-confidence">

                <strong>
                    ${confidence.toFixed(2)}%
                </strong>

                <div class="mini-progress">

                    <div
                        class="mini-progress-fill"
                        style="width:
                        ${Math.min(
                            confidence,
                            100
                        )}%"
                    >
                    </div>

                </div>

            </div>


            <div class="history-date">

                ${escapeHtml(date)}

            </div>


            <div class="history-action">

                <button
                    class="delete-history-button"
                    type="button"
                    data-id="${item.id}"
                >
                    Delete
                </button>

            </div>
        `;


        historyContainer.appendChild(
            row
        );

    });


    /* DELETE BUTTON EVENTS */

    document
        .querySelectorAll(
            ".delete-history-button"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                function () {

                    const id =
                        this.dataset.id;

                    deleteHistoryItem(
                        id
                    );
                }
            );

        });
}


/* =========================
   DELETE ONE ITEM
========================= */

async function deleteHistoryItem(id) {

    if (!id) {
        alert(
            "Unable to find this prediction."
        );

        return;
    }


    const confirmed =
        confirm(
            "Delete this prediction?"
        );


    if (!confirmed) {
        return;
    }


    const token =
        localStorage.getItem(
            "authToken"
        );


    try {

        const response =
            await fetch(
                `${API_URL}/history/${id}`,
                {
                    method:
                        "DELETE",

                    headers: {
                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );


        const data =
            await response.json();


        if (
            response.status === 401
        ) {

            logoutUser();

            return;
        }


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to delete prediction."
            );
        }


        /* REMOVE LOCALLY */

        allHistory =
            allHistory.filter(
                item =>
                    String(item.id) !==
                    String(id)
            );


        renderHistory(
            allHistory
        );

    }

    catch (error) {

        console.error(
            "Delete error:",
            error
        );

        alert(
            error.message
        );
    }
}


/* =========================
   CLEAR ALL HISTORY
========================= */

clearHistoryButton.addEventListener(
    "click",
    async () => {

        if (
            allHistory.length === 0
        ) {
            return;
        }


        const confirmed =
            confirm(
                "Are you sure you want to clear your complete prediction history?"
            );


        if (!confirmed) {
            return;
        }


        const token =
            localStorage.getItem(
                "authToken"
            );


        clearHistoryButton.disabled =
            true;

        clearHistoryButton.textContent =
            "Clearing...";


        try {

            const response =
                await fetch(
                    `${API_URL}/history`,
                    {
                        method:
                            "DELETE",

                        headers: {
                            Authorization:
                                `Bearer ${token}`
                        }
                    }
                );


            const data =
                await response.json();


            if (
                response.status === 401
            ) {

                logoutUser();

                return;
            }


            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Unable to clear history."
                );
            }


            allHistory = [];


            renderHistory(
                allHistory
            );

        }

        catch (error) {

            console.error(
                "Clear history error:",
                error
            );

            alert(
                error.message
            );

        }

        finally {

            clearHistoryButton.textContent =
                "Clear History";

        }
    }
);


/* =========================
   SEARCH HISTORY
========================= */

historySearch.addEventListener(
    "input",
    function () {

        const searchValue =
            this.value
                .toLowerCase()
                .trim();


        if (!searchValue) {

            renderHistory(
                allHistory
            );

            return;
        }


        const filtered =
            allHistory.filter(
                item => {

                    const prediction =
                        (
                            item.predicted_class ||
                            item.prediction ||
                            ""
                        )
                            .toLowerCase();


                    const file =
                        (
                            item.file_name ||
                            item.filename ||
                            ""
                        )
                            .toLowerCase();


                    return (
                        prediction.includes(
                            searchValue
                        ) ||
                        file.includes(
                            searchValue
                        )
                    );
                }
            );


        renderHistory(
            filtered
        );
    }
);


/* =========================
   EXPORT CSV
========================= */

exportCsvButton.addEventListener(
    "click",
    function () {

        if (
            allHistory.length === 0
        ) {

            alert(
                "There is no history to export."
            );

            return;
        }


        let csv =
            "File,Prediction,Confidence,Date\n";


        allHistory.forEach(
            item => {

                const file =
                    item.file_name ||
                    item.filename ||
                    "Uploaded image";


                const prediction =
                    item.predicted_class ||
                    item.prediction ||
                    "Unknown";


                const confidence =
                    item.confidence || 0;


                const date =
                    formatDate(
                        item.created_at ||
                        item.timestamp ||
                        item.date
                    );


                csv +=
                    `"${cleanCsv(file)}",` +
                    `"${cleanCsv(prediction)}",` +
                    `"${confidence}%",` +
                    `"${cleanCsv(date)}"\n`;

            }
        );


        const blob =
            new Blob(
                [csv],
                {
                    type:
                        "text/csv;charset=utf-8;"
                }
            );


        const url =
            URL.createObjectURL(
                blob
            );


        const link =
            document.createElement(
                "a"
            );


        link.href = url;

        link.download =
            "waste_prediction_history.csv";


        document.body.appendChild(
            link
        );


        link.click();


        document.body.removeChild(
            link
        );


        URL.revokeObjectURL(
            url
        );
    }
);


/* =========================
   FORMAT CLASS NAME
========================= */

function formatClassName(value) {

    if (!value) {
        return "Unknown";
    }


    return String(value)

        .replaceAll(
            "_",
            " "
        )

        .replace(
            /\b\w/g,
            letter =>
                letter.toUpperCase()
        );
}


/* =========================
   FORMAT DATE
========================= */

function formatDate(value) {

    if (!value) {
        return "—";
    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(value);
    }


    return date.toLocaleString();
}


/* =========================
   ESCAPE HTML
========================= */

function escapeHtml(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =========================
   CSV CLEANER
========================= */

function cleanCsv(value) {

    return String(value)
        .replaceAll(
            '"',
            '""'
        );
}


/* =========================
   LOGOUT IF TOKEN EXPIRES
========================= */

function logoutUser() {

    localStorage.removeItem(
        "authToken"
    );

    localStorage.removeItem(
        "authUser"
    );


    alert(
        "Your session has expired. Please log in again."
    );


    window.location.href =
        "login.html";
}


/* =========================
   START
========================= */

document.addEventListener(
    "DOMContentLoaded",
    loadHistory
);