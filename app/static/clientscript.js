document.addEventListener("DOMContentLoaded", async () => {
    const apiUrl = "https://v3.dandsappliances.com/index.php?r=api%2Fclients-list";
    const loader = document.getElementById("loader");
    const tableBody = document.querySelector("#clientTable tbody");
    const searchInput = document.getElementById("searchInput");
    const pagination = document.getElementById("pagination");

    let currentPage = 1;
    const rowsPerPage = 10;
    let clientData = [];

    async function fetchData() {
        try {
            loader.style.display = "block";
            const response = await fetch(apiUrl, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            loader.style.display = "none";

            clientData = data || [];
            renderTable(clientData, currentPage, rowsPerPage);
            setupPagination(clientData.length);
        } catch (error) {
            loader.style.display = "none";
            tableBody.innerHTML = `<tr>
                <td colspan="3" style="text-align: center; color: red;">Failed to load data: ${error.message}</td>
            </tr>`;
            console.error("Error fetching client data:", error);
        }
    }

    function renderTable(data, page, rows) {
        tableBody.innerHTML = "";
        const start = (page - 1) * rows;
        const end = start + rows;
        const paginatedData = data.slice(start, end);

        if (paginatedData.length === 0) {
            tableBody.innerHTML = `<tr>
                <td colspan="3" style="text-align: center;">No data available</td>
            </tr>`;
            return;
        }

        paginatedData.forEach((client) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${client.id || "N/A"}</td>
                <td>${client.clientname || "N/A"}</td>
                <td>${client.commission || "N/A"}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    function setupPagination(totalRows) {
        pagination.innerHTML = "";
        const totalPages = Math.ceil(totalRows / rowsPerPage);

        for (let i = 1; i <= totalPages; i++) {
            const pageButton = document.createElement("button");
            pageButton.textContent = i;
            pageButton.style.margin = "0 5px";
            pageButton.className = i === currentPage ? "active" : "";

            pageButton.addEventListener("click", () => {
                currentPage = i;
                renderTable(clientData, currentPage, rowsPerPage);
                updatePaginationButtons(totalPages);
            });

            pagination.appendChild(pageButton);
        }
    }

    function updatePaginationButtons(totalPages) {
        const buttons = pagination.querySelectorAll("button");
        buttons.forEach((button, index) => {
            button.className = index + 1 === currentPage ? "active" : "";
        });
    }

    searchInput.addEventListener("input", () => {
        const searchTerm = searchInput.value.toLowerCase();
        const filteredData = clientData.filter((client) =>
            client.clientname.toLowerCase().includes(searchTerm)
        );
        currentPage = 1; // Reset to first page on search
        renderTable(filteredData, currentPage, rowsPerPage);
        setupPagination(filteredData.length);
    });

    // Fetch and initialize data
    fetchData();
});
