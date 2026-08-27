fetch("/api/initial-data")
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        return response.json();
    })
    .then(data => {

        console.log("Initial data:", data);


        // =========================================================
        // FOOTER
        // =========================================================

        document.querySelector(".ver").textContent =
            "Version: " + data.version;

        document.querySelector(".store").textContent =
            data.storage + "% of backup drive full";

        document.querySelector(".total").textContent =
            "Total Jobs: " + data.jobs.length;


        // =========================================================
        // DISPLAY JOBS
        // =========================================================

        function renderJobs(jobList) {

            const jobs = document.querySelector(".jobs");

            // Clear current jobs
            jobs.innerHTML = "";


            // No jobs to display
            if (jobList.length === 0) {
                return;
            }


            // Create a card for every job
            jobList.forEach(job => {

                // -------------------------------------------------
                // CARD
                // -------------------------------------------------

                const card = document.createElement("div");
                card.className = "job-card";


                // -------------------------------------------------
                // HEADER
                // -------------------------------------------------

                const header = document.createElement("div");
                header.className = "job-card-header";


                // Job ID
                const jobId = document.createElement("p");
                jobId.className = "job-id";
                jobId.textContent = "Job Id: " + job.job_id;


                // Buttons container
                const actions = document.createElement("div");
                actions.className = "job-actions";


                // -------------------------------------------------
                // EDIT BUTTON
                // -------------------------------------------------

                const editButton = document.createElement("button");

                editButton.className = "job-edit";
                editButton.type = "button";


                const editIcon = document.createElement("img");

                editIcon.src = "/gui/assets/Edit icon.svg";
                editIcon.alt = "Edit";


                editButton.appendChild(editIcon);


                // -------------------------------------------------
                // DELETE BUTTON
                // -------------------------------------------------

                const deleteButton = document.createElement("button");

                deleteButton.className = "job-delete";
                deleteButton.type = "button";


                const deleteIcon = document.createElement("img");

                deleteIcon.src = "/gui/assets/Delete icon.svg";
                deleteIcon.alt = "Delete";


                deleteButton.appendChild(deleteIcon);


                // Add buttons to actions
                actions.appendChild(editButton);
                actions.appendChild(deleteButton);


                // Add ID and actions to header
                header.appendChild(jobId);
                header.appendChild(actions);


                // -------------------------------------------------
                // SEPARATOR
                // -------------------------------------------------

                const separator = document.createElement("div");

                separator.className = "job-separator";


                // -------------------------------------------------
                // JOB INFORMATION
                // -------------------------------------------------

                const info = document.createElement("div");

                info.className = "job-info";


                // Helper function for information items
                function addInfo(title, value, iconPath) {

                    const item = document.createElement("div");

                    item.className = "job-info-item";


                    // Icon
                    const iconBox = document.createElement("div");

                    iconBox.className = "job-icon";


                    const icon = document.createElement("img");

                    icon.className = "job-icon-image";
                    icon.src = iconPath;
                    icon.alt = "";


                    iconBox.appendChild(icon);


                    // Text
                    const text = document.createElement("div");

                    text.className = "job-info-text";


                    const titleElement = document.createElement("p");

                    titleElement.className = "job-info-title";
                    titleElement.textContent = title;


                    const valueElement = document.createElement("p");

                    valueElement.className = "job-info-value";
                    valueElement.textContent = value;


                    text.appendChild(titleElement);
                    text.appendChild(valueElement);


                    // Put item together
                    item.appendChild(iconBox);
                    item.appendChild(text);

                    info.appendChild(item);
                }


                // -------------------------------------------------
                // EXCEPTIONS
                // -------------------------------------------------

                let exceptions = [];

                try {
                    exceptions = JSON.parse(job.exceptions);
                }
                catch {
                    exceptions = [];
                }


                const exceptionText =
                    exceptions.length > 0
                        ? exceptions.join(", ")
                        : "None";


                // -------------------------------------------------
                // ADD INFORMATION
                // -------------------------------------------------

                addInfo(
                    "Source",
                    job.source,
                    "/gui/assets/Folder Icon.svg"
                );


                addInfo(
                    "Destination",
                    job.destination,
                    "/gui/assets/Folder Icon.svg"
                );


                addInfo(
                    "Time Period",
                    job.time,
                    "/gui/assets/Clock icon.svg"
                );


                addInfo(
                    "Exceptions",
                    exceptionText,
                    "/gui/assets/Exceptions icon.svg"
                );


                addInfo(
                    "Archiving",
                    job.zip,
                    "/gui/assets/Archive icon.svg"
                );


                // -------------------------------------------------
                // BUILD CARD
                // -------------------------------------------------

                card.appendChild(header);
                card.appendChild(separator);
                card.appendChild(info);


                // Add card to page
                jobs.appendChild(card);

            });
        }


        // Display all jobs when the page first loads
        renderJobs(data.jobs);


        // =========================================================
        // JOB ID SEARCH
        // =========================================================

        const jobSearch = document.querySelector("#job-id-search");


        // Only allow numbers
        jobSearch.addEventListener("input", () => {

            jobSearch.value =
                jobSearch.value.replace(/\D/g, "");

        });


        // Search when Enter is pressed
        jobSearch.addEventListener("keydown", event => {

            if (event.key !== "Enter") {
                return;
            }


            // Empty search → restore all jobs
            if (jobSearch.value === "") {

                renderJobs(data.jobs);

                return;
            }


            const id = Number(jobSearch.value);


            // Find matching job
            const matchingJob = data.jobs.find(
                job => job.job_id === id
            );


            // Job found → show only that job
            if (matchingJob) {

                renderJobs([matchingJob]);

            }

            // Job not found → show nothing
            else {

                renderJobs([]);

            }

        });

    })
    .catch(error => {

        console.error(
            "Failed to get initial data:",
            error
        );

    });