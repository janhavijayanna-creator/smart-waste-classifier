const API_BASE = "https://smart-waste-classifier-production-580f.up.railway.app";

let categoryChart = null;
let countChart = null;


/* =========================
   LOAD COMPLETE DASHBOARD
========================= */

async function loadDashboard() {
    await Promise.all([
        loadStatistics(),
        checkBackendStatus()
    ]);
}


/* =========================
   LOAD STATISTICS
========================= */

async function loadStatistics() {
    try {
        const response = await fetch(
    `${API_BASE}/statistics`,
    {
        headers: getAuthHeaders()
    }
);

        if (!response.ok) {
            throw new Error(
                `Statistics request failed: ${response.status}`
            );
        }

        const data = await response.json();

        console.log(
            "Statistics response:",
            data
        );

        const statistics =
            data.statistics || data;

        updateStatisticCards(statistics);
        updateClassCounts(statistics);
        createCharts(statistics);

    } catch (error) {
        console.error(
            "Unable to load statistics:",
            error
        );

        setText(
            "totalScans",
            "0"
        );

        setText(
            "averageConfidence",
            "0%"
        );

        setText(
            "mostDetectedClass",
            "Unavailable"
        );

        setText(
            "wasteCategories",
            "0"
        );

        const classCountsElement =
            document.getElementById(
                "classCounts"
            );

        if (classCountsElement) {
            classCountsElement.innerHTML = `
                <p class="empty-message">
                    Unable to load prediction data.
                </p>
            `;
        }

        createCharts({});
    }
}


/* =========================
   UPDATE STATISTIC CARDS
========================= */

function updateStatisticCards(statistics) {
    const totalScans =
        statistics.total_predictions ??
        statistics.total_scans ??
        statistics.total ??
        0;

    const averageConfidence =
        statistics.average_confidence ??
        statistics.avg_confidence ??
        0;

    const mostDetectedClass =
        statistics.most_detected_class ??
        statistics.most_common_class ??
        statistics.top_class ??
        null;

    const wasteCategories =
        statistics.waste_categories ??
        Object.keys(
            statistics.class_counts || {}
        ).length;

   animateNumber(
    "totalScans",
    totalScans,
    {
        duration: 900,
        decimals: 0
    }
);

animateNumber(
    "averageConfidence",
    averageConfidence,
    {
        duration: 1000,
        decimals: 2,
        suffix: "%"
    }
);

setText(
    "mostDetectedClass",
    formatClassName(
        mostDetectedClass
    )
);

animateNumber(
    "wasteCategories",
    wasteCategories,
    {
        duration: 850,
        decimals: 0
    }
);
}


/* =========================
   UPDATE CATEGORY COUNTS
========================= */

function updateClassCounts(statistics) {
    const categoryCounts = {
        ...(
            statistics.category_counts ||
            statistics.class_counts ||
            statistics.counts ||
            {}
        )
    };

    categoryCounts.uncertain =
        Number(
            statistics.uncertain_count || 0
        );

    const categoryLabels = [
    "Broken Toys",
    "Cardboard",
    "E-Waste",
    "Glass",
    "Metal",
    "Organic",
    "Paper",
    "Plastic",
    "Uncertain"
];

    const classCountsElement =
        document.getElementById(
            "classCounts"
        );

    if (!classCountsElement) {
        return;
    }

    classCountsElement.innerHTML = "";

    categories.forEach(category => {
        const count =
            Number(
                categoryCounts[category] || 0
            );

        const item =
            document.createElement("div");

        item.className =
            "class-count-item";

        const className =
            document.createElement("span");

        className.className =
            "class-name";

        className.textContent =
            formatClassName(category);

        const classValue =
            document.createElement("span");

        classValue.className =
            "class-value";

        classValue.textContent =
            count;

        item.appendChild(className);
        item.appendChild(classValue);

        classCountsElement.appendChild(item);
    });
}


/* =========================
   CREATE CHART DATA
========================= */

function createCharts(statistics) {
    const categoryCounts = {
        ...(
            statistics.category_counts ||
            statistics.class_counts ||
            statistics.counts ||
            {}
        )
    };

    categoryCounts.uncertain =
        Number(
            statistics.uncertain_count || 0
        );

    const categoryLabels = [
    "Broken Toys",
    "Cardboard",
    "E-Waste",
    "Glass",
    "Metal",
    "Organic",
    "Paper",
    "Plastic",
    "Uncertain"
];

    const labels =
        categories.map(
            formatClassName
        );

    const values =
        categories.map(category =>
            Number(
                categoryCounts[category] || 0
            )
        );

    const colors = [
        "#2563EB",
        "#16A34A",
        "#F97316",
        "#EC4899",
        "#64748B",
        "#EAB308",
        "#06B6D4",
        "#8B5CF6",
        "#9CA3AF"
    ];

    createCategoryChart(
        labels,
        values,
        colors
    );

    createCountChart(
        labels,
        values,
        colors
    );
}


/* =========================
   DOUGHNUT CHART
========================= */

