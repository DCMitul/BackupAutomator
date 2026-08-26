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
        // JOBS
        // =========================================================

        const jobs = document.querySelector(".jobs");

        // Remove the placeholder content
        jobs.innerHTML = "";


        // ---------------------------------------------------------
        // NO JOBS
        // ---------------------------------------------------------

        if (data.jobs.length === 0) {

            const noJobs = document.createElement("p");

            noJobs.className = "nojob";
            noJobs.textContent = "No Backup Jobs Found.";

            jobs.appendChild(noJobs);

            return;
        }


        // =========================================================
        // CREATE A CARD FOR EVERY JOB
        // =========================================================

        data.jobs.forEach(job => {

            // -----------------------------------------------------
            // CARD
            // -----------------------------------------------------

            const card = document.createElement("div");

            card.className = "job-card";


            // -----------------------------------------------------
            // HEADER
            // -----------------------------------------------------

            const header = document.createElement("div");

            header.className = "job-card-header";


            // Job ID

            const jobId = document.createElement("p");

            jobId.className = "job-id";
            jobId.textContent = "Job Id: " + job.job_id;


            // Buttons container

            const actions = document.createElement("div");

            actions.className = "job-actions";


            // Edit button

            const editButton = document.createElement("button");

            editButton.className = "job-edit";
            editButton.type = "button";


            const editIcon = document.createElement("img");

            editIcon.src = "/gui/assets/Edit icon.svg";
            editIcon.alt = "Edit";


            editButton.appendChild(editIcon);


            // Delete button

            const deleteButton = document.createElement("button");

            deleteButton.className = "job-delete";
            deleteButton.type = "button";


            const deleteIcon = document.createElement("img");

            deleteIcon.src = "/gui/assets/Delete icon.svg";
            deleteIcon.alt = "Delete";


            deleteButton.appendChild(deleteIcon);


            // Put buttons together

            actions.appendChild(editButton);
            actions.appendChild(deleteButton);


            // Put header together

            header.appendChild(jobId);
            header.appendChild(actions);


            // -----------------------------------------------------
            // SEPARATOR
            // -----------------------------------------------------

            const separator = document.createElement("div");

            separator.className = "job-separator";


            // -----------------------------------------------------
            // INFORMATION CONTAINER
            // -----------------------------------------------------

            const info = document.createElement("div");

            info.className = "job-info";


            // -----------------------------------------------------
            // HELPER FOR INFORMATION ITEMS
            // -----------------------------------------------------

            function addInfo(title, value, iconPath) {

                const item = document.createElement("div");

                item.className = "job-info-item";


                // Icon box

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


            // -----------------------------------------------------
            // EXCEPTIONS
            // -----------------------------------------------------

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


            // -----------------------------------------------------
            // ADD JOB INFORMATION
            // -----------------------------------------------------

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


            // -----------------------------------------------------
            // PUT CARD TOGETHER
            // -----------------------------------------------------

            card.appendChild(header);
            card.appendChild(separator);
            card.appendChild(info);


            // Add card to page

            jobs.appendChild(card);

        });

    })
    .catch(error => {
        console.error("Failed to get initial data:", error);
    });