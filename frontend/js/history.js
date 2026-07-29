const API_BASE = "http://127.0.0.1:8000";

let historyData = [];

async function loadHistory() {
    const table = document.getElementById("historyTable");

    table.innerHTML = `
        <tr>
            <td colspan="5">Loading...</td>
        </tr>
    `;

    try {
        const response = await fetch(`${API_BASE}/history`);

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();

        // Backend returns: { "history": [...] }
        historyData = Array.isArray(data.history)
            ? data.history
            : [];

        renderTable(historyData);

    } catch (error) {
        console.error("History loading error:", error);

        table.innerHTML = `
            <tr>
                <td colspan="5">
                    Failed to load history.
                </td>
            </tr>
        `;
    }
}


function renderTable(data) {
    const table = document.getElementById("historyTable");

    if (!Array.isArray(data) || data.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="5">
                    No prediction history found.
                </td>
            </tr>
        `;

        return;
    }

    table.innerHTML = "";

    data.forEach(item => {
        const row = document.createElement("tr");

        const confidence = Number(item.confidence || 0);

        const formattedDate = formatDate(item.created_at);

        row.innerHTML = `
            <td>${escapeHTML(item.file_name || "Unknown file")}</td>

            <td>
                ${escapeHTML(formatClassName(
                    item.predicted_class || "Unknown"
                ))}
            </td>

            <td>${confidence.toFixed(2)}%</td>

            <td>${formattedDate}</td>

            <td>
                <button
                    class="delete-button"
                    onclick="deletePrediction(${item.id})"
                >
                    Delete
                </button>
            </td>
        `;

        table.appendChild(row);
    });
}


async function deletePrediction(id) {
    const confirmed = confirm(
        "Are you sure you want to delete this prediction?"
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE}/history/${id}`,
            {
                method: "DELETE"
            }
        );

        if (!response.ok) {
            throw new Error(
                `Delete failed: ${response.status}`
            );
        }

        await loadHistory();

    } catch (error) {
        console.error("Delete error:", error);

        alert("Unable to delete the prediction.");
    }
}


async function clearHistory() {
    if (historyData.length === 0) {
        alert("Prediction history is already empty.");
        return;
    }

    const confirmed = confirm(
        "Are you sure you want to clear the entire history?"
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE}/history`,
            {
                method: "DELETE"
            }
        );

        if (!response.ok) {
            throw new Error(
                `Clear history failed: ${response.status}`
            );
        }

        await loadHistory();

    } catch (error) {
        console.error("Clear history error:", error);

        alert("Unable to clear prediction history.");
    }
}


function exportCSV() {
    if (historyData.length === 0) {
        alert("There is no history to export.");
        return;
    }

    const headings = [
        "File Name",
        "Prediction",
        "Confidence",
        "Date"
    ];

    const rows = historyData.map(item => [
        item.file_name || "",
        item.predicted_class || "",
        Number(item.confidence || 0).toFixed(2),
        item.created_at || ""
    ]);

    const csvContent = [
        headings,
        ...rows
    ]
        .map(row =>
            row
                .map(value => escapeCSV(value))
                .join(",")
        )
        .join("\n");

    const blob = new Blob(
        [csvContent],
        {
            type: "text/csv;charset=utf-8;"
        }
    );

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;
    link.download = "prediction_history.csv";

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);
}


function searchHistory(event) {
    const searchText =
        event.target.value.trim().toLowerCase();

    const filteredHistory = historyData.filter(item => {
        const fileName =
            String(item.file_name || "").toLowerCase();

        const predictedClass =
            String(item.predicted_class || "").toLowerCase();

        return (
            fileName.includes(searchText) ||
            predictedClass.includes(searchText)
        );
    });

    renderTable(filteredHistory);
}


function formatDate(dateValue) {
    if (!dateValue) {
        return "Unknown";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
        return dateValue;
    }

    return date.toLocaleString();
}


function formatClassName(className) {
    return String(className)
        .replaceAll("_", " ")
        .replace(/\b\w/g, letter =>
            letter.toUpperCase()
        );
}


function escapeCSV(value) {
    const text = String(value);

    return `"${text.replaceAll('"', '""')}"`;
}


function escapeHTML(value) {
    const element = document.createElement("div");

    element.textContent = String(value);

    return element.innerHTML;
}


document
    .getElementById("searchInput")
    .addEventListener("input", searchHistory);


document
    .getElementById("clearButton")
    .addEventListener("click", clearHistory);


document
    .getElementById("exportButton")
    .addEventListener("click", exportCSV);


loadHistory();