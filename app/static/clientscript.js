document.addEventListener("DOMContentLoaded", () => {
    const apiUrl = "https://v3.dandsappliances.com/index.php?r=api%2Fclients-list";
    const createApiUrl = "https://v3.dandsappliances.com/index.php?r=api/clients";
    const loader = document.getElementById("loader");
    const tableBody = document.querySelector("#clientTable tbody");
    const searchInput = document.getElementById("searchInput");
    const pagination = document.getElementById("pagination");
    const createButton = document.getElementById("createButton");
    const popupOverlay = document.getElementById("popupOverlay");
    const submitButton = document.getElementById("submitButton");
    const closeButton = document.getElementById("closeButton");
    const companyNameInput = document.getElementById("companyName");
    const commissionInput = document.getElementById("commission");

    let currentPage = 1;
    const rowsPerPage = 10;
    let clientData = [];

    // Show popup
    createButton.addEventListener("click", () => {
        popupOverlay.style.display = "flex";
    });

    // Hide popup
    closeButton.addEventListener("click", () => {
        popupOverlay.style.display = "none";
        clearForm();
    });

    // Submit new client
    submitButton.addEventListener("click", async () => {
        const companyName = companyNameInput.value.trim();
        const commission = commissionInput.value.trim();

        if (!companyName || !commission) {
            alert("Please fill in all fields!");
            return;
        }

        try {
            const response = await fetch(createApiUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ company_name: companyName, commission }),
            });

            if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
            alert("Client created successfully!");
            popupOverlay.style.display = "none";
            clearForm();
            fetchData();
        } catch (error) {
            alert("Failed to create client: " + error.message);
        }
    });

    function clearForm() {
        companyNameInput.value = "";
        commissionInput.value = "";
    }

    async function fetchData() {
        try {
            loader.style.display = "block";
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

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
            tableBody.innerHTML = `<tr><td colspan="3" style="text-align: center;">No data available</td></tr>`;
            return;
        }

        paginatedData.forEach(client => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${client.id}</td>
                <td>${client.clientname}</td>
                <td>${client.commission}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    function setupPagination(totalRows) {
        pagination.innerHTML = "";
        const totalPages = Math.ceil(totalRows / rowsPerPage);

        for (let i = 1; i <= totalPages; i++) {
            const button = document.createElement("button");
            button.textContent = i;
            button.classList.toggle("active", i === currentPage);
            button.addEventListener("click", () => {
                currentPage = i;
                renderTable(clientData, currentPage, rowsPerPage);
            });
            pagination.appendChild(button);
        }
    }

    searchInput.addEventListener("input", () => {
        const searchValue = searchInput.value.toLowerCase();
        const filteredData = clientData.filter(client =>
            client.company_name.toLowerCase().includes(searchValue)
        );
        renderTable(filteredData, 1, rowsPerPage);
    });

    fetchData();
});