function createCategoryChart(
    labels,
    values,
    colors
) {
    const canvas =
        document.getElementById(
            "categoryChart"
        );

    if (!canvas) {
        console.error(
            "categoryChart canvas was not found."
        );

        return;
    }

    if (categoryChart) {
        categoryChart.destroy();
    }

    categoryChart = new Chart(
        canvas,
        {
            type: "doughnut",

            data: {
                labels: labels,

                datasets: [
                    {
                        label:
                            "Predictions",

                        data:
                            values,

                        backgroundColor:
                            colors,

                        borderColor:
                            "#FFFFFF",

                        borderWidth:
                            2
                    }
                ]
            },

            options: {
                responsive:
                    true,

                maintainAspectRatio:
                    false,

                plugins: {
                    legend: {
                        position:
                            "bottom"
                    },

                    tooltip: {
                        callbacks: {
                            label(context) {
                                const label =
                                    context.label ||
                                    "";

                                const value =
                                    Number(
                                        context.raw ||
                                        0
                                    );

                                const total =
                                    context
                                        .dataset
                                        .data
                                        .reduce(
                                            (
                                                sum,
                                                currentValue
                                            ) =>
                                                sum +
                                                Number(
                                                    currentValue
                                                ),
                                            0
                                        );

                                const percentage =
                                    total > 0
                                        ? (
                                            (
                                                value /
                                                total
                                            ) *
                                            100
                                        ).toFixed(1)
                                        : "0.0";

                                return (
                                    `${label}: ` +
                                    `${value} ` +
                                    `(${percentage}%)`
                                );
                            }
                        }
                    }
                }
            }
        }
    );
}


/* =========================
   BAR CHART
========================= */

function createCountChart(
    labels,
    values,
    colors
) {
    const canvas =
        document.getElementById(
            "countChart"
        );

    if (!canvas) {
        console.error(
            "countChart canvas was not found."
        );

        return;
    }

    if (countChart) {
        countChart.destroy();
    }

    countChart = new Chart(
        canvas,
        {
            type: "bar",

            data: {
                labels: labels,

                datasets: [
                    {
                        label:
                            "Number of Predictions",

                        data:
                            values,

                        backgroundColor:
                            colors,

                        borderColor:
                            colors,

                        borderWidth:
                            1,

                        borderRadius:
                            8
                    }
                ]
            },

            options: {
                responsive:
                    true,

                maintainAspectRatio:
                    false,

                scales: {
                    y: {
                        beginAtZero:
                            true,

                        ticks: {
                            precision:
                                0,

                            stepSize:
                                1
                        }
                    }
                },

                plugins: {
                    legend: {
                        display:
                            false
                    }
                }
            }
        }
    );
}


/* =========================
   BACKEND HEALTH CHECK
========================= */

async function checkBackendStatus() {
    const statusElement =
        document.getElementById(
            "backendStatus"
        );

    const connectionText =
        document.getElementById(
            "connectionText"
        );

    try {
        const response = await fetch(
            `${API_BASE}/health`
        );

        if (!response.ok) {
            throw new Error(
                `Health request failed: ${response.status}`
            );
        }

        const data =
            await response.json();

        console.log(
            "Health response:",
            data
        );

        const healthy =
            String(
                data.status || ""
            ).toLowerCase() ===
            "healthy";

        if (statusElement) {
            statusElement.textContent =
                healthy
                    ? "Connected"
                    : "Unavailable";

            statusElement.classList.remove(
                "status-checking",
                "status-online",
                "status-offline"
            );

            statusElement.classList.add(
                healthy
                    ? "status-online"
                    : "status-offline"
            );
        }

        if (connectionText) {
            connectionText.textContent =
                healthy
                    ? (
                        `Backend connected. ` +
                        `Model: ${data.model}. ` +
                        `Database: ${data.database}.`
                    )
                    : (
                        "Backend returned " +
                        "an unhealthy status."
                    );
        }

    } catch (error) {
        console.error(
            "Health check failed:",
            error
        );

        if (statusElement) {
            statusElement.textContent =
                "Offline";

            statusElement.classList.remove(
                "status-checking",
                "status-online"
            );

            statusElement.classList.add(
                "status-offline"
            );
        }

        if (connectionText) {
            connectionText.textContent =
                "Unable to connect to the backend.";
        }
    }
}


/* =========================
   REFRESH BUTTON
========================= */

const refreshButton =
    document.getElementById(
        "refreshButton"
    );

if (refreshButton) {
    refreshButton.addEventListener(
        "click",
        async () => {
            const refreshIcon =
                document.getElementById(
                    "refreshIcon"
                );

            refreshButton.disabled =
                true;

            refreshButton.classList.add(
                "refreshing"
            );

            if (refreshIcon) {
                refreshIcon.textContent =
                    "↻";
            }

            await loadDashboard();

            refreshButton.disabled =
                false;

            refreshButton.classList.remove(
                "refreshing"
            );
        }
    );
}


/* =========================
   HELPER FUNCTIONS
========================= */

function setText(
    elementId,
    value
) {
    const element =
        document.getElementById(
            elementId
        );

    if (element) {
        element.textContent =
            value;
    }
}


function formatClassName(value) {
    if (!value) {
        return "No predictions";
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
   START DASHBOARD
========================= */

document.addEventListener(
    "DOMContentLoaded",
    loadDashboard
);
function animateNumber(
    elementId,
    finalValue,
    options = {}
) {
    const element =
        document.getElementById(
            elementId
        );

    if (!element) {
        return;
    }

    const duration =
        options.duration || 900;

    const decimals =
        options.decimals || 0;

    const suffix =
        options.suffix || "";

    const startTime =
        performance.now();

    const numericValue =
        Number(finalValue) || 0;

    function updateNumber(
        currentTime
    ) {
        const elapsed =
            currentTime - startTime;

        const progress =
            Math.min(
                elapsed / duration,
                1
            );

        const easedProgress =
            1 - Math.pow(
                1 - progress,
                3
            );

        const currentValue =
            numericValue *
            easedProgress;

        element.textContent =
            `${currentValue.toFixed(
                decimals
            )}${suffix}`;

        if (progress < 1) {
            requestAnimationFrame(
                updateNumber
            );
        }
    }

    requestAnimationFrame(
        updateNumber
    );
}